-- DuckDB executable parity query over the normalized requests relation.
-- created_at/closed_at are TIMESTAMPTZ; as_of is bound by the caller ($as_of).
-- No BigQuery field names are assumed. See verify_bigquery.sql first.
WITH base AS (
 SELECT *, CAST(timezone('America/Los_Angeles', created_at) AS DATE)::VARCHAR AS created_date,
   epoch(closed_at-created_at)/86400.0 AS elapsed,
   NOT timestamp_uncertain AND status='closed' AND closed_at>=created_at AND closed_at<=$as_of::TIMESTAMPTZ AS valid,
   epoch($as_of::TIMESTAMPTZ-created_at)/86400.0 AS age
 FROM requests
)
SELECT created_date, category, agency, neighborhood,
 CASE WHEN valid THEN floor(elapsed)::INTEGER ELSE -1 END AS duration_day,
 count(*) AS requests,
 sum(CASE WHEN age>=7 THEN 1 ELSE 0 END) AS eligible7,
 sum(CASE WHEN age>=7 AND valid AND elapsed<=7 THEN 1 ELSE 0 END) AS closed7,
 sum(CASE WHEN age>=30 THEN 1 ELSE 0 END) AS eligible30,
 sum(CASE WHEN age>=30 AND valid AND elapsed<=30 THEN 1 ELSE 0 END) AS closed30,
 sum(CASE WHEN valid THEN 1 ELSE 0 END) AS closed_valid
FROM base GROUP BY ALL;
