# Data Classification Platform

AI-powered data classification for Unity Catalog using Claude 3.7 Sonnet.

## What It Does

Automatically classifies database columns against your organization's data taxonomy. Uses AI to identify sensitive data like SSN, email addresses, and personal information, then applies Unity Catalog tags for governance.

## Key Features

- AI classification with Claude 3.7 Sonnet
- Web UI for managing your custom taxonomy
- Support for any number of data elements
- Automatic Unity Catalog tag application
- Review and approve classifications before tagging

## Setup and Installation

### Prerequisites
- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (get the warehouse ID)
- Databricks CLI installed and configured
- Python 3.9+
- Your organization's data taxonomy in Excel format

### Step 1: Customize for Your Organization

Before deployment, update hardcoded values for your organization:

**In `sql/setup_taxonomy.sql`:**
- Line 7: Change `main.carmax_taxonomy` to `main.<your_org>_taxonomy`

**In `sql/setup_governance.sql`:**
- Line 7: Change `main.carmax_governance` to `main.<your_org>_governance`

**In `app/taxonomy_manager.py`:**
- Line 30: Change `self.taxonomy_schema = "main.carmax_taxonomy"` to your org name

**In `scripts/setup_schemas.py`:**
- Lines 11-12: Update warehouse_id and profile for your environment

### Step 2: Create Database Schemas and Tables

Option A - Automated (recommended):
```bash
export DATABRICKS_CONFIG_PROFILE=your_profile
python3 scripts/setup_schemas.py
```

Option B - Manual:
```bash
databricks sql execute --warehouse-id YOUR_WAREHOUSE_ID --file sql/setup_taxonomy.sql
databricks sql execute --warehouse-id YOUR_WAREHOUSE_ID --file sql/setup_governance.sql
```

This creates two schemas:
- `main.<your_org>_taxonomy` - Data element definitions
- `main.<your_org>_governance` - Classification tracking

### Step 3: Import Your Taxonomy

Prepare your taxonomy Excel files with these exact columns:

**Data Elements File** (name: `Data_Element_Descriptions.xlsx`):
- Data Element Name (e.g., "Social Security Number")
- Data Category (e.g., "Personal Identifiers")
- Sensitive_Flag ("Yes" or "No")
- Description (optional)

**Subject Types File** (name: `Personal_Data_subject_types.xlsx`):
- Data Subject Type Id (e.g., "CUSTOMER")
- Data Subject Type Name (e.g., "Customer")
- Description

Place Excel files in the `data/` folder with the exact names above, then run:

```bash
export WAREHOUSE_ID="your_warehouse_id"
export DATABRICKS_CONFIG_PROFILE=your_profile
python3 scripts/import_taxonomy.py
```

### Step 4: Configure and Deploy the App

Update `databricks.yml` with your settings:
- App name
- Warehouse ID
- Service principal name (optional)

Deploy the app:

```bash
databricks bundle deploy -t dev
```

### Step 4: Grant Permissions

Grant the app's service principal access to Unity Catalog:

```sql
GRANT ALL PRIVILEGES ON SCHEMA main.<your_org>_taxonomy TO `your-service-principal`;
GRANT ALL PRIVILEGES ON SCHEMA main.<your_org>_governance TO `your-service-principal`;
GRANT USE CATALOG ON CATALOG main TO `your-service-principal`;
```

### Step 5: Access the App

After deployment, Databricks CLI will output the app URL. Open it in your browser to start classifying data!

## How To Use

### 1. Dashboard
View statistics about your taxonomy and classifications.

### 2. Taxonomy Tab
- View all your data elements
- Add, edit, or delete elements
- Search and filter by category
- Import taxonomy from Excel files

### 3. Classify Tab
1. Select a catalog and schema
2. Click "Classify Columns"
3. Wait for AI to analyze and classify

### 4. Review Tab
- Review AI classifications
- Approve or reject suggestions
- Edit classifications if needed


## Project Structure

```
ai_catalog/
├── app/                    # Flask backend
│   ├── main.py            # REST API
│   ├── taxonomy_manager.py
│   └── templates/app.html # Web UI
├── static/app.js          # Frontend JavaScript
├── sql/                   # Database setup scripts
├── scripts/               # Import scripts
├── data/                  # Sample Excel files
└── databricks.yml         # Deployment config
```

## Customization

### Ongoing Taxonomy Management
After initial setup, use the Taxonomy Tab in the web UI to:
- Add new data elements
- Edit existing elements
- Delete elements
- Search and filter by category

No need to re-import Excel files for ongoing updates.

### Schema Names
To change schema names from default "carmax" to your organization:
- `sql/setup_taxonomy.sql` line 7
- `sql/setup_governance.sql` line 7
- `app/taxonomy_manager.py` line 30

### Branding
Update these files for your organization:
- `app/templates/app.html` - Header and title
- `databricks.yml` - App name and description
- `README.md` - This file

## Troubleshooting

**No data elements showing:**
- Make sure you ran Step 2 (create schemas/tables) successfully
- Verify you ran Step 3 (import script) with correct Excel files
- Check that your Excel files have the exact required column names
- Verify filenames are exactly: `Data_Element_Descriptions.xlsx` and `Personal_Data_subject_types.xlsx`

**Schema creation errors:**
- If using `setup_schemas.py`, update hardcoded warehouse_id and profile (lines 11-12)
- For manual SQL execution, ensure you have CREATE SCHEMA permissions
- Verify catalog name is "main" or update SQL files accordingly

**Import script errors:**
- Check environment variables: `WAREHOUSE_ID` and `DATABRICKS_CONFIG_PROFILE`
- Ensure Excel files are in the `data/` folder with exact names
- Review error messages for missing required columns

**Permission errors:**
- Grant ALL PRIVILEGES on both schemas to service principal
- Ensure service principal has warehouse access and USE CATALOG permission

**App not starting:**
- Verify warehouse ID is correct in `databricks.yml`
- Check service principal has warehouse access
- Ensure schemas exist before starting app

**Changes not showing in browser:**
- Do a hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

---

**Built with Databricks Apps, Claude 3.7 Sonnet, and Unity Catalog**
