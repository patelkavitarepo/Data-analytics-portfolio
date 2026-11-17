# Independent synthetic serial-dependence investigation · v3

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

Question: does IID training-row bootstrap understate or otherwise mischaracterize
allocation instability under constructed serial dependence? The observed answer
is **conditional and mixed**. There are material method differences for local
max-Sharpe targets, including reversals, even with independent returns. This is
not evidence of systematic IID underestimation or calibrated block-bootstrap
uncertainty. No market conclusion or strategy winner follows.

Authorized by [Holmes checkpoint 6807359399](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6807359399).
The [design](SYNTHETIC_SERIAL_PLAN.md) was committed in
[`dd77e94`](https://github.com/patelkavitarepo/Data-analytics-portfolio/commit/dd77e94)
before v3 numerical runs. All seeds/cases/draws are retained in the
[labeled numerical artifact](synthetic-serial-results.json). Earlier synthetic
code/results, frozen ETF methodology, permissions safeguards and real holdout
are preserved. No provider data, correspondence, merge or deployment.

## Design and validity

Seeds **6006–6010**, **504** ordinal training steps, **15** draws per method,
six abstract assets, **35%** cap and **2%** assumed effective annual risk-free.
Methods: IID complete-row resampling and **circular moving blocks of length 5**.
The optimization objectives, finite solver limits and independent constraint
rechecks are the original implementation: minimum variance, LOCAL max Sharpe,
and fixed equal weights. There is no new empirical strategy or tuning.

Training is stationary Gaussian AR(1) with phi **0** or **.5**. The centered
initial state and each innovation independently have covariance C, the original
one-step daily covariance (pairwise correlation .35). The recurrence is
`x[t] = phi*x[t−1] + sqrt(1−phi²)*epsilon[t]`. Thus covariance remains C and
lag-k covariance is `phi^k*C`. Original arithmetic means/252 are added afterward.
Initialization is exactly stationary; no burn-in or finite-sample normalization.
Both cases share initial and innovation normals for each seed. V3 consumes the
first normal row for initialization; its phi=0 sample therefore is not the v2
training pool, and v3 does not replace that earlier baseline. Sample means,
volatilities and correlations still differ; they are logged, not forced equal.
Observed per-asset lag-one correlations span −.1092 to .1171 for phi=0 and
.3939 to .5690 for phi=.5 across these training samples.

IID uses 504 source-row indices per draw. Moving blocks use 101 starts, retain
five consecutive rows per start modulo 504, and truncate the last block to four
rows. Complete contemporaneous asset vectors stay together. Both methods use
the same original training sample and stream-2 uniform integer array; its first
101 values supply block starts. This pairing shares random starts, **not equal
bootstrap observations** or independent method experiments. Each generator case
reuses those indices. Fits/bootstrap accept only training; **no future sample is
generated**. Ordered source indices, starts, hashes and input hashes are exported.

The fixed objective annualizes sample one-step covariance by 252. Under positive
AR dependence, this is not actual multi-period variance; we deliberately do not
change to a long-run covariance/HAC estimator. The diagnostic asks about the
existing target estimator, not optimal allocation under a different objective.

## Observed allocation-instability diagnostics

Half-L1 is half the sum of absolute bootstrap-versus-original target weight
differences. It measures conditional target reassignment, **not realized trading
turnover or uncertainty coverage**. Below, percentages express target capital
reassignment; differences use percentage points (pp). Medians/ranges use five
seeds separately by generator/strategy. A median paired difference is not the
difference of the two method medians.

The predeclared materiality flag is `|MBB mean half-L1 − IID mean half-L1| ≥ .02`
(**2 pp**). This is a descriptive decision aid, not a significance test,
confidence bound, or economically calibrated threshold. Borderline values
(e.g. seed 6007/.5 max Sharpe, +2.0223 pp) are sensitive to 15-draw Monte Carlo
variation; no extra draws or seed selection were used to resolve them.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Across-seed mean half-L1**

| phi | Target | IID median [range] % | MBB median [range] % | Paired MBB−IID median [range] pp | ≥2 pp flags |
| --- | --- | --- | --- | --- | --- |
| 0 | min_vol | 3.4224 [2.3979, 4.2060] | 2.7038 [2.5602, 4.1458] | -0.5433 [-0.9510, +0.3059] | 0/5 |
| 0 | max_sharpe | 26.3152 [17.9104, 38.2268] | 16.4608 [12.2750, 44.5362] | -5.6225 [-9.8544, +6.3094] | 5/5 |
| 0 | equal_weight | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | +0.0000 [+0.0000, +0.0000] | 0/5 |
| 0.5 | min_vol | 2.9767 [2.6972, 4.1738] | 3.0369 [2.8123, 4.2386] | +0.1920 [-0.1644, +0.6043] | 0/5 |
| 0.5 | max_sharpe | 13.9379 [12.9737, 29.9062] | 15.5774 [10.4381, 36.7857] | +1.6396 [-2.7834, +6.8795] | 3/5 |
| 0.5 | equal_weight | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | +0.0000 [+0.0000, +0.0000] | 0/5 |

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Every optimized seed/case (mean half-L1 %)**

| Seed | phi | Target | IID % | MBB % | MBB−IID pp | ≥2 pp |
| --- | --- | --- | --- | --- | --- | --- |
| 6006 | 0 | min_vol | 2.3979 | 2.7038 | +0.3059 | no |
| 6006 | 0 | max_sharpe | 17.9104 | 12.2879 | -5.6225 | yes |
| 6006 | 0.5 | min_vol | 2.7331 | 2.9251 | +0.1920 | no |
| 6006 | 0.5 | max_sharpe | 12.9737 | 12.0976 | -0.8760 | no |
| 6007 | 0 | min_vol | 3.4224 | 2.8188 | -0.6036 | no |
| 6007 | 0 | max_sharpe | 34.0837 | 30.1501 | -3.9336 | yes |
| 6007 | 0.5 | min_vol | 3.5793 | 4.1836 | +0.6043 | no |
| 6007 | 0.5 | max_sharpe | 25.8944 | 27.9167 | +2.0223 | yes |
| 6008 | 0 | min_vol | 3.5457 | 2.5947 | -0.9510 | no |
| 6008 | 0 | max_sharpe | 26.3152 | 16.4608 | -9.8544 | yes |
| 6008 | 0.5 | min_vol | 2.6972 | 3.0369 | +0.3397 | no |
| 6008 | 0.5 | max_sharpe | 13.9379 | 15.5774 | +1.6396 | no |
| 6009 | 0 | min_vol | 4.2060 | 4.1458 | -0.0602 | no |
| 6009 | 0 | max_sharpe | 38.2268 | 44.5362 | +6.3094 | yes |
| 6009 | 0.5 | min_vol | 4.1738 | 4.2386 | +0.0647 | no |
| 6009 | 0.5 | max_sharpe | 29.9062 | 36.7857 | +6.8795 | yes |
| 6010 | 0 | min_vol | 3.1035 | 2.5602 | -0.5433 | no |
| 6010 | 0 | max_sharpe | 18.3896 | 12.2750 | -6.1146 | yes |
| 6010 | 0.5 | min_vol | 2.9767 | 2.8123 | -0.1644 | no |
| 6010 | 0.5 | max_sharpe | 13.2215 | 10.4381 | -2.7834 | yes |

Equal-weight mean/SD/quantiles of target distance are exactly zero in every
seed/case/method, by construction. This does not imply its risk is known.

- **Minimum variance:** with phi=.5, MBB mean instability exceeds IID in 4/5
  seeds, but all mean differences are below 2 pp (−.1644 to +.6043 pp). The
  median paired difference is +.1920 pp. In the independent control, MBB is
  lower in 4/5 seeds. No mean difference triggers materiality in either regime.
  However, under phi=.5 the median paired p95 difference is **+1.5791 pp**
  (range −.9438 to +2.6854 pp), so mean differences do not describe the entire
  resampling distribution. All per-case SDs/quantiles are retained in the JSON.
- **Local max Sharpe:** with phi=.5, MBB is higher in 3/5 seeds. Material mean
  differences occur in seeds **6007 (+2.0223 pp), 6009 (+6.8795 pp), and
  6010 (−2.7834 pp)**. Seeds 6006 (−.8760 pp) and 6008 (+1.6396 pp) are below
  threshold. The paired median is +1.6396 pp, below threshold; one cannot
  generalize from the two positive flagged cases.
- **Independent-control counterexample:** all five max-Sharpe method differences
  exceed 2 pp in magnitude even at phi=0, with MBB lower in four cases and
  higher in one. The paired median is **−5.6225 pp**, ranging −9.8544 to
  +6.3094 pp. Method differences alone do not identify serial-dependence effects.
- **Distribution reversal:** at phi=.5 max Sharpe, the paired median mean-distance
  difference is positive, while the paired median p95 difference is
  **−2.4250 pp** (range −3.5000 to +21.0000 pp). Quantiles from 15 draws are
  coarse; do not equate a higher mean with every upper-tail summary increasing.

## Concentration, caps and solver evidence

HHI, effective number (1/HHI), maximum weight and cap count are reported both
for original targets and successful resamples alongside instability. The cap
count uses the original `|weight−.35| ≤ 1e-7` tolerance. These are target bounds,
not constraints on hypothetical drifting exposures.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Concentration across method/seed summaries**

| phi | Target | Bootstrap mean HHI range | Bootstrap mean effective-number range | Bootstrap mean cap-count range |
| --- | --- | --- | --- | --- |
| 0 | Minimum variance | .2778–.3052 | 3.2791–3.6039 | 1.4000–2.0000 |
| .5 | Minimum variance | .2728–.2992 | 3.3440–3.6724 | 1.1333–1.9333 |
| 0 | Local max Sharpe | .3052–.3208 | 3.1316–3.3083 | 1.6667–1.9333 |
| .5 | Local max Sharpe | .3063–.3314 | 3.0222–3.2797 | 1.4000–2.0000 |
| Both | Equal weight | 1/6 | 6 | 0 |

These ranges describe ten seed/method summaries per optimized target/regime,
not independent extra seeds or per-draw extrema. Mean 1/HHI is not 1/mean HHI.
All **300/300** minimum-variance resamples bind at least one cap. Max Sharpe
binds in **297/300**. The three nonbinding draws occur in phi=0/seed6008/IID,
phi=0/seed6007/MBB and phi=.5/seed6007/IID (one draw in each). Thus cap incidence
is 14/15 in those groups and 15/15 otherwise; equal weight is 0/300. The high
incidence can suppress target variation without establishing statistical
confidence. The v2 statement that all optimized resamples bind remains a result
of v2, not a fact imposed on this new experiment.

All **30 original targets** and **900 strategy-level bootstrap candidates** are
valid under the existing independent checks. There are **zero candidate failures**,
**16 failed individual bootstrap solver starts**, **one failed reference solver
start**, and **zero unknown start counts** in bootstrap logs. Alternative starts
produce valid candidates. The maximum checked bootstrap constraint violation is
**9.51e-12**, below the unchanged **1e-7** tolerance. Failures are not silently
hidden or treated as zero distance. Reports retain explicit recorded/planned,
successful/failed/unrecorded and valid-distance counts; reference failures make
distances unavailable even when resample fits succeed. Full solver messages are
available from the reproducible CLI sidecar.

## Reproduction and verification

Use the existing pinned Python environment from this project directory:

```bash
.venv/bin/python -m markowitz.synthetic_serial --output work/synthetic-serial-v3
.venv/bin/python -m pytest -q
.venv/bin/streamlit run app.py
# Optional browser smoke, with the app running on this port:
SYNTHETIC_APP_URL=http://127.0.0.1:8504 .venv/bin/python tests/browser_serial_smoke.py
```

CLI outputs `SYNTHETIC_serial_report.json` and
`SYNTHETIC_serial_full_solver_diagnostics.json` in ignored `work/`. The former
contains all numerical summaries, draw weights, ordered resampling indices,
hashes and original target diagnostics; the latter retains full bootstrap
solver messages. The independent Streamlit page **Synthetic serial dependence**
reads the fixed report, without running fits, searching seeds or accessing data.
Every table/chart/export carries **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**.

The fixed grid reproduced byte-for-byte before adding audit-only denominator and
reference-start counters. Algorithm tests cover deterministic recurrence, a
100,000-row fixed Gaussian fixture for marginal scales/correlations/lag-one
correlation within explicit tolerances, exact circular order/wrap/truncation,
block-length-one equivalence to IID, complete-vector indices and hashes,
training-only interface/network isolation, failure injection and missing-reference
handling, duplicate/unrecorded draws, paired denominators, materiality flags and
preserved artifact/safeguard hashes. Streamlit tests forbid fitting/generation and
network access, check labels, and verify an explicit missing-report stop.
The final local full suite passed: **127 tests** (including all 118 previous
tests). Desktop/mobile browser smoke passed with **zero JavaScript errors**, **zero
external requests** and **390px document width at 390px viewport**.

## Limits and next interpretation

Only five fixed seeds, one phi=.5 alternative and one block length are examined;
15 draws leave substantial Monte Carlo variation, especially for local max-Sharpe
solutions near constraints. Shared streams reduce some comparison noise but do
not prove calibration. The circular boundary is artificial, joins break temporal
dependence, and five-row blocks omit dependence beyond their length. Gaussian AR
returns omit tails, regime changes and nonlinear dependence. There is no
repeated-sample coverage/reference-uncertainty experiment.

The methods **do produce descriptively material differences under some specified
conditions**, chiefly max Sharpe here, with both signs. For min-vol mean distance,
the selected 2 pp criterion does not flag any case, although some p95 differences
are larger. Neither observation proves a method is preferable or that IID
systematically understates allocation uncertainty. A later authorized study could
separate block-length effects and bootstrap Monte Carlo error using an independently
predeclared design; no such tuning or expanded experiment was performed here.

The Kenneth French inquiry remains pending. Empirical validation remains blocked
by unresolved rights and independent adjusted-price verification. No synthetic
result resolves those requirements or opens the real holdout.
