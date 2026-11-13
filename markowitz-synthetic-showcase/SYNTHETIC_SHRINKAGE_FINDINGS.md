# Fixed diagonal covariance shrinkage · 006-synthetic-shrinkage-v1

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

In this fixed constructed grid, diagonal shrinkage **did not consistently improve
allocation stability and worsened covariance estimation error in every training
case**. It usually reduced concentration and improved matrix conditioning, but
those properties did not establish more accurate risk or better later outcomes.
There are favorable cases, null cases and reversals, retained below. No estimator
winner, market claim or empirical challenger is selected.

Authorized by [Holmes checkpoint 6833950415](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6833950415).
The [predeclared plan](SYNTHETIC_SHRINKAGE_PLAN.md) was committed in
[`cb6f7ca`](https://github.com/patelkavitarepo/Data-analytics-portfolio/commit/cb6f7ca)
before any numerical run. The [complete labeled artifact](synthetic-shrinkage-results.json)
contains every seed/window/method, paired contrasts, per-method and contrast
median/ranges, failures, bootstrap weights, index hashes and input/matrix manifests.
This is an **independent exploratory synthetic candidate**, not a registered or
approved empirical challenger, replacement champion or confirmation test.

## Fixed design and interpretation

Seeds **7001–7005**; nested trailing training lengths **126/504** from one
504-step pool; **252 later steps**, identical across windows and methods.
Original six abstract assets, annual arithmetic means [.06,.07,.08,.09,.10,.11]
and vols [.10,.13,.16,.19,.22,.25]. IID Gaussian one-factor returns have training
correlation **+.35**. Paired stationary future remains +.35; an **unseen** future
jumps to **+.85**. PCG64 seed streams 0/1/2 separate training, future and bootstrap.
No market calibration, AR dependence, seed selection or parameter search.

Both methods use exactly the same training sample mean. They differ only in
covariance: sample S (ddof=1, annualized by 252) versus **.75*S + .25*diag(diag(S))**.
The latter preserves diagonal sample variances and scales off-diagonals by .75.
The .25 coefficient is predetermined and illustrative. Minimum variance and
LOCAL max Sharpe reuse the original checked solver, cap **35%**, assumed effective
annual RF **2%**. Equal weight is one unchanged control portfolio with two
estimated-risk views, not two independent competing allocations.

**15 IID complete-row resamples** per training case use identical indices/means
across methods. Each method's half-L1 distance is relative to its own original
fitted target. This is conditional target reassignment, not path turnover or a
calibrated uncertainty bound. Contrasts subtract successful-draw means; both
methods have all 15 successes in this run. If failures differ in a future run,
those means would have different denominators, not matched-success-draw estimates.

All fitting/resampling completes before future construction/evaluation. The two
future regimes reuse the same targets and bootstrap diagnostics. Later paths
reset targets every **21 steps**, drift between resets, and compare **0/10 bps**
per gross traded notional including initial purchase, for every method/strategy.
Equal rates do not imply equal trades. Fixed-target covariance risk is distinct
from realized volatility under drifting holdings.

All differences below are **shrinkage minus sample**. Medians/ranges summarize
five seeds separately by window/strategy/regime/cost, not pooled independent
observations. Differences within **1e-10** are numerical ties only, not materiality
or significance thresholds. Percentage points (pp) are used for differences in
fractional risk, CAGR or target reassignment. Counts describe directions in this
grid, not real-world probabilities.

## Covariance error: unfavorable in all training cases

Relative training error is ||estimated C−true C(.35)||F / ||true C(.35)||F.
It increased for **10/10** seed/window pairs. Median paired increase was **.055117**
(range .033572–.071432) for 126 rows and **.067075** (.034787–.089908) for 504.
Matrix condition numbers improved in all ten cases; better conditioning is not
proof of better covariance estimation. The fixed diagonal target removes some
real positive correlations, introducing bias in this design.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Relative training covariance error**

| Seed | Window | Sample | Shrinkage | Difference |
| --- | --- | --- | --- | --- |
| 7001 | 126 | 0.111727 | 0.163532 | +0.051805 |
| 7001 | 504 | 0.092038 | 0.140624 | +0.048586 |
| 7002 | 126 | 0.174510 | 0.245942 | +0.071432 |
| 7002 | 504 | 0.152274 | 0.225898 | +0.073623 |
| 7003 | 126 | 0.159399 | 0.192971 | +0.033572 |
| 7003 | 504 | 0.061879 | 0.128955 | +0.067075 |
| 7004 | 126 | 0.154023 | 0.209140 | +0.055117 |
| 7004 | 504 | 0.059438 | 0.149346 | +0.089908 |
| 7005 | 126 | 0.136240 | 0.204192 | +0.067952 |
| 7005 | 504 | 0.082405 | 0.117192 | +0.034787 |

Distance to the +.85 future covariance also increased in all ten cases. That is
**future-regime misspecification**, not a training-estimation target or evidence
that an estimator should predict a shock. Both distances and conditioning are
retained separately in the artifact.

## Allocation stability and concentration

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Bootstrap mean half-L1 contrasts**

| Window | Target | Sample median % | Shrinkage median % | Median paired difference [range] pp | Lower / higher / tie |
| --- | --- | --- | --- | --- | --- |
| 126 | min_vol | 4.0053 | 4.3483 | +0.2358 [-1.2556, +0.4507] | 1 / 4 / 0 |
| 126 | max_sharpe | 28.8508 | 26.2199 | +0.0000 [-4.2429, +0.6053] | 2 / 2 / 1 |
| 126 | equal_weight | 0.0000 | 0.0000 | +0.0000 [+0.0000, +0.0000] | 0 / 0 / 5 |
| 504 | min_vol | 2.1832 | 2.5368 | +0.3062 [-0.9072, +1.1618] | 2 / 3 / 0 |
| 504 | max_sharpe | 20.2222 | 19.9985 | -0.2236 [-1.2767, +1.3815] | 3 / 2 / 0 |
| 504 | equal_weight | 0.0000 | 0.0000 | +0.0000 [+0.0000, +0.0000] | 0 / 0 / 5 |

A median paired difference need not equal the difference of method medians.
Minimum-variance mean distance rises in **7/10** cases, falls in three. Max Sharpe
falls in **5/10**, rises in four, and is a numerical tie in one. Thus shrinkage
is not a uniform stability improvement. Some p95 changes have the opposite
direction to mean changes; all SDs/quantiles are retained.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Every optimized seed/window, bootstrap mean half-L1 %**

| Seed | Window | Target | Sample % | Shrinkage % | Difference pp |
| --- | --- | --- | --- | --- | --- |
| 7001 | 126 | min_vol | 5.9382 | 6.1741 | +0.2358 |
| 7001 | 126 | max_sharpe | 28.8508 | 26.2199 | -2.6309 |
| 7001 | 504 | min_vol | 2.1832 | 2.9019 | +0.7187 |
| 7001 | 504 | max_sharpe | 19.6115 | 19.9363 | +0.3249 |
| 7002 | 126 | min_vol | 4.0053 | 4.3266 | +0.3213 |
| 7002 | 126 | max_sharpe | 40.1214 | 35.8785 | -4.2429 |
| 7002 | 504 | min_vol | 3.6715 | 2.7643 | -0.9072 |
| 7002 | 504 | max_sharpe | 20.2222 | 19.9985 | -0.2236 |
| 7003 | 126 | min_vol | 2.3832 | 2.5171 | +0.1339 |
| 7003 | 126 | max_sharpe | 15.1984 | 15.8037 | +0.6053 |
| 7003 | 504 | min_vol | 1.3749 | 2.5368 | +1.1618 |
| 7003 | 504 | max_sharpe | 22.9040 | 24.2855 | +1.3815 |
| 7004 | 126 | min_vol | 6.9009 | 5.6453 | -1.2556 |
| 7004 | 126 | max_sharpe | 21.7355 | 22.0218 | +0.2862 |
| 7004 | 504 | min_vol | 2.2851 | 2.1000 | -0.1851 |
| 7004 | 504 | max_sharpe | 19.1334 | 17.8567 | -1.2767 |
| 7005 | 126 | min_vol | 3.8976 | 4.3483 | +0.4507 |
| 7005 | 126 | max_sharpe | 40.3333 | 40.3333 | +0.0000 |
| 7005 | 504 | min_vol | 1.6606 | 1.9668 | +0.3062 |
| 7005 | 504 | max_sharpe | 40.5600 | 39.8955 | -0.6646 |

Fitted HHI falls in **19/20 optimized targets**; the remaining target is a
numerical tie (seed 7005, 126-row max Sharpe). Effective number rises correspondingly.
Bootstrap mean HHI falls in all 20 optimized seed/window/method contrasts, but
mean instability often rises. Every min-vol resample binds at least one cap:
**150/150 per method**. Max-Sharpe cap incidence is **142/150** for sample and
**138/150** for shrinkage; equal weight has none. HHI, effective number, cap count,
maximum weight and fitted weight differences are in the artifact. They describe
targets, not bounds on drifting path exposures. Lower concentration does not
necessarily lower constructed risk.

## Reported risk versus known constructed risk

Every reference row distinguishes the method's own estimated volatility, the same
target cross-evaluated using original S, and known training covariance volatility.
Future-risk rows add known fixed-target future volatility plus signed/absolute
estimate-minus-known gaps. This separates a change in weights from a change in
the risk-reporting matrix.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Equal-weight control, seed 7001 / 126 rows**

| Quantity | Sample view | Shrinkage view |
| --- | --- | --- |
| Estimated volatility | 12.0777% | 11.1127% |
| Original-S cross-evaluated volatility | 12.0777% | 12.0777% |
| Known stationary covariance volatility | 11.9670% | 11.9670% |
| Known shocked covariance volatility | 16.3898% | 16.3898% |

Weights, known risks and all equal-weight path outcomes are **exactly identical**
across methods. Yet its estimated risk falls, and absolute risk error increases
under both future regimes in every seed/window. A lower displayed estimate is
not portfolio improvement.

Minimum-variance targets have **higher known shocked-future volatility in all ten
cases** despite lower fitted HHI. Stationary known-risk changes are mixed. For
optimized portfolios, own-estimate absolute risk gaps widen in **19/20 stationary**
cases and **20/20 shocked** cases. Preserve the favorable counterexample: seed
**7003 / 126 / max Sharpe** reduces stationary absolute gap from **0.5761 pp to
0.0363 pp**, although its bootstrap mean distance rises. These are comparisons on
each method's own target, not an equal-target estimator-calibration experiment.

Seed **7005 / 126 / max Sharpe** supplies a null portfolio comparison: weights,
known risk and path outcomes are numerically unchanged at the fixed tolerance,
but estimated volatility falls **16.8670% → 15.9664%**. Its fitted HHI stays .3350.
Do not mistake the reporting change for robust estimation or a better allocation.

## Finite later-path outcomes, matched costs

The full JSON retains each seed/window/regime/method/cost's CAGR, volatility,
drawdown and gross trades, plus every paired difference and across-seed summaries.
Below, each entry counts **lower volatility / higher CAGR / less-negative drawdown**
with shrinkage out of five seeds. The same direction counts occur at both 0 and
10 bps in this run; magnitudes and traded amounts differ. A tie is not counted as
an improvement. These are metric directions, not composite strategy scores.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Favorable path-direction counts (each cost separately)**

| Window | Target | Stationary: vol / CAGR / drawdown | Unseen jump: vol / CAGR / drawdown |
| --- | --- | --- | --- |
| 126 | min_vol | 3 / 1 / 5 | 0 / 1 / 1 |
| 504 | min_vol | 3 / 2 / 2 | 0 / 2 / 0 |
| 126 | max_sharpe | 3 / 2 / 3 | 1 / 2 / 2 |
| 504 | max_sharpe | 3 / 3 / 5 | 2 / 4 / 4 |
| Both | equal_weight | 0 / 0 / 0 (all ties) | 0 / 0 / 0 (all ties) |

Under the unseen jump, min-vol realized volatility rises with shrinkage in all
ten cases at each cost. Long-window min-vol drawdown is worse in all five seeds;
short-window drawdown is worse in four and improves in one. A lower HHI did not
protect these generated paths from greater common-factor risk.

The findings are not uniformly unfavorable: seed **7002 / 126 / max Sharpe** at
10 bps has stationary CAGR **−9.0349% → −8.2109%**, volatility **12.7594% →
12.1004%**, and drawdown **−13.9485% → −12.9230%**. Its shocked path also improves
these metrics, but CAGR remains negative (**−17.3511% → −16.5867%**). Its mean
bootstrap half-L1 falls by **4.2429 pp**, while its covariance training error and
own-estimate risk gap worsen. Improvement on one path is not estimator superiority.

## Failures, reproducibility and scope

All **60 reference rows** and **900 strategy-level bootstrap rows** contain valid
candidates: no candidate failure, **22 individual bootstrap solver-start failures**,
no reference-start failures and no unknown start counts. Alternative starts yielded
valid candidates. Maximum checked bootstrap constraint violation is **9.75e-12**,
below unchanged tolerance **1e-7**. Full diagnostics/failures are retained, not
converted to zero instability or hidden. Summaries state recorded/planned,
successful/failed and valid-distance/pair denominators.

The fixed grid was reproduced with identical existing numerical tables, manifests,
weights, index hashes and diagnostics. Per-method descriptive summaries were added
without changing the predeclared design or those outputs. No new seed/parameter
sweep or post hoc materiality rule was used.

From this directory, with the existing pinned Python environment:

```bash
.venv/bin/python -m markowitz.synthetic_shrinkage --output work/synthetic-shrinkage-v1
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_case_study.py
.venv/bin/python scripts/check_model_evolution.py
```

The CLI writes `SYNTHETIC_shrinkage_report.json` and full
`SYNTHETIC_shrinkage_solver_details.json` under ignored `work/`. Every JSON table
row and every findings table carries the synthetic evidence label. No extra
dashboard or app-time optimization is added. Tests cover deterministic nested/
paired scenarios, shrinkage/PSD/diagonal math, original sample-method equivalence,
identical rows/means, future-mutation isolation, independent constraint checks,
invalid candidates/covariance, failures/missing reference/unknown starts, valid
pair denominators, costs, labels and preserved historical/registry hashes.

Verification: **183 local tests passed**, including **15 new shrinkage tests**
and all 168 earlier tests. The new offline report audit passed **212 assertions**;
existing case-study checks passed **130 assertions / 47 local links and anchors**.
The evolution checkpoint still reports proposal-only, not cleared for evaluation.

Five seeds, only 15 IID draws, six Gaussian assets and two stipulated correlation
regimes do not establish uncertainty coverage or real-world behavior. The .25
coefficient is neither empirically calibrated nor the best shrinkage intensity.
Different targets, intensities, mean estimators or dependence structures are not
part of this study; they need separate predeclaration. Better conditioning or
concentration is not a substitute for risk accuracy or investing evidence.

All **26 historical fingerprints**, earlier v1/v2/v3 artifacts and the empirical
registry/template remain unchanged, with zero empirical decisions or consumption
events. The ETF model, permissions and real holdout are untouched. The Kenneth
French inquiry is still pending, not a licence. No market/vendor data, merge or
deployment. No empirical promotion is requested from these exploratory findings.
