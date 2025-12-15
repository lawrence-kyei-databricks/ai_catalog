"""
CarMax Data Classification Platform - Flask API
Simple, clean backend for classification workflow
"""

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from werkzeug.utils import secure_filename
import os
import json
import tempfile

from .taxonomy_manager import TaxonomyManager
from .classification_engine import ClassificationEngine
from .init_taxonomy import init_taxonomy

app = Flask(__name__, static_folder='../static', template_folder='templates')
CORS(app)

# Configuration
WAREHOUSE_ID = os.environ.get('WAREHOUSE_ID')
TARGET_CATALOG = os.environ.get('TARGET_CATALOG', 'main')

# Initialize Databricks client
w = WorkspaceClient()

# Initialize services with warehouse_id
taxonomy_mgr = TaxonomyManager(w, warehouse_id=WAREHOUSE_ID)
classifier = ClassificationEngine(w, taxonomy_mgr)

# Auto-initialize taxonomy on startup
try:
    print("Checking taxonomy initialization...")
    init_result = init_taxonomy(warehouse_id=WAREHOUSE_ID)
    print(f"Taxonomy initialization result: {init_result}")
except Exception as e:
    print(f"Warning: Could not auto-initialize taxonomy: {e}")
    print("You can manually import using /api/taxonomy/import endpoint")

# ========================================
# MAIN APP PAGE
# ========================================

@app.route('/', methods=['GET'])
def home():
    """Serve unified app interface"""
    return render_template('app.html')


# ========================================
# TAXONOMY ENDPOINTS
# ========================================

@app.route('/api/taxonomy/import', methods=['POST'])
def import_taxonomy():
    """Import taxonomy from Excel files"""
    try:
        # Get file paths from request
        elements_file = request.json.get('elements_file')
        subjects_file = request.json.get('subjects_file')
        version = request.json.get('version', '1.0')

        # Import
        result = taxonomy_mgr.import_from_excel(elements_file, subjects_file, version)

        return jsonify({'success': True, **result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/taxonomy', methods=['GET'])
def get_taxonomy():
    """Get current active taxonomy"""
    try:
        taxonomy = taxonomy_mgr.get_active_taxonomy()
        return jsonify(taxonomy)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# ADMIN ENDPOINTS
# ========================================

@app.route('/api/admin/taxonomy-status', methods=['GET'])
def taxonomy_status():
    """Check if taxonomy is initialized"""
    try:
        check_sql = "SELECT COUNT(*) as cnt FROM main.carmax_taxonomy.data_elements"
        result = _execute_sql(check_sql)

        if result and len(result) > 0:
            element_count = result[0]['cnt'] if isinstance(result[0], dict) else result[0][0]
            element_count = int(element_count)  # Convert to int (SQL results sometimes return strings)

            if element_count > 0:
                # Get additional stats
                tags_sql = "SELECT COUNT(*) as cnt FROM main.carmax_taxonomy.data_elements WHERE active = true"
                tags_result = _execute_sql(tags_sql)
                tags_count = int(tags_result[0]['cnt']) if tags_result and len(tags_result) > 0 else 0

                subjects_sql = "SELECT COUNT(*) as cnt FROM main.carmax_taxonomy.subject_types"
                subjects_result = _execute_sql(subjects_sql)
                subjects_count = int(subjects_result[0]['cnt']) if subjects_result and len(subjects_result) > 0 else 0

                return jsonify({
                    'initialized': True,
                    'stats': {
                        'elements': element_count,
                        'tags': tags_count,
                        'subjects': subjects_count
                    }
                })

        return jsonify({'initialized': False})

    except Exception as e:
        return jsonify({'initialized': False, 'error': str(e)})


@app.route('/api/admin/import-taxonomy', methods=['POST'])
def admin_import_taxonomy():
    """Handle file upload and import taxonomy"""
    try:
        # Check if files were uploaded
        if 'elements_file' not in request.files or 'subjects_file' not in request.files:
            return jsonify({'success': False, 'error': 'Both files are required'}), 400

        elements_file = request.files['elements_file']
        subjects_file = request.files['subjects_file']
        version = request.form.get('version', '1.0')

        # Validate files
        if elements_file.filename == '' or subjects_file.filename == '':
            return jsonify({'success': False, 'error': 'No files selected'}), 400

        # Save files temporarily
        with tempfile.TemporaryDirectory() as tmpdir:
            elements_path = os.path.join(tmpdir, secure_filename(elements_file.filename))
            subjects_path = os.path.join(tmpdir, secure_filename(subjects_file.filename))

            elements_file.save(elements_path)
            subjects_file.save(subjects_path)

            # Import taxonomy
            result = taxonomy_mgr.import_from_excel(elements_path, subjects_path, version)

            return jsonify({'success': True, **result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# CATALOG/SCHEMA ENDPOINTS
# ========================================

@app.route('/api/catalogs', methods=['GET'])
def list_catalogs():
    """List accessible catalogs"""
    try:
        catalogs = [c.name for c in w.catalogs.list()]
        return jsonify({'catalogs': catalogs})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/schemas', methods=['GET'])
def list_schemas():
    """List schemas in catalog"""
    try:
        catalog = request.args.get('catalog', TARGET_CATALOG)
        schemas = [s.name for s in w.schemas.list(catalog_name=catalog)]
        return jsonify({'schemas': schemas})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# CLASSIFICATION ENDPOINTS
# ========================================

@app.route('/api/classify', methods=['POST'])
def classify_columns():
    """Classify columns in a schema"""
    try:
        catalog = request.json.get('catalog', TARGET_CATALOG)
        schema = request.json.get('schema')

        if not schema:
            return jsonify({'error': 'Schema required'}), 400

        # Get columns to classify
        columns = _get_unclassified_columns(catalog, schema)

        # Classify each column
        results = []
        for col in columns[:100]:  # Limit to 100 for now
            try:
                result = classifier.classify_column(
                    col['catalog'],
                    col['schema'],
                    col['table'],
                    col['column']
                )
                results.append({
                    'column': f"{col['table']}.{col['column']}",
                    'status': 'success',
                    **result
                })
            except Exception as e:
                results.append({
                    'column': f"{col['table']}.{col['column']}",
                    'status': 'error',
                    'error': str(e)
                })

        return jsonify({
            'total': len(columns),
            'processed': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications', methods=['GET'])
def get_classifications():
    """Get classifications with optional filters"""
    try:
        status = request.args.get('status', 'PENDING')
        priority = request.args.get('priority')
        limit = int(request.args.get('limit', 100))

        # Build query
        where_clauses = [f"review_status = '{status}'"]

        if priority:
            where_clauses.append(f"review_priority = '{priority}'")

        if status == 'PENDING':
            where_clauses.append("requires_review = TRUE")

        where_clause = ' AND '.join(where_clauses)

        sql = f"""
        SELECT
            id,
            catalog_name,
            schema_name,
            table_name,
            column_name,
            column_type,
            suggested_element,
            suggested_category,
            confidence_score,
            sensitive_flag,
            data_subjects,
            review_priority,
            reasoning,
            sample_values,
            created_at
        FROM main.carmax_governance.classification_governance
        WHERE {where_clause}
        ORDER BY
            CASE review_priority
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
            END,
            created_at DESC
        LIMIT {limit}
        """

        results = _execute_sql(sql)

        return jsonify({
            'count': len(results),
            'items': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications/<int:id>/approve', methods=['POST'])
def approve_classification(id):
    """Approve a classification"""
    try:
        notes = request.json.get('notes', '')

        sql = f"""
        UPDATE main.carmax_governance.classification_governance
        SET
            review_status = 'APPROVED',
            approved_element = suggested_element,
            reviewer = current_user(),
            reviewed_at = current_timestamp(),
            review_notes = '{notes.replace("'", "''")}'
        WHERE id = {id}
        """

        _execute_sql(sql)

        return jsonify({'success': True, 'id': id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications/<int:id>/reject', methods=['POST'])
def reject_classification(id):
    """Reject a classification"""
    try:
        reason = request.json.get('reason', '')

        sql = f"""
        UPDATE main.carmax_governance.classification_governance
        SET
            review_status = 'REJECTED',
            reviewer = current_user(),
            reviewed_at = current_timestamp(),
            review_notes = '{reason.replace("'", "''")}'
        WHERE id = {id}
        """

        _execute_sql(sql)

        return jsonify({'success': True, 'id': id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications/bulk-approve', methods=['POST'])
def bulk_approve():
    """Bulk approve classifications"""
    try:
        min_confidence = request.json.get('min_confidence', 80)
        exclude_sensitive = request.json.get('exclude_sensitive', False)

        conditions = ["review_status = 'PENDING'"]
        conditions.append(f"confidence_score >= {min_confidence}")

        if exclude_sensitive:
            conditions.append("sensitive_flag = FALSE")

        where_clause = ' AND '.join(conditions)

        sql = f"""
        UPDATE main.carmax_governance.classification_governance
        SET
            review_status = 'APPROVED',
            approved_element = suggested_element,
            reviewer = current_user(),
            reviewed_at = current_timestamp(),
            review_notes = 'Bulk approved (confidence >= {min_confidence}%)'
        WHERE {where_clause}
        """

        result = _execute_sql(sql)

        return jsonify({
            'success': True,
            'approved_count': result.get('rows_affected', 0)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# TAG APPLICATION
# ========================================

@app.route('/api/apply-tags', methods=['POST'])
def apply_tags():
    """Apply approved classifications as UC tags"""
    try:
        # Get approved classifications
        sql = """
        SELECT
            catalog_name,
            schema_name,
            table_name,
            column_name,
            COALESCE(approved_element, suggested_element) as element
        FROM main.carmax_governance.classification_governance
        WHERE review_status IN ('APPROVED', 'AUTO_APPROVED')
          AND applied_at IS NULL
        LIMIT 100
        """

        classifications = _execute_sql(sql)

        applied = 0
        errors = []

        for item in classifications:
            try:
                # Get element_id for tag
                element_id = _generate_element_id(item['element'])

                # Apply tag to column
                tag_sql = f"""
                ALTER TABLE `{item['catalog_name']}`.`{item['schema_name']}`.`{item['table_name']}`
                ALTER COLUMN `{item['column_name']}`
                SET TAGS ('main.carmax_tags.`{element_id}`' = 'CLASSIFIED')
                """

                _execute_sql(tag_sql)

                # Mark as applied
                update_sql = f"""
                UPDATE main.carmax_governance.classification_governance
                SET
                    review_status = 'APPLIED',
                    applied_at = current_timestamp()
                WHERE catalog_name = '{item['catalog_name']}'
                  AND schema_name = '{item['schema_name']}'
                  AND table_name = '{item['table_name']}'
                  AND column_name = '{item['column_name']}'
                """

                _execute_sql(update_sql)

                applied += 1

            except Exception as e:
                errors.append({
                    'column': f"{item['catalog_name']}.{item['schema_name']}.{item['table_name']}.{item['column_name']}",
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'applied': applied,
            'total': len(classifications),
            'errors': errors
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# DASHBOARD STATS
# ========================================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats_sql = """
        SELECT
            COUNT(*) as total_classified,
            COUNT(CASE WHEN review_status = 'PENDING' THEN 1 END) as pending_review,
            COUNT(CASE WHEN review_status IN ('APPROVED', 'AUTO_APPROVED') THEN 1 END) as approved,
            COUNT(CASE WHEN review_status = 'APPLIED' THEN 1 END) as applied,
            COUNT(CASE WHEN sensitive_flag = TRUE THEN 1 END) as sensitive_count,
            AVG(confidence_score) as avg_confidence
        FROM main.carmax_governance.classification_governance
        """

        stats = _execute_sql(stats_sql)[0]

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# STATIC FILES (React App)
# ========================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve React app"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ========================================
# HELPER FUNCTIONS
# ========================================

def _get_unclassified_columns(catalog, schema):
    """Get columns that haven't been classified yet"""
    sql = f"""
    SELECT
        c.table_catalog as catalog,
        c.table_schema as schema,
        c.table_name as table,
        c.column_name as column
    FROM system.information_schema.columns c
    LEFT JOIN main.carmax_governance.classification_governance g
        ON c.table_catalog = g.catalog_name
        AND c.table_schema = g.schema_name
        AND c.table_name = g.table_name
        AND c.column_name = g.column_name
    WHERE c.table_catalog = '{catalog}'
      AND c.table_schema = '{schema}'
      AND g.id IS NULL
      AND c.column_name NOT IN ('_rescued_data', '_metadata')
    ORDER BY c.table_name, c.ordinal_position
    """

    return _execute_sql(sql)


def _execute_sql(sql):
    """Execute SQL using Databricks SDK"""
    statement = w.statement_execution.execute_statement(
        statement=sql,
        warehouse_id=WAREHOUSE_ID,
        wait_timeout="50s"
    )

    import time
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state != StatementState.SUCCEEDED:
        raise Exception(f"Query failed: {statement.status.error}")

    if hasattr(statement, 'result') and statement.result:
        columns = [col.name for col in statement.manifest.schema.columns] if statement.manifest else []
        data_array = statement.result.data_array if statement.result.data_array else []
        return [dict(zip(columns, row)) for row in data_array]

    return []


def _generate_element_id(element_name):
    """Convert element name to tag ID"""
    import re
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', element_name)
    return clean_name.lower().replace(' ', '_').replace('__', '_').strip('_')


# ========================================
# RUN APP
# ========================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
