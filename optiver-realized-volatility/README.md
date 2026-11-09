# Project 002 · Optiver Realized Volatility Prediction

**Human-led research. AI-assisted code and analytical support.**

Research question: can stock-specific vulnerabilities and context-dependent
information sharing improve short-horizon volatility forecasts beyond own-stock
signals and a common market state? The human lead supplied the hypothesis and
retains control over research questions, consequential methodological decisions,
interpretation, and conclusions. AI assistance wrote the current code, tests,
source review, and proposed protocol. See [DECISIONS.md](research/DECISIONS.md).

## Current phase and evidence boundary

**Official dataset access is blocked in the present runtime. No official rows have
been inspected and no empirical findings or model scores exist.** Current work is
a tested research foundation, not a finished prediction project. Source-derived
facts and AI recommendations are explicitly separated from human decisions.
There are no fabricated market observations, demo scores, or invented charts.

Completed in this branch:

- Recorded the human hypothesis and the decisions still pending.
- Reviewed accessible official data/evaluation/host-Q&A documentation.
- Documented measurable indicators and a proposed leakage-aware experiment design.
- Implemented target-free book/trade measurements, discovery-manifest enforcement,
  local source hashing, stock summaries, and private descriptive charts.
- Added a private research review UI, which shows no findings without artifacts.
- Added tests using explicitly synthetic fixtures, never presented as real evidence.

Deferred until official access and lead choices: actual schema/quality audit,
stock-level and conditional EDA interpretation, finalized split/context definitions,
relationship selection, baseline/advanced model fitting, out-of-sample RMSPE,
and conclusions. This staging intentionally respects the request to interpret
initial evidence before complex training.

## Research documents

- [Human research decision log](research/DECISIONS.md)
- [Draft protocol and financial reasoning](research/PROTOCOL.md)
- [Access blocker and authorized routes](research/ACCESS.md)
- [Primary source ledger](research/SOURCES.md)
- [AI implementation and verification log](research/IMPLEMENTATION.md)

## Install and test

Python 3.11 or 3.12, from this folder:

```bash
python -m venv .venv
source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests require no Kaggle credentials, network, or official observations. Unit tests
use transparent mathematical fixtures. Passing them verifies implementation
behavior, not financial validity or performance on the competition dataset.

## Private inputs and discovery approval

Obtain the competition files through your own authorized Kaggle account after
reviewing/accepting current competition terms. Do not send API tokens in chat.
The code does not download data or access Kaggle. It expects this layout:

```text
<private data root>/
  train.csv
  book_train.parquet/stock_id=.../...parquet
  trade_train.parquet/stock_id=.../...parquet
```

The standard Kaggle notebook mount is
`/kaggle/input/optiver-realized-volatility-prediction`. Local filenames alone do
not authenticate provenance: confirm the files came from that official source.
Hashes in each private run support later reproducibility; they do not independently
prove authorization or authenticity.

Before EDA, the lead must approve a discovery/confirmation allocation by whole
`time_id` groups. This decision has **not** been made. A private JSON manifest must
record `approval: "lead-approved"`, a real `decision_id` from the research log, and
an explicit `time_ids` list. Do not mark a draft as approved. The runner rejects
unapproved or empty manifests; no approved example with real IDs is included.

Once that choice is made, run:

```bash
python -m optiver.explore \
  --data-root /path/to/authorized/official/data \
  --discovery-manifest data/private-discovery-manifest.json \
  --output artifacts/discovery-001
```

The command filters to approved discovery IDs before feature generation. It
checks for `train.csv` but **never reads its targets**. It processes one stock at
a time, retaining a small stock/window feature table. Full local source file
checksums can add I/O time. Missing partitions, bad quote levels, nonfinite values,
and duplicate time/second keys raise explicit errors. Review anomalies rather
than silently changing the data. Missing requested discovery IDs are reported.

Outputs (all ignored by Git): `features.parquet`, `stock_profiles.csv`, `audit.json`,
`stock_volatility.html`, and `spread_vs_observed_volatility.html`. HTML charts embed
Plotly so they can be viewed offline; they also embed observations, so keep them
private. The scatter compares spread to **contemporaneous observed volatility**,
not to future targets. It cannot show predictive improvement.

The exploratory `conditional_similarity` utility requires explicit discovery
context IDs and a minimum matched-window support. It returns correlations of
observed log midpoint RV and sample counts; it does not select peers, train a
model, identify stress regimes, or establish a future-volatility relationship.

## Private research dashboard

```bash
streamlit run app.py
```

Enter a run folder such as `discovery-001` in the sidebar. Missing artifacts produce
an honest status message with no market charts or scores. With actual approved
outputs, the UI presents stock distributions and spread-versus-observed-RV charts.
It is a private research review tool, not a public data deployment. Never publish
competition inputs, stock-level derivatives, or this dashboard with data until
applicable permissions have been reviewed. `.gitignore` excludes data, artifacts,
credentials, archives, and model files; inspect staged changes as well.

## Why validation is not a normal chronological backtest

All stocks sharing a time_id belong in the same fold. Scales, context thresholds,
neighbor selection, and tuning must be learned within training folds. The shuffled
window IDs do not supply reliable chronology; sorted IDs cannot establish lagged
history or forward deployment robustness. Unknown adjacent/overlapping dependence
cannot be fully purged without verified chronology. See the draft protocol for
nested validation, common-factor controls, ablations, and uncertainty limitations.

RMSPE is implemented and tested, but no predictions exist yet. A lower score alone
would not establish causal shared vulnerability or trading profitability.

## Project isolation

This branch starts from the current `main` and adds only this project and its own
CI workflow. Project 001 remains on `feat/stock-market-dashboard` and its existing
pull request. It has not been copied, modified, merged, or redeployed. The branch
uses a separate Git worktree. The two projects may be reviewed independently.
