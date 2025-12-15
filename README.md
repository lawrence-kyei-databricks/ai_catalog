# CarMax Data Classification Platform

AI-powered data classification for Unity Catalog using Claude 3.7 Sonnet with smart auto-approval.

## Overview

This platform automatically classifies Unity Catalog columns against CarMax's 172-element data taxonomy with 90% auto-approval, reducing manual review burden.

**Key Features:**
- Claude 3.7 Sonnet AI classification
- Smart 3-tier auto-approval system
- Pattern-based instant classification
- Flexible taxonomy management (loads from your Excel files)
- Unity Catalog tag application
- Web UI for human review
- Deploy with Databricks Asset Bundles (DABs)

---

## Quick Start

### Prerequisites
- Databricks workspace (AWS, Azure, or GCP)
- SQL Warehouse with Unity Catalog access
- Databricks CLI installed
- Your two Excel files:
  - `Data_Element_Descriptions.xlsx` (172 elements)
  - `Personal Data_2025-11-14T14_18_26 (1).xlsx` (3 subject types)

### 1. Setup Database

```bash
# Run SQL setup scripts
databricks sql -e "$(cat sql/setup_taxonomy.sql)"
databricks sql -e "$(cat sql/setup_governance.sql)"
```

### 2. Import CarMax Taxonomy

```python
# In a Databricks notebook
from taxonomy_manager import TaxonomyManager
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
taxonomy_mgr = TaxonomyManager(w)

# Import from your Excel files
result = taxonomy_mgr.import_from_excel(
    elements_file='/path/to/Data_Element_Descriptions.xlsx',
    subjects_file='/path/to/Personal Data_2025-11-14T14_18_26 (1).xlsx',
    version='1.0'
)

print(f"Imported {result['elements_imported']} elements")
print(f"Created {result['tags_created']} UC tags")
```

### 3. Deploy App

```bash
# Configure warehouse ID
export WAREHOUSE_ID="your-warehouse-id"

# Deploy to dev
databricks bundle deploy -t dev

# Get app URL
databricks apps get carmax-classification-dev
```

### 4. Grant Permissions

```sql
-- Get service principal ID from app
-- Then grant permissions:

GRANT USAGE ON CATALOG main TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_taxonomy TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_governance TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_tags TO `<service-principal-id>`;

GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `<service-principal-id>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_governance TO `<service-principal-id>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `<service-principal-id>`;

-- Grant access to catalogs you want to classify
GRANT USAGE ON CATALOG your_catalog TO `<service-principal-id>`;
GRANT SELECT ON CATALOG your_catalog TO `<service-principal-id>`;
GRANT MODIFY ON CATALOG your_catalog TO `<service-principal-id>`;
```

---

## Usage Workflow

### Step 1: Classify Columns

Via API:
```bash
curl -X POST http://your-app-url/api/classify \
  -H "Content-Type: application/json" \
  -d '{"catalog": "main", "schema": "your_schema"}'
```

Via UI:
1. Go to "Classify" page
2. Select catalog and schema
3. Click "Classify Columns"
4. Wait for results

### Step 2: Review Classifications

The system auto-approves 90% of classifications. Only review pending items:

- **Auto-Approved (90%)**: High confidence, no review needed
- **Pending Review (10%)**: Low confidence or sensitive data

In the UI:
1. Go to "Review" page
2. Filter by "High Priority" (sensitive + low confidence)
3. Approve, edit, or reject each classification

### Step 3: Apply Tags

Apply approved classifications as Unity Catalog tags:

Via API:
```bash
curl -X POST http://your-app-url/api/apply-tags
```

Via UI:
1. Go to "Compliance" page
2. Click "Apply Approved Classifications"
3. Tags are applied to UC columns

### Step 4: View in Governance Hub

Tags automatically appear in Databricks Governance Hub:
1. Open Unity Catalog Explorer
2. Navigate to a classified table
3. View column tags and lineage

---

## Project Structure

```
ai_catalog/
├── sql/
│   ├── setup_taxonomy.sql         # Creates taxonomy schema and tables
│   └── setup_governance.sql       # Creates governance tracking table
├── app/
│   ├── main.py                    # Flask REST API
│   ├── taxonomy_manager.py        # Excel import and taxonomy CRUD
│   └── classification_engine.py   # Claude 3.7 classification
├── resources/
│   └── apps.yml                   # DABs app configuration
├── databricks.yml                 # Main DABs bundle config
├── requirements.txt               # Python dependencies
├── SOLUTION_DESIGN.md             # Complete architecture guide
└── README.md                      # This file
```

---

## API Reference

### Taxonomy

- `POST /api/taxonomy/import` - Import Excel files
- `GET /api/taxonomy` - Get current taxonomy

### Catalogs

- `GET /api/catalogs` - List catalogs
- `GET /api/schemas?catalog=main` - List schemas

### Classification

- `POST /api/classify` - Classify columns
  ```json
  {"catalog": "main", "schema": "your_schema"}
  ```

- `GET /api/classifications?status=PENDING` - Get classifications
- `POST /api/classifications/:id/approve` - Approve one
- `POST /api/classifications/:id/reject` - Reject one
- `POST /api/classifications/bulk-approve` - Bulk approve
  ```json
  {"min_confidence": 80, "exclude_sensitive": false}
  ```

### Tags

- `POST /api/apply-tags` - Apply approved classifications as UC tags

### Dashboard

- `GET /api/dashboard/stats` - Get statistics

---

## Configuration

### Environment Variables

Set in `resources/apps.yml`:

- `WAREHOUSE_ID` - SQL Warehouse ID (required)
- `TARGET_CATALOG` - Default catalog (default: "main")
- `FLASK_ENV` - Environment (dev/prod)

### Deployment Environments

**Dev** (databricks bundle deploy -t dev)
- Catalog: `main`
- App name: `carmax-classification-dev`
- Debug mode: enabled

**Prod** (databricks bundle deploy -t prod)
- Catalog: `carmax`
- App name: `carmax-classification`
- Debug mode: disabled

---

## Taxonomy Management

### Update Taxonomy (Add/Edit Elements)

When CarMax updates their taxonomy:

1. **Option A: Re-import Excel**
   ```python
   taxonomy_mgr.import_from_excel(
       elements_file='updated_file.xlsx',
       subjects_file='subjects.xlsx',
       version='1.1'  # Increment version
   )
   ```

2. **Option B: Direct database update**
   ```sql
   INSERT INTO main.carmax_taxonomy.data_elements
   (element_id, element_name, element_category, sensitive_flag)
   VALUES ('new_element', 'New Element', 'Identifiers', 'No');
   ```

3. **Option C: API (future feature)**
   Add admin UI for taxonomy CRUD operations

Changes take effect within 5 minutes (cache refresh).

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

## Cost Estimate

**Monthly cost: $50-100**

- SQL Warehouse (serverless): $30-60
- Claude 3.7 API: $15-30
- Storage (Delta Lake): $5-10

**Cost per 10,000 columns:** ~$10-15

---

## Troubleshooting

### "No module named 'taxonomy_manager'"

Ensure app directory structure is correct:
```bash
ls -la app/
# Should show: main.py, taxonomy_manager.py, classification_engine.py
```

### "Permission denied" errors

Grant permissions to service principal (see Step 4 above).

### "Model endpoint does not exist"

Check if Claude 3.7 is available:
```bash
databricks serving-endpoints list | grep claude
```

If not available, update `classification_engine.py`:
```python
self.model = "databricks-meta-llama-3-3-70b-instruct"  # Use Llama instead
```

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

## Support

For issues:
1. Check `SOLUTION_DESIGN.md` for architecture details
2. Review app logs: `databricks apps logs carmax-classification-dev`
3. Contact your Databricks account team

---

## Next Steps

1. **Test with sample data**
   - Classify a small schema first
   - Verify auto-approval rates
   - Test review workflow

2. **Scale to production**
   - Deploy to prod environment
   - Classify all catalogs
   - Monitor costs and performance

3. **Customize taxonomy**
   - Add CarMax-specific patterns
   - Adjust confidence thresholds
   - Create custom rules

4. **Integrate with governance**
   - Create tag-based policies
   - Setup automated reports
   - Configure compliance dashboards

---

**Built with Databricks Apps, Claude 3.7, Unity Catalog, and Delta Lake**
