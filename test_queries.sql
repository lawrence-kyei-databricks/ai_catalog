-- Verify Taxonomy Import
-- Run these queries in Databricks SQL Editor to verify the import

-- 1. Check data elements loaded
SELECT COUNT(*) as element_count FROM main.carmax_taxonomy.data_elements;

-- 2. Check subject types loaded
SELECT COUNT(*) as subject_count FROM main.carmax_taxonomy.subject_types;

-- 3. Check tags created
SELECT COUNT(*) as tag_count FROM main.carmax_taxonomy.data_elements WHERE active = true;

-- 4. View sample elements
SELECT element_id, element_name, element_category, sensitive_flag
FROM main.carmax_taxonomy.data_elements
LIMIT 10;

-- 5. View subject types
SELECT * FROM main.carmax_taxonomy.subject_types;
