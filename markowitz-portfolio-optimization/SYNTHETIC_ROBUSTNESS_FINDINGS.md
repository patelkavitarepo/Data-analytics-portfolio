# Focused synthetic robustness findings · 006-synthetic-robustness-v2

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

This is an additive investigation authorized by [Holmes checkpoint 6805027667](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6805027667).
The grid was committed before numerical runs in
[`6231b6c`](https://github.com/patelkavitarepo/Data-analytics-portfolio/commit/6231b6ca9b8e9d914f65dc0e8ecf24259307986c).
See the unchanged [predeclaration](SYNTHETIC_ROBUSTNESS_PLAN.md) and complete
[labeled numerical report](synthetic-robustness-results.json). No seed was dropped
or chosen after outcomes. The original lab module, defaults and
[seed-6006/20-draw artifact](synthetic-default-summary.json) are preserved.

## Reproduce and inspect

Using the existing pinned Python 3.12 environment, from this directory:

```bash
.venv/bin/python -m markowitz.synthetic_robustness --output work/synthetic-robustness-v2
.venv/bin/python -m pytest -q
.venv/bin/streamlit run app.py
```

Select **Synthetic robustness check** in Streamlit navigation. It displays the
fixed committed report without fitting, searching seeds or network requests.
Every chart/table/download carries **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**.
CLI outputs `SYNTHETIC_robustness_report.json` and
`SYNTHETIC_full_solver_diagnostics.json` under ignored `work/`. The former is the
committed numerical report; the latter retains all available per-start bootstrap
messages. The public report retains every draw's success/failure, checked
violation, sampled-index hash, target weights and concentration. Unknown
quantities are JSON null, never zero-imputed.

### Fixed design

Seeds **6006–6010**, windows **126/504**, **10 IID bootstrap draws** per training
case, **252 future steps**, six original abstract assets, cap **35%**, assumed
effective annual risk-free **2%**, and cost rates **0/10 bps** per gross traded
notional. Synthetic targets reset every 21 steps with intervening drift and an
initial purchase charge. No new strategy or winner selection.

A 504-step training pool ends at original step 503. Both windows end there;
short training is the latest 126 steps (378–503), long training is 0–503. This
short window intentionally differs from the old lab's first-126-draw option.
Both see the identical later innovations on original steps 504–755. Training
helpers reindex locally only; original positions/hashes are retained.

Training correlation is **+0.35** in both conditions. The paired stationary
future stays at **+0.35**, while the **unseen** future changes to **+0.85**.
Common-factor and idiosyncratic innovations are paired across conditions and
windows, with true means/volatilities fixed. Each training fit and bootstrap is
computed once, before future construction/evaluation, and reused across both
conditions. No future covariance or observations enter fit/bootstrap. Target
HHI, cap count and instability therefore do **not** change merely because the
future condition changes; only their risk/path consequences do.

This differs from the original known-regime correlation-spike illustration,
where both training and future had +0.85 and targets could adapt to training.
The new investigation does not overwrite or reinterpret those earlier results.

## Observed outcomes across all predeclared seeds

All medians/ranges below summarize **five seeds separately within each window**.
They are descriptive conditional outcomes, not confidence intervals, real-world
probabilities, historical analogues or estimator rankings. Paired futures and
nested windows are not extra independent seeds.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Known covariance volatility inflation**

| Window | Target | Median jump/baseline volatility ratio | Range across five seeds |
| --- | --- | --- | --- |
| 126 | Minimum variance | 1.3245 (+32.45%) | 1.2916–1.3360 |
| 504 | Minimum variance | 1.3078 (+30.78%) | 1.2887–1.3260 |
| 126 | Local max Sharpe | 1.2576 (+25.76%) | 1.2475–1.3108 |
| 504 | Local max Sharpe | 1.2602 (+26.02%) | 1.2299–1.2658 |
| Both | Equal weight | 1.3696 (+36.96%) | Identical by construction |

All 30 paired target distances were **exactly zero**, with unchanged bootstrap
reuse IDs. These known risks are sqrt(w′Σw) under stipulated future covariance,
not estimates from future returns. For long-only targets here, higher positive
cross-covariances raise modeled variance. Lower relative inflation is not evidence
of a better strategy: targets have different baseline risk and concentration.
Nor is target covariance risk identical to realized risk with drifting holdings.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Training-window sensitivity and caps**

| Window | Target | Median bootstrap half-L1 reassignment | Across-seed range | Median fitted HHI | Bootstrap incidence of any cap |
| --- | --- | --- | --- | --- | --- |
| 126 | Minimum variance | 6.46% | 5.45–9.40% | 0.2818 | 100% for each seed |
| 504 | Minimum variance | 3.12% | 2.84–3.67% | 0.2908 | 100% for each seed |
| 126 | Local max Sharpe | 26.83% | 22.68–35.00% | 0.2926 | 100% for each seed |
| 504 | Local max Sharpe | 28.84% | 14.67–33.29% | 0.3268 | 100% for each seed |
| Both | Equal weight | 0% | 0% | 0.1667 | 0% |

Half-L1 measures target allocation reassigned from the original fit under
resampled training data, **not actual path turnover**. Every optimized target
has one or two binding caps; maximum target weight is 35%. Every successful
optimized bootstrap draw has at least one binding cap (50/50 per strategy/window,
not a market probability). Equal weights are 16.67% each and have no binding cap.
Mean cap counts, effective number 1/HHI, max weight and dispersion are in the
per-seed report; “any cap” alone is not discriminative in this grid.

Longer training reduced minimum-variance bootstrap distance in all five paired
seeds, while median HHI increased: less variability is not automatically less
concentration. Max-Sharpe distance increased with the long window in **three of
five** seeds and decreased in two. Thus this grid does not support a blanket
claim that more training observations improve every diagnostic.

The median short-versus-long target reassignment was **5.44%** for minimum
variance (range **2.88–6.31%**), **31.61%** for local max Sharpe (**21.05–38.20%**)
and zero for equal weight. These are paired training-window target differences,
not an empirical recommendation about the frozen ETF training dates.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Per-seed bootstrap distances**

| Seed | Min-vol 126 | Min-vol 504 | Max-Sharpe 126 | Max-Sharpe 504 |
| --- | --- | --- | --- | --- |
| 6006 | 6.46% | 2.84% | 26.83% | 14.67% |
| 6007 | 5.45% | 3.05% | 27.29% | 31.18% |
| 6008 | 6.97% | 3.12% | 25.26% | 28.84% |
| 6009 | 9.40% | 3.67% | 22.68% | 33.29% |
| 6010 | 5.45% | 3.27% | 35.00% | 20.77% |

These new ten-draw values do not replace the original seed-6006 **twenty-draw**
result (2.55% / 12.73% for min-vol / max Sharpe). The shorter trailing window is
also a different controlled training sample. Both experiments remain versioned.

### Noisy realized path outcomes, separately from known covariance risk

At both cost rates, realized volatility rose for all five seeds within every
window/strategy group. Drawdown became more negative in five of five seeds for
all groups **except long-window minimum variance**, where it worsened in **four
of five**. In seed 6006 with 504-step training and zero cost, baseline drawdown
was **−12.1597%**, versus **−12.0684%** after the jump: slightly less negative even
though modeled and realized volatility rose. The same exception remains at
10 bps. No seed or exception was removed.

All per-seed cost-matched CAGR, realized volatility/Sharpe/drawdown, gross traded
notional, paired changes and across-seed medians/ranges are retained in the JSON
and read-only page. Identical rates do not imply identical transaction amounts:
path-driven weight drift changes trade notional. These finite paths are not an
ETF backtest or a test of investment superiority.

## Numerical checks and validation

- **10 training cases**, **30 fitted strategy records**, and **300 bootstrap
  strategy records**: no rejected fitted targets or bootstrap candidates.
- **11 individual bootstrap local-solver starts failed**; alternative starts
  returned checked valid candidates. Fitted-reference starts had no failures.
  Candidate success is separate from individual-start success. No unknown start
  counts were reported in this run.
- Maximum accepted checked bootstrap constraint violation was approximately
  **5.4e-12**, versus the unchanged **1e-7** tolerance. All cap counts use the
  predeclared absolute-distance tolerance of 1e-7.
- Tests cover exact grid/nested windows, deterministic and paired innovations,
  covariance PSD, training without any future-covariance access, mutation of
  future data without refitting or bootstrap changes, cost alignment, known cap
  counts/effective number, failures without zero imputation, summary denominators
  and prevention of duplicate-seed pooling, labels and offline read-only display.
- Browser smoke opens the new page from native navigation, checks synthetic
  labels and absence of holdout/refit controls, and blocks external requests.
  Desktop and 390px mobile have no page-level horizontal overflow or JavaScript
  errors. The existing lab and empirical app tests remain part of the full suite.

Full local suite: **118 passed**. The browser smoke recorded zero JavaScript
errors and zero external requests; mobile document width was 390px at a 390px
viewport. No provider acquisition or empirical validation was run.

## What remains untested

Only five fixed seeds, two nested windows and ten IID bootstrap draws are used.
The generator is Gaussian, with fixed means/volatilities and a deliberately
specified correlation jump. No tails, serial dependence, learned change-point,
liquidity, security-level trading or parameter-calibration uncertainty is modeled.
IID bootstrap is a conditional training diagnostic, not a guarantee against
regime changes; a well-estimated training covariance can still be wrong later.

Serial dependence and moving-block bootstrap are a **separate later investigation**,
not implemented here. No seed/window, cap, model or strategy was chosen as a
winner. No provider data, permissions grant, empirical ETF changes, real holdout
inspection, merge or deployment. The pending permission inquiry remains pending.
