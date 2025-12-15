-- =====================================================
-- FIX SCHEMA MISMATCH - Drop and Recreate All Tables
-- Run this ONCE in Databricks SQL Editor
-- =====================================================

-- STEP 1: Drop existing tables (to fix schema mismatch)
DROP TABLE IF EXISTS main.carmax_taxonomy.data_elements;
DROP TABLE IF EXISTS main.carmax_taxonomy.data_categories;
DROP TABLE IF EXISTS main.carmax_taxonomy.subject_types;
DROP TABLE IF EXISTS main.carmax_taxonomy.taxonomy_versions;
DROP TABLE IF EXISTS main.carmax_taxonomy.element_mappings;

-- STEP 2: Ensure schemas exist
CREATE SCHEMA IF NOT EXISTS main.carmax_taxonomy
COMMENT 'CarMax Data Classification Taxonomy - Source of Truth';

CREATE SCHEMA IF NOT EXISTS main.carmax_tags
COMMENT 'CarMax Classification Tags (172 elements)';

-- =====================================================
-- TABLE 1: Data Elements (172 from Excel)
-- =====================================================
CREATE TABLE main.carmax_taxonomy.data_elements (
  element_id STRING PRIMARY KEY,
  element_name STRING NOT NULL,
  element_category STRING NOT NULL,
  element_description STRING,
  sensitive_flag STRING NOT NULL CHECK (sensitive_flag IN ('Yes', 'No')),
  data_classification STRING,

  -- For pattern matching and AI hints
  keywords ARRAY<STRING>,
  sample_patterns ARRAY<STRING>,

  -- Metadata
  metadata STRING COMMENT 'JSON metadata for extensibility',

  -- Lifecycle
  active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  created_by STRING
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'CarMax 172 Data Elements - Loaded from Excel';

-- =====================================================
-- TABLE 2: Data Categories
-- =====================================================
CREATE TABLE main.carmax_taxonomy.data_categories (
  category_id STRING PRIMARY KEY,
  category_name STRING NOT NULL,
  category_description STRING,
  element_count INT,
  active BOOLEAN,
  created_at TIMESTAMP
)
USING DELTA
COMMENT 'CarMax Data Categories (14 categories)';

-- =====================================================
-- TABLE 3: Subject Types
-- =====================================================
CREATE TABLE main.carmax_taxonomy.subject_types (
  subject_type_id STRING PRIMARY KEY,
  subject_type_name STRING NOT NULL,
  subject_description STRING,
  active BOOLEAN,
  created_at TIMESTAMP
)
USING DELTA
COMMENT 'CarMax Data Subject Types (Associate, B2B, Consumer)';

-- =====================================================
-- TABLE 4: Taxonomy Versions (Change Tracking)
-- =====================================================
CREATE TABLE main.carmax_taxonomy.taxonomy_versions (
  version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_number STRING NOT NULL,
  change_type STRING CHECK (change_type IN ('INITIAL', 'ADD_ELEMENT', 'UPDATE_ELEMENT', 'REMOVE_ELEMENT', 'BULK_UPDATE')),
  change_description STRING,
  element_count INT,
  changes_json STRING COMMENT 'JSON: {added: [], removed: [], updated: []}',
  changed_by STRING,
  changed_at TIMESTAMP
)
USING DELTA
COMMENT 'Taxonomy change history and audit trail';

-- =====================================================
-- TABLE 5: Element Mappings (Rename tracking)
-- =====================================================
CREATE TABLE main.carmax_taxonomy.element_mappings (
  mapping_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  old_element_name STRING NOT NULL,
  new_element_name STRING NOT NULL,
  mapping_reason STRING,
  effective_date TIMESTAMP,
  created_at TIMESTAMP
)
USING DELTA
COMMENT 'Track element name changes for backward compatibility';

-- =====================================================
-- Grant permissions to service principal
-- =====================================================
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `47e9c744-0efc-494d-8d8f-baac21801d18`;
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `47e9c744-0efc-494d-8d8f-baac21801d18`;

-- Verify tables were created correctly
DESCRIBE TABLE main.carmax_taxonomy.data_elements;
