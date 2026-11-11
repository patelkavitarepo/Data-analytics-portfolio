# Research evidence — Project 005

## Empirical intake: pending

As of 2026-11-11 UTC, no real Retailrocket file was present in this checkout or analyzed in this implementation. No event counts, customer counts, conversion rates or empirical conclusions are claimed. Data acquisition from the original Kaggle publisher remains a human step subject to its current terms/access. No full raw dataset is committed and redistribution rights have not been verified.

Primary proposed source: https://www.kaggle.com/retailrocket/ecommerce-dataset

Record the following after real intake: download timestamp/version, source checksum, transformations/date-slice command, source notes, quality-summary download, full-input counts, excluded rows, UTC coverage, selected date window, visitor denominators, ordered stage counts, same-item sensitivity, timestamp ties and contrary evidence. The app's audit is descriptive and does not authenticate provenance.

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

The 100 MiB file limit, single cached intake and limited previews reduce resource exposure, but raw strings and intermediate joins may still exceed low-memory hosting capacity. No full Retailrocket-scale load or Community Cloud deployment has been tested. The streaming CLI makes date slices, not complete visitor histories or a full-source audit. Original timestamp errors outside a slice are not measured by its audit. Performance and conclusions on real data remain pending.

## Optional GA4 intake — not executed

The preserved `sql/01_evidence_intake.sql` is a future optional BigQuery adapter, not part of Streamlit startup. Execution date, project/location, bytes processed, coverage, rows and user-ID quality remain **pending**. Google cautions that the obfuscated GA4 sample has placeholders and limited internal consistency: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset
