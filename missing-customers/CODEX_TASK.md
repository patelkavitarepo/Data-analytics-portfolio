# Codex build task — Project 004: The Missing Customers

## Goal
Build and test a deployable **Streamlit analytics investigation** within this existing GitHub repository, preserving the investigative rigor of the portfolio. Work in the existing `project-004-missing-customers` branch (or a branch based on it); **do not overwrite other projects**.

The permanent stack is **GitHub (source + review) → Codex (code + tests) → Streamlit Community Cloud (published app)**. No BigQuery account or paid cloud service is required for v1. BigQuery and the existing Google GA4 SQL intake file are **optional future data-source adapters**, not launch blockers.

## Case question
**Where do customers drop off in an online shopping journey, and what can the recorded events actually establish?**

## Evidence source
- Preferred standalone v1 source: Retailrocket Ecommerce dataset from its original Kaggle publisher: https://www.kaggle.com/retailrocket/ecommerce-dataset
- Analyze `events.csv` with fields `timestamp` (Unix **milliseconds**), `visitorid`, `event` (view, addtocart, transaction), `itemid`, and optional `transactionid`.
- Download or source real data only if legitimately accessible. **No fabricated observations.** Do not commit the full raw multi-million-event dataset without explicit authorization or verification of distribution rights and repo size constraints.
- Support a file-based ingest using a user-uploaded CSV in Streamlit and an optional ignored local data directory. The app must start and explain how to provide data even with no input file. Small synthetic fixtures are allowed **for automated testing only**, visibly labeled synthetic, not displayed as empirical findings.
- Validate source provenance, missing columns, nulls, duplicate events, event timestamps, event ordering, and visitor IDs. Track event and visitor counts separately.
- Do not assume sessions, marketing acquisition channels, geography, devices, prices, revenue, or customer identity exist in this dataset. Do not claim monetary losses from event logs alone.
- If the data source is unavailable, complete a runnable empty-state app with tests and precise instructions instead of claiming a dataset was analyzed.

## Analytical design
Build a clean, understandable, responsive Streamlit app with:
1. **Case overview**: question, source, date coverage after loading, status, limitations.
2. **Evidence audit**: rows, distinct visitors, event-type coverage, missing IDs, timestamp validity, duplicates, and field availability. Expose a downloadable data-quality summary.
3. **Shopping journey**: clearly distinguish event counts, unique visitors with each event, and a **sequential timestamp-ordered view → addtocart → transaction** journey. Explain denominators and possible ambiguity with multiple products or returning visitors. Show a visitor-level cohort, and when feasible an item-matched stricter check.
4. **Alternative explanations**: instrumentation gaps, left censoring, re-entry, anonymous visitors, and absent transactions. Write careful observational commentary, not causal conclusions.
5. **Interactive exploration**: date filter, event-type filter where relevant, readable plots and tables with methodological footnotes. Avoid heavy on-the-fly processing and limit previews to prevent cloud memory failure.
6. **Research notes**: distinguish observed findings from hypotheses and the human investigator's conclusions. The human interpretation section stays explicitly pending.

## Engineering requirements
- App entry: `missing-customers/app.py`; dependencies: `missing-customers/requirements.txt` (or repo-root if needed for Streamlit). Community Cloud should be configured for the subdirectory app.
- Put reusable data loading, cleaning and analysis logic in `missing-customers/src/`; tests in `missing-customers/tests/`. Include a reproducible offline preprocessing CLI if source size makes Streamlit memory-intensive.
- Use pandas or DuckDB (choose practical, minimal dependencies), plus Plotly/Streamlit charts.
- Make parsing and timestamp units explicit. Timezone: UTC for source timestamps by default, disclosed in UI.
- Avoid a fixed numeric funnel assumption such as using total event counts as a sequential conversion rate; implement actual visitor/time ordering, verify whether item matching is feasible.
- Tests should cover valid data, missing columns, no events, duplicates, out-of-order records, stage reversals, missing IDs and repeat transactions. Provide the test command and run it.
- A Streamlit smoke check should confirm the app can start even if no data is installed.
- Include `.gitignore` for datasets and secrets. Never commit API keys, cloud credentials or personal data.
- Update `missing-customers/README.md` with installation, local start, reproducible data acquisition, source attribution and **Streamlit Community Cloud** deployment instructions.
- Record any real execution outputs / audited metrics in `missing-customers/research/EVIDENCE.md` with dataset source and timestamp. If not executed, leave as **pending**.
- Preserve `missing-customers/sql/01_evidence_intake.sql` for an **optional** future GA4/BigQuery comparison. Label it as optional; it should never block the Streamlit build.
- Do not edit `optiver-realized-volatility/`, other portfolio projects, or the root README unless narrowly necessary and justified.

## Delivery / acceptance
1. App loads gracefully with no data and loads a valid provided `events.csv`.
2. Visualizations have defensible units and clearly state the analysis grain.
3. Real event data is never replaced by invented values for portfolio claims.
4. Tests run and are reported honestly, with failures or limitations.
5. Entry path and dependency path work for Streamlit Community Cloud.
6. Summarize changed files, test results, remaining blockers, and steps for deployment.
7. Open a **draft pull request** for review if possible; **do not merge or deploy** without the human researcher's review.

## Important research stance
Treat findings as provisional and ask the human researcher for interpretation after presenting actual evidence. No artificial 'big revelation', no conclusions inferred merely from the project title. We want a credible analytics portfolio investigation, not a decorative dashboard.
