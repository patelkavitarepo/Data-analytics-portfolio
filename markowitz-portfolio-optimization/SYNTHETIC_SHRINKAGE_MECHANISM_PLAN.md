# Predeclaration · 006-synthetic-shrinkage-mechanism-v1

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

[Holmes checkpoint 6834605433](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6834605433)
authorizes this independent, narrow mechanism study. Commit before numerical
runs. It is deliberately constructed research after earlier results, **not
independent confirmation**, a seed search, or an empirical challenger.

## Fixed grid and information boundary

- Seeds **7101–7105**, true correlations **rho=0/.35**, nested trailing training
  windows **63/504** from a 504-row pool (source steps 441–503 / 0–503). Locally
  reindex training but retain original positions/hashes. All 20 cases retained.
- Original six abstract assets: annual arithmetic means [.06,.07,.08,.09,.10,.11]
  and annual vols [.10,.13,.16,.19,.22,.25]. IID Gaussian common factor plus
  idiosyncratic normals; means/252 and vols/sqrt(252). For each seed,
  PCG64 SeedSequence(seed).spawn(3)[0] gives the same 504×7 normal innovations
  for both rho values and all methods/windows. At rho=0 only the six
  idiosyncratic columns contribute. Streams 1/2 unused; **no future paths,
  shocks, transaction costs, bootstrap or other resampling** in this pass.
- Exactly S (sample covariance ddof=1 ×252) and .75*S+.25*diag(diag(S)). Coefficient
  .25 fixed, not tuned. Both receive the same sample mean ×252. Reuse original
  checked min-vol/LOCAL max-Sharpe objective logic, long-only full investment,
  cap .35, effective annual RF .02, equal-weight reference. No extra strategy.
- New prototype files; do not alter analytics.py/research.py, old synthetic
  calculations/results, source gates or the original minimum training-length
  restriction. The new prototype explicitly validates its own 63/504-row input.
- Fit all candidate portfolios from training only **before** constructing any
  scoring/oracle object. Candidate fitting accepts no true covariance, oracle,
  future data or true mean. True covariance is used only in the scoring stage.

## Predeclared scoring and comparisons

Use annual covariance matrices. Report per seed/rho/window/method:

1. Frobenius **squared** covariance error sum((C_hat−C_true)^2), its diagonal and
   off-diagonal components (both symmetric off-diagonal entries counted), and
   relative squared error divided by sum(C_true^2). Preserve unrounded values.
2. Paired shrink-minus-sample total/diagonal/off-diagonal squared-error changes,
   minimum eigenvalue and condition number. Validate total = diagonal + offdiagonal.
3. An exact mechanism decomposition. With E=S−C and a=.25, the off-diagonal
   paired loss change is
   `(−.4375)*sum(E_off^2) + .0625*sum(C_off^2) − .375*sum(E_off*C_off)`.
   Record all three terms and their sum. These are a realized algebraic
   sample-error term, target term and interaction, **not estimated population
   bias/variance from five seeds**. For unbiased S, E[E_off]=0; the target bias
   is −.25*C_off, but the realized cross term need not vanish.
4. At rho=0, diagonal loss is unchanged and shrink off-diagonal squared loss is
   exactly .5625 times sample loss, hence matrix total error cannot worsen.
   Treat this as a mathematical control, not an empirical discovery. At rho=.35
   retain any favorable or unfavorable finite-sample result. Matrix error does
   not order constrained allocation quality.
5. Candidate fitted weights, HHI, effective number, maximum weight and cap count
   (|weight−.35|≤1e-7), method target half-L1, estimated variance and **true
   fixed-target variance w′C_true*w**. No realized return/Sharpe or future risk.
6. A separately labelled **THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC**:
   one original checked min-variance solve per true rho, using known C_true,
   zeros for irrelevant mean inputs and the same constraints/cap. This is a
   numerical approximation to the convex theoretical constrained optimum,
   not a fitted strategy, third estimator, future forecast or selected model.
7. Min-vol absolute true-variance regret `w′C_true*w − oracle_variance`, and relative
   regret / oracle_variance. Raw small negatives stay visible; tolerance **1e-9
   annual variance units** accounts for numerical optimization. Larger negatives
   flag a scoring/oracle inconsistency, with an explicit invalid-regret flag,
   never a clipped zero or performance claim. If oracle/candidate fails, keep
   the case and missing regret. Max-Sharpe/EW true variance may be displayed,
   but min-vol oracle regret is reported ONLY for the min-vol objective.

Show every case, paired contrasts, median/min/max across five seeds separately
by rho/window/strategy. Do not pool nested windows/regimes/methods as independent
seeds. Direction tolerance **1e-12** is floating-point tie handling only, not a
materiality/significance threshold; retain raw values. Check decomposition with
absolute tolerance 1e-12. Log candidate/oracle solver failures, rejected weights,
constraint residuals and known/unknown start counts. Retain full diagnostics.
No winner, post hoc criterion, intensity/target search or market inference.

## Deliverables and preservation

Bounded fixed-grid CLI, labelled JSON/Markdown and deterministic unit tests for
paired/nested draws, zero-correlation PSD, squared-error/decomposition identities,
same means, 63-row chronology, oracle separation/regret tolerance, rejected solver
candidates, no network and persistent labels. Reproduce the same grid to check
reproducibility; do not expand it. Prefer reports to another dashboard.

Preserve all 26 historical fingerprints, prior shrinkage study, evolution plan,
registry/template, ETF settings/permissions and untouched real holdout. No
empirical registration, confirmation reservation/consumption, provider calls,
market data, merge or deployment. No approved source exists; pending French
inquiry is not permission. Five seeds, Gaussian returns and an unrealistic known-
truth oracle cannot establish market value or calibrated optimal shrinkage.
