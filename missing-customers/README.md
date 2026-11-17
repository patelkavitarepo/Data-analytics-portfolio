# Project 005 — The Missing Customers

**Status:** implemented, awaiting real evidence and human interpretation. No empirical findings are bundled. No deployment has been performed.

Where do customers drop off in an online shopping journey, and what can recorded events establish?

## Run locally

From the repository root, with Python 3.11 or 3.12:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r missing-customers/requirements.txt
streamlit run missing-customers/app.py --browser.gatherUsageStats false
```

The application starts without data. Upload a CSV, or put it at the ignored path `missing-customers/data/events.csv` and select the local-file checkbox. Files must be at most 100 MiB; this is a safety limit, not a guarantee that every 100 MiB file fits a particular hosting tier. Raw string columns and intermediate joins can require substantially more RAM. Use a smaller date slice on constrained hosts. Previews are limited to 100 rows; one intake result is cached per server. Uploaded evidence is processed by the Streamlit server: use only data authorized for that host and audience. Source notes are user declarations, not independent verification.

## Acquire evidence reproducibly

1. Visit the [original Retailrocket Kaggle publisher](https://www.kaggle.com/retailrocket/ecommerce-dataset), review its current terms and attribution requirements, and authenticate if required. Download the published archive legitimately and extract `events.csv` locally. No third-party mirrors or fabricated fallback data are used.
2. Record the publisher URL, download time, archive/version and any transformations. Keep a SHA-256 checksum, for example `sha256sum events.csv`. Enter the source notes in the app; record reviewed findings in `research/EVIDENCE.md`.
3. Keep raw and derived evidence outside Git or under the ignored `data/` directory. Distribution rights have not been verified; do not commit the full dataset.
4. Required headers: `timestamp,visitorid,event,itemid`; `transactionid` is optional. Timestamp is integer Unix **milliseconds**, UTC; accepted bounds are 2000-01-01 inclusive through 2100-01-01 exclusive. IDs are read as strings to preserve leading zeros. Supported event values are `view`, `addtocart`, `transaction`.

For a large source, create a bounded-memory date slice before uploading:

```sh
cd missing-customers
python -m src.preprocess /path/to/events.csv data/april-events.csv --start 2015-04-01 --end 2015-04-30
```

Create `data/` first. Dates are inclusive UTC calendar days. The CLI streams 100,000 rows per chunk and refuses to overwrite files. It does not deduplicate across chunks or produce precomputed findings: the app performs the audit. Retain the original file and exact command; slices censor visitor histories and change denominators. Use a narrower window if the slice still exceeds 100 MiB. Malformed CSV/schema errors fail the CLI; invalid timestamps are not included in a slice. Audit the original separately when estimating original-source timestamp errors.

## Analytical definitions

- The audit describes the full input before date and event filtering, including nulls by field, event-type counts, invalid timestamps, missing IDs, exact duplicates, and visitors whose input records reverse chronological order.
- Accepted records exclude invalid timestamps, missing visitor IDs and unsupported/missing event labels. Exact duplicates across **all supplied columns** are removed. A legitimate repeated identical event cannot be distinguished from duplication; audit this assumption.
- Event counts count accepted rows. Stage visitor counts count distinct identifiers and overlap. Neither is a sequential conversion rate. Transaction events and IDs do not establish purchase value or unique purchases.
- The sequential cohort starts with each visitor's earliest view in the selected UTC window, then the earliest strictly later cart and earliest strictly later transaction. Equal timestamps cannot prove order and do not progress. Each visitor contributes at most once; no session boundaries are inferred. Percentages use view entrants as denominator, including zero-safe empty cohorts.
- The same-item check requires a non-null shared item ID for every stage. A visitor contributes once when any item qualifies. Its denominator is visitors with an identified-item view. It is a stricter recorded path, not proof of a continuous shopping session.
- The date filter affects the entire analysis window. Event-type filtering affects only descriptive counts and the event preview; journeys always use all supported stages. Date slicing can omit earlier or later stages. Cohort tables can combine returning visits and visitor-level paths can cross products.
- Missing events can reflect instrumentation, censoring, re-entry or anonymous-ID behavior. Browser identifiers are not known people. Channels, geography, devices, prices, revenue, intent, causal effects and monetary losses are unavailable from these fields.

## Validate

```sh
pip install -r missing-customers/requirements-dev.txt
python -m pytest -q missing-customers/tests
# In another terminal, start the app as above, then:
python missing-customers/tests/browser_smoke.py
```

The browser script uses system Chromium at `/usr/bin/chromium`; adjust that path for other platforms. Tests contain explicitly synthetic fixtures for verification only; these are never bundled as portfolio evidence. The suite covers intake, missing fields/IDs, empty files, timestamp units, duplicates, unordered records, reversed stages, ties, repeated transactions, cross-item paths, offline slicing and Streamlit startup/interactions. Validation results and limits are in [`research/EVIDENCE.md`](research/EVIDENCE.md).

## Streamlit Community Cloud (after human review)

In Community Cloud, select `patelkavitarepo/Data-analytics-portfolio`, the reviewed branch (or `main` after merge), and main file **`missing-customers/app.py`**. Select Python 3.12. Streamlit discovers **`missing-customers/requirements.txt`** beside the entrypoint; no BigQuery account or secrets are required. Start with the empty app, then upload authorized evidence and check the audit. Configure hosting access appropriately before uploading any restricted information. No raw file is expected in Git. Do not publish until the researcher has reviewed the draft PR, source rights and limitations.

## Research and optional extension

Human interpretation is explicitly pending. [`research/EVIDENCE.md`](research/EVIDENCE.md) separates execution checks from empirical findings; [`research/SOURCES.md`](research/SOURCES.md) preserves source context. The unchanged [`sql/01_evidence_intake.sql`](sql/01_evidence_intake.sql) is **optional future GA4/BigQuery comparison**, not a launch requirement and not executed. GA4 and Retailrocket results are not interchangeable. Other portfolio projects are unchanged.
