# Predeclared synthetic serial-dependence investigation · v3

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Authorized by Holmes [checkpoint 6807359399](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6807359399).
This design is committed before any v3 numerical results. Additive only: preserve
v1/v2 modules and artifacts and frozen 006-v1 ETF methodology/permissions/holdout.
No provider contact, market data, future sample, merge or deployment.

- Seeds 6006–6010; 504 ordinal training rows; six original abstract assets;
  original annual marginal means (.06 through .11) and vols (.10,.13,.16,.19,.22,.25),
  contemporaneous correlation .35. Cases phi=0 and phi=.5.
- Construct centered stationary Gaussian AR(1): x[initial] ~ N(0,C), then
  x[t]=phi*x[t-1]+sqrt(1-phi²)*epsilon[t], epsilon ~ N(0,C), independent of
  initialization. Add the original annual arithmetic means/252. Exact stationary
  initialization, no burn-in. C is the original DAILY covariance. Thus theoretical
  one-step marginal mean/covariance match across phi; finite sample estimates need
  not match. No normalization to force sample moments. Same initialization and
  innovation normals across phi for each seed. PCG64 SeedSequence(seed).spawn(3):
  stream 0 gives 505×7 normals (first row initialization, rest innovations);
  stream 1 reserved/unused; stream 2 resampling. No future observations generated.
- Same original checked min-vol, LOCAL max-Sharpe, equal-weight solvers, sample
  moments annualized by 252, cap .35 and assumed effective annual RF .02. No
  long-run covariance/HAC objective, new strategy or tuning. Under AR dependence,
  252×one-step covariance is an estimator convention, not true multi-step risk.
- Both methods resample entire six-asset vectors of the SAME training sample.
  15 draws per method. One stream-2 integer array of shape (15,504), uniform on
  0..503, reused across phi and methods. IID uses all 504 indices. Circular moving
  blocks use the first ceil(504/5)=101 integers as block starts, add offsets 0..4
  modulo 504, concatenate and truncate the last block to four rows. Exactly 504
  rows; circular boundary 503→0 is artificial and disclosed. No independent
  per-asset shuffle. Method draws share random starts, not identical samples;
  paired differences compare method summaries on the same original sample.
- Fit original target once per seed/phi, not once per method. Bootstrap may only
  see its training argument. Record training/sample index hashes, block starts,
  source indices, weights, diagnostics/failures/residuals and stream discipline.
  Retain full original solver diagnostics in a reproducible CLI sidecar.
- Per seed/phi/strategy/method: successful/failed draw counts, reference success,
  half-L1 mean/SD/p05/p50/p95, mean asset-weight SD, fitted and resampled HHI,
  effective number, max weight, cap count/incidence, solver-start failures and
  residuals. Failed fits stay missing, never replaced with zeros. Instability
  needs a valid reference; dispersion needs >=2 successful draws. Summaries state
  valid/planned denominators. Equal-weight distance is zero by construction.
- Report MBB minus IID differences and across-five-seed median/min/max separately
  by phi and strategy. No confidence interval or significance claim. A difference
  of |delta mean half-L1| >= .02 (two percentage points of target reassignment)
  is a PREDECLARED descriptive materiality flag, not a statistical test or a
  strategy-selection rule. Report all seeds, reversals, and below-threshold cases.
- Read-only labeled report view; no app-time refits. CLI fixed grid, no seed search.
  Tests: deterministic stationary AR construction and large-sample marginal/lag
  checks, pairing, complete-row resampling, circular order/length/truncation,
  leakage/network isolation, solver failures/missing denominators, persistent
  synthetic labels, prior artifact hashes unchanged.

Limits: five seeds, only 15 draws, one positive phi, one block length. Finite
bootstrap Monte Carlo variability is substantial. Blocks break dependence at
joins and omit lags >=5; artificial circular joins occur. IID discards serial
ordering; MBB does not automatically give calibrated uncertainty. No repeated-
sample coverage study, tail behavior, nonlinear dependence, regime changes,
market evidence, investing inference or permission grant. Do not presume IID
underestimates; cap-bound optima can mask uncertainty under either method.
