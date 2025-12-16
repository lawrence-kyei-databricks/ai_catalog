"""
Taxonomy Initialization Script
Automatically imports CarMax taxonomy from Excel files on app startup if not already loaded
"""

import os
from databricks.sdk import WorkspaceClient
from .taxonomy_manager import TaxonomyManager


def init_taxonomy(warehouse_id: str = None):
    """
    Initialize taxonomy from Excel files if not already loaded
    This runs automatically on app startup

    Args:
        warehouse_id: SQL warehouse ID (optional, falls back to environment variable)
    """
    try:
        if not warehouse_id:
            warehouse_id = os.environ.get('WAREHOUSE_ID')

        w = WorkspaceClient()
        taxonomy_mgr = TaxonomyManager(w, warehouse_id=warehouse_id)

        # Check if taxonomy tables exist and are initialized
        try:
            # Use dynamic schema name from TaxonomyManager
            check_sql = f"SELECT COUNT(*) as cnt FROM {taxonomy_mgr.taxonomy_schema}.data_elements"
            result = taxonomy_mgr._execute_sql(check_sql)

            if result and len(result) > 0:
                count = result[0]['cnt'] if isinstance(result[0], dict) else result[0][0]
                count = int(count)  # Convert to int (SQL results sometimes return strings)
                if count > 0:
                    print(f"✓ Taxonomy already initialized with {count} elements.")
                    return {"status": "already_initialized", "count": count}
                else:
                    print("Taxonomy tables exist but are empty. Use the Taxonomy tab in the UI to upload Excel files.")
                    return {"status": "tables_exist_but_empty"}
        except Exception as e:
            # Tables don't exist yet - this is expected on first run
            print(f"[init_taxonomy] ERROR in table check: {e}")
            print(f"[init_taxonomy] Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            print("Taxonomy tables not found. Please run the SQL setup scripts first:")
            print("  1. Run sql/setup_taxonomy.sql in Databricks SQL Editor")
            print("  2. Run sql/setup_governance.sql in Databricks SQL Editor")
            print("  3. Grant permissions to the service principal")
            print("  4. Use the Taxonomy tab in the UI to upload Excel files")
            return {"status": "tables_not_found", "message": "Run SQL setup scripts first"}

    except Exception as e:
        print(f"Startup check completed with info: {e}")
        return {"status": "info", "message": "App ready - configure taxonomy via UI"}


if __name__ == "__main__":
    init_taxonomy()
