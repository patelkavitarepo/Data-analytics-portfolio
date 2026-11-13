# Focused synthetic robustness predeclaration · 006-synthetic-robustness-v2

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Declared before running or inspecting this investigation's numerical outputs.
Authorized by [Holmes checkpoint 6805027667](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6805027667).
The original synthetic lab/results and frozen 006-v1 ETF study stay unchanged.

## Fixed bounded grid

- Seeds: **6006, 6007, 6008, 6009, 6010**, all reported; no seed selection.
- Training lengths: **126 and 504**. Generate a 504-step baseline training pool
  per seed. Use its latest 126 steps or all 504; both end at original step 503.
  Relabel each training input 0..n-1 only for the existing training-only helper;
  record original source positions (378..503 or 0..503) in the manifest.
- Future: **252 steps**, original ordinal positions 504..755, identical innovations
  across windows. These are simulated steps, never historical dates/holdout data.
- Baseline: training and future pairwise correlation **+0.35**.
- Unseen jump: the **identical training data**, then future correlation **+0.85**.
  Pair baseline/jump using the same future common-factor/idiosyncratic normals.
  No future covariance or future sample enters estimation or bootstrap.
- Use the original six abstract assets, assumed true means/volatilities, PCG64 /
  SeedSequence streams 0=train, 1=future, 2=bootstrap. No provider inputs.
- **10 IID bootstrap draws** per seed/window training case. Reuse the identical
  training fit/bootstrap across the two future scenarios; do not count those as
  independent fits or seeds. 10 training cases total.
- Strategies: existing checked min-vol, local max Sharpe, equal weight. No new
  strategy or winner selection. Cap **0.35**, assumed effective annual RF **0.02**.
- Future trading: unchanged synthetic 21-step resets with drifting holdings,
  costs **0 and 10 bps** per gross traded notional, including initial purchase.
- Core numerical acceptance tolerance **1e-7**, unchanged. A target is at its
  cap when abs(weight − .35) <= **1e-7**. Cap diagnostics describe targets, not
  drifted holdings or exposure limits between resets.

## Outputs fixed before observation

Report all seeds separately and across-seed **median, minimum and maximum** by
window and strategy (also cost where applicable), with valid/failed counts.
Never pool windows or count the paired futures as extra independent seeds.
These descriptive ranges are not confidence intervals or real-world probabilities.

1. Paired target equality and bootstrap reuse identifiers; no hypothetical refit
   using later knowledge. Fitted estimated moments remain training-only.
2. Analytically known baseline/jump covariance volatility and their ratio, on
   the same fitted target. Distinguish this assumption-based risk from noisy
   realized future sample volatility, drawdown, Sharpe and CAGR.
3. Cost-matched baseline/jump path metrics and paired changes. Count how many
   seeds have higher realized volatility / more negative drawdown without
   assuming every particular sample deteriorates.
4. Target HHI, effective number 1/HHI, max weight, count at cap; bootstrap mean
   half-L1 distance and dispersion beside cap-binding incidence, mean cap count,
   HHI/effective-number/max-weight summaries over successful draws only.
5. Paired short-versus-long target half-L1 distance and concentration/instability
   differences for each seed. Longer training is a sensitivity comparison,
   not a promised improvement or an empirical setting recommendation.
6. Seed, window, draws, generator/versions, training/future hashes, sampled-index
   hashes, fitted/draw solver failures and constraint checks. Exclude failed
   candidates, preserve errors and unknown diagnostics, never zero-impute.

The CLI runs this fixed grid; a separate read-only Streamlit page may display
its committed report without running the whole grid on widget changes. Full
solver details can remain in reproducible ignored work outputs; public synthetic
summaries retain per-draw success/constraint/cap diagnostics.

## Scope limits and decision rules

All choices above precede findings. Keep predeclaration and results in separate
files. Publish every planned seed/window/strategy, including failure records.
Do not reinterpret failed fits as zero-return allocations or choose a better seed.
A negative realized effect for a seed is an observation, not a reason to drop it.
Only constructed Gaussian/IID behavior is studied. Serial dependence and moving-
block bootstrap are explicitly deferred. No permission grant, provider contact,
market data, ETF hyperparameter changes, real holdout evaluation, merge or deploy.
