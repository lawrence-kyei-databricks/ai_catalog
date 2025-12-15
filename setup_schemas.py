"""
Setup database schemas for CarMax Data Classification Platform
Run this after deploying the app to create the required schemas and tables
"""

from databricks.sdk import WorkspaceClient
import os

def main():
    # Initialize workspace client
    w = WorkspaceClient(profile="e2-demo-field-eng")
    warehouse_id = "8baced1ff014912d"

    print("Setting up CarMax Data Classification schemas...")

    # Read SQL files
    with open('sql/setup_taxonomy.sql', 'r') as f:
        taxonomy_sql = f.read()

    with open('sql/setup_governance.sql', 'r') as f:
        governance_sql = f.read()

    print("\n1. Creating taxonomy schema...")
    try:
        result = w.statement_execution.execute_statement(
            statement=taxonomy_sql,
            warehouse_id=warehouse_id,
            wait_timeout="30s"
        )
        print("   ✓ Taxonomy schema created successfully")
    except Exception as e:
        print(f"   Error creating taxonomy schema: {e}")

    print("\n2. Creating governance schema...")
    try:
        result = w.statement_execution.execute_statement(
            statement=governance_sql,
            warehouse_id=warehouse_id,
            wait_timeout="30s"
        )
        print("   ✓ Governance schema created successfully")
    except Exception as e:
        print(f"   Error creating governance schema: {e}")

    print("\n3. Verifying schemas...")
    try:
        result = w.statement_execution.execute_statement(
            statement="SHOW SCHEMAS IN main LIKE 'carmax*'",
            warehouse_id=warehouse_id,
            wait_timeout="30s"
        )
        print("   ✓ Schemas verified:")
        if result.result and result.result.data_array:
            for row in result.result.data_array:
                print(f"     - {row[0]}")
    except Exception as e:
        print(f"   Error verifying schemas: {e}")

    print("\n✓ Database setup complete!")
    print("\nNext steps:")
    print("1. Import taxonomy using the Excel files")
    print("2. Grant permissions to service principal (ID: 72348755394055)")
    print("3. Start classifying columns")

if __name__ == "__main__":
    main()
