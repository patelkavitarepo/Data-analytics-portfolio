# Project 005 — The Missing Customers

**Status:** Investigation setup / no empirical findings yet.

## Case question
Where might potential customers drop out of the shopping journey, and what can the event-level evidence actually support?

## Dataset and stack
- **Primary portable v1 source (proposed):** Retailrocket Ecommerce event logs, `events.csv`, https://www.kaggle.com/retailrocket/ecommerce-dataset
- **V1 stack:** GitHub → Codex → Streamlit Community Cloud. The app will support CSV upload and reproducible local processing; no BigQuery account needed.
- **Optional source for a future extension:** Google Merchandise Store obfuscated GA4 sample in BigQuery. The original SQL intake remains at `sql/01_evidence_intake.sql` and has **not** been run.
- **Source cautions:** Retailrocket contains hashed IDs and event logs, not sales revenue, channel attribution, or directly observed customer intent. GA4's obfuscated sample also has documented consistency limits. Neither supports claims about what *caused* lost conversions without additional evidence.
- **Codex build specification:** [`CODEX_TASK.md`](CODEX_TASK.md).
- **Evidence log:** [`research/EVIDENCE.md`](research/EVIDENCE.md). No empirical data has yet been analyzed in this project.

## Investigation sequence (proposed, not yet interpreted)
1. **Evidence intake:** Check covered dates, event volume, user IDs and missingness.
2. **Event instrumentation audit:** Determine which ecommerce event types exist and whether IDs and timestamps support journey reconstruction.
3. **Definitions:** Distinguish events, users, sessions, transaction IDs, and purchases; test for duplicate/missing IDs.
4. **Funnel analysis:** Reconstruct stage progression with ordering and a consistent analysis unit. Do **not** call unrelated stage totals a sequential funnel.
5. **Segment comparisons:** Examine acquisition/device/geography only where the fields are sufficiently complete and interpretable.
6. **Alternative explanations and implications:** Test rival explanations and separate observed associations from causal claims.

## How to get started
1. Have Codex read [`CODEX_TASK.md`](CODEX_TASK.md) and implement the Streamlit app in `missing-customers/` on this working branch.
2. Download `events.csv` from the Retailrocket dataset page when its terms and access allow; keep the file outside git or use the planned CSV uploader.
3. Run Codex's tests and inspect data-quality checks before interpreting any results.
4. After reviewing and merging tested code, deploy `missing-customers/app.py` on [Streamlit Community Cloud](https://share.streamlit.io).
5. BigQuery users can *optionally* run `sql/01_evidence_intake.sql` against the separate GA4 sample, after checking estimated bytes processed; its results are not interchangeable with Retailrocket.

## Research conventions
- Queries are a proposed methodology, not proof they executed.
- Raw data remains on BigQuery; do not commit credential files or sensitive data.
- Document missingness, failures, ambiguous metrics, and contrary evidence.
- Distinguish human researcher interpretations/decisions from AI-generated drafts.
- Keep work in this branch until ready for human review.