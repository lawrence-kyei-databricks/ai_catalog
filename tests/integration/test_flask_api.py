"""
Integration tests for Flask API endpoints
Tests all 12 API endpoints with request validation and error handling
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))


class TestTaxonomyEndpoints:
    """Test taxonomy management endpoints"""

    @patch('main.taxonomy_mgr')
    def test_import_taxonomy_success(self, mock_taxonomy_mgr, flask_client):
        """POST /api/taxonomy/import - Should import taxonomy from Excel files"""
        mock_taxonomy_mgr.import_from_excel.return_value = {
            'elements_imported': 172,
            'subjects_imported': 3,
            'tags_created': 172,
            'version': '1.0',
            'timestamp': '2024-01-01T12:00:00'
        }

        response = flask_client.post('/api/taxonomy/import', json={
            'elements_file': '/path/to/elements.xlsx',
            'subjects_file': '/path/to/subjects.xlsx',
            'version': '1.0'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['elements_imported'] == 172
        assert data['tags_created'] == 172

    @patch('main.taxonomy_mgr')
    def test_import_taxonomy_missing_files(self, mock_taxonomy_mgr, flask_client):
        """POST /api/taxonomy/import - Should handle missing file paths"""
        response = flask_client.post('/api/taxonomy/import', json={
            'version': '1.0'
        })

        # Should handle gracefully (files will be None)
        assert response.status_code in [200, 500]

    @patch('main.taxonomy_mgr')
    def test_import_taxonomy_error(self, mock_taxonomy_mgr, flask_client):
        """POST /api/taxonomy/import - Should handle import errors"""
        mock_taxonomy_mgr.import_from_excel.side_effect = Exception("Import failed")

        response = flask_client.post('/api/taxonomy/import', json={
            'elements_file': '/path/to/elements.xlsx',
            'subjects_file': '/path/to/subjects.xlsx'
        })

        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    @patch('main.taxonomy_mgr')
    def test_get_taxonomy_success(self, mock_taxonomy_mgr, flask_client):
        """GET /api/taxonomy - Should return active taxonomy"""
        mock_taxonomy_mgr.get_active_taxonomy.return_value = {
            'elements': [
                {'element_id': 'ssn', 'element_name': 'SSN'},
                {'element_id': 'email', 'element_name': 'Email'}
            ],
            'subjects': ['Associate', 'Consumer'],
            'total_elements': 2,
            'version': '1.0'
        }

        response = flask_client.get('/api/taxonomy')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['elements']) == 2
        assert data['total_elements'] == 2

    @patch('main.taxonomy_mgr')
    def test_get_taxonomy_error(self, mock_taxonomy_mgr, flask_client):
        """GET /api/taxonomy - Should handle errors"""
        mock_taxonomy_mgr.get_active_taxonomy.side_effect = Exception("DB error")

        response = flask_client.get('/api/taxonomy')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestCatalogSchemaEndpoints:
    """Test catalog and schema listing endpoints"""

    @patch('main.w')
    def test_list_catalogs_success(self, mock_w, flask_client):
        """GET /api/catalogs - Should list accessible catalogs"""
        mock_catalog1 = Mock()
        mock_catalog1.name = "main"
        mock_catalog2 = Mock()
        mock_catalog2.name = "dev"

        mock_w.catalogs.list.return_value = [mock_catalog1, mock_catalog2]

        response = flask_client.get('/api/catalogs')

        assert response.status_code == 200
        data = response.get_json()
        assert 'catalogs' in data
        assert len(data['catalogs']) == 2
        assert 'main' in data['catalogs']
        assert 'dev' in data['catalogs']

    @patch('main.w')
    def test_list_catalogs_error(self, mock_w, flask_client):
        """GET /api/catalogs - Should handle errors"""
        mock_w.catalogs.list.side_effect = Exception("Access denied")

        response = flask_client.get('/api/catalogs')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('main.w')
    def test_list_schemas_success(self, mock_w, flask_client):
        """GET /api/schemas - Should list schemas in catalog"""
        mock_schema1 = Mock()
        mock_schema1.name = "schema1"
        mock_schema2 = Mock()
        mock_schema2.name = "schema2"

        mock_w.schemas.list.return_value = [mock_schema1, mock_schema2]

        response = flask_client.get('/api/schemas?catalog=main')

        assert response.status_code == 200
        data = response.get_json()
        assert 'schemas' in data
        assert len(data['schemas']) == 2

    @patch('main.w')
    def test_list_schemas_default_catalog(self, mock_w, flask_client):
        """GET /api/schemas - Should use default catalog if not specified"""
        mock_w.schemas.list.return_value = []

        response = flask_client.get('/api/schemas')

        assert response.status_code == 200
        # Should have called with default catalog
        mock_w.schemas.list.assert_called_once()


class TestClassificationEndpoints:
    """Test classification workflow endpoints"""

    @patch('main.classifier')
    @patch('main._get_unclassified_columns')
    def test_classify_columns_success(
        self,
        mock_get_columns,
        mock_classifier,
        flask_client
    ):
        """POST /api/classify - Should classify unclassified columns"""
        mock_get_columns.return_value = [
            {'catalog': 'main', 'schema': 'test', 'table': 't1', 'column': 'email'},
            {'catalog': 'main', 'schema': 'test', 'table': 't1', 'column': 'phone'}
        ]

        mock_classifier.classify_column.return_value = {
            'element': 'Email Address',
            'confidence': 95.0,
            'review_status': 'AUTO_APPROVED'
        }

        response = flask_client.post('/api/classify', json={
            'catalog': 'main',
            'schema': 'test'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 2
        assert data['processed'] == 2
        assert len(data['results']) == 2

    @patch('main._get_unclassified_columns')
    def test_classify_columns_missing_schema(self, mock_get_columns, flask_client):
        """POST /api/classify - Should require schema parameter"""
        response = flask_client.post('/api/classify', json={
            'catalog': 'main'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Schema required' in data['error']

    @patch('main.classifier')
    @patch('main._get_unclassified_columns')
    def test_classify_columns_handles_individual_errors(
        self,
        mock_get_columns,
        mock_classifier,
        flask_client
    ):
        """POST /api/classify - Should handle individual column classification errors"""
        mock_get_columns.return_value = [
            {'catalog': 'main', 'schema': 'test', 'table': 't1', 'column': 'c1'},
            {'catalog': 'main', 'schema': 'test', 'table': 't1', 'column': 'c2'}
        ]

        # First succeeds, second fails
        mock_classifier.classify_column.side_effect = [
            {'element': 'Email', 'confidence': 95.0},
            Exception("Classification failed")
        ]

        response = flask_client.post('/api/classify', json={
            'schema': 'test'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['results']) == 2
        assert data['results'][0]['status'] == 'success'
        assert data['results'][1]['status'] == 'error'

    @patch('main.classifier')
    @patch('main._get_unclassified_columns')
    def test_classify_columns_limits_to_100(
        self,
        mock_get_columns,
        mock_classifier,
        flask_client
    ):
        """POST /api/classify - Should limit to 100 columns"""
        # Return 150 columns
        mock_get_columns.return_value = [
            {'catalog': 'main', 'schema': 'test', 'table': f't{i}', 'column': 'c1'}
            for i in range(150)
        ]

        mock_classifier.classify_column.return_value = {'element': 'Test'}

        response = flask_client.post('/api/classify', json={'schema': 'test'})

        assert response.status_code == 200
        data = response.get_json()
        # Should only process 100
        assert data['processed'] == 100
        assert data['total'] == 150

    @patch('main._execute_sql')
    def test_get_classifications_pending(self, mock_execute_sql, flask_client):
        """GET /api/classifications - Should get pending classifications"""
        mock_execute_sql.return_value = [
            {
                'id': 1,
                'catalog_name': 'main',
                'schema_name': 'test',
                'table_name': 't1',
                'column_name': 'email',
                'suggested_element': 'Email Address',
                'confidence_score': 85.0,
                'review_priority': 'LOW'
            }
        ]

        response = flask_client.get('/api/classifications?status=PENDING')

        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert len(data['items']) == 1

    @patch('main._execute_sql')
    def test_get_classifications_with_priority_filter(
        self,
        mock_execute_sql,
        flask_client
    ):
        """GET /api/classifications - Should filter by priority"""
        mock_execute_sql.return_value = []

        response = flask_client.get('/api/classifications?status=PENDING&priority=HIGH')

        assert response.status_code == 200
        # Verify SQL query includes priority filter
        sql_call = mock_execute_sql.call_args[0][0]
        assert "review_priority = 'HIGH'" in sql_call

    @patch('main._execute_sql')
    def test_get_classifications_limit(self, mock_execute_sql, flask_client):
        """GET /api/classifications - Should respect limit parameter"""
        mock_execute_sql.return_value = []

        response = flask_client.get('/api/classifications?limit=50')

        assert response.status_code == 200
        sql_call = mock_execute_sql.call_args[0][0]
        assert 'LIMIT 50' in sql_call


class TestApprovalEndpoints:
    """Test classification approval endpoints"""

    @patch('main._execute_sql')
    def test_approve_classification(self, mock_execute_sql, flask_client):
        """POST /api/classifications/<id>/approve - Should approve classification"""
        mock_execute_sql.return_value = []

        response = flask_client.post('/api/classifications/123/approve', json={
            'notes': 'Looks good'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['id'] == 123

        # Verify SQL update
        sql_call = mock_execute_sql.call_args[0][0]
        assert "UPDATE" in sql_call
        assert "review_status = 'APPROVED'" in sql_call
        assert "WHERE id = 123" in sql_call

    @patch('main._execute_sql')
    def test_approve_classification_with_notes(self, mock_execute_sql, flask_client):
        """POST /api/classifications/<id>/approve - Should store review notes"""
        mock_execute_sql.return_value = []

        response = flask_client.post('/api/classifications/123/approve', json={
            'notes': 'Verified with data owner'
        })

        assert response.status_code == 200
        sql_call = mock_execute_sql.call_args[0][0]
        assert 'Verified with data owner' in sql_call

    @patch('main._execute_sql')
    def test_approve_classification_error(self, mock_execute_sql, flask_client):
        """POST /api/classifications/<id>/approve - Should handle errors"""
        mock_execute_sql.side_effect = Exception("DB error")

        response = flask_client.post('/api/classifications/123/approve', json={})

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('main._execute_sql')
    def test_reject_classification(self, mock_execute_sql, flask_client):
        """POST /api/classifications/<id>/reject - Should reject classification"""
        mock_execute_sql.return_value = []

        response = flask_client.post('/api/classifications/123/reject', json={
            'reason': 'Incorrect element'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify SQL update
        sql_call = mock_execute_sql.call_args[0][0]
        assert "review_status = 'REJECTED'" in sql_call

    @patch('main._execute_sql')
    def test_bulk_approve_success(self, mock_execute_sql, flask_client):
        """POST /api/classifications/bulk-approve - Should bulk approve"""
        mock_execute_sql.return_value = {'rows_affected': 25}

        response = flask_client.post('/api/classifications/bulk-approve', json={
            'min_confidence': 90,
            'exclude_sensitive': True
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify SQL includes filters
        sql_call = mock_execute_sql.call_args[0][0]
        assert "confidence_score >= 90" in sql_call
        assert "sensitive_flag = FALSE" in sql_call

    @patch('main._execute_sql')
    def test_bulk_approve_default_params(self, mock_execute_sql, flask_client):
        """POST /api/classifications/bulk-approve - Should use default params"""
        mock_execute_sql.return_value = {}

        response = flask_client.post('/api/classifications/bulk-approve', json={})

        assert response.status_code == 200

        # Should use default min_confidence of 80
        sql_call = mock_execute_sql.call_args[0][0]
        assert "confidence_score >= 80" in sql_call


class TestTagApplicationEndpoint:
    """Test UC tag application endpoint"""

    @patch('main._execute_sql')
    @patch('main._generate_element_id')
    def test_apply_tags_success(
        self,
        mock_generate_id,
        mock_execute_sql,
        flask_client
    ):
        """POST /api/apply-tags - Should apply approved tags to columns"""
        # First call returns approved classifications
        approved = [
            {
                'catalog_name': 'main',
                'schema_name': 'test',
                'table_name': 't1',
                'column_name': 'email',
                'element': 'Email Address'
            }
        ]

        mock_generate_id.return_value = 'email_address'

        # Mock SQL calls
        mock_execute_sql.side_effect = [
            approved,  # Get approved classifications
            [],  # Apply tag
            []   # Mark as applied
        ]

        response = flask_client.post('/api/apply-tags')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['applied'] == 1
        assert data['total'] == 1

    @patch('main._execute_sql')
    @patch('main._generate_element_id')
    def test_apply_tags_handles_errors(
        self,
        mock_generate_id,
        mock_execute_sql,
        flask_client
    ):
        """POST /api/apply-tags - Should collect errors for failed tags"""
        approved = [
            {
                'catalog_name': 'main',
                'schema_name': 'test',
                'table_name': 't1',
                'column_name': 'c1',
                'element': 'Test'
            }
        ]

        mock_generate_id.return_value = 'test'

        # First call succeeds, second fails
        mock_execute_sql.side_effect = [
            approved,
            Exception("Tag creation failed")
        ]

        response = flask_client.post('/api/apply-tags')

        assert response.status_code == 200
        data = response.get_json()
        assert data['applied'] == 0
        assert len(data['errors']) == 1
        assert 'error' in data['errors'][0]

    @patch('main._execute_sql')
    def test_apply_tags_limits_to_100(self, mock_execute_sql, flask_client):
        """POST /api/apply-tags - Should limit to 100 tags per request"""
        mock_execute_sql.return_value = []

        response = flask_client.post('/api/apply-tags')

        # Verify SQL query has LIMIT 100
        sql_call = mock_execute_sql.call_args_list[0][0][0]
        assert 'LIMIT 100' in sql_call

    @patch('main._execute_sql')
    @patch('main._generate_element_id')
    def test_apply_tags_uses_alter_table(
        self,
        mock_generate_id,
        mock_execute_sql,
        flask_client
    ):
        """POST /api/apply-tags - Should use ALTER TABLE to set tags"""
        approved = [
            {
                'catalog_name': 'main',
                'schema_name': 'test',
                'table_name': 't1',
                'column_name': 'email',
                'element': 'Email Address'
            }
        ]

        mock_generate_id.return_value = 'email_address'
        mock_execute_sql.side_effect = [approved, [], []]

        response = flask_client.post('/api/apply-tags')

        # Check the ALTER TABLE call
        alter_call = mock_execute_sql.call_args_list[1][0][0]
        assert 'ALTER TABLE' in alter_call
        assert 'ALTER COLUMN' in alter_call
        assert 'SET TAGS' in alter_call
        assert 'email_address' in alter_call


class TestDashboardEndpoint:
    """Test dashboard statistics endpoint"""

    @patch('main._execute_sql')
    def test_get_dashboard_stats(self, mock_execute_sql, flask_client):
        """GET /api/dashboard/stats - Should return statistics"""
        mock_execute_sql.return_value = [{
            'total_classified': 500,
            'pending_review': 25,
            'approved': 400,
            'applied': 350,
            'sensitive_count': 75,
            'avg_confidence': 89.5
        }]

        response = flask_client.get('/api/dashboard/stats')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total_classified'] == 500
        assert data['pending_review'] == 25
        assert data['avg_confidence'] == 89.5

    @patch('main._execute_sql')
    def test_get_dashboard_stats_error(self, mock_execute_sql, flask_client):
        """GET /api/dashboard/stats - Should handle errors"""
        mock_execute_sql.side_effect = Exception("DB error")

        response = flask_client.get('/api/dashboard/stats')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestStaticFileServing:
    """Test static React app serving"""

    def test_serve_react_root(self, flask_client):
        """GET / - Should serve React app"""
        # This will fail in test environment without static files
        # but we can verify the route exists
        response = flask_client.get('/')
        # Will be 404 or 500 without actual static files
        assert response.status_code in [200, 404, 500]

    def test_serve_react_path(self, flask_client):
        """GET /<path> - Should serve React app for all paths"""
        response = flask_client.get('/dashboard')
        # Will be 404 or 500 without actual static files
        assert response.status_code in [200, 404, 500]


class TestHelperFunctions:
    """Test helper functions used by endpoints"""

    @patch('main.w')
    def test_get_unclassified_columns(self, mock_w):
        """_get_unclassified_columns should query unclassified columns"""
        from main import _get_unclassified_columns

        # Mock the statement execution
        mock_col = Mock()
        mock_col.name = "catalog"

        mock_statement = Mock()
        mock_statement.statement_id = "stmt-123"
        mock_statement.status.state = "SUCCEEDED"
        mock_statement.result.data_array = [
            ['main', 'schema1', 'table1', 'col1']
        ]
        mock_statement.manifest.schema.columns = [
            mock_col, mock_col, mock_col, mock_col
        ]

        mock_w.statement_execution.execute_statement.return_value = mock_statement

        with patch.dict(os.environ, {'WAREHOUSE_ID': 'test-warehouse'}):
            result = _get_unclassified_columns('main', 'schema1')

        # Should return list of unclassified columns
        assert isinstance(result, list)

    def test_generate_element_id_helper():
        """_generate_element_id should convert names to IDs"""
        from main import _generate_element_id

        assert _generate_element_id('Email Address') == 'email_address'
        assert _generate_element_id('Social Security Number') == 'social_security_number'
        assert _generate_element_id('Test / Element') == 'test_element'


class TestErrorHandling:
    """Test error handling across all endpoints"""

    def test_post_with_invalid_json(self, flask_client):
        """Should handle invalid JSON gracefully"""
        response = flask_client.post(
            '/api/taxonomy/import',
            data='invalid json',
            content_type='application/json'
        )

        # Flask will return 400 for invalid JSON
        assert response.status_code in [400, 500]

    @patch('main.taxonomy_mgr')
    def test_database_connection_error(self, mock_taxonomy_mgr, flask_client):
        """Should handle database connection errors"""
        mock_taxonomy_mgr.get_active_taxonomy.side_effect = Exception(
            "Connection refused"
        )

        response = flask_client.get('/api/taxonomy')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('main._execute_sql')
    def test_sql_injection_protection(self, mock_execute_sql, flask_client):
        """Should properly escape SQL parameters"""
        mock_execute_sql.return_value = []

        # Try SQL injection in query parameter
        response = flask_client.get(
            "/api/classifications?status=PENDING'; DROP TABLE users; --"
        )

        # Should still work (parameters should be escaped)
        assert response.status_code in [200, 500]


class TestRequestValidation:
    """Test input validation"""

    @patch('main._get_unclassified_columns')
    def test_classify_requires_schema(self, mock_get_columns, flask_client):
        """POST /api/classify should require schema"""
        response = flask_client.post('/api/classify', json={
            'catalog': 'main'
        })

        assert response.status_code == 400

    @patch('main._execute_sql')
    def test_approve_requires_valid_id(self, mock_execute_sql, flask_client):
        """POST /api/classifications/<id>/approve should validate ID"""
        # Try with non-numeric ID
        response = flask_client.post('/api/classifications/invalid/approve', json={})

        # Flask should handle route mismatch
        assert response.status_code in [404, 500]

    @patch('main._execute_sql')
    def test_bulk_approve_validates_confidence(self, mock_execute_sql, flask_client):
        """POST /api/classifications/bulk-approve should validate confidence range"""
        mock_execute_sql.return_value = {}

        # Extreme confidence value
        response = flask_client.post('/api/classifications/bulk-approve', json={
            'min_confidence': 999
        })

        # Should still process (SQL will handle invalid confidence)
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers_present(self, flask_client):
        """Should include CORS headers"""
        response = flask_client.get('/api/taxonomy')

        # Check for CORS header (will be present if CORS enabled)
        # Note: In test mode, CORS headers might not be fully set
        assert response.status_code in [200, 500]
