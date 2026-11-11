# Validation record — 2026-11-11

## Acquisition repair validation

- GitHub-hosted probe run [43060974195](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43060974195): metadata HTTP 200, small 2025 query HTTP 200. Official identity `vw6y-z8j6` / `311 Cases`, attribution San Francisco 311. Full schema/types/descriptions saved to `data/source_schema.json`; corrected `agency_responsible`.
- Revised local suite: **38 passed, 6 authentic-artifact checks skipped** because no authentic artifact is configured locally. New coverage includes keyset pages, cross-page duplicates, metadata types/identity, conservative fall-back-hour handling, report generation and safe diagnostics. Compilation and dependency consistency passed.
- First full extraction run [43061652996](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43061652996): source count 872,427; 50,000 rows validated before HTTP 428. No verified bundle produced. Added two-second page pacing, bounded retries including observed 428, and safe status/error diagnostics.
- Successful retry [43062021912](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43062021912): **872,427 downloaded and unique requests**, matching both source counts. All **88 pages** passed SQL/Python parity. Extraction ran 2026-11-11 16:49:30Z–16:58:42Z with an unchanged source update marker. The cube has 474,929 rows and is 3,208,220 bytes.
- Authentic integration suite: **6 passed in 80.53 seconds**, covering aggregate reconciliation, mature unresolved denominators, sensitivity nesting and all five Streamlit sections with category/agency filter interactions. These execute against the artifact in-process; they do not replace the shipped pending bundle.
- Latest Python 3.11 and 3.12 CI jobs on `ad921ed` both passed. Local revised suite: **38 passed, 6 skipped** (authentic integration runs on Actions). The successful acquisition commit `6d2937a` ran its then-current 36 unit tests plus all 6 authentic tests.
- [Review artifact](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43062021912/artifacts/13873914252): 12 files, including cube, provenance, readable data-quality report, observations and comparison/sensitivity CSVs. No raw records were committed or uploaded. The ZIP digest is `47c1015ef20fe0f59cb3936e772a932bdf15b3dac679dc158559db1d517b0a58`.

## Initial dashboard validation (historical record)

## Executed in the managed development environment

- Python 3.12.14; dependencies installed in a project-local development virtual environment. Runtime packages are pinned; NumPy 2.2.6 avoids incompatibility warnings from newer NumPy with pandas 2.3.3.
- `python -m pytest -q`: **32 passed**. Covers exact 7/30-day eligibility, unresolved denominators, invalid/future closure dates, duplicates/missing IDs, daylight-saving ambiguity, zero records, peer exclusion/no overlap, 10/15-point persistence sensitivity, aggregate hash and synthetic marker rejection, mocked ingestion count/schema/page/update failures, five-section pending UI, five-section test-fixture chart rendering, nonempty peer tables/heatmap/briefs, filters and zero-match UI.
- DuckDB normalized-schema SQL and Python produce matching additive cubes on deterministic test fixtures. BigQuery source queries were not executed.
- `python -m compileall -q app.py src`: passed.
- `pip check`: passed.
- Streamlit server starts on localhost; Chromium (Playwright, system `/usr/bin/chromium`) loads the application, navigates all five sections and checks a 390×844 mobile viewport with no JavaScript page errors. Desktop screenshot inspected at 1440×1050. Browser testing uses the shipped evidence-pending bundle; fixture-driven charts are checked with Streamlit AppTest, never published as findings.
- Existing Optiver files were not changed. Only this project and its dedicated Actions workflow are committed. No credentials, raw records, caches or development virtual environment are staged.

## Remaining verification limits

- Codex direct access remains blocked with HTTP CONNECT 403. DataSF schema is now verified through Actions; BigQuery remains unverified and unnecessary. No GCP identity, billing resource or visitor credential is used.
- Full-volume extraction and authentic AppTest UI checks passed on Actions. Authentic evidence was not downloaded into the Codex workspace, and a separate headed-browser test of that artifact was not performed. Source completeness beyond the reconciled public API cohort and causal operational conclusions are not established.
- Python 3.11 locally: only 3.12 is installed here. Both Python 3.11 and 3.12 GitHub Actions jobs subsequently completed successfully on the review commit.
- Public Streamlit hosting: no application was published, so no public deployment is claimed. Account authorization/publication and review of a real bundle remain owner actions.

## Release interpretation

The first authentic analytical package is ready for review; the bundled dashboard deliberately remains **evidence pending**. Screening candidates are reported in the artifact, not promoted into the application. No causal operational failures are confirmed. Use the GitHub-hosted acquisition workflow and README refresh instructions, review quality/provenance, repeat tests and inspect real-data workspaces before treating the portfolio study as evidence complete.
