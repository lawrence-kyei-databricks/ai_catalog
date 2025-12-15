# CarMax Data Classification - Databricks App Deployment Guide

## Prerequisites

1. Databricks CLI installed and authenticated
```bash
databricks --version  # Should be v0.200+
databricks auth login --host https://your-workspace.cloud.databricks.com
```

2. SQL Warehouse with Unity Catalog access
```bash
# List available warehouses
databricks sql warehouses list

# Note the warehouse ID for deployment
export WAREHOUSE_ID="your-warehouse-id"
```

3. Required permissions
   - CREATE CATALOG on metastore
   - CREATE SCHEMA on target catalog
   - USE CATALOG, USE SCHEMA permissions
   - Apps admin permissions

## Deployment Steps

### Step 1: Setup Database Schemas

Run the SQL setup scripts to create taxonomy and governance schemas:

```bash
# Navigate to project directory
cd /Users/lawrence.kyei/Desktop/dbx-demos/ai_catalog

# Create taxonomy schema (172 CarMax elements)
databricks sql -e "$(cat sql/setup_taxonomy.sql)"

# Create governance schema (classification tracking)
databricks sql -e "$(cat sql/setup_governance.sql)"
```

Verify schemas were created:
```bash
databricks sql -e "SHOW SCHEMAS IN main LIKE 'carmax*'"
```

### Step 2: Validate DABs Configuration

Verify the bundle configuration:

```bash
# Validate bundle syntax
databricks bundle validate -t dev

# View what will be deployed
databricks bundle validate -t dev --output json
```

### Step 3: Deploy to Development

Deploy the app to your development environment:

```bash
# Set warehouse ID (if not already set)
export WAREHOUSE_ID="your-warehouse-id"

# Deploy to dev
databricks bundle deploy -t dev
```

This will:
- Create a Databricks App named `carmax-classification-dev`
- Configure environment variables (WAREHOUSE_ID, TARGET_CATALOG=main)
- Set up permissions (admins: CAN_MANAGE, users: CAN_USE)
- Deploy Flask API with all endpoints

### Step 4: Start the App

After deployment, start the app:

```bash
# Start the app
databricks apps start carmax-classification-dev

# Check status
databricks apps get carmax-classification-dev

# Get app URL
databricks apps get carmax-classification-dev --output json | jq -r '.url'
```

### Step 5: Import CarMax Taxonomy

Use a Databricks notebook to import your Excel files:

```python
from databricks.sdk import WorkspaceClient
from taxonomy_manager import TaxonomyManager

w = WorkspaceClient()
taxonomy_mgr = TaxonomyManager(w)

# Import from Excel files (update paths to your files)
result = taxonomy_mgr.import_from_excel(
    elements_file='/Volumes/main/your_volume/Data_Element_Descriptions.xlsx',
    subjects_file='/Volumes/main/your_volume/Personal Data_2025-11-14T14_18_26 (1).xlsx',
    version='1.0'
)

print(f"Imported {result['elements_imported']} elements")
print(f"Created {result['tags_created']} UC tags")
```

Or use the API endpoint:
```bash
curl -X POST https://your-app-url/api/taxonomy/import \
  -H "Content-Type: application/json" \
  -d '{
    "elements_file": "/Volumes/main/your_volume/Data_Element_Descriptions.xlsx",
    "subjects_file": "/Volumes/main/your_volume/Personal Data_2025-11-14T14_18_26 (1).xlsx",
    "version": "1.0"
  }'
```

### Step 6: Grant Service Principal Permissions

Get the service principal ID:
```bash
APP_SP=$(databricks apps get carmax-classification-dev --output json | jq -r '.service_principal_id')
echo $APP_SP
```

Grant permissions:
```sql
-- Grant access to taxonomy and governance schemas
GRANT USAGE ON CATALOG main TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_taxonomy TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_governance TO `<service-principal-id>`;
GRANT USAGE ON SCHEMA main.carmax_tags TO `<service-principal-id>`;

GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `<service-principal-id>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_governance TO `<service-principal-id>`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `<service-principal-id>`;

-- Grant access to catalogs you want to classify
GRANT USAGE ON CATALOG your_data_catalog TO `<service-principal-id>`;
GRANT SELECT ON CATALOG your_data_catalog TO `<service-principal-id>`;
GRANT MODIFY ON CATALOG your_data_catalog TO `<service-principal-id>`;
```

### Step 7: Test the Deployment

Test API endpoints:

```bash
# Get app URL
APP_URL=$(databricks apps get carmax-classification-dev --output json | jq -r '.url')

# Health check
curl $APP_URL/

# Get taxonomy
curl $APP_URL/api/taxonomy

# List catalogs
curl $APP_URL/api/catalogs

# Classify a schema
curl -X POST $APP_URL/api/classify \
  -H "Content-Type: application/json" \
  -d '{"catalog": "main", "schema": "your_schema"}'
```

## Production Deployment

When ready for production:

```bash
# Deploy to prod (uses 'carmax' catalog)
databricks bundle deploy -t prod

# Start the production app
databricks apps start carmax-classification

# Get production URL
databricks apps get carmax-classification --output json | jq -r '.url'
```

Production configuration:
- App name: `carmax-classification`
- Target catalog: `carmax`
- Debug mode: disabled
- Same permissions model

## Monitoring and Management

### View App Logs

```bash
# View real-time logs
databricks apps logs carmax-classification-dev --follow

# View last 100 lines
databricks apps logs carmax-classification-dev --tail 100
```

### Update the App

After making code changes:

```bash
# Validate changes
databricks bundle validate -t dev

# Deploy updates
databricks bundle deploy -t dev

# Restart app (if needed)
databricks apps restart carmax-classification-dev
```

### Stop the App

```bash
databricks apps stop carmax-classification-dev
```

### Delete the App

```bash
databricks bundle destroy -t dev
```

## Troubleshooting

### App won't start
- Check logs: `databricks apps logs carmax-classification-dev`
- Verify WAREHOUSE_ID is set correctly
- Ensure service principal has required permissions

### "No module named 'taxonomy_manager'"
- Verify app.yaml has correct PYTHONPATH
- Check source_code_path in resources/apps.yml

### Classification errors
- Verify Claude 3.7 model is available: `databricks serving-endpoints list`
- Check warehouse is running: `databricks sql warehouses get $WAREHOUSE_ID`
- Verify taxonomy was imported: `SELECT COUNT(*) FROM main.carmax_taxonomy.data_elements`

### Permission errors
- Grant all required permissions to service principal
- Check catalog/schema ownership
- Verify UC metastore access

## Architecture

```
ai_catalog/
├── app.yaml                  # Databricks App entry point
├── databricks.yml            # DABs bundle configuration
├── resources/apps.yml        # App resource definition
├── app/
│   ├── main.py              # Flask API
│   ├── taxonomy_manager.py  # Taxonomy management
│   └── classification_engine.py  # Claude 3.7 classification
├── sql/
│   ├── setup_taxonomy.sql   # Taxonomy schema
│   └── setup_governance.sql # Governance schema
└── requirements.txt         # Python dependencies
```

## Cost Estimates

Monthly cost for dev environment:
- SQL Warehouse (serverless): $30-60
- Claude 3.7 API: $15-30
- Storage: $5-10
- **Total: $50-100/month**

## Next Steps

1. Test classification workflow
2. Review auto-approval rates (target: 90%)
3. Customize confidence thresholds if needed
4. Add UI (optional - see DELIVERY.md)
5. Scale to production catalogs
6. Monitor costs and performance

## Support

- View logs: `databricks apps logs carmax-classification-dev`
- Check app status: `databricks apps get carmax-classification-dev`
- Review architecture: `SOLUTION_DESIGN.md`
- API reference: `README.md`
