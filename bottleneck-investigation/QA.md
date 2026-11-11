# Validation record — 2026-11-11

## Executed in the managed development environment

- Python 3.12.14; dependencies installed in a project-local development virtual environment. Runtime packages are pinned; NumPy 2.2.6 avoids incompatibility warnings from newer NumPy with pandas 2.3.3.
- `python -m pytest -q`: **32 passed**. Covers exact 7/30-day eligibility, unresolved denominators, invalid/future closure dates, duplicates/missing IDs, daylight-saving ambiguity, zero records, peer exclusion/no overlap, 10/15-point persistence sensitivity, aggregate hash and synthetic marker rejection, mocked ingestion count/schema/page/update failures, five-section pending UI, five-section test-fixture chart rendering, nonempty peer tables/heatmap/briefs, filters and zero-match UI.
- DuckDB normalized-schema SQL and Python produce matching additive cubes on deterministic test fixtures. BigQuery source queries were not executed.
- `python -m compileall -q app.py src`: passed.
- `pip check`: passed.
- Streamlit server starts on localhost; Chromium (Playwright, system `/usr/bin/chromium`) loads the application, navigates all five sections and checks a 390×844 mobile viewport with no JavaScript page errors. Desktop screenshot inspected at 1440×1050. Browser testing uses the shipped evidence-pending bundle; fixture-driven charts are checked with Streamlit AppTest, never published as findings.
- Existing Optiver files were not changed. Only this project and its dedicated Actions workflow are committed. No credentials, raw records, caches or development virtual environment are staged.

## Not verified

- Actual DataSF/BigQuery schema, source coverage and authentic data metrics: HTTPS requests fail with managed proxy HTTP CONNECT 403. Current network policy has no custom allowed hosts. No GCP identity is configured, and no paid resources were provisioned.
- Full-volume extraction size, performance and real-data charts: cannot be validated without accessible authentic records. The field mapping is provisional and fails closed when metadata differs. Dataset completeness is not claimed.
- Python 3.11 locally: only 3.12 is installed/tested here; the GitHub Actions matrix targets 3.11 and 3.12.
- Public Streamlit hosting: no application was published, so no public deployment is claimed. Account authorization/publication and review of a real bundle remain owner actions.

## Release interpretation

This is an implementation ready for code review and a credential-free **evidence-pending deployment**, not a completed empirical investigation. No confirmed San Francisco bottlenecks or operational failures are reported. After network access is enabled, run the README refresh instructions, review quality/provenance, repeat tests and inspect real-data workspaces before treating the portfolio study as evidence complete.
