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

## Publisher listing verified — 2026-11-11

The [original Kaggle Retailrocket page](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset/home) currently lists the dataset under **Creative Commons Attribution–NonCommercial–ShareAlike 4.0 (CC BY-NC-SA 4.0)**. License terms: https://creativecommons.org/licenses/by-nc-sa/4.0/

- Attribute the original dataset and its publisher, identify material transformations, and respect noncommercial and share-alike requirements where applicable. A public portfolio website does not automatically grant permission to redistribute the full raw dataset or use it commercially.
- Original publisher description reports **2,756,101 event rows**, including **2,664,312 views**, **69,332 add-to-cart events**, **22,457 transactions**, and **1,407,580 unique visitor identifiers** spanning ~4.5 months. These are **publisher-reported reference counts, not findings from our pipeline**.
- Researcher should obtain the original publisher archive under the published terms, record source URL, download date and file SHA-256, then compare our full-file intake totals with the publisher's figures. Differences require investigation; they are not automatically errors.
- Raw data remains out of Git; the dashboard must disclose that user-provided uploaded files are not provenance-verified. Before a public deployment, decide whether exposing raw identifiers or downloadable records is appropriate for this license and audience. Do not represent a dashboard showing only an uploaded subset as analysis of the full dataset.

**Execution status:** license and source listing verified via public documentation; real data has **not** been downloaded or analyzed here. No audit output has been verified.
