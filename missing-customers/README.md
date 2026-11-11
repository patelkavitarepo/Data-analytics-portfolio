# Project 004 — The Missing Customers

**Status:** Investigation setup / no empirical findings yet.

## Case question
Where might potential customers drop out of the shopping journey, and what can the event-level evidence actually support?

## Dataset
- Source: Google Merchandise Store obfuscated GA4 BigQuery ecommerce sample.
- Tables: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
- Period: 2020-11-01 through 2021-01-31.
- Official documentation: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset

**Caution:** Google deliberately obfuscated the dataset. Some values are placeholders or null, and its internal consistency may be limited. Results are historical, sample-specific, and are not verified business performance for the current Google Merchandise Store.

## Investigation sequence (proposed, not yet interpreted)
1. **Evidence intake:** Check covered dates, event volume, user IDs and missingness.
2. **Event instrumentation audit:** Determine which ecommerce event types exist and whether IDs and timestamps support journey reconstruction.
3. **Definitions:** Distinguish events, users, sessions, transaction IDs, and purchases; test for duplicate/missing IDs.
4. **Funnel analysis:** Reconstruct stage progression with ordering and a consistent analysis unit. Do **not** call unrelated stage totals a sequential funnel.
5. **Segment comparisons:** Examine acquisition/device/geography only where the fields are sufficiently complete and interpretable.
6. **Alternative explanations and implications:** Test rival explanations and separate observed associations from causal claims.

## How to reproduce the first check
1. Open the [BigQuery console](https://console.cloud.google.com/bigquery).
2. Select a Google Cloud project with BigQuery enabled (Sandbox or free tier is sufficient for light exploration).
3. Run `sql/01_evidence_intake.sql`.
4. Inspect BigQuery's estimated bytes processed before running.
5. Record the returned result in `research/EVIDENCE.md` **only after it is actually run**. Do not invent values.

## Research conventions
- Queries are a proposed methodology, not proof they executed.
- Raw data remains on BigQuery; do not commit credential files or sensitive data.
- Document missingness, failures, ambiguous metrics, and contrary evidence.
- Distinguish human researcher interpretations/decisions from AI-generated drafts.
- Keep work in this branch until ready for human review.