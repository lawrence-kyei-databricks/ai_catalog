# CarMax Data Classification - Simple Setup Guide

## Prerequisites

1. Databricks workspace
2. SQL Warehouse ID: `8baced1ff014912d`
3. Two Excel files with your taxonomy data
4. Databricks CLI installed

## Setup Steps

### 1. Create Database Tables

Run this **once** in Databricks SQL Editor:

```bash
sql/fix_and_recreate_tables.sql
```

This creates all required schemas and tables.

### 2. Import Taxonomy Data

Place your Excel files in the `data/` folder:
- `data/Data_Element_Descriptions.xlsx`
- `data/Personal_Data_subject_types.xlsx`

**Excel Format Requirements:**

**Data Elements File columns:**
- `Data Element Name`
- `Data Category`
- `Sensitive_Flag` (must be "Yes" or "No")
- `Description` (optional)
- `Data Classification` (optional)

**Subject Types File columns:**
- `Data Subject Type Id`
- `Data Subject Type Name`
- `Description`

Then run:

```bash
cd ai_catalog
export WAREHOUSE_ID="8baced1ff014912d"
python3 scripts/import_taxonomy.py
```

### 3. Deploy the App

```bash
export DATABRICKS_CONFIG_PROFILE=e2-demo-field-eng
databricks bundle deploy -t dev --var warehouse_id="8baced1ff014912d"
databricks apps start carmax-classification-dev --profile e2-demo-field-eng
```

### 4. Grant Permissions

```sql
-- Get service principal ID from app
-- Run: databricks apps get carmax-classification-dev --profile e2-demo-field-eng

-- Then grant permissions (replace <SP_ID>)
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_governance TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `<SP_ID>`;
```

## That's It!

Your app is now ready at:
https://carmax-classification-dev-1444828305810485.aws.databricksapps.com

## Usage

1. **Dashboard** - View stats
2. **Classify** - Select catalog/schema and classify columns
3. **Review** - Approve/reject classifications

## Updating Taxonomy

If you need to update the taxonomy later:

1. Update your Excel files in `data/`
2. Re-run: `python3 scripts/import_taxonomy.py`

The script will update existing elements and add new ones.

## Troubleshooting

**Tables not found:**
- Run `sql/fix_and_recreate_tables.sql` again

**Permission errors:**
- Verify service principal has ALL PRIVILEGES on schemas

**Import errors:**
- Check Excel column names match exactly (case-sensitive)
- See `EXCEL_FILE_FORMAT.md` for details
