-- Fix Tables - Drop and Recreate with All Columns
-- Run this in Databricks SQL Editor to fix the schema mismatch

-- Drop existing tables
DROP TABLE IF EXISTS main.carmax_taxonomy.data_elements;
DROP TABLE IF EXISTS main.carmax_taxonomy.data_categories;
DROP TABLE IF EXISTS main.carmax_taxonomy.subject_types;
DROP TABLE IF EXISTS main.carmax_taxonomy.version_history;

-- Now rerun the full setup_taxonomy.sql script
-- (Copy and paste the entire setup_taxonomy.sql content after this)
