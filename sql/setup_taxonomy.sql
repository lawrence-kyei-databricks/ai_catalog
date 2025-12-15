-- =====================================================
-- CarMax Data Classification Platform
-- Taxonomy Database Setup
-- =====================================================

-- Create taxonomy schema
CREATE SCHEMA IF NOT EXISTS main.carmax_taxonomy
COMMENT 'CarMax Data Classification Taxonomy - Source of Truth';

-- Create tags schema
CREATE SCHEMA IF NOT EXISTS main.carmax_tags
COMMENT 'CarMax Classification Tags (172 elements)';

-- =====================================================
-- TABLE 1: Data Elements (172 from Excel)
-- =====================================================
CREATE TABLE IF NOT EXISTS main.carmax_taxonomy.data_elements (
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
CREATE TABLE IF NOT EXISTS main.carmax_taxonomy.data_categories (
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
CREATE TABLE IF NOT EXISTS main.carmax_taxonomy.subject_types (
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
CREATE TABLE IF NOT EXISTS main.carmax_taxonomy.taxonomy_versions (
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
CREATE TABLE IF NOT EXISTS main.carmax_taxonomy.element_mappings (
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
-- Indexes for performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_elements_active
ON main.carmax_taxonomy.data_elements (active, element_category);

CREATE INDEX IF NOT EXISTS idx_elements_sensitive
ON main.carmax_taxonomy.data_elements (sensitive_flag);

-- =====================================================
-- Sample data for testing (optional)
-- =====================================================
/*
INSERT INTO main.carmax_taxonomy.subject_types
(subject_type_id, subject_type_name, subject_description)
VALUES
  ('aa2dfd55-ffa1-4bc6-b9e6-335564e3d89c', 'Associate', 'Internal personnel (e.g., employees, contractors)'),
  ('2374b463-0605-4e51-96c1-332addd22e84', 'B2B', 'External business contacts (e.g., vendors, partners)'),
  ('1fdbd718-31f4-4613-a7ca-6564226a0dbf', 'Consumer', 'Individual customers who interact with CarMax for personal or household purposes');
*/

-- =====================================================
-- Grant permissions (adjust as needed)
-- =====================================================
-- GRANT ALL PRIVILEGES ON SCHEMA main.carmax_taxonomy TO `<service-principal-id>`;
-- GRANT ALL PRIVILEGES ON SCHEMA main.carmax_tags TO `<service-principal-id>`;
