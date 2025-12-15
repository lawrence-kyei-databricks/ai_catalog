-- Verify Unity Catalog Tags
-- Run these queries to verify tags were applied

-- 1. List all tags created
SHOW TAGS IN main.carmax_tags;

-- 2. View tags applied to columns
SELECT
  catalog_name,
  schema_name,
  table_name,
  column_name,
  tag_name,
  tag_value
FROM system.information_schema.column_tags
WHERE tag_name LIKE 'main.carmax_tags.%'
ORDER BY table_name, column_name;

-- 3. Check specific table tags
DESCRIBE TABLE EXTENDED main.carmax_test.customers;

-- 4. View tag lineage for a specific column
SELECT * FROM system.information_schema.column_tags
WHERE catalog_name = 'main'
  AND schema_name = 'carmax_test'
  AND table_name = 'customers'
  AND column_name = 'ssn';

-- 5. Count tags by table
SELECT
  table_name,
  COUNT(*) as tagged_columns
FROM system.information_schema.column_tags
WHERE tag_name LIKE 'main.carmax_tags.%'
GROUP BY table_name
ORDER BY tagged_columns DESC;
