"""
One-time script to import CarMax taxonomy from Excel files
Run this once after setting up the database tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from databricks.sdk import WorkspaceClient
from app.taxonomy_manager import TaxonomyManager

def main():
    """Import taxonomy from Excel files"""

    # Get warehouse ID from environment or command line
    warehouse_id = os.environ.get('WAREHOUSE_ID', '8baced1ff014912d')

    # Paths to Excel files (absolute paths from script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, '..')
    elements_file = os.path.join(project_dir, "data", "Data_Element_Descriptions.xlsx")
    subjects_file = os.path.join(project_dir, "data", "Personal_Data_subject_types.xlsx")

    print("=" * 60)
    print("CarMax Taxonomy Import Script")
    print("=" * 60)
    print(f"Warehouse ID: {warehouse_id}")
    print(f"Elements file: {elements_file}")
    print(f"Subjects file: {subjects_file}")
    print()

    # Initialize
    w = WorkspaceClient()
    taxonomy_mgr = TaxonomyManager(w, warehouse_id=warehouse_id)

    # Import
    print("Starting import...")
    result = taxonomy_mgr.import_from_excel(elements_file, subjects_file, version="1.0")

    print()
    print("=" * 60)
    print("Import Complete!")
    print("=" * 60)
    print(f"Elements imported: {result['elements_imported']}")
    print(f"Subjects imported: {result['subjects_imported']}")
    print(f"Tags created: {result['tags_created']}")
    print(f"Version: {result['version']}")
    print()
    print("You can now use the app to classify data!")
    print("=" * 60)

if __name__ == "__main__":
    main()
