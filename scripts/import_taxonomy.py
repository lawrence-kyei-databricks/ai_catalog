"""
One-time script to import taxonomy from Excel/CSV files
Run this once after setting up the database tables
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from databricks.sdk import WorkspaceClient
from app.taxonomy_manager import TaxonomyManager

def main():
    """Import taxonomy from Excel files"""
    parser = argparse.ArgumentParser(description='Import taxonomy from Excel/CSV files')
    parser.add_argument('--elements-file', type=str, help='Path to data elements file')
    parser.add_argument('--subjects-file', type=str, help='Path to subject types file')
    parser.add_argument('--version', type=str, default='1.0', help='Version number for this import')

    args = parser.parse_args()

    # Get warehouse ID from environment
    warehouse_id = os.environ.get('WAREHOUSE_ID')
    if not warehouse_id:
        raise ValueError("WAREHOUSE_ID environment variable is required")

    org_name = os.environ.get('ORG_NAME', 'carmax')

    # Get file paths from arguments or use defaults
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, '..')

    elements_file = args.elements_file or os.path.join(project_dir, "data", "Data_Element_Descriptions.xlsx")
    subjects_file = args.subjects_file or os.path.join(project_dir, "data", "Personal_Data_subject_types.xlsx")

    print("=" * 60)
    print(f"Data Classification Taxonomy Import for '{org_name}'")
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
    result = taxonomy_mgr.import_from_excel(elements_file, subjects_file, version=args.version)

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
