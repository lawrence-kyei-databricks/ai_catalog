# CarMax Data Classification Platform

AI-powered data classification for Unity Catalog using Claude 3.7 Sonnet.

## What It Does

Automatically classifies database columns against CarMax's taxonomy of 172 data elements. Uses AI to identify sensitive data like SSN, email addresses, and personal information, then applies Unity Catalog tags for governance.

## Key Features

- AI classification with Claude 3.7 Sonnet
- Web UI for managing taxonomy and reviewing classifications
- Automatic Unity Catalog tag application
- Support for 172 CarMax data elements

## Quick Setup

See **[SIMPLE_SETUP.md](SIMPLE_SETUP.md)** for step-by-step instructions.

**Summary:**
1. Create database tables (run SQL script)
2. Import taxonomy from Excel files
3. Deploy the Databricks App
4. Grant permissions to service principal

## How To Use

### 1. Dashboard
View statistics about your taxonomy and classifications.

### 2. Taxonomy Tab
- View all 172 data elements
- Add, edit, or delete elements
- Search and filter by category

### 3. Classify Tab
1. Select a catalog and schema
2. Click "Classify Columns"
3. Wait for AI to analyze and classify

### 4. Review Tab
- Review AI classifications
- Approve or reject suggestions
- Edit classifications if needed

## Excel File Format

Your taxonomy Excel files need these columns:

**Data Elements File:**
- Data Element Name
- Data Category
- Sensitive_Flag (Yes or No)
- Description (optional)

**Subject Types File:**
- Data Subject Type Id
- Data Subject Type Name
- Description

See **[EXCEL_FILE_FORMAT.md](EXCEL_FILE_FORMAT.md)** for details.

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

## Troubleshooting

**No data elements showing:**
- Make sure you ran the import script (see SIMPLE_SETUP.md Step 2)

**Permission errors:**
- Grant ALL PRIVILEGES on schemas to service principal
- Check SIMPLE_SETUP.md Step 4

**App not starting:**
- Verify warehouse ID is correct
- Check service principal has warehouse access

**Changes not showing in browser:**
- Do a hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

## Documentation

- **[SIMPLE_SETUP.md](SIMPLE_SETUP.md)** - Quick setup guide
- **[EXCEL_FILE_FORMAT.md](EXCEL_FILE_FORMAT.md)** - Excel file requirements

## Requirements

- Databricks workspace
- SQL Warehouse with Unity Catalog
- Databricks CLI
- Python 3.9+

## Support

For detailed deployment help, see SIMPLE_SETUP.md or contact your Databricks account team.

---

**Built with Databricks Apps, Claude 3.7 Sonnet, and Unity Catalog**
