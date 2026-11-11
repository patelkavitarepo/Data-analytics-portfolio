# Project 006 · The Efficient Frontier

Can capped Markowitz portfolios improve out-of-sample risk-adjusted performance
versus equal weights? This MVP implements the experiment; **no empirical answer
has been established in this environment**. Real Yahoo/FRED access was blocked by
the network proxy (403). No vendor prices or synthetic performance results are
bundled. Educational research only, not investment advice.

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

In the dashboard, click **Load / refresh live data**. Yahoo adjusted daily Close
prices are retrieved separately for SPY, QQQ, IWM, EFA, EEM, TLT, GLD and VNQ from
2016-01-01. The conservative cutoff is the last XNYS session **before the current
New York calendar date**, even after today's close; it can lag the latest close
by one session. It deliberately avoids intraday and same-day vendor uncertainty.
The actual last observed date, retrieval UTC timestamp, versions, adjustments
and checksums are disclosed. Cache TTL is six hours; refresh forces acquisition.
Vendor timezone/cookie caches stay in ignored `work/vendor-cache/`.

Network access may require `query1.finance.yahoo.com`,
`query2.finance.yahoo.com`, `fc.yahoo.com` and, depending on Yahoo's cookie
flow, `guce.yahoo.com` / `consent.yahoo.com`. Rate limits or any failed asset
stop acquisition with a conspicuous warning after one bounded retry. No asset
is silently dropped and no synthetic fallback is offered.

### Offline CSV fallback

Select Upload in the sidebar; provide the source, adjustment method and
retrieval date, and attest real prices/use rights. Supply a CSV with an ISO
`Date` column followed by ticker columns, with one date per row. Prices must be
split- and dividend-adjusted daily closes, not unadjusted closes. SPY is always
required as a benchmark, plus every selected asset. The uploader's assertions
are visible and cannot be independently certified by this application.

Data must cover every expected XNYS session from January 2016 through the
current conservative cutoff. A stale CSV is audited but cannot produce
performance tables. Missing prices, dates, long gaps, calendars, coverage and
lost intervals are reported; duplicate dates/columns, infinities, zero/negative
prices and non-session dates are rejected. No fill is applied. Common valid
prices are aligned first; a return needs two consecutive complete exchange
sessions. Backtests are blocked on **any missing price session**, rather than
skipping investment periods. Dates outside the research interval are counted
and ignored. Adjusted-price accuracy still depends on the vendor/uploader.

### Command line and artifacts

```bash
cd markowitz-portfolio-optimization
.venv/bin/python -m markowitz.run --output work/run
# Optional: consumes final holdout, do not tune after inspecting it
.venv/bin/python -m markowitz.run --output work/final --reveal-holdout
# Fallback, only with legitimately acquired real adjusted historical prices
.venv/bin/python -m markowitz.run --csv /path/to/prices.csv --source 'vendor; adjusted method; retrieval UTC' --output work/offline
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
  default. Reveal explicitly; once viewed it is no longer untouched. A future
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
probe and blocked (403). Historical yield ingestion, publication lags and
vintage handling are deferred. The prominently labeled user-entered constant
(default 2% effective annual) is an assumption, not a reconstructed historical
series. Convert it to daily as `(1 + annual)^(1/252) - 1`; use the same scaling
for optimization and realized Sharpe. Sensitivity to this assumption matters.

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
`requirements.txt`. Verify host egress, vendor terms and live retrieval first.
Do not bundle a market-data copy. No deployment or merge is authorized yet.
