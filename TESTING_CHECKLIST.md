# CarMax Data Classification Platform - Testing Checklist

## Prerequisites
- [ ] SQL setup scripts executed (setup_taxonomy.sql, setup_governance.sql)
- [ ] Service principal permissions granted
- [ ] App deployed and running
- [ ] Excel files ready (Data Elements + Subject Types)

## 1. Taxonomy Import Test
- [ ] Navigate to app URL
- [ ] Go to Taxonomy tab
- [ ] Upload Data Elements Excel file
- [ ] Upload Subject Types Excel file
- [ ] Click "Import Taxonomy" button
- [ ] Verify success message appears
- [ ] Verify status banner shows "✓ Ready (172 elements)" or similar
- [ ] Check Dashboard tab shows element count

**SQL Verification:**
```sql
SELECT COUNT(*) FROM main.carmax_taxonomy.data_elements;  -- Should return 172
SELECT COUNT(*) FROM main.carmax_taxonomy.subject_types;  -- Should return 3
```

## 2. Test Data Setup
- [ ] Run create_test_data.sql in Databricks SQL Editor
- [ ] Verify main.carmax_test.customers table created
- [ ] Verify 3 sample rows inserted
- [ ] Verify service principal has SELECT/MODIFY permissions

## 3. Column Classification Test
- [ ] Go to Classify tab in app
- [ ] Select catalog: main
- [ ] Select schema: carmax_test
- [ ] Click "Classify Columns" button
- [ ] Wait for classification to complete
- [ ] Verify success message shows number of columns classified
- [ ] Check Dashboard tab updates with classification count

**Expected Classifications:**
- ssn → Social Security Number (high confidence, sensitive)
- email → Email Address (high confidence)
- phone_number → Phone Number (high confidence)
- first_name → First Name
- last_name → Last Name
- date_of_birth → Date of Birth (sensitive)
- address, city, state, zip_code → Address components
- credit_score → Credit Score (sensitive)

**SQL Verification:**
```sql
SELECT column_name, suggested_element, confidence_score, sensitive_flag
FROM main.carmax_governance.classification_governance
WHERE schema_name = 'carmax_test'
ORDER BY confidence_score DESC;
```

## 4. Review Classifications Test
- [ ] Go to Review tab
- [ ] Verify pending classifications appear (if any require review)
- [ ] For each classification:
  - [ ] View suggested element
  - [ ] Check confidence score
  - [ ] Verify sensitive flag is correct
  - [ ] Click Approve or Reject
- [ ] Verify item disappears from pending list after approval

**SQL Verification:**
```sql
SELECT review_status, COUNT(*) as count
FROM main.carmax_governance.classification_governance
GROUP BY review_status;
```

## 5. Tag Application Test
- [ ] Ensure classifications are approved
- [ ] Call apply tags API or use UI button (if available)
- [ ] Verify success message
- [ ] Check Dashboard shows tags applied count

**SQL Verification:**
```sql
-- Check tags were created
SHOW TAGS IN main.carmax_tags;

-- Check tags applied to columns
SELECT table_name, column_name, tag_name
FROM system.information_schema.column_tags
WHERE tag_name LIKE 'main.carmax_tags.%';
```

## 6. Unity Catalog Integration Test
- [ ] Open Databricks workspace
- [ ] Navigate to Unity Catalog Explorer
- [ ] Browse to main → carmax_test → customers
- [ ] Click on "ssn" column
- [ ] Verify tag appears: main.carmax_tags.social_security_number
- [ ] Check other classified columns for tags

## 7. End-to-End Workflow Test
- [ ] Create new test table with different data
- [ ] Classify columns
- [ ] Review and approve
- [ ] Apply tags
- [ ] Verify in Unity Catalog
- [ ] Verify lineage tracking works

## 8. Performance Test
- [ ] Classify 50+ columns
- [ ] Measure time to complete
- [ ] Verify auto-approval rate (should be ~90%)
- [ ] Check only low-confidence items require review

## 9. Error Handling Test
- [ ] Try classifying with invalid catalog name
- [ ] Try classifying empty schema
- [ ] Upload invalid Excel file format
- [ ] Verify appropriate error messages appear

## 10. Dashboard Validation
- [ ] Check all statistics display correctly:
  - [ ] Data Elements count
  - [ ] UC Tags count
  - [ ] Total Classifications
  - [ ] Pending Review count
- [ ] Verify numbers match SQL queries

## Common Issues & Solutions

### Issue: Taxonomy shows "Not Initialized"
**Solution:** Upload Excel files via Taxonomy tab

### Issue: Classification fails with permission error
**Solution:** Grant permissions to service principal (see README)

### Issue: Tags don't appear in Unity Catalog
**Solution:**
1. Check tags were created: `SHOW TAGS IN main.carmax_tags`
2. Verify apply-tags API was called
3. Check service principal has MODIFY permission on catalog

### Issue: Low confidence scores
**Solution:**
- Check if sample data in columns is representative
- Verify column names are descriptive
- May need more sample data for better classification

## Success Criteria
- ✅ 172 taxonomy elements loaded
- ✅ All test columns classified
- ✅ Auto-approval rate ≥ 85%
- ✅ Tags visible in Unity Catalog
- ✅ No errors in classification process
- ✅ Sensitive data flagged correctly
