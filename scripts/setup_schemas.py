"""
Setup database schemas for Data Classification Platform
Run this after deploying the app to create the required schemas and tables
"""

from databricks.sdk import WorkspaceClient
import os

def main():
    # Get configuration from environment variables
    org_name = os.environ.get('ORG_NAME', 'carmax')
    warehouse_id = os.environ.get('WAREHOUSE_ID')
    profile = os.environ.get('DATABRICKS_CONFIG_PROFILE')

    if not warehouse_id:
        raise ValueError("WAREHOUSE_ID environment variable is required")

    # Initialize workspace client
    w = WorkspaceClient(profile=profile) if profile else WorkspaceClient()

    print(f"Setting up Data Classification schemas for '{org_name}'...")
    print(f"Warehouse ID: {warehouse_id}")

    # Read SQL files and replace placeholder with org name
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, '..')

    with open(os.path.join(project_dir, 'sql/setup_taxonomy.sql'), 'r') as f:
        taxonomy_sql = f.read().replace('carmax', org_name)

    with open(os.path.join(project_dir, 'sql/setup_governance.sql'), 'r') as f:
        governance_sql = f.read().replace('carmax', org_name)

    print("\n1. Creating taxonomy schema...")
    try:
        result = w.statement_execution.execute_statement(
            statement=taxonomy_sql,
            warehouse_id=warehouse_id,
            wait_timeout="50s"
        )
        print("   ✓ Taxonomy schema created successfully")
    except Exception as e:
        print(f"   Error creating taxonomy schema: {e}")

    print("\n2. Creating governance schema...")
    try:
        result = w.statement_execution.execute_statement(
            statement=governance_sql,
            warehouse_id=warehouse_id,
            wait_timeout="50s"
        )
        print("   ✓ Governance schema created successfully")
    except Exception as e:
        print(f"   Error creating governance schema: {e}")

    print("\n3. Verifying schemas...")
    try:
        result = w.statement_execution.execute_statement(
            statement=f"SHOW SCHEMAS IN main LIKE '{org_name}*'",
            warehouse_id=warehouse_id,
            wait_timeout="50s"
        )
        print("   ✓ Schemas verified:")
        if result.result and result.result.data_array:
            for row in result.result.data_array:
                print(f"     - {row[0]}")
    except Exception as e:
        print(f"   Error verifying schemas: {e}")

    print("\n✓ Database setup complete!")
    print("\nNext steps:")
    print("1. Set ORG_NAME environment variable (or it defaults to 'carmax')")
    print("2. Import taxonomy using: python3 scripts/import_taxonomy.py")
    print("3. Grant permissions to service principal")
    print("4. Deploy and start the app")

if __name__ == "__main__":
    main()
