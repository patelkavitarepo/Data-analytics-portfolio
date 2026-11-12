# Project 006 — Markowitz Portfolio Optimization: The Efficient Frontier

Can a constrained Markowitz portfolio improve **out-of-sample risk-adjusted
performance** over equal weights? That empirical question remains unanswered.
The completed work shows why estimation error, changing asset relationships and
resampling assumptions must be examined before interpreting an optimized portfolio.

This synthesis covers the original three synthetic stages. The later independent
[fixed covariance-shrinkage study](SYNTHETIC_SHRINKAGE_FINDINGS.md) is exploratory
and leaves their evidence and the empirical registry unchanged. A subsequent
[mechanism study](SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md) isolates target mismatch
and sampling error using a labelled theoretical oracle; it is not confirmation.

## Two distinct research tracks

The **unvalidated ETF application** is a Python/Streamlit research engine for
SPY, QQQ, IWM, EFA, EEM, TLT, GLD and VNQ. Its frozen protocol estimates on
**2016–2022**, validates on **2023–2024**, and reserves **2025 onward** as an
untouched holdout. It compares prespecified minimum-variance and local
maximum-Sharpe candidates with equal weights and an external SPY benchmark.
**No real validation or holdout performance has been evaluated or established.**
The dashboard's implementation and tests are not evidence of investment value.

The **completed offline stress laboratory** uses six abstract assets and ordinal
simulation steps, not ETF proxies or calendar histories. Three versioned studies
examine mechanisms under deliberately constructed assumptions. Their numerical
findings below are **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**. They neither answer
the ETF performance question nor license any market dataset.

## Methods and how to read the evidence

All studies retain long-only, fully invested targets, a **35% per-asset cap**,
and **2% assumed effective annual risk-free rate**. Sample daily means and
covariance are annualized using **252 steps/year**. The original checked solver
finds a minimum-variance candidate and a deterministic multi-start **local**
max-Sharpe candidate; equal weights provide a fixed comparator. Solver success,
finite weights and constraint residuals are checked independently. Failed
candidates remain logged and unavailable, rather than becoming zero instability.

The evidence types answer different questions:

- **Fitted estimated risk/Sharpe:** calculated from training-sample estimates;
  changing an estimated mean can change reported Sharpe without improving outcomes.
- **Stipulated future covariance risk:** `sqrt(w′Σw)` for a fixed target and a
  covariance supplied by the synthetic generator. This is analytically known
  within the constructed model, not an observation about future markets.
- **Finite-path outcomes:** volatility and drawdown realized on a particular
  generated later path. They need not move in the same direction. The first two
  stages reset targets every **21 steps**, allow intervening weight drift and
  compare **0/10 bps** costs per gross traded notional, including initial purchase.
- **Bootstrap half-L1:** half the sum of absolute differences between a resampled
  fit's weights and the original target. A percentage measures target capital
  reassigned, **not actual trading turnover**, realized loss or uncertainty coverage.
  Actual path trading uses gross absolute changes from drifted holdings.

HHI (sum of squared weights), effective number (1/HHI) and cap incidence accompany
weight variability. A bound can hold weights almost fixed while risk rises.

## Stage 1 — Baseline, estimation error and known regimes

[Design and findings](SYNTHETIC_LAB.md) · [Committed evidence](synthetic-default-summary.json)

The original study uses seed **6006**, **504 training / 252 later steps**, and
**20 IID bootstrap draws** per scenario. Five scenarios cover a baseline,
high correlation in both samples, an asset-volatility shock, biased estimated
means, and an unseen cross-group correlation sign flip. Common random streams
support comparisons; fitting and resampling use training data only.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Single-seed examples**

| Diagnostic | Committed observation | Interpretation boundary |
| --- | --- | --- |
| Baseline mean bootstrap half-L1 | Minimum variance **2.55%**; local max Sharpe **12.73%** | Conditional sensitivity, not an estimator ranking |
| Mean bias, minimum-variance estimated Sharpe | **0.420 → 0.571**, with unchanged weights and later outcomes | An estimate improved; the portfolio did not |
| Known high-correlation regime, min-vol estimated volatility / HHI | **9.25% → 11.94%** / **0.2973 → 0.3350** | Nearly fixed bootstrap weights can coexist with greater risk/concentration |
| Unseen sign flip, equal-weight stipulated future volatility | **11.97% → 6.57%** | A scenario called stress can diversify rather than harm |

The positive-correlation illustration changes **both training and later**
distributions, so it does not test an unanticipated jump. The next stage addresses
that distinction. These one-seed observations cannot establish general robustness.

## Stage 2 — An unseen correlation jump and training-window sensitivity

[Predeclaration](SYNTHETIC_ROBUSTNESS_PLAN.md) · [Findings](SYNTHETIC_ROBUSTNESS_FINDINGS.md) · [Evidence](synthetic-robustness-results.json)

Seeds **6006–6010**, nested trailing windows **126/504**, and **10 IID draws** per
training case were committed before numerical runs. Training correlation stays
**+0.35**. Paired later paths retain +0.35 or jump unseen to **+0.85**, sharing
innovations across conditions/windows. Fits and bootstrap are reused unchanged;
future covariance and future returns cannot enter training.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Five-seed descriptive summaries**

| Diagnostic | Committed observation | Counterexample or limit |
| --- | --- | --- |
| Paired targets | All **30** target distances exactly **0** | Identical weights do not imply identical risk |
| Long-window min-vol stipulated volatility inflation | Median **+30.78%**, relative to stationary future | A model-risk ratio, not a realized return or strategy ranking |
| Min-vol bootstrap mean half-L1, short → long | Median **6.46% → 3.12%**; lower in **5/5** seeds | Median target concentration increased; less variability is not less concentration |
| Local max-Sharpe bootstrap mean half-L1, short → long | Median **26.83% → 28.84%**; higher in **3/5** seeds | More observations did not improve every diagnostic |
| Seed 6006, long-window min-vol, cost-free drawdown | **−12.1597% → −12.0684%** after the jump | A slightly shallower drawdown despite higher modeled and realized volatility |

Every optimized bootstrap candidate binds at least one cap. All paired targets
have higher stipulated volatility after the jump, yet the drawdown exception
persists under the cost sensitivity. Short and long windows are nested, not
independent experiments. Across-seed medians/ranges are descriptive, not confidence
intervals. These ten-draw results preserve, rather than replace, the original
twenty-draw baseline.

## Stage 3 — Serial dependence: IID versus moving blocks

[Predeclaration](SYNTHETIC_SERIAL_PLAN.md) · [Findings](SYNTHETIC_SERIAL_FINDINGS.md) · [Evidence](synthetic-serial-results.json)

Seeds **6006–6010**, **504 training steps**, **15 draws per method**, and circular
blocks of length **5** were predeclared. Gaussian AR(1) cases use **phi=0/.5**,
with stationary initialization and the same theoretical one-step marginal means
and covariance. Paired innovations do not force finite-sample moments to match.
IID resamples complete six-asset rows; moving blocks retain within-block order,
wrap at the training boundary, and truncate the final block. Shared random starts
do not make the two resampled datasets identical. No future sample is generated.

Below, each difference is **moving blocks minus IID mean half-L1**, in percentage
points (pp). The median is taken over paired seed differences, not obtained by
subtracting method medians. The predeclared **2 pp** absolute threshold is a
**descriptive materiality flag**, not a statistical test or confidence bound.

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS · Paired method contrasts**

| Generator | Target | Median difference (pp) | Range (pp) | Flagged seeds |
| --- | --- | --- | --- | --- |
| phi=0 | Minimum variance | −0.5433 | −0.9510 to +0.3059 | 0/5 |
| phi=.5 | Minimum variance | +0.1920 | −0.1644 to +0.6043 | 0/5 |
| phi=0 | Local max Sharpe | −5.6225 | −9.8544 to +6.3094 | 5/5 |
| phi=.5 | Local max Sharpe | +1.6396 | −2.7834 to +6.8795 | 3/5 |

Under positive dependence, the material max-Sharpe differences include **both
signs**. Material differences also occur in every independent-control max-Sharpe
case. Therefore a method contrast alone does not establish a causal effect of
serial dependence or systematic IID underestimation. Mean and tail summaries can
also disagree: the phi=.5 max-Sharpe paired median p95-distance difference is
**−2.4250 pp**, despite its positive mean-distance contrast.

Cap incidence remains high: **300/300** minimum-variance and **297/300** max-Sharpe
resamples bind a cap. Equal-weight target instability is zero by construction,
not proof that its risk is known. The fixed objective still annualizes one-step
sample covariance; under AR dependence it is not true multi-period variance.
No method calibration, coverage guarantee or strategy winner is established.

## What is established, and what remains limited

The software distinguishes training estimates, stipulated model risk, later-path
outcomes, target sensitivity and trading. Deterministic streams, input/index
hashes, failure logs, constraint checks and future-mutation tests make the studies
auditable. The reviewed implementation passed [**127 tests in GitHub CI**](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43104105168); the
read-only later-stage pages display committed results without app-time refits.
Tests verify calculations and isolation, not investment performance.

The evidence is intentionally narrow: one baseline seed in the first stage,
five fixed seeds in each later stage, short bootstrap runs and Gaussian inputs.
The studies do not model market tails, liquidity, nonlinear dependence or actual
executions. Circular blocks create artificial boundary joins and omit longer
lags; few draws leave substantial Monte Carlo variation, especially for local
max-Sharpe candidates near caps. None of the bootstrap ranges are demonstrated
uncertainty bounds. Findings do not transfer automatically across samples,
strategies or real markets.

Future changes follow the [Model Evolution Protocol](MODEL_EVOLUTION_PLAN.md):
versioned preregistration, as-of information and a fresh confirmation reservation.
This policy adds no experiment or result. The owner’s personal lesson/quotation
remains **pending final editorial approval**.

## Status and gates to empirical validation

[DATA_RIGHTS.md](DATA_RIGHTS.md) records rights questions separately for automated
collection, private analysis/retention, independent comparison, public derived
outputs and raw redistribution. **No source is approved for this workflow.**
A successful download, software licence or educational label is not a data-use
grant. As recorded in [Holmes's synthesis checkpoint](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6807747362),
the owner's Kenneth French permission inquiry has been sent; no grant has
been received or recorded. Earlier rights documents are dated investigation
snapshots, not proof of current authorization.

Before any authorized ETF validation, obtain documented compatible primary and
independent-reference rights, then verify all ETF coverage and split/dividend
adjustment on the same timestamped, hashed snapshot under
[ADJUSTMENT_REVIEW.md](ADJUSTMENT_REVIEW.md). Only a separately reviewed source-policy
change and complete evidence can unblock the frozen validation period. This
pass authorizes no acquisition, correspondence or evaluation. The real holdout
stays hidden; publication remains subject to owner approval.

An academic **10-industry companion** would require a separate research protocol,
permissions and methodological assessment. Industry portfolios are not the ETF
universe and cannot validate the ETF application. A future synthetic investigation
would likewise need a new authorization and predeclaration; no fourth experiment
was run for this synthesis.

## Short glossary

| Term | Meaning here |
| --- | --- |
| Minimum variance | Weights chosen to minimize estimated portfolio variance under the constraints |
| Max Sharpe / local candidate | Weights seeking the highest estimated excess return per unit of volatility; a local solver does not certify the global best |
| Covariance / correlation | How returns vary together; correlation rescales covariance to remove units |
| Concentration / 35% cap | Uneven exposure across assets; the cap limits each target weight, not drifted weights between resets |
| Bootstrap | Refit portfolios on resampled training observations to examine conditional estimator sensitivity |
| IID | Independent, identically distributed; row bootstrap ignores temporal ordering |
| Moving blocks | Resampling consecutive row groups to retain some short-range temporal relationships |
| AR(1) / phi | Constructed dependence of the current centered return on the preceding one; phi controls persistence |
| Out-of-sample | Evaluation on observations excluded from fitting; a synthetic later path is not real ETF validation |
| Holdout | Reserved empirical period kept untouched for a later, explicitly authorized evaluation |

Use the [README navigation and reproduction commands](README.md#navigation) to
inspect the evidence. Owner review determines interpretation and any publication;
this case study is a review artifact, not an investment recommendation.
