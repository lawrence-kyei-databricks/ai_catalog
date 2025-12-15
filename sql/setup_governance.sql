-- =====================================================
-- CarMax Data Classification Platform
-- Governance Database Setup
-- =====================================================

-- Create governance schema
CREATE SCHEMA IF NOT EXISTS main.carmax_governance
COMMENT 'CarMax Data Classification Governance and Tracking';

-- =====================================================
-- MAIN TABLE: Classification Governance
-- =====================================================
CREATE TABLE IF NOT EXISTS main.carmax_governance.classification_governance (
  -- Primary key
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

  -- Column reference
  catalog_name STRING NOT NULL,
  schema_name STRING NOT NULL,
  table_name STRING NOT NULL,
  column_name STRING NOT NULL,
  column_type STRING,

  -- AI Classification results
  suggested_element STRING,
  suggested_category STRING,
  confidence_score DECIMAL(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),
  sensitive_flag BOOLEAN,
  data_subjects ARRAY<STRING>,
  reasoning STRING,

  -- Auto-approval intelligence
  review_status STRING DEFAULT 'PENDING' CHECK (
    review_status IN ('PENDING', 'AUTO_APPROVED', 'APPROVED', 'REJECTED', 'APPLIED')
  ),
  approval_tier INT CHECK (approval_tier IN (1, 2, 3)),
  requires_review BOOLEAN DEFAULT TRUE,
  review_priority STRING CHECK (review_priority IN ('HIGH', 'MEDIUM', 'LOW')),

  -- Human review
  approved_element STRING,
  reviewer STRING,
  review_notes STRING,

  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  reviewed_at TIMESTAMP,
  applied_at TIMESTAMP,

  -- Metadata
  sample_values STRING COMMENT 'JSON array of sample values',
  model_used STRING DEFAULT 'databricks-claude-3-7-sonnet',
  classification_source STRING CHECK (
    classification_source IN ('CLAUDE', 'UC_NATIVE', 'PATTERN_RULE', 'CACHE', 'MANUAL')
  ),

  -- Performance optimization
  column_fingerprint STRING COMMENT 'Hash for caching similar columns',

  -- Unique constraint: one classification per column
  CONSTRAINT unique_column UNIQUE (catalog_name, schema_name, table_name, column_name)
)
USING DELTA
CLUSTER BY (review_status, review_priority, catalog_name, schema_name)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true',
  'delta.columnMapping.mode' = 'name'
)
COMMENT 'CarMax Classification Governance - Main tracking table with Liquid Clustering';

-- =====================================================
-- QUEUE TABLE: Async Processing
-- =====================================================
CREATE TABLE IF NOT EXISTS main.carmax_governance.classification_queue (
  queue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  catalog_name STRING NOT NULL,
  schema_name STRING NOT NULL,
  table_name STRING NOT NULL,
  column_name STRING NOT NULL,

  status STRING DEFAULT 'QUEUED' CHECK (
    status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')
  ),
  priority INT DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message STRING
)
USING DELTA
CLUSTER BY (status, priority)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Queue for background classification processing';

-- =====================================================
-- MATERIALIZED VIEW: Dashboard Metrics
-- =====================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS main.carmax_governance.classification_summary AS
SELECT
  catalog_name,
  schema_name,
  review_status,
  approval_tier,
  sensitive_flag,
  classification_source,
  COUNT(*) as column_count,
  AVG(confidence_score) as avg_confidence,
  COUNT(CASE WHEN requires_review THEN 1 END) as pending_review_count,
  COUNT(CASE WHEN sensitive_flag THEN 1 END) as sensitive_count,
  DATE(created_at) as classification_date
FROM main.carmax_governance.classification_governance
GROUP BY ALL;

-- Refresh schedule (every 15 minutes)
-- ALTER MATERIALIZED VIEW main.carmax_governance.classification_summary
-- REFRESH ON SCHEDULE CRON '*/15 * * * *';

-- =====================================================
-- INDEXES for Performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_review_status
ON main.carmax_governance.classification_governance (review_status, review_priority);

CREATE INDEX IF NOT EXISTS idx_catalog_schema
ON main.carmax_governance.classification_governance (catalog_name, schema_name);

CREATE INDEX IF NOT EXISTS idx_created_at
ON main.carmax_governance.classification_governance (created_at);

CREATE INDEX IF NOT EXISTS idx_fingerprint
ON main.carmax_governance.classification_governance (column_fingerprint)
WHERE column_fingerprint IS NOT NULL;

-- =====================================================
-- HELPER VIEW: Pending Reviews
-- =====================================================
CREATE OR REPLACE VIEW main.carmax_governance.pending_reviews AS
SELECT
  id,
  catalog_name,
  schema_name,
  table_name,
  column_name,
  column_type,
  suggested_element,
  suggested_category,
  confidence_score,
  sensitive_flag,
  review_priority,
  reasoning,
  sample_values,
  created_at,
  CONCAT(catalog_name, '.', schema_name, '.', table_name, '.', column_name) as full_column_path
FROM main.carmax_governance.classification_governance
WHERE review_status = 'PENDING'
  AND requires_review = TRUE
ORDER BY
  CASE review_priority
    WHEN 'HIGH' THEN 1
    WHEN 'MEDIUM' THEN 2
    WHEN 'LOW' THEN 3
  END,
  created_at ASC;

-- =====================================================
-- HELPER VIEW: Auto-Approved Items
-- =====================================================
CREATE OR REPLACE VIEW main.carmax_governance.auto_approved AS
SELECT
  catalog_name,
  schema_name,
  table_name,
  column_name,
  suggested_element,
  confidence_score,
  approval_tier,
  classification_source,
  created_at
FROM main.carmax_governance.classification_governance
WHERE review_status = 'AUTO_APPROVED'
ORDER BY created_at DESC;

-- =====================================================
-- HELPER VIEW: Sensitive Data Inventory
-- =====================================================
CREATE OR REPLACE VIEW main.carmax_governance.sensitive_data_inventory AS
SELECT
  catalog_name,
  schema_name,
  table_name,
  column_name,
  COALESCE(approved_element, suggested_element) as classified_element,
  confidence_score,
  review_status,
  reviewer,
  reviewed_at,
  applied_at
FROM main.carmax_governance.classification_governance
WHERE sensitive_flag = TRUE
ORDER BY catalog_name, schema_name, table_name, column_name;

-- =====================================================
-- Grant permissions (adjust as needed)
-- =====================================================
-- GRANT ALL PRIVILEGES ON SCHEMA main.carmax_governance TO `<service-principal-id>`;
-- GRANT SELECT ON main.carmax_governance.classification_summary TO `carmax_data_stewards`;
-- GRANT SELECT ON main.carmax_governance.sensitive_data_inventory TO `carmax_compliance_team`;
