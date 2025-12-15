-- Verify Classifications
-- Run these queries after classification completes

-- 1. View all classifications
SELECT
  catalog_name,
  schema_name,
  table_name,
  column_name,
  suggested_element,
  confidence_score,
  sensitive_flag,
  review_status,
  review_priority
FROM main.carmax_governance.classification_governance
ORDER BY created_at DESC;

-- 2. Check classification statistics
SELECT
  review_status,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence
FROM main.carmax_governance.classification_governance
GROUP BY review_status;

-- 3. View high-confidence classifications
SELECT
  table_name,
  column_name,
  suggested_element,
  confidence_score,
  sensitive_flag
FROM main.carmax_governance.classification_governance
WHERE confidence_score >= 90
ORDER BY confidence_score DESC;

-- 4. View pending reviews
SELECT
  table_name,
  column_name,
  suggested_element,
  confidence_score,
  review_priority,
  reasoning
FROM main.carmax_governance.classification_governance
WHERE review_status = 'PENDING'
ORDER BY review_priority, confidence_score DESC;
