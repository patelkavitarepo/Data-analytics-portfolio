# Research evidence — Project 005

## Empirical intake — 2026-11-11 UTC (independent full-source audit)

**Status:** Full `events.csv` from a user-provided Retailrocket-labelled archive was independently audited outside GitHub. Counts match the original publisher's advertised event/visitor totals. This is **not** proof of the file's provenance and is **not yet a Streamlit full-source performance test**. Human interpretation remains pending.

- Original listing: https://www.kaggle.com/retailrocket/ecommerce-dataset
- Input: user-supplied `events.csv.zip` containing one `events.csv`; archived CSV decompressed size **94,237,913 bytes** (no subset or date slicing). Archive size **33,971,694 bytes**.
- Archive SHA-256: `b605e916a9379585d4a0a3f3c76abe7e5be4ed178b73d969e89061a2340ae191`
- Extracted CSV SHA-256: `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`
- Source download timestamp/version: **not independently verified**; supplied by the researcher on 2026-11-11.
- Method: independent pandas (2.2.3) full CSV intake; IDs retained numerically for this publisher's integer IDs. Timestamp interpreted as Unix milliseconds, dates UTC. Full-row exact deduplication using all five input columns. Invalid/missing visitor IDs, timestamps and unsupported event types excluded; then grouped by visitor, with strict `view_time < cart_time < transaction_time`. Same-item sensitivity additionally required the same `itemid` for all stages. No session inference.

### Audited input and quality

| Measure | Observed |
|---|---:|
| Raw event rows | 2,756,101 |
| Distinct visitor IDs in full file | 1,407,580 |
| Distinct item IDs | 235,061 |
| Raw view events | 2,664,312 |
| Raw add-to-cart events | 69,332 |
| Raw transaction events | 22,457 |
| Exact full-row duplicates | 460 |
| Accepted rows after deduplication | 2,755,641 |
| Invalid timestamps / missing visitor IDs / missing item IDs / unsupported event types | 0 / 0 / 0 / 0 |
| Non-null transaction IDs | 22,457 event rows |
| Distinct transaction IDs | 17,672 |
| Input-order reversals (visitor IDs affected) | 259,807 |
| Earliest timestamp (UTC) | 2015-05-03 03:00:04.384 |
| Latest timestamp (UTC) | 2015-09-18 02:59:47.788 |

The event file's **transactionid** is intentionally blank on non-transaction events (2,733,644 rows); do not categorize these as unexplained missing values. Input-order reversals show raw rows are not sorted by visitor's timestamp; they do **not** establish timestamp corruption. All 460 duplicates were views/carts; accepted transaction event count remained 22,457. Counts for raw events and visitor IDs match publisher-reported figures; this is a cross-check, not provenance authentication.

### Descriptive visitor/event counts and strict temporal journeys

| Measure | Visitors |
|---|---:|
| At least one accepted product view | 1,404,179 |
| At least one accepted cart event (any order) | 37,722 |
| At least one accepted transaction event (any order) | 11,719 |
| View → later cart | 32,934 |
| View → later cart → later transaction | 9,952 |
| Same-item view → later cart | 30,344 |
| Same-item view → later cart → later transaction | 9,641 |

- Broad visitor-level sequential cart progression: **2.3454%** of view-entrants.
- Broad visitor-level sequential transaction progression: **0.7087%** of view-entrants or **30.2180%** of ordered cart-stage visitors.
- Same-item progression: **2.1610%** of identified-item view-entrants reached cart; **0.6866%** reached a later transaction. These are recorded visitor sequences across the entire observation span, **not session conversion rates**.
- Event counts, distinct visitors participating at any stage, and ordered-journey cohorts are **different units**. No monetary loss, actual customer intent, root cause or causal interpretation is supported by these fields.
- Next validation: compare the same calculations in the deployed app or exact `src.analytics` functions, assess full-source hosting memory, and test sensitivity to observation windows / tied timestamps / repeat behavior.

### Additional supplied file

`category_tree.csv`: 1,669 rows, unique category IDs 1,669, and 25 records with blank parent IDs. This is a hierarchy reference, not an event-level item-category mapping. It was **not joined to events**. The evidence above is based solely on `events.csv`.

**Researcher interpretation:** **PENDING.** The AI's potential leads or competing explanations are not findings attributed to the researcher.

## Implementation execution — 2026-11-11 UTC

Synthetic fixtures used in automated tests only. They are not empirical evidence and do not appear as startup findings. Final validation completed in this managed Linux environment:

- Python 3.12; Streamlit 1.67.0, pandas 2.3.3, Plotly 6.9.0. No BigQuery or paid service.
- `python -m pytest -q missing-customers/tests`: **12 passed in 2.51 seconds** (intake, journey edge cases, offline slicing and Streamlit AppTest).
- `streamlit run missing-customers/app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false` plus `python missing-customers/tests/browser_smoke.py`: **passed** in real system Chromium. Verified empty state, synthetic CSV upload, quality-summary download, journey tab, 390 px mobile viewport and invalid-schema error.
- `python -m compileall -q missing-customers/app.py missing-customers/src` and `git diff --check`: **passed**.
- Initial browser upload failed because Streamlit telemetry attempted to write to the read-only home directory. Restarting with `--browser.gatherUsageStats false` resolved the environment issue; the documented start command includes that flag.
- Initial test execution exposed an empty-input audit reduction bug; fixed before final verification.
- Human interpretation: **pending**. Do not attribute AI hypotheses to the researcher.

## Limits requiring review

Strict temporal ordering excludes equal-timestamp stages. The visitor funnel can cross products and visits; the same-item check narrows product ambiguity but does not infer sessions or known people. The date window can censor both ends of paths. Exact duplicate removal may remove genuine identical events. Missing item IDs remain in the broad visitor analysis and are excluded from the item-matched cohort. Invalid/missing visitor IDs, unsupported events and invalid timestamps are excluded and counted. Transaction records are not deduplicated into confirmed purchases beyond exact-row deduplication. No revenue or monetary loss can be computed.

The 100 MiB file limit, single cached intake and limited previews reduce resource exposure, but raw strings and intermediate joins may still exceed low-memory hosting capacity. An independent full-source pandas audit has been completed, but the exact Streamlit app has not yet been stress-tested on the full source and Community Cloud deployment has not been tested. The streaming CLI makes date slices, not complete visitor histories or a full-source audit. Original timestamp errors outside a slice are not measured by its audit. App/hosting performance and substantive human conclusions on real data remain pending.

## Optional GA4 intake — not executed

The preserved `sql/01_evidence_intake.sql` is a future optional BigQuery adapter, not part of Streamlit startup. Execution date, project/location, bytes processed, coverage, rows and user-ID quality remain **pending**. Google cautions that the obfuscated GA4 sample has placeholders and limited internal consistency: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset
