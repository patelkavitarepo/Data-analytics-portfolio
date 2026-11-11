# Source decision / event-data contract

## Existing source
The initial scoping draft selected the Google Merchandise Store GA4 obfuscated BigQuery sample (`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`), whose first intake query remains at `sql/01_evidence_intake.sql`. This is **optional** and has not been executed.

## Proposed no-BigQuery v1 source
Retailrocket Ecommerce event logs: https://www.kaggle.com/retailrocket/ecommerce-dataset

`events.csv` fields typically include:
- `timestamp` — Unix milliseconds
- `visitorid` — anonymized visitor identifier
- `event` — `view`, `addtocart`, `transaction`
- `itemid` — anonymized product identifier
- `transactionid` — populated on transaction events when available

This source records events, **not** real sessions, channel attribution, cart monetary values, or revenue. We cannot directly calculate lost revenue or diagnose causes. Attribute the dataset to its publisher. Do not redistribute raw data without checking its permissions.

**Status:** Proposed input for implementation. No dataset downloaded or analyzed in this repository yet. No empirical findings approved. The primary business question remains unchanged.
