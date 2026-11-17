# Synthetic Markowitz Stress Laboratory · 006-synthetic-lab-v1

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Authorized by [Holmes's synthetic-only assignment](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6804550830).
This separate experiment studies optimizer fragility with constructed inputs.
It does not substitute for ETF evidence, validate the industry-data proposal,
change 006-v1, or establish an investment forecast. No provider observations,
historical analogues or real holdout outcomes are used.

## Run offline

Use the existing pinned Python 3.12 environment; no new dependency is required.
From the repository root:

```bash
markowitz-portfolio-optimization/.venv/bin/streamlit run markowitz-portfolio-optimization/app.py
```

Choose **Synthetic scenario lab** in navigation or the main page's link. The
page works while the real-data gate is blocked. Submit the lab form to run;
editing controls alone does not refit. Outputs identify the last submitted
settings. Lab-only controls do not alter empirical settings or session state.
Every table includes an Evidence column; every chart title includes
**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**, including exports/downloads.

Reproduce all default constructed runs, with full manifests and draw logs:

```bash
cd markowitz-portfolio-optimization
.venv/bin/python -m markowitz.synthetic --scenario all --seed 6006 --draws 20 --output work/synthetic
.venv/bin/python -m pytest -q
```

For one bounded example:

```bash
.venv/bin/python -m markowitz.synthetic --scenario mean_estimation_error --seed 6006 --draws 10 --output work/synthetic-example
```

Both commands generate only synthetic outputs. `work/` is ignored. The committed
[synthetic-default-summary.json](synthetic-default-summary.json) contains labeled
estimates, synthetic realized metrics, instability summaries, settings, versions
and input hashes for the default runs described below. Full per-start diagnostics
are reproducible via the CLI and downloadable from the page. Unavailable values
serialize as JSON null, not invented zero diagnostics.

## Fixed constructed assumptions, before inspecting results

Six abstract assets **Synthetic A–F**, not the eight ETFs or French industries.
True annual arithmetic means: 6%, 7%, 8%, 9%, 10%, 11%. Baseline annual volatilities:
10%, 13%, 16%, 19%, 22%, 25%. One common Gaussian factor plus independent normal
idiosyncratic terms yields a positive-definite covariance. A daily step assumes
1/252 year; means/covariance divide by 252 when generating simple returns.
Gaussian tails are unbounded; a draw <= -100% is rejected, never silently clipped.

Default seed **6006**, **504 training steps**, **252 later steps**, **20 bootstrap
draws**, **35% cap**, **2% assumed effective annual risk-free rate**. Steps are
ordinal, with training 0–503 and later path 504–755; they are not calendar dates.
PCG64 / SeedSequence streams separate training, later-path and bootstrap draws.
Scenarios use common innovations for paired comparisons. No market calibration,
seed search, empirical hyperparameter tuning or automatic winner selection.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Scenario design**

| Constructed scenario | Training assumption | Later-path assumption / interpretation |
| --- | --- | --- |
| Baseline | All pairwise factor correlations +0.35 | Same distribution |
| Correlation spike | Correlations +0.85 | Same +0.85: controlled known-regime comparison, not an unexpected out-of-sample spike |
| Asset-volatility shock | A volatility triples, 10% → 30%; other volatilities/correlations unchanged | Same shock: controlled known-assumption comparison |
| Mean-estimation error | Baseline return draws; add +8 pp/year to estimated mean A and −4 pp to B | Identical baseline path and true means; only estimator input changes |
| Abrupt sign flip | Baseline training | At the first later step, cross-group correlations turn −0.35 between A–C and D–F; within-group +0.35. Weights are not refitted using the new path |

This design separates effects visible in the training assumptions from one
unforeseen future regime change. It does not claim every “stress” must make risk
worse: the chosen negative cross-group correlations can improve diversification.

## Allocation, path and diagnostic calculations

All three allocations use the same training sample, cap, risk-free assumption
and scenario: checked capped long-only minimum variance, deterministic multi-start
**local** max-Sharpe candidate, and fixed equal weight. Shared `analytics.py` is
unchanged. Fit and bootstrap accept training only, never a future-path object.
Weights are independently checked for finiteness, budget and bound residuals
<=1e-7, even if a solver reports success. Failed candidates are omitted from
weights and path metrics, with errors/residuals logged.

Training arithmetic return, estimated volatility/Sharpe and target HHI/max weight
are separate from realized later-path CAGR, volatility, Sharpe and drawdown. The
page also shows known *constructed* later covariance risk of frozen targets;
this is a generator assumption, not an estimate from future observations.
Returns/volatilities/weights are decimal fractions; Sharpe and HHI are unitless.
Target changes are fractions (multiply by 100 for percentage points).

Later-path targets reset before returns every **21 synthetic steps**, drifting
between resets. Compare **zero cost and 10 bps per gross traded notional** for
all allocations, including an initial purchase of 1 unit. Gross trades are
sum(abs(target − drifted weights)); net factor is `(1 − cost × trades) × gross`.
This proportional-cost approximation is not real execution. Target caps need not
hold between resets. Inception wealth 1 is included in maximum drawdown. These
are isolated synthetic paths, never the ETF backtest or empirical holdout.

The IID bootstrap resamples complete contemporaneous training rows with
replacement, preserving within-row cross-asset relationships. Each strategy
uses the same sampled row indices. The configured mean bias is reapplied in each
draw. Logs include seed, RNG stream, index hash, method, draws, checked violations,
failures and full available solver diagnostics. Resampling destroys time order;
it does not model serial dependence, hidden regimes or nonstationarity.

Instability is relative to the original fitted target: L1 distance is
sum(abs(draw weights − original weights)); half-L1 is the fraction of target
allocation reassigned, **not realized path turnover**. Also report p95/max L1 and
mean per-asset weight SD across successful draws. Failed draws are counted, not
zero-imputed. When no reference or successful draw is available, distance is
unavailable. Bootstrap distributions are not confidence intervals or forecasts.

Streamlit bounds: **2–30 draws**, **126/504/1008 training observations** (core
ceiling 1260), **252 later steps** (core ceiling 504), **six assets**, at most seven
local Sharpe starts per fitted sample, existing 1000-iteration/start limit.
Form submission and an eight-entry cache bound repeated interactive work.

## Observed default-run findings

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Seed 6006 only**

| Constructed observation | Measured outcome | What it supports investigating |
| --- | --- | --- |
| Baseline training-row bootstrap | Mean half-L1 reassignment: min-vol **2.55%**, max-Sharpe **12.73%**, equal weight **0%** by construction | Mean-sensitive allocation can be less stable in this constructed sample; this is not a general empirical ranking |
| Biased estimated means | Max-Sharpe target L1 change **0.2273**, i.e. **11.36%** reassigned; min-vol/equal-weight targets unchanged | Estimated means affect max Sharpe; minimum variance does not use means in its objective |
| Same mean bias, unchanged min-vol weights/path | Reported estimated min-vol Sharpe rises **0.420 → 0.571** despite identical later outcomes | A displayed ex-ante Sharpe can change without any portfolio improvement |
| Correlation +0.35 → +0.85 in both samples | Estimated min-vol volatility **9.25% → 11.94%**, target HHI **0.2973 → 0.3350**; high-correlation bootstrap weights almost fixed at bounds | Low weight dispersion can reflect binding caps, not low risk or high confidence |
| A volatility triples | Min-vol A weight **35% → 0%**; **35%** target reassigned. Max-Sharpe target unchanged here, because it already assigned A approximately zero | Sensitivity depends on exposure; one unaffected candidate is not proof of robustness |
| Unseen cross-group sign flip | Targets and training-only bootstrap unchanged; equal-weight modeled later volatility **11.97% → 6.57%** | Fixed targets can face materially different risk; this constructed sign change is diversifying, not uniformly adverse |
| Baseline max-Sharpe sample versus later path | Estimated Sharpe **1.762**; later realized Sharpe **0.672** cost-free / **0.662** at 10 bps | Keep training estimates and finite-path outcomes separate; no inference about real expected Sharpe |

Default numerical validation: each of the five scenarios produced valid fitted
candidates and **20/20 successful bootstrap candidates per strategy**. Across the
five runs, **three individual local max-Sharpe starts failed** (one each in the
correlation-spike, volatility-shock and mean-error bootstrap); alternative starts
produced valid accepted candidates. These failures remain logged. The largest
checked accepted bootstrap constraint residual was about **5.5e-12**, below 1e-7.
These figures describe synthetic numerical experiments only.

## Verification and scope limits

- **105 pytest tests passed** locally on the pinned Python 3.12 environment,
  including the original 80 tests. Added scenario construction, PSD, reproducible
  RNG streams, exact perturbations, bounds, known instability metrics, path/cost
  accounting, failed solver and false-success rejection, labels, offline UI and
  future-mutation checks. Mutating the later sample cannot change fitted weights
  or bootstrap outputs; overlapping synthetic step ranges are rejected.
- Browser smoke on a fresh local Streamlit server: opened the page from the main
  app, ran the default experiment, found persistent synthetic labels, no real
  holdout control, no JavaScript errors or external requests. Desktop and 390px
  mobile layout checked; no page-level horizontal overflow. AppTest checks every
  chart title and table Evidence column, including forced failure handling.
- No provider datasets, permissions bypass, external accounts, purchases or
  provider correspondence. Acquisition remains disabled. Documentation network
  jobs are paused for this synthetic-only pass; pytest CI remains enabled.
- `analytics.py`, `research.py`, the original ETF universe/splits/cap/risk-free
  defaults, permission gates and real holdout gate are unchanged. Only a link to
  the independent lab is added to the empirical app. French-library inquiry
  remains pending; sending it is not permission. No empirical strategy is added.

Next investigation questions: do these patterns persist across predeclared seeds
and shorter training windows? How does an *unseen* positive-correlation spike
compare with the known-regime example? Would a block bootstrap under constructed
serial dependence expose uncertainty that IID resampling misses? Any follow-up
is a synthetic investigation, not justification to tune frozen 006-v1 settings.
No merge or deployment.
