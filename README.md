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

### Step 1: Create Database Schema and Tables

Run the SQL setup scripts to create required tables:

```sql
-- Run sql/setup_taxonomy.sql
-- Run sql/setup_governance.sql
```

These scripts create two schemas:
- `main.<your_org>_taxonomy` - Data element definitions
- `main.<your_org>_governance` - Classification tracking

### Step 2: Import Your Taxonomy

Prepare your taxonomy Excel files with these columns:

**Data Elements File:**
- Element Name (e.g., "Social Security Number")
- Element Category (e.g., "Personal Identifiers")
- Sensitive_Flag ("Yes" or "No")
- Description (optional)

**Subject Types File (optional):**
- Data Subject Type Id (e.g., "CUSTOMER")
- Data Subject Type Name (e.g., "Customer")
- Description

Place Excel files in the `data/` folder and run the import script:

```bash
export WAREHOUSE_ID="your_warehouse_id"
export DATABRICKS_CONFIG_PROFILE=your_profile
python3 scripts/import_taxonomy.py
```

### Step 3: Configure and Deploy the App

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

### Schema Names
Update `databricks.yml` and SQL scripts to change schema names:
- `<your_org>_taxonomy` - Data element definitions
- `<your_org>_governance` - Classification tracking

### Branding
Update these files for your organization:
- `app/templates/app.html` - Header and title
- `databricks.yml` - App name and description
- `README.md` - This file

## Troubleshooting

**No data elements showing:**
- Make sure you ran the import script (see Setup and Installation Step 2)
- Check that your Excel files have the required columns

**Permission errors:**
- Grant ALL PRIVILEGES on schemas to service principal
- Ensure service principal has warehouse access

**App not starting:**
- Verify warehouse ID is correct in `databricks.yml`
- Check service principal has warehouse access

**Changes not showing in browser:**
- Do a hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

---

**Built with Databricks Apps, Claude 3.7 Sonnet, and Unity Catalog**
