# CarMax Data Classification Platform

AI-powered data classification for Unity Catalog using Claude 3.7 Sonnet with smart auto-approval.

## Overview

This platform automatically classifies Unity Catalog columns against CarMax's 172-element data taxonomy with 90% auto-approval, reducing manual review burden.

**Key Features:**
- Claude 3.7 Sonnet AI classification
- Smart 3-tier auto-approval system
- Web UI for taxonomy upload and management
- Unity Catalog tag application
- Deploy with Databricks Asset Bundles (DABs)
- Single-page app with drag-and-drop file upload

---

## Quick Start

### Prerequisites
- Databricks workspace (AWS, Azure, or GCP)
- SQL Warehouse with Unity Catalog access
- Databricks CLI installed (`pip install databricks-cli`)
- Your two Excel files (see `data/` folder for examples):
  - Data Element Descriptions (172 elements)
  - Personal Data subject types (3 subject types)

### 1. Setup Database

Run SQL setup scripts to create schemas and tables:

```bash
# Navigate to project directory
cd ai_catalog

# Run taxonomy setup
databricks sql -e "$(cat sql/setup_taxonomy.sql)" --warehouse-id YOUR_WAREHOUSE_ID

# Run governance setup
databricks sql -e "$(cat sql/setup_governance.sql)" --warehouse-id YOUR_WAREHOUSE_ID
```

### 2. Deploy App

```bash
# Configure your Databricks profile
databricks configure --profile e2-demo-field-eng

# Deploy to dev environment
export DATABRICKS_CONFIG_PROFILE=e2-demo-field-eng
databricks bundle deploy -t dev --var warehouse_id="YOUR_WAREHOUSE_ID"

# Start the app
databricks apps start carmax-classification-dev --profile e2-demo-field-eng
```

### 3. Grant Permissions

Get your service principal ID from the app:

```bash
databricks apps get carmax-classification-dev --profile e2-demo-field-eng | grep service_principal_client_id
```

Then grant permissions in SQL:

```sql
-- Replace <SP_ID> with your service principal ID
GRANT USAGE, CREATE ON CATALOG main TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_governance TO `<SP_ID>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `<SP_ID>`;

-- Grant SQL Warehouse access
GRANT USE ON WAREHOUSE YOUR_WAREHOUSE_ID TO `<SP_ID>`;

-- Grant access to catalogs you want to classify
GRANT USAGE ON CATALOG your_catalog TO `<SP_ID>`;
GRANT SELECT ON CATALOG your_catalog TO `<SP_ID>`;
GRANT MODIFY ON CATALOG your_catalog TO `<SP_ID>`;
```

### 4. Upload Taxonomy via UI

1. **Open the app URL** (get it from `databricks apps get carmax-classification-dev`)
2. **Go to Taxonomy tab**
3. **Drag and drop your Excel files** or click to browse:
   - Data Element Descriptions.xlsx
   - Personal Data subject types.xlsx
4. **Click Import**
5. **Verify** - Status changes from "⚠ Taxonomy Not Initialized" to "✓ Ready (172 elements)"

That's it! The app is now ready to classify your data.

---

## Usage Workflow

### Step 1: Classify Columns

In the UI:
1. Go to **Classify** tab
2. Select catalog and schema
3. Click "Classify Columns"
4. Wait for AI classification to complete

### Step 2: Review Classifications

The system auto-approves 90% of classifications. Only review pending items:

In the UI:
1. Go to **Review** tab
2. Filter by "High Priority" (sensitive data or low confidence)
3. Approve, edit, or reject each classification
4. Bulk approve high-confidence items

### Step 3: Apply Tags

Apply approved classifications as Unity Catalog tags:

In the UI:
1. Go to **Dashboard** tab
2. Click "Apply Tags"
3. Tags are automatically applied to columns

### Step 4: View in Governance Hub

Tags automatically appear in Databricks Governance Hub:
1. Open Unity Catalog Explorer
2. Navigate to a classified table
3. View column tags and lineage

---

## Project Structure

```
ai_catalog/
├── app/
│   ├── main.py                    # Flask REST API
│   ├── taxonomy_manager.py        # Excel import and taxonomy CRUD
│   ├── classification_engine.py   # Claude 3.7 classification
│   ├── init_taxonomy.py           # Startup initialization
│   └── templates/
│       └── app.html               # Unified web UI
├── sql/
│   ├── setup_taxonomy.sql         # Creates taxonomy schema and tables
│   └── setup_governance.sql       # Creates governance tracking table
├── data/
│   ├── Data_Element_Descriptions.xlsx      # Sample taxonomy elements
│   └── Personal Data_*.xlsx                # Sample subject types
├── docs/
│   ├── DEPLOYMENT_GUIDE.md        # Detailed deployment guide
│   ├── SOLUTION_DESIGN.md         # Architecture documentation
│   └── *.md                       # Other documentation
├── assets/
│   └── CarMax-Logo_*.png          # Logo and images
├── resources/
│   └── apps.yml                   # Databricks App configuration
├── static/
│   └── app.js                     # Frontend JavaScript
├── databricks.yml                 # DABs bundle config
├── app.yaml                       # App entry point config
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## API Reference

### Admin

- `GET /api/admin/taxonomy-status` - Check if taxonomy is initialized
- `POST /api/admin/import-taxonomy` - Upload and import Excel files

### Taxonomy

- `GET /api/taxonomy` - Get current active taxonomy

### Catalogs

- `GET /api/catalogs` - List accessible catalogs
- `GET /api/schemas?catalog=main` - List schemas in catalog

### Classification

- `POST /api/classify` - Classify columns in schema
  ```json
  {"catalog": "main", "schema": "your_schema"}
  ```

- `GET /api/classifications?status=PENDING` - Get classifications
- `POST /api/classifications/:id/approve` - Approve classification
- `POST /api/classifications/:id/reject` - Reject classification
- `POST /api/classifications/bulk-approve` - Bulk approve
  ```json
  {"min_confidence": 80, "exclude_sensitive": false}
  ```

### Tags

- `POST /api/apply-tags` - Apply approved classifications as UC tags

### Dashboard

- `GET /api/dashboard/stats` - Get classification statistics

---

## Configuration

### Environment Variables

Set in `app.yaml`:

- `WAREHOUSE_ID` - SQL Warehouse ID (required)
- `TARGET_CATALOG` - Default catalog (default: "main")
- `MODEL_ENDPOINT` - Foundation model endpoint (default: "databricks-claude-3-7-sonnet")

### Deployment Targets

Configure in `databricks.yml`:

**Dev** (`databricks bundle deploy -t dev`)
- Catalog: `main`
- App name: `carmax-classification-dev`
- Workspace: e2-demo-field-eng

**Prod** (`databricks bundle deploy -t prod`)
- Catalog: `carmax`
- App name: `carmax-classification`
- Configure in databricks.yml before deploying

---

## Excel File Format

### Data Elements File

Required columns:
- `Data Element Name` - Element name (e.g., "Social Security Number")
- `Data Category` - Category (e.g., "Personal Identifiers")
- `Sensitive_Flag` - "Yes" or "No"
- `Description` - Optional description
- `Data Classification` - Optional classification level

### Subject Types File

Required columns:
- `Data Subject Type Id` - ID (e.g., "CUSTOMER")
- `Data Subject Type Name` - Name (e.g., "Customer")
- `Description` - Description

---

## How Auto-Approval Works

### Tier 1 (Auto-Approve - 60%)
- Confidence ≥ 95%
- Pattern match ≥ 80%
- **Example:** Column "ssn" with values "123-45-6789" → Social Security Number (99% confidence)

### Tier 2 (Auto-Approve - 30%)
- Confidence ≥ 85%
- Non-sensitive data
- **Example:** Column "email" with emails → Email Address (92% confidence, not sensitive)

### Tier 3 (Human Review - 10%)
- Confidence < 85%
- Sensitive data + confidence < 95%
- Pattern mismatch
- **Example:** Column "data" with mixed values → Low confidence (65%), needs review

---

## Troubleshooting

### App shows "Taxonomy Not Initialized"

**Solution:** Upload your Excel files via the Taxonomy tab in the UI.

### "Permission denied" errors

**Solution:** Grant permissions to service principal (see Step 3 above).

### App not starting

**Solution:** Check warehouse permissions and ensure service principal has USE privilege.

### Tags not appearing

1. Verify tags were created:
   ```sql
   SHOW TAGS IN main.carmax_tags;
   ```

2. Check tag application:
   ```sql
   SELECT * FROM system.information_schema.column_tags
   WHERE tag_name LIKE 'main.carmax_tags.%';
   ```

---

## Documentation

Detailed documentation available in `docs/`:

- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `SOLUTION_DESIGN.md` - Architecture and design decisions
- `TESTING_GUIDE.md` - Testing strategies and procedures

---

## Support

For issues:
1. Check `docs/DEPLOYMENT_GUIDE.md` for deployment help
2. Review `docs/SOLUTION_DESIGN.md` for architecture details
3. Contact your Databricks account team

---

## Cost Estimate

**Monthly cost: $50-100**

- SQL Warehouse (serverless): $30-60
- Claude 3.7 API: $15-30
- Storage (Delta Lake): $5-10

**Cost per 10,000 columns:** ~$10-15

---

**Built with Databricks Apps, Claude 3.7, Unity Catalog, and Delta Lake**
