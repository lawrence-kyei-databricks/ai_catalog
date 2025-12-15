"""
Taxonomy Initialization Script
Automatically imports CarMax taxonomy from Excel files on app startup if not already loaded
"""

import os
from databricks.sdk import WorkspaceClient
from .taxonomy_manager import TaxonomyManager


def init_taxonomy():
    """
    Initialize taxonomy from Excel files if not already loaded
    This runs automatically on app startup
    """
    try:
        w = WorkspaceClient()
        taxonomy_mgr = TaxonomyManager(w)

        # Check if taxonomy already exists
        try:
            check_sql = "SELECT COUNT(*) as cnt FROM main.carmax_taxonomy.data_elements"
            result = taxonomy_mgr._execute_sql(check_sql)

            if result and len(result) > 0:
                count = result[0]['cnt'] if isinstance(result[0], dict) else result[0][0]
                if count > 0:
                    print(f"Taxonomy already initialized with {count} elements. Skipping import.")
                    return {"status": "already_initialized", "count": count}
        except Exception as e:
            print(f"Taxonomy table doesn't exist yet or error checking: {e}")

        # Get the workspace file paths for Excel files
        # These files are deployed with the app bundle
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        elements_file = os.path.join(base_path, 'Data_Element_Descriptions.xlsx')
        subjects_file = os.path.join(base_path, 'Personal Data_2025-11-14T14_18_26 (1).xlsx')

        print(f"Importing taxonomy from Excel files...")
        print(f"Elements file: {elements_file}")
        print(f"Subjects file: {subjects_file}")

        # Import taxonomy
        result = taxonomy_mgr.import_from_excel(
            elements_file=elements_file,
            subjects_file=subjects_file,
            version='1.0'
        )

        print(f"✓ Taxonomy initialized successfully!")
        print(f"  - Elements imported: {result['elements_imported']}")
        print(f"  - Tags created: {result['tags_created']}")

        return result

    except Exception as e:
        print(f"Error initializing taxonomy: {e}")
        print("You can manually import using the /api/taxonomy/import endpoint")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    init_taxonomy()
