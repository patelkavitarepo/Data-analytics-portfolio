-- Project 005 | 01: evidence intake
-- Purpose: verify volume, date coverage, and availability of user identifiers.
-- Dataset: Google's publicly available, obfuscated GA4 ecommerce sample.
-- Expected date range: 2020-11-01 to 2021-01-31 (92 calendar days).
-- This is a descriptive audit; it does not measure a conversion funnel.
-- Check BigQuery's estimated bytes processed before running.

SELECT
  MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_event_date,
  MAX(PARSE_DATE('%Y%m%d', event_date)) AS last_event_date,
  COUNT(DISTINCT event_date) AS observed_days,
  COUNT(*) AS event_rows,
  COUNT(DISTINCT user_pseudo_id) AS distinct_non_null_user_ids,
  COUNTIF(user_pseudo_id IS NULL) AS events_missing_user_id,
  ROUND(SAFE_DIVIDE(COUNTIF(user_pseudo_id IS NULL), COUNT(*)) * 100, 2)
    AS pct_events_missing_user_id
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131';
