# Project 002 · Conditional stock vulnerabilities: daily-data pilot

Human-led quantitative research; AI-assisted implementation. The human lead's
hypothesis is unchanged: stock-specific vulnerabilities may make selectively
chosen other-stock signals useful under particular conditions. This hypothesis
has not been tested by a prediction model.

The lead approved the Plotly dataset and provisionally approved a five-session
horizon in D002. The original Optiver data access track is preserved in
[the archived foundation guide](README_OPTIVER_FOUNDATION.md); this pilot is not
claimed to use the official Optiver data.

## Current checkpoint: cleaning methodology awaits review

Read the [full integrity investigation with charts and evidence](research/daily-quality/README.md).
It includes missingness, calendar gaps, OHLC contradictions, repeated historical
records, documented actions/news events, unresolved cases, proposed masking rules,
measured data loss, the precise provisional target, and chronological-validation
safeguards. No prices were corrected, no cleaning policy was applied, and no
models were trained.

The original human hypothesis and subsequent approvals are in
[research/DECISIONS.md](research/DECISIONS.md). Code, AI recommendations and actual
verification runs are distinguished in [research/IMPLEMENTATION.md](research/IMPLEMENTATION.md).
None of the AI's cleaning proposals is recorded as a human approval.

## Reproduce the investigation

Use Python 3.11 or 3.12, from this directory:

```bash
python -m venv .venv
source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-quality.txt
python -m pytest -q
python -m daily_study.quality \
  --csv /private/path/all_stocks_5yr.csv \
  --evidence research/daily-quality/evidence.json \
  --output artifacts/quality-new-run
```

The source URL/hash and exact software versions are recorded in the report.
The runner expects the audited snapshot and refuses a hash mismatch. It produces
an investigation preview, not a cleaned dataset or fitted predictions. Inputs and
working artifacts remain ignored by Git. Selected derived issue registers,
aggregate counts and charts in `research/daily-quality/` are review evidence.
The report flags, rather than resolves, the lack of comprehensive adjustment metadata.

## Code layout

- `daily_study/quality.py`: calendar-aligned audit, evidence-led issue ledger,
  repeated-record detection, and masking-policy sensitivity.
- `daily_study/targets.py`: exchange-session returns, complete five-session RV,
  lookback sensitivity and purged date eligibility. No training.
- `tests/test_daily_quality.py`: labeled synthetic mathematical fixtures; these
  are not market findings. The report is generated separately from actual data.
- `optiver/` and `app.py`: preserved initial Optiver exploration tools/private
  no-data review UI. They have not been repurposed to display daily forecasts.

After the lead approves or revises cleaning methodology, update the decision log
before implementing that policy. Stock/peer selection, stress regimes, training
and confirmation dates, interpretation and conclusions remain human-led choices.
Project 001's separate checkout and branch remain unchanged; no PR has been merged.
