# Project 006 · The Efficient Frontier

Can capped Markowitz portfolios improve out-of-sample risk-adjusted performance
versus equal weights? **No empirical conclusion has been established.**

**Current checkpoint: all real performance evaluation is blocked.** Latest Holmes
review requires provider rights and multi-date independent adjustment checks.
[DATA_RIGHTS.md](DATA_RIGHTS.md) separates automation, private analysis, public
derived output and redistribution. [ADJUSTMENT_REVIEW.md](ADJUSTMENT_REVIEW.md)
predeclares the verification plan; no source has completed it. Yahoo acquisition
and its GitHub job are disabled. A checkbox or JSON cannot enable the source-policy
gate. No raw data, real validation results or holdout results are bundled.
Educational research only, not investment advice.

## Synthetic scenario lab — works offline

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

The separately authorized [Stress Laboratory](SYNTHETIC_LAB.md) is available from
Streamlit navigation or the main page link, even while all real-data analysis is
blocked. It compares min-vol, local max-Sharpe and equal weight across five
seeded constructed scenarios, with training-only bootstrap instability, explicit
solver failures and separate estimated versus realized synthetic metrics.
It uses six abstract assets and ordinal steps, never ETF proxies or historical
holdout data. Lab controls do not change 006-v1. Every chart/table/download is
labeled synthetic. No provider acquisition, licence grant or empirical conclusion
is implied. The original “synthetic fixtures only in tests” restriction on
empirical fallbacks is unchanged; this independent synthetic laboratory was
explicitly authorized by the owner's latest instruction.

```bash
cd markowitz-portfolio-optimization
.venv/bin/python -m markowitz.synthetic --scenario all --seed 6006 --draws 20 --output work/synthetic
```

See [SYNTHETIC_LAB.md](SYNTHETIC_LAB.md) for fixed assumptions, cost/rebalance
interpretation, reproducibility, measured toy findings and limits. No additional
dependencies. GitHub provider/documentation network jobs are paused during this
synthetic-only work; the test job continues and acquisition remains disabled.

## Reproduce (Python 3.12)

From the repository root:

```bash
cd markowitz-portfolio-optimization
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pytest -q
cd ..
markowitz-portfolio-optimization/.venv/bin/streamlit run markowitz-portfolio-optimization/app.py
```

`requirements.txt` pins the direct runtime/test dependencies; the lock records
all versions installed for verification (including Playwright for browser smoke
checks). All tests use deterministic **synthetic fixtures**, never research
results. No network is needed for pytest. On Windows, use `.venv/Scripts/`.

The live Yahoo control is visibly disabled: no express collection permission is
recorded. The legacy yfinance acquisition implementation remains unit-tested with
synthetic vendor responses, but `download_prices` rejects before a vendor call.
Old live session caches are discarded, and new price probes/acquisitions do not
run in Actions. The earlier all-eight coverage audit is historical evidence only.

For an entitled source, CSV audit supports SPY, QQQ, IWM, EFA, EEM, TLT, GLD and
VNQ. The conservative live cutoff rule remains the last XNYS session before the
current New York date. Explicit historical `as_of` supports archived snapshots;
coverage and provenance are independent of permission to compute performance.

### Offline CSV fallback

Select Upload in the sidebar; provide source, adjustment method, retrieval date
and an **explicit historical `as_of` session date**. Attest permission to analyze
these real prices here. Permission to analyze is separate from permission to
redistribute, publish or bundle vendor data; the uploader no longer requires a
redistribution license merely to perform private analysis.

Supply an ISO `Date` column followed by **all eight prespecified ETF columns**,
one date per row. Prices must be split- and dividend-adjusted daily closes.
The source is checked for all eight even when the optimizer explores a subset.

Every expected XNYS session from January 2016 through `as_of` is audited.
`as_of` must be a trading session no later than both the last eligible complete
session and the snapshot's latest observed session. It is never inferred from
missing data. Archived snapshots are visibly labeled historical/stale, with
`as_of`, last observed date, latest eligible session and excluded rows recorded.
A longer supplied snapshot cannot use an earlier cutoff to conceal missing
sessions in its excluded tail. Missing sessions inside the research interval
still block performance. Fixed 2016–2022 / 2023–2024 / 2025+ boundaries never move.

Duplicate dates/columns, infinities, zero/negative prices and non-session dates
are rejected. No fill is applied. Common valid prices are aligned first; each
return needs two consecutive complete exchange sessions. The default live audit
still requires coverage through the conservative current cutoff, with no silent
shortening to the vendor's last date.

### Independent source review before performance

Acquisition and audit alone do not authorize performance analysis.
**The current `source_policy.py` blocks every unapproved source.** No source has
passed the latest rights and action-date evidence checkpoint, so this template
cannot currently enable real performance. Full investigation and actual completed
[adjustment review](ADJUSTMENT_REVIEW.md) must precede a reviewed policy change.
The older one-price-per-ETF checker below tests consistency only and is not the
complete latest review requirement. Both CLI and
UI require a review JSON tied to the audited `as_of` and canonical snapshot
SHA-256. Download the **unverified** template after auditing (CLI also writes
`source_review_template.json`). Complete it only after actually checking:

- Reviewer, original source URL, timezone-aware retrieval timestamp.
- `adjustment_convention: "split_and_dividend_adjusted_close"` and evidence of
  the source's dividend/split treatment (`adjustment_evidence`).
- `analysis_use_authorized: true` and specific source terms/license evidence in
  `analysis_permission_evidence`. This establishes no redistribution permission.
- `spot_checks` entries for SPY, QQQ, IWM, EFA, EEM, TLT, GLD and VNQ: an actual
  training/validation session `date`, `reference_url`, independently observed
  `reference_price`, and `adjustment_basis: "split_and_dividend_adjusted_close"`.

References must use a documented publisher (Nasdaq, the ETF issuers or
Alpha Vantage); Yahoo cannot independently verify itself. The same adjustment
basis and snapshot convention matter: do not compare unadjusted closes with
adjusted prices. A fixed **0.5%** relative spot-check tolerance flags discrepancies
for investigation; it is a data check, not a tunable model parameter. Reference
dates must be within 2016–2024 and the snapshot, so verification cannot inspect
holdout prices. No observations are invented in the template.

The application checks review consistency and numeric agreement, **not the
truth of human source/entitlement assertions**. Retain reference/rights evidence
privately; do not commit the input CSV or completed review with vendor values.
Manifests retain references, outcomes and relative differences rather than raw
reference prices. Verify rights before sharing derived artifacts too.

### Command line and artifacts

```bash
cd markowitz-portfolio-optimization
.venv/bin/python -m markowitz.run --output work/run
# An unverified run saves audit/template then stops, without performance.
# An archived, licensed and independently checked input can evaluate validation:
.venv/bin/python -m markowitz.run --csv /path/to/prices.csv --as-of 2024-12-31 --source 'vendor; adjusted method; retrieval UTC' --source-review /private/review.json --output work/offline
# Keep holdout hidden for this review. No --reveal-holdout was used.
```

CLI defaults are fixed before evidence: eight assets, cap .35, assumed annual
risk-free .02, and 10 bps cost sensitivity. Manifests record protocol, data digest,
provenance, versions, settings, fit/test dates and solver diagnostics. Local
CSV metrics, weights, returns and traded notionals support independent
recalculation. UI downloads also include audits, manifests, weights, metrics
and net returns. Keep legitimately acquired input snapshots privately if their
terms permit; a hash identifies revisions but cannot recreate an unavailable
vendor snapshot. Repeated acquisition may change with vendor revisions.

## Frozen research protocol 006-v1

- Train: 2016–2022. Estimate daily simple-return means ×252 and sample covariance
  (`ddof=1`) ×252. Solve minimum variance and maximum ex-ante Sharpe separately.
- Validate: 2023–2024 with those fixed training weights. Both strategies were
  prespecified; there is no automatic strategy selection or validation tuning.
- Final holdout: 2025 through the eligible latest session. Refit the same two
  objectives on 2016–2024 only. Holdout is hidden and not fitted/evaluated by
  default. Reveal requires at least 60 audited holdout sessions, both in the
  analytical engine and UI. Reveal explicitly; once viewed it is no longer untouched. A future
  dataset is needed for clean confirmation after exploratory tuning.
- Long-only, fully invested, default .35 cap; check `n × cap >= 1`. Equal weights
  use the identical subset. SPY is an external, uncapped benchmark. Caps bind
  target allocations, not weights drifting between rebalances.
- SLSQP solves a convex minimum-variance problem; all solutions require solver
  success, finite objectives and constraint residual ≤1e-7. Near-singular
  covariance is rejected and condition numbers are reported. Max Sharpe uses
  deterministic multiple feasible starts and is labeled a **local candidate**.
  Frontier targets run from minimum-variance expected return to a linear-program
  maximum feasible return; failed points are reported and omitted.
- Diversified targets reset monthly, before the first session's return, from
  previous-close holdings; holdings drift between resets. No daily rebalancing.
  No future return enters a rebalance decision. Each evaluation period starts
  from cash; no position continuity across validation/holdout is implied.
- Compare cost-free and 10 bps per gross traded notional for **all** portfolios,
  including SPY initial investment. Gross notional is sum(abs(weight changes)),
  not one-way turnover; initial purchase = 1. Net daily factor is
  `(1 - cost_rate × traded_notional) × (1 + portfolio_return)`.
  This proportional-cost, prior-close execution model is an approximation;
  actual fills, spreads, taxes, fees and market impact are not reconstructed.
- CAGR is geometric wealth growth annualized by `252/n`; volatility is sample
  daily standard deviation ×sqrt(252). Sharpe is mean daily excess return / daily
  standard deviation ×sqrt(252), with no serial-correlation correction. Maximum
  drawdown includes initial wealth 1. HHI and maximum weight measure target
  concentration. All strategies share exactly the same evaluation dates.

**Risk-free limitation:** FRED DGS3MO retrieval was attempted as a connectivity
probe: blocked by Codex’s proxy and timed out on the initial GitHub runner. No
historical yield observations have been retrieved or verified. Historical yield ingestion, publication lags and
vintage handling are deferred. The prominently labeled user-entered constant
(default 2% effective annual) is an assumption, not a reconstructed historical
series. Convert it to daily as `(1 + annual)^(1/252) - 1`; use the same scaling
for optimization and realized Sharpe. Sensitivity to this assumption matters.

## GitHub-based access verification

`.github/workflows/markowitz-research.yml` uses GitHub-hosted Ubuntu/Python 3.12
with read-only repository permissions; the existing Project 002 workflow is
unchanged. The currently enabled job runs all synthetic tests. Previously enabled
status-only documentation connectivity and `scripts/rights_receipts.py` receipts
are paused during this synthetic-only assignment. Their retained receipts use
bounded requests and status/hash/predeclared phrase detections only. No receipt automatically
decides legal permission or logs full documents, prices or credentials.

The prior `source-audit` job is explicitly **skipped** pending express provider
permission. Yahoo financial/chart endpoints are no longer probed. The legacy
audit script also cannot collect Yahoo prices through the guarded downloader.
A source must satisfy both rights and independent verification before any
acquisition/performance path is enabled. No current job computes performance.
See the research record for historical coverage and the rights investigation
for current decisions. HTTP access and document phrase detection are not grants.

## Evidence and limits

See [RESEARCH_SUMMARY.md](RESEARCH_SUMMARY.md) for exactly what was verified.
SPY/QQQ/IWM have overlapping US equity exposures; VNQ also adds equity risk.
EFA/EEM, TLT and GLD are not independent risk sources. All eight ETF inception
dates precede 2016, but actual coverage is checked rather than assumed. A
retrospective surviving ETF universe, adjusted-price revisions and a single
holdout limit causal/generalized claims. No survivorship-bias-free claim is
made. Expected returns and sample covariance are uncertain; shrinkage,
walk-forward evaluation and statistical significance analysis are deferred.

The owner should interpret validation versus holdout, cost sensitivity,
concentration and economic significance only after real evidence is available.
Changing universe/cap/risk-free inputs after viewing holdout is exploratory.

## Data rights and future deployment (not performed)

No raw downloaded prices are committed or redistributed. CSV/parquet outputs,
cache and work artifacts are ignored. Yahoo/yfinance accessibility does not
grant redistribution rights; review [Yahoo terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)
and [yfinance's data-use notice](https://github.com/ranaroussi/yfinance#readme)
before storing/sharing vendor data or deploying. No permission to bundle data
has been established. CSV users must check their source's terms too.

After owner approval, Streamlit Community Cloud can use this repository, branch
`project-006-markowitz-portfolio-optimization`, entrypoint
`markowitz-portfolio-optimization/app.py`, Python 3.12, and the colocated
`requirements.txt`. Resolve provider automation/analysis/publication rights and the independent review first; no source is currently approved.
Do not bundle a market-data copy. No deployment or merge is authorized yet.
