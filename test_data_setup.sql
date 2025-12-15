-- =====================================================
-- Test Data Setup for CarMax Classification Platform
-- Run this in Databricks SQL Editor
-- =====================================================

-- Create test schema
CREATE SCHEMA IF NOT EXISTS main.carmax_class_test
COMMENT 'Test schema for data classification platform';

-- Grant permissions to app service principal
GRANT ALL PRIVILEGES ON SCHEMA main.carmax_class_test TO `47e9c744-0efc-494d-8d8f-baac21801d18`;

-- =====================================================
-- Table 1: Customer Data (PII-heavy)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.customers (
  customer_id BIGINT COMMENT 'Unique customer identifier',
  first_name STRING COMMENT 'Customer first name',
  last_name STRING COMMENT 'Customer last name',
  email STRING COMMENT 'Customer email address',
  phone_number STRING COMMENT 'Customer phone number',
  ssn STRING COMMENT 'Social security number',
  date_of_birth DATE COMMENT 'Customer date of birth',
  drivers_license STRING COMMENT 'Driver license number',
  street_address STRING COMMENT 'Street address',
  city STRING COMMENT 'City',
  state STRING COMMENT 'State',
  zip_code STRING COMMENT 'ZIP code',
  created_at TIMESTAMP COMMENT 'Record creation timestamp'
)
COMMENT 'Customer information with PII data';

-- Insert sample data
INSERT INTO main.carmax_class_test.customers VALUES
  (1, 'John', 'Smith', 'john.smith@email.com', '555-123-4567', '123-45-6789', '1985-03-15', 'D1234567', '123 Main St', 'Richmond', 'VA', '23220', current_timestamp()),
  (2, 'Jane', 'Doe', 'jane.doe@email.com', '555-987-6543', '987-65-4321', '1990-07-22', 'D9876543', '456 Oak Ave', 'Glen Allen', 'VA', '23060', current_timestamp()),
  (3, 'Bob', 'Johnson', 'bob.j@email.com', '555-555-5555', '555-55-5555', '1978-12-01', 'D5555555', '789 Elm St', 'Henrico', 'VA', '23229', current_timestamp());

-- =====================================================
-- Table 2: Vehicles (Less sensitive)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.vehicles (
  vin STRING COMMENT 'Vehicle identification number',
  make STRING COMMENT 'Vehicle manufacturer',
  model STRING COMMENT 'Vehicle model',
  year INT COMMENT 'Model year',
  color STRING COMMENT 'Vehicle color',
  license_plate STRING COMMENT 'License plate number',
  mileage INT COMMENT 'Current mileage',
  price DECIMAL(10,2) COMMENT 'Sale price',
  purchase_date DATE COMMENT 'Date purchased'
)
COMMENT 'Vehicle inventory data';

-- Insert sample data
INSERT INTO main.carmax_class_test.vehicles VALUES
  ('1HGBH41JXMN109186', 'Honda', 'Accord', 2018, 'Silver', 'ABC-1234', 45000, 18500.00, '2023-01-15'),
  ('5FNRL6H78MB123456', 'Honda', 'Odyssey', 2021, 'White', 'XYZ-9876', 28000, 32000.00, '2023-06-22'),
  ('1FTFW1ET5DFC12345', 'Ford', 'F-150', 2019, 'Blue', 'DEF-5555', 62000, 28900.00, '2023-03-10');

-- =====================================================
-- Table 3: Transactions (Financial)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.transactions (
  transaction_id BIGINT COMMENT 'Transaction identifier',
  customer_id BIGINT COMMENT 'Customer ID',
  vin STRING COMMENT 'Vehicle VIN',
  transaction_date TIMESTAMP COMMENT 'Transaction date',
  sale_price DECIMAL(10,2) COMMENT 'Final sale price',
  credit_card_last4 STRING COMMENT 'Last 4 digits of credit card',
  payment_method STRING COMMENT 'Payment method used',
  tax_amount DECIMAL(10,2) COMMENT 'Tax amount',
  total_amount DECIMAL(10,2) COMMENT 'Total transaction amount',
  bank_account_number STRING COMMENT 'Bank account number for financing'
)
COMMENT 'Sales transaction records';

-- Insert sample data
INSERT INTO main.carmax_class_test.transactions VALUES
  (1001, 1, '1HGBH41JXMN109186', '2023-01-15 14:30:00', 18500.00, '4532', 'Credit Card', 1480.00, 19980.00, NULL),
  (1002, 2, '5FNRL6H78MB123456', '2023-06-22 10:15:00', 32000.00, '8765', 'Financing', 2560.00, 34560.00, '****1234'),
  (1003, 3, '1FTFW1ET5DFC12345', '2023-03-10 16:45:00', 28900.00, '1111', 'Credit Card', 2312.00, 31212.00, NULL);

-- =====================================================
-- Table 4: Employee Data (Internal)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.employees (
  employee_id BIGINT COMMENT 'Employee ID',
  username STRING COMMENT 'System username',
  first_name STRING COMMENT 'First name',
  last_name STRING COMMENT 'Last name',
  employee_email STRING COMMENT 'Work email address',
  department STRING COMMENT 'Department name',
  job_title STRING COMMENT 'Job title',
  salary DECIMAL(10,2) COMMENT 'Annual salary',
  ssn STRING COMMENT 'Social security number',
  hire_date DATE COMMENT 'Date of hire',
  manager_id BIGINT COMMENT 'Manager employee ID'
)
COMMENT 'Employee directory and HR information';

-- Insert sample data
INSERT INTO main.carmax_class_test.employees VALUES
  (101, 'jsmith', 'John', 'Smith', 'john.smith@carmax.com', 'Sales', 'Sales Associate', 45000.00, '111-11-1111', '2020-01-15', 201),
  (102, 'mjones', 'Mary', 'Jones', 'mary.jones@carmax.com', 'Finance', 'Finance Manager', 75000.00, '222-22-2222', '2018-03-22', 202),
  (201, 'rmanager', 'Robert', 'Manager', 'robert.m@carmax.com', 'Sales', 'Sales Manager', 85000.00, '333-33-3333', '2015-06-01', NULL);

-- =====================================================
-- Table 5: Service Records (Mixed sensitivity)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.service_records (
  service_id BIGINT COMMENT 'Service record ID',
  vin STRING COMMENT 'Vehicle VIN',
  customer_id BIGINT COMMENT 'Customer ID',
  service_date DATE COMMENT 'Date of service',
  service_type STRING COMMENT 'Type of service performed',
  technician_name STRING COMMENT 'Technician who performed service',
  cost DECIMAL(10,2) COMMENT 'Service cost',
  notes STRING COMMENT 'Service notes'
)
COMMENT 'Vehicle service and maintenance records';

-- Insert sample data
INSERT INTO main.carmax_class_test.service_records VALUES
  (5001, '1HGBH41JXMN109186', 1, '2023-02-10', 'Oil Change', 'Mike Wilson', 45.00, 'Standard oil change and filter replacement'),
  (5002, '5FNRL6H78MB123456', 2, '2023-07-15', 'Brake Service', 'Sarah Chen', 350.00, 'Replaced front brake pads'),
  (5003, '1FTFW1ET5DFC12345', 3, '2023-04-05', 'Tire Rotation', 'Mike Wilson', 35.00, 'Rotated all four tires');

-- =====================================================
-- Table 6: Marketing Data (Contact info)
-- =====================================================
CREATE OR REPLACE TABLE main.carmax_class_test.marketing_contacts (
  contact_id BIGINT COMMENT 'Contact ID',
  email_address STRING COMMENT 'Email address',
  phone STRING COMMENT 'Phone number',
  preferred_contact STRING COMMENT 'Preferred contact method',
  opted_in BOOLEAN COMMENT 'Marketing opt-in status',
  ip_address STRING COMMENT 'IP address from signup',
  user_agent STRING COMMENT 'Browser user agent',
  signup_date TIMESTAMP COMMENT 'Date signed up for marketing'
)
COMMENT 'Marketing contact list';

-- Insert sample data
INSERT INTO main.carmax_class_test.marketing_contacts VALUES
  (9001, 'prospect1@email.com', '555-111-2222', 'Email', true, '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2023-08-01 09:15:00'),
  (9002, 'lead2@email.com', '555-333-4444', 'Phone', false, '192.168.1.101', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)', '2023-08-15 14:22:00'),
  (9003, 'customer3@email.com', '555-777-8888', 'Email', true, '192.168.1.102', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '2023-09-01 11:30:00');

-- =====================================================
-- Verify tables were created
-- =====================================================
SHOW TABLES IN main.carmax_class_test;

-- Show sample row counts
SELECT 'customers' as table_name, COUNT(*) as row_count FROM main.carmax_class_test.customers
UNION ALL
SELECT 'vehicles', COUNT(*) FROM main.carmax_class_test.vehicles
UNION ALL
SELECT 'transactions', COUNT(*) FROM main.carmax_class_test.transactions
UNION ALL
SELECT 'employees', COUNT(*) FROM main.carmax_class_test.employees
UNION ALL
SELECT 'service_records', COUNT(*) FROM main.carmax_class_test.service_records
UNION ALL
SELECT 'marketing_contacts', COUNT(*) FROM main.carmax_class_test.marketing_contacts;
