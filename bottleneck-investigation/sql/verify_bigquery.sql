-- Metadata-only candidate inspection. NOT executed or verified in this environment.
-- Do not create a billing project or run a paid scan. DataSF is the free fallback.
SELECT table_name, column_name, data_type
FROM `bigquery-public-data.san_francisco_311.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '311_service_requests'
ORDER BY ordinal_position;
-- Only after identity/schema verification, design a year-restricted query using
-- actual timestamp names and inspect a dry-run cost estimate before execution.
