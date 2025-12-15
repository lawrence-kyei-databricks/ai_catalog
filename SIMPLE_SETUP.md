# Data Classification Platform - Simple Setup Guide

## Prerequisites

1. Databricks workspace
2. SQL Warehouse ID
3. Your organization's taxonomy data in Excel format
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
export WAREHOUSE_ID="<your_warehouse_id>"
python3 scripts/import_taxonomy.py
```

### 3. Deploy the App

```bash
export DATABRICKS_CONFIG_PROFILE=<your_profile>
databricks bundle deploy -t dev --var warehouse_id="<your_warehouse_id>"
databricks apps start <app_name>-dev --profile <your_profile>
```

### 4. Grant Permissions

```sql
-- Get service principal ID from app
-- Run: databricks apps get <app_name>-dev --profile <your_profile>

-- Then grant permissions (replace <SP_ID>)
GRANT ALL PRIVILEGES ON SCHEMA main.<your_org>_taxonomy TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.<your_org>_governance TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.<your_org>_tags TO `<SP_ID>`;
```

## That's It!

Your app is now ready!

## Usage

1. **Dashboard** - View stats
2. **Taxonomy** - Manage your data elements
3. **Classify** - Select catalog/schema and classify columns
4. **Review** - Approve/reject classifications

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
