# Shrinkage target mismatch and sampling error · mechanism v1

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Fixed diagonal shrinkage reduces off-diagonal sampling error when true
correlations are zero. With genuine positive correlations, it also introduces
target mismatch. This study shows why **matrix accuracy, conditioning,
concentration and constrained portfolio risk are different diagnostics**.

In the fixed grid, shrinkage lowered matrix loss and min-vol true-variance regret
in all ten zero-correlation cases. At rho=.35, matrix loss worsened in nine cases
and improved in one, while min-vol regret worsened in all ten. The favorable
matrix exception is retained; it did not produce a better min-vol allocation.
No market conclusion, calibrated intensity or empirical model promotion follows.

[Holmes checkpoint 6834605433](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6834605433)
authorized this deliberately constructed follow-up. The
[predeclaration](SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md) was committed as
[`90c137c`](https://github.com/patelkavitarepo/Data-analytics-portfolio/commit/90c137c)
**before numerical runs**. [All numerical evidence](synthetic-shrinkage-mechanism-results.json)
is retained. This is mechanism exploration after the earlier result, **not
independent confirmation**, a seed search or an empirical challenger.

## Frozen design and scoring boundaries

Seeds **7101–7105**, true training rho **0/.35**, nested trailing **63/504** rows
from one 504-row pool per seed/regime. The original six abstract assets have
annual arithmetic means [.06,.07,.08,.09,.10,.11] and vols
[.10,.13,.16,.19,.22,.25]. Gaussian common-factor/idiosyncratic innovations are
paired across methods, regimes and windows; daily means divide by 252 and
volatilities divide by sqrt(252).
At rho=0 the common-factor column has zero loading. Source ranges and input hashes
are retained; local reindexing does not change their temporal origin.

Exactly two estimators: sample S (ddof=1, annualized) and
**.75*S+.25*diag(diag(S))**. Same sample means, original checked min-variance and
LOCAL max-Sharpe algorithms, long-only/full investment, **35% cap**, **2% assumed
annual RF**, and unchanged equal-weight reference. The new prototype validates
its own shorter window; the original empirical/lab training rules are untouched.

All candidate fits finish before true scoring covariance or oracle objects are
constructed. True covariance never enters candidate fitting. **No future samples,
regime shocks, cost-adjusted paths, bootstrap or other resampling** were run in
this pass. The earlier study's path evidence remains separate.

## Matrix-loss mechanism: an identity, not a population estimate

Loss is squared Frobenius error `sum((C_hat−C_true)^2)`, split into diagonal and
off-diagonal squared errors. Both symmetric off-diagonal entries are counted.
These values have **squared annual covariance units**; they are not volatility,
returns or percentage points. Relative squared loss divides by `sum(C_true^2)`.
The earlier report used a relative Frobenius norm, so their levels differ.

Let E=S−C. Diagonal loss is unchanged. The paired off-diagonal loss change is:

`−.4375*sum(E_off²) + .0625*sum(C_off²) − .375*sum(E_off*C_off)`.

The first term reflects reduced realized sample error, the second a fixed target
term, and the third an interaction. This is an **algebraic decomposition using
known truth**, not a measured population bias–variance decomposition from five
seeds. For unbiased S the population off-diagonal target bias is −.25*C_off;
the finite-sample interaction need not vanish.

When rho=0, the target and interaction terms are zero; shrink off-diagonal loss
is **exactly .5625 × sample off-diagonal loss** and total matrix loss cannot worsen.
That is a mathematical control, not a discovery or a guarantee about portfolio
regret. Under positive correlation the three terms compete: do not presume every
sample must worsen. Diagonal equality and both loss identities hold to the
predeclared numerical tolerance in every case.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Every covariance-loss case**

| Seed | rho | Rows | Sample total | Shrink total | Shared diagonal | Sample offdiag | Shrink offdiag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7101 | 0 | 63 | 1.143622e-03 | 8.276236e-04 | 4.213406e-04 | 7.222810e-04 | 4.062830e-04 |
| 7101 | 0 | 504 | 1.687685e-04 | 1.181741e-04 | 5.312415e-05 | 1.156444e-04 | 6.504995e-05 |
| 7101 | 0.35 | 63 | 6.930220e-04 | 9.539644e-04 | 3.835700e-04 | 3.094520e-04 | 5.703944e-04 |
| 7101 | 0.35 | 504 | 1.768241e-04 | 5.150554e-04 | 4.049763e-05 | 1.363265e-04 | 4.745577e-04 |
| 7102 | 0 | 63 | 4.501919e-04 | 3.402565e-04 | 1.989111e-04 | 2.512808e-04 | 1.413454e-04 |
| 7102 | 0 | 504 | 7.871671e-05 | 6.417290e-05 | 4.547373e-05 | 3.324298e-05 | 1.869918e-05 |
| 7102 | 0.35 | 63 | 3.984892e-04 | 4.844830e-04 | 1.612036e-04 | 2.372857e-04 | 3.232795e-04 |
| 7102 | 0.35 | 504 | 2.429809e-04 | 1.464951e-04 | 9.773498e-05 | 1.452459e-04 | 4.876015e-05 |
| 7103 | 0 | 63 | 5.326559e-04 | 3.782522e-04 | 1.797331e-04 | 3.529228e-04 | 1.985191e-04 |
| 7103 | 0 | 504 | 1.051952e-04 | 8.271901e-05 | 5.382110e-05 | 5.137407e-05 | 2.889791e-05 |
| 7103 | 0.35 | 63 | 1.121204e-03 | 1.513493e-03 | 2.001208e-04 | 9.210830e-04 | 1.313372e-03 |
| 7103 | 0.35 | 504 | 1.286309e-04 | 4.844908e-04 | 4.326564e-05 | 8.536527e-05 | 4.412251e-04 |
| 7104 | 0 | 63 | 4.336004e-04 | 3.183144e-04 | 1.700895e-04 | 2.635109e-04 | 1.482249e-04 |
| 7104 | 0 | 504 | 9.057812e-05 | 5.691674e-05 | 1.363781e-05 | 7.694031e-05 | 4.327892e-05 |
| 7104 | 0.35 | 63 | 9.388936e-04 | 9.852436e-04 | 6.168862e-04 | 3.220074e-04 | 3.683574e-04 |
| 7104 | 0.35 | 504 | 8.114428e-05 | 4.035764e-04 | 2.113686e-05 | 6.000742e-05 | 3.824395e-04 |
| 7105 | 0 | 63 | 8.023620e-04 | 6.027622e-04 | 3.461339e-04 | 4.562282e-04 | 2.566284e-04 |
| 7105 | 0 | 504 | 4.029766e-05 | 2.862659e-05 | 1.362092e-05 | 2.667674e-05 | 1.500567e-05 |
| 7105 | 0.35 | 63 | 5.596168e-04 | 8.803610e-04 | 2.072852e-04 | 3.523315e-04 | 6.730758e-04 |
| 7105 | 0.35 | 504 | 3.243659e-05 | 2.649402e-04 | 1.113668e-05 | 2.129991e-05 | 2.538035e-04 |

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Five-seed paired matrix-loss summaries**

| rho | Rows | Median shrink−sample total loss | Range | Lower / higher / tie |
| --- | --- | --- | --- | --- |
| 0 | 63 | -1.544037e-04 | -3.159979e-04 to -1.099353e-04 | 5 / 0 / 0 |
| 0 | 504 | -2.247615e-05 | -5.059440e-05 to -1.167107e-05 | 5 / 0 / 0 |
| 0.35 | 63 | +2.609424e-04 | +4.635002e-05 to +3.922894e-04 | 0 / 5 / 0 |
| 0.35 | 504 | +3.224321e-04 | -9.648573e-05 to +3.558599e-04 | 1 / 4 / 0 |

Matrix conditioning improves in all **20** cases, including those with worse
covariance loss. Numerical conditioning alone does not establish risk accuracy.

## Theoretical oracle: scoring baseline only

**THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC**

One separate numerical constrained min-variance solve per rho uses the known
true covariance, the same cap/budget constraints, and zeros for irrelevant mean
inputs. It approximates the convex theoretical optimum. It is not an estimated
portfolio, third covariance estimator, forecast, investable strategy or choice
available to the candidate. No max-Sharpe oracle is fitted.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Theoretical oracle variances**

| rho | Oracle annual variance | Solver/constraint status |
| --- | --- | --- |
| 0 | 3.823463537645e-03 | checked valid |
| 0.35 | 9.077565007171e-03 | checked valid |

Min-vol absolute regret is `w′C_true*w − oracle_variance`, in **annual variance
units**. Relative regret divides by oracle variance; it is not excess return,
Sharpe regret or realized loss. Raw negative gaps would remain visible: gaps
below −1e-9 flag an invalid oracle comparison, and invalid/missing gaps are
excluded from summaries. No negatives or invalid gaps occurred here.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Every min-vol regret/concentration case**

| Seed | rho | Rows | Sample regret | Shrink regret | Difference | HHI difference | Cap count S / shrink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7101 | 0 | 63 | 1.263942e-04 | 4.394405e-05 | -8.245018e-05 | -0.000677 | 1 / 1 |
| 7101 | 0 | 504 | 2.535931e-05 | 1.785959e-05 | -7.499726e-06 | +0.000185 | 1 / 1 |
| 7101 | 0.35 | 63 | 2.238591e-05 | 3.374902e-05 | +1.136311e-05 | -0.008611 | 2 / 2 |
| 7101 | 0.35 | 504 | 1.995743e-04 | 2.273994e-04 | +2.782510e-05 | -0.023832 | 1 / 1 |
| 7102 | 0 | 63 | 6.821847e-05 | 4.448683e-05 | -2.373164e-05 | +0.002423 | 1 / 1 |
| 7102 | 0 | 504 | 1.274412e-05 | 7.070619e-06 | -5.673496e-06 | +0.000295 | 0 / 1 |
| 7102 | 0.35 | 63 | 1.933663e-04 | 2.232820e-04 | +2.991575e-05 | -0.002740 | 2 / 2 |
| 7102 | 0.35 | 504 | 1.271912e-05 | 2.563266e-05 | +1.291354e-05 | -0.006882 | 2 / 2 |
| 7103 | 0 | 63 | 7.724589e-05 | 3.592938e-05 | -4.131651e-05 | +0.000727 | 1 / 0 |
| 7103 | 0 | 504 | 3.662755e-05 | 2.389638e-05 | -1.273117e-05 | -0.002147 | 1 / 1 |
| 7103 | 0.35 | 63 | 5.512094e-04 | 5.769664e-04 | +2.575705e-05 | -0.004229 | 0 / 0 |
| 7103 | 0.35 | 504 | 3.130487e-05 | 7.494158e-05 | +4.363671e-05 | -0.004519 | 2 / 2 |
| 7104 | 0 | 63 | 2.241866e-05 | 1.575913e-05 | -6.659528e-06 | +0.000827 | 1 / 1 |
| 7104 | 0 | 504 | 1.688631e-05 | 9.362431e-06 | -7.523875e-06 | +0.001508 | 0 / 0 |
| 7104 | 0.35 | 63 | 1.146272e-04 | 2.899829e-04 | +1.753557e-04 | -0.015534 | 2 / 1 |
| 7104 | 0.35 | 504 | 1.041565e-05 | 5.134340e-05 | +4.092775e-05 | -0.011497 | 2 / 1 |
| 7105 | 0 | 63 | 4.787582e-04 | 2.334981e-04 | -2.452601e-04 | +0.004121 | 0 / 0 |
| 7105 | 0 | 504 | 1.285510e-05 | 8.496579e-06 | -4.358521e-06 | -0.000096 | 1 / 1 |
| 7105 | 0.35 | 63 | 1.060655e-04 | 1.127072e-04 | +6.641655e-06 | -0.025893 | 1 / 1 |
| 7105 | 0.35 | 504 | 1.764078e-05 | 3.524854e-05 | +1.760776e-05 | -0.016521 | 2 / 1 |

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Five-seed min-vol regret summaries**

| rho | Rows | Median paired regret difference | Range | Lower / higher / tie |
| --- | --- | --- | --- | --- |
| 0 | 63 | -4.131651e-05 | -2.452601e-04 to -6.659528e-06 | 5 / 0 / 0 |
| 0 | 504 | -7.499726e-06 | -1.273117e-05 to -4.358521e-06 | 5 / 0 / 0 |
| 0.35 | 63 | +2.575705e-05 | +6.641655e-06 to +1.753557e-04 | 0 / 5 / 0 |
| 0.35 | 504 | +2.782510e-05 | +1.291354e-05 to +4.363671e-05 | 0 / 5 / 0 |

HHI is the sum of squared weights; lower means less concentrated. At rho=0,
min-vol HHI **increases in 7/10 cases** although regret falls in every case. At
rho=.35, HHI **falls in all 10** although regret rises in every case. Lower
concentration is neither necessary nor sufficient for lower variance relative
to this constrained oracle. Caps bind targets, not hypothetical future exposures.
Raw max weights, effective number and cap counts are retained for all strategies.

## Counterexample to an overly simple shrinkage story

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Seed 7102 / rho=.35 / 504 rows**

Covariance total loss improves **2.429809e-04 → 1.464951e-04**,
while min-vol regret worsens **1.271912e-05 → 2.563266e-05**.
The sample-error / target / interaction terms are **-6.354507e-05 / +2.389306e-04 / -2.718712e-04**.
The negative interaction outweighs the target term in this finite sample.
That favorable matrix result does not order errors in the particular directions
that matter for the constrained optimizer. It also refutes a blanket claim that
a misspecified diagonal target must worsen every finite-sample covariance loss.

Equal-weight weights and true variance are identical across estimators in every
case. Max-Sharpe and equal-weight true/estimated variances and concentration are
reported, but **oracle regret is not assigned to their different objectives**.
No allocation is selected. The rho=0 min-vol improvement in this grid is an
observation, not a theorem transferring the matrix-loss identity to portfolio risk.

## Numerical checks, reproduction and limits

All **120 candidate records** and **two oracle solves** pass the unchanged checked
constraints. One individual candidate solver start failed; a valid alternative
succeeded. No candidate/oracle failures or unknown start counts occurred. All
**40 min-vol regret rows** are valid with none missing. Maximum checked candidate
constraint residual is **4.64e-12** (limit 1e-7); oracle residuals are zero.
Solver/start diagnostics are included in the JSON, not suppressed.

The fixed grid reproduced every existing numerical table and manifest field
exactly. Explicit valid/missing regret counters were added without changing
those results. Summaries retain five-seed valid/recorded/planned denominators;
paired methods, regimes and nested windows are not independent extra seeds.
Direction ties use 1e-12 only for floating-point handling; no significance,
materiality or winner threshold was chosen. The decomposition tolerance is 1e-12;
reported raw values are not clamped or rounded before calculation.

From the project directory in the pinned environment:

```bash
.venv/bin/python -m markowitz.synthetic_shrinkage_mechanism --output work/synthetic-shrinkage-mechanism-v1
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_mechanism_report.py
.venv/bin/python scripts/check_case_study.py
.venv/bin/python scripts/check_shrinkage_report.py
.venv/bin/python scripts/check_model_evolution.py
```

The fixed CLI writes `SYNTHETIC_mechanism_report.json` in ignored `work/`. Every
table/export carries **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**, with the oracle
separately labelled. No new dashboard or resampling/future-path computation is
part of this mechanism experiment. Prior experiments and all 26 historical
fingerprints, evolution plan/registry/template and previous shrinkage evidence
are preserved. No empirical decision/reservation/consumption is added; no provider
data, real holdout, merge or deployment is accessed.

Verification: **200 local tests passed**, including **17 new mechanism tests**
and all 183 earlier tests. The mechanism evidence audit passed **216 assertions**;
case-study checks passed **135 assertions / 52 local links and anchors**, and the
prior shrinkage audit passed **212 assertions**. The evolution checker remains
proposal-only, not cleared for evaluation. All **34 protected files** (the original
26 fingerprints plus prior-study/evolution files) match reviewed head 43b13c32.

Five seeds, Gaussian one-factor returns, fixed intensity and a known-covariance
oracle cannot establish market behavior or calibrated shrinkage. The zero-target
control is intentionally favorable to this target; the positive-correlation
condition intentionally exposes mismatch. Population sampling noise, target bias
and a realized cross term are distinct. Do not infer population bias/variance,
causal market relationships or optimal intensity from five realizations. A future
variant needs its own authorization and predeclaration, not tuning of this grid.
The ETF study remains unvalidated and source permissions remain unresolved.
