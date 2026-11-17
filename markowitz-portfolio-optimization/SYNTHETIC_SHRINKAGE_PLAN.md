# Predeclaration · 006-synthetic-shrinkage-v1

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Authorized by [Holmes checkpoint 6833950415](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6833950415).
Commit this design before any numerical run. Independent exploratory synthetic
candidate only: not an empirical challenger, champion replacement, confirmation
reservation or consumption event. No ETF settings, original calculations,
26 historical fingerprints, earlier synthetic artifacts or evolution registry
changes. No provider data, holdout access, merge or deployment.

## Fixed experiment

- Version `006-synthetic-shrinkage-v1`; seeds **7001–7005**; training pool 504
  ordinal steps; nested trailing lengths **126/504** ending at source step 503.
  Relabel training locally; record source positions and hashes. Future **252**
  steps at 504–755, identical across windows/methods. Do not search seeds/windows.
- Original six abstract assets A–F, true annual arithmetic means
  [.06,.07,.08,.09,.10,.11], annual volatilities [.10,.13,.16,.19,.22,.25].
  Gaussian common-factor plus independent idiosyncratic normals, daily means
  divided by 252 and vols by sqrt(252). No clipping or sample-moment forcing.
- PCG64 `SeedSequence(seed).spawn(3)`: stream 0 gives 504×7 training normals;
  stream 1 gives 252×7 future normals; stream 2 gives bootstrap row indices.
  Training correlation **+.35**. Future stationary +.35 or unseen jump **+.85**,
  sharing common/idiosyncratic innovations across regimes, methods and windows.
  Fixed true means/vols, no AR/serial dependence in this study.
- Two covariance estimators: annualized sample covariance S (ddof=1), and
  **.75*S + .25*diag(diag(S))**. This preserves marginal sample variances and
  scales off-diagonals by .75. Coefficient .25 is illustrative and fixed, not
  learned/tuned. Both use the identical training-only mean estimate (mean×252).
- Original checked min-vol and deterministic multi-start LOCAL max-Sharpe solver,
  cap **.35**, assumed effective annual RF **.02**, six fully invested long-only
  weights. Fixed equal weights are a method-independent comparator; repeat their
  estimated-risk views only to show estimator differences, not as new portfolios.
  Do not modify analytics.py/research.py. Validate chosen covariance, solver
  success, finite objectives/weights and independent residual ≤1e-7. Retain
  failures explicitly; do not impute zero risk, weights or distance.
- **15 IID bootstrap draws** per seed/window. Reset stream 2 for each window;
  draw a (15,window) integer array uniform on 0..window−1. Both methods/strategies
  use the exact same complete contemporaneous rows. Recompute the SAME sample
  mean and S on each resample, then compare S with its fixed shrinkage. No claim
  bootstrap samples are nested across windows. Reference/bootstraps never see
  future observations or true future covariance. Fit once, reuse across futures.
- Both future regimes use existing 21-step target resets with intervening drift,
  **0/10 bps** per gross traded notional and initial purchase charge, identically
  across methods/strategies. Rates/conventions match; traded amounts need not.

## Comparisons fixed before results

Keep every seed, failures, known/unknown solver-start counts, residuals and valid
pair counts. Retain full original solver diagnostics in a reproducible sidecar.
Per-seed/window/method/strategy reference and bootstrap tables include:

1. Fitted weights, HHI, effective number 1/HHI, max weight, cap count/incidence
   (|w−.35| ≤1e-7), and paired shrink-minus-sample target half-L1.
2. Bootstrap mean/SD/p05/p50/p95 half-L1 distance to EACH method's own fitted
   reference, mean per-asset weight SD, resample concentration/caps and failures.
   Paired method contrasts compare these conditional diagnostics, not turnover.
3. Covariance error: ||estimated C − stipulated training C(.35)||F /
   ||C(.35)||F. Also report distance to C(.85), explicitly as future-regime
   misspecification, NOT evidence an estimator should foresee a jump. Report
   estimated matrices, minimum eigenvalue/conditioning and diagonal equality.
4. Portfolio risk: own-estimator estimated vol, original-S cross-evaluated vol,
   stipulated TRAINING vol and stipulated FUTURE vol for each fitted target;
   signed and absolute own-estimate-minus-known risk gaps for each regime.
   These are fixed-target sqrt(w′Cw), separate from drifting realized path risk.
5. Later-path volatility/CAGR/drawdown, gross trades and paired method differences
   for each future regime/cost. EW target, path and constructed-risk contrasts
   must be exactly zero. Covariance changes can alter its estimated risk only.

Summarize median/min/max across five seeds separately by window, strategy,
regime/cost where relevant. Do not pool paired regimes/costs/windows as new seeds.
Report direction counts for key contrasts: smaller covariance error, instability,
HHI or risk/absolute risk gap; larger CAGR and less negative drawdown. Numerical
|difference|≤1e-10 is a predeclared floating-point tie tolerance only, not a
materiality/significance threshold. Lower risk/concentration or higher CAGR in
one metric is not a portfolio winner. Preserve reversals, null and unfavorable
results. No confidence interval, real-world ranking, threshold tuning or automated
winner. Raw per-seed values and denominators take precedence over rounded prose.

## Deliverables and limitations

Separate prototype module, deterministic tests, fixed-grid CLI, labeled JSON and
concise Markdown findings. Prefer this to another dashboard. The empirical model
evolution registry/template/plan remain untouched. Five seeds, short bootstrap
runs and Gaussian IID returns cannot establish calibrated uncertainty or market
value. Diagonal shrinkage deliberately reduces positive correlations, potentially
biasing risk downward, especially under an unseen positive-correlation jump.
A larger sample may reduce sampling error without fixing regime misspecification.
Any other coefficient, target, estimator or regime-adaptive rule needs separate
predeclaration and authorization; no additional variant is part of this study.
