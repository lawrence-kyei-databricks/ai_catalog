-- Create Test Data for Classification
-- Run this in Databricks SQL Editor to create sample data

-- Create test schema
CREATE SCHEMA IF NOT EXISTS main.carmax_test;

-- Create sample customer table with various data types
CREATE OR REPLACE TABLE main.carmax_test.customers (
  customer_id INT,
  first_name STRING,
  last_name STRING,
  email STRING,
  phone_number STRING,
  ssn STRING,
  date_of_birth DATE,
  address STRING,
  city STRING,
  state STRING,
  zip_code STRING,
  credit_score INT,
  account_balance DECIMAL(10,2),
  created_at TIMESTAMP
);

-- Insert sample data
INSERT INTO main.carmax_test.customers VALUES
  (1, 'John', 'Doe', 'john.doe@email.com', '555-123-4567', '123-45-6789', '1980-05-15', '123 Main St', 'Richmond', 'VA', '23220', 750, 25000.00, current_timestamp()),
  (2, 'Jane', 'Smith', 'jane.smith@email.com', '555-987-6543', '987-65-4321', '1985-08-22', '456 Oak Ave', 'Norfolk', 'VA', '23510', 680, 15000.00, current_timestamp()),
  (3, 'Bob', 'Johnson', 'bob.j@email.com', '555-456-7890', '456-78-9012', '1990-03-10', '789 Pine Rd', 'Arlington', 'VA', '22201', 720, 30000.00, current_timestamp());

-- Grant permissions to service principal
GRANT SELECT ON TABLE main.carmax_test.customers TO `47e9c744-0efc-494d-8d8f-baac21801d18`;
GRANT MODIFY ON TABLE main.carmax_test.customers TO `47e9c744-0efc-494d-8d8f-baac21801d18`;

-- Verify test data
SELECT * FROM main.carmax_test.customers;
