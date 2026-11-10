# Project 002 · Daily Stock Volatility Prediction and Model Failure Analysis

Human-led quantitative research; AI-assisted implementation. The human lead's
hypothesis is unchanged: stock-specific vulnerabilities may make selectively
chosen other-stock signals useful under particular conditions. This hypothesis
has not been tested by a prediction model. D008 moves that advanced multi-reference
idea to a future extension, while prioritizing a limited completed forecasting
project with the approved Plotly source.

The lead approved the Plotly dataset and provisionally approved a five-session
horizon in D002. The original Optiver data access track is preserved in
[the archived foundation guide](README_OPTIVER_FOUNDATION.md); this pilot is not
claimed to use the official Optiver data.

## Current checkpoint: D008 forecasting experiment plan awaits approval

The lead temporarily stopped the expanded-source search and requested three
comparisons: historical volatility, a stock-specific model, and own-stock plus
market information, with failure analysis and both approved cleaning policies.
Read the [concise proposed experiment and leakage controls](research/forecast-D008/PLAN.md).
**Approve that plan before model implementation.** No model has been fitted.
Development/internal validation stays within 2013–2015; the 2016–2018 period
remains reserved for separately approved evaluation.

D001–D006 is frozen at commit `db4d868` / tag `research-d001-d006-freeze`.
All original findings, code, evidence, decisions and masks remain available.
The [paused D007 access-probe record](research/source-search-D007/PAUSED.md) is
preserved without adopting a new source. Project 001 and all historical evidence
remain unchanged. No merge.

## Frozen exploratory foundation

The lead approved D005's evidence-profile methodology and a discovery-only
feasibility phase. Read the [D006 evidence packet with charts, all definition
comparisons, precision limits and data requirements](research/feasibility-D006/README.md).
The audit reports support rather than pair CVRs or rankings: few stress episodes,
coverage-sensitive historical baselines and wide attainable uncertainty limit
what can be established. No final reliability gates, weighted score or predictive
model is adopted. The next direction remains a human research decision.

The lead interpreted D004 cautiously: high correlation and sensitivity to
measurements, episodes and cleaning do not establish a reliable reference stock.
The lead proposed Conditional Vulnerability Ratio (CVR). Read the
[mathematical feasibility and reliability-methods proposal](research/CVR-D005/README.md).
It explains symmetry, directional companions, event support, episode uncertainty,
market-severity confounding, masking sensitivity and later replication. It is not
a final scoring system; no stock CVRs or later-period relationships were computed.
D006 authorized feasibility only, not final relationship criteria. No predictive
training is authorized.

Read the [D004 broad-decline evidence packet with charts and examples](research/declines-D004/README.md).
It preserves the discovery observations and robustness checks that informed the
lead's interpretation in D005. No prediction models were trained or future target
columns read.

The [D003 cleaned-panel comparison, selection-bias audit and complete ledger](research/cleaning-D003/README.md) remains available.

The earlier [integrity investigation with charts and evidence](research/daily-quality/README.md) is preserved as the pre-approval research record.
It includes missingness, calendar gaps, OHLC contradictions, repeated historical
records, documented actions/news events, unresolved cases, proposed masking rules,
measured data loss, the precise provisional target, and chronological-validation
safeguards. D003 authorized provisional masks, which are now implemented in separate
versioned views; the original source is unchanged. No prices were corrected and
no models were trained.

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

- `daily_study/feasibility.py`: discovery-only stress definitions, support/coverage
  distributions, episode/precision diagnostics and labeled synthetic experiments;
  no observed pair CVRs, reference rankings or predictive models.
- `daily_study/declines.py`: predeclared discovery-period contexts, stock profiles,
  leave-out market controls, pair descriptors and episode checks; no forecasts.
- `daily_study/decline_diagnostics.py`: separately labeled post-hoc measurement
  and masking diagnostics; no re-selection of hypothesis candidates.
- `daily_study/clean.py`: approved masking layers, paired policy comparison, complete
  exclusion causes, artifact verification and selection-bias audit.
- `daily_study/quality.py`: calendar-aligned audit, evidence-led issue ledger,
  repeated-record detection, and masking-policy sensitivity.
- `daily_study/targets.py`: exchange-session returns, complete five-session RV,
  lookback sensitivity and purged date eligibility. No training.
- `tests/test_daily_quality.py`: labeled synthetic mathematical fixtures; these
  are not market findings. The report is generated separately from actual data.
- `optiver/` and `app.py`: preserved initial Optiver exploration tools/private
  no-data review UI. They have not been repurposed to display daily forecasts.

D003 records the lead’s masking approval. The implementation and comparison are
complete. D004 records broad market declines as the first context; D005 records
the lead's interpretation and CVR research objective. D006 approves the evidence
framework and feasibility study; final criteria still await approval.
Later-period relationship results remain unexamined.
Stock/peer selection, stress regimes, training
and confirmation dates, interpretation and conclusions remain human-led choices.
Project 001's separate checkout and branch remain unchanged; no PR has been merged.
