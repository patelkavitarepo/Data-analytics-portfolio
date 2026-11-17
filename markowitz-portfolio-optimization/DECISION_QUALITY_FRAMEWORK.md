# Decision Quality Framework · 006-decision-quality-v1

Status: **documentation and audit only**. This is an additive research scorecard,
not a new experiment, model, empirical preregistration or investment recommendation.
[Holmes checkpoint 6835142013](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6835142013)
requests this synthesis. The ETF question remains unanswered; no source has passed
the rights/independent-verification gates and the original holdout remains untouched.

The purpose is to ask **which claim the evidence supports**, not to compress
incompatible claims into one score. A cleaner estimate, a different allocation,
a favorable path and reliable software are separate findings. None substitutes
for the others.

## Four distinct evidence columns

| Review question | Estimation quality | Decision quality | Forward behavior | Operational trust |
| --- | --- | --- | --- | --- |
| What is being assessed? | Input/vintage reliability and the estimated relationships | Weights chosen under the stated objective and constraints | Behavior after fitting, under known model assumptions or new observations | Whether access, information timing, computation and evidence can be trusted |
| Record separately | Covariance loss and its units where truth is known; PSD/conditioning; coverage, adjustments and vintage | Target weights, objective, HHI/effective number, caps, sensitivity; synthetic min-vol oracle regret | Synthetic fixed-target model risk; separately, held-out realized volatility/drawdown/Sharpe/CAGR and matched costs where lawfully available | Rights/verification evidence, timestamps, point-in-time manifests, hashes, versions/seeds, solver/start failures and residuals, confirmation access history |
| What cannot be inferred? | PSD or improved conditioning does not prove lower estimation loss | Lower HHI or weight variability does not prove a better objective outcome; target half-L1 is not trading turnover | A training estimate is not a prediction guarantee; higher volatility need not deepen every realized drawdown | Test/solver success does not prove model value, data correctness, entitlement or unseen confirmation |
| Real-market availability | Data quality/estimated covariance can be reviewed with lawful evidence; **loss against true covariance is unobservable** | Weights/objectives/concentration are measurable; **true-covariance oracle regret is unavailable** | Lawful held-out outcomes can eventually be observed; **known true future covariance risk is unavailable** | Evidence can be audited, but assertions/hashes alone cannot establish its truth |

True covariance is a generator privilege in synthetic work, not something a
subscription or independent price check reveals. A realized covariance matrix
is another sample estimate, not privileged population truth. A model-implied
risk calculation remains conditional on that model; it is not known future risk.
The oracle is a **THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC**, used only for
scoring synthetic min-vol decisions under identical constraints. It is not a
third estimator or a benchmark that can be recreated from observed market prices.

The evidence sequence is software/synthetic checks → time-separated validation →
fresh unseen confirmation. This is a sequence of justified claims, not a ranking
or weighting of the four columns. Validation used to revise a model is development
evidence. It cannot simultaneously be its untouched confirmation.

## Committed counterexamples

Every numerical example in this section is **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**.
The selectors below identify exact rows in the linked JSON; values are rounded
only for display. These are constructed cases, not market probabilities.

### Better matrix estimation, worse allocation regret

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

[Mechanism findings](SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md) ·
[artifact](synthetic-shrinkage-mechanism-results.json): `paired_covariances` and
`paired_portfolios`, seed **7102**, rho **.35**, **504** rows, min-vol.

| Quantity | Sample covariance | Fixed diagonal shrinkage |
| --- | --- | --- |
| Total covariance squared loss | 2.429809e-04 | 1.464951e-04 |
| True min-vol variance regret | 1.271912e-05 | 2.563266e-05 |
| Target HHI | 0.292250 | 0.285368 |

Matrix loss improves and concentration falls, yet decision regret worsens.
Squared matrix loss has squared annual covariance units; regret has annual
variance units. Neither is return or volatility. This is a counterexample to
substituting an estimation diagnostic for the constrained decision objective.
The same study's zero-correlation loss reduction includes an algebraic control;
its observed portfolio improvements are not a universal shrinkage guarantee.

### A lower estimate, with no new portfolio

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

[Shrinkage findings](SYNTHETIC_SHRINKAGE_FINDINGS.md) ·
[artifact](synthetic-shrinkage-results.json): `references` and `paired_paths`,
seed **7001**, **126** rows, equal weight.

| Quantity | Sample view | Shrinkage view |
| --- | --- | --- |
| Estimated volatility | 12.0777% | 11.1127% |
| Known training-covariance volatility | 11.9670% | 11.9670% |

Weights and later-path outcomes are identical across estimators. Only the
risk-reporting matrix changes. This is not a portfolio improvement; the known
covariance risk is available only because the experiment specifies truth.

### Higher realized volatility, shallower drawdown on one path

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

[Robustness v2 findings](SYNTHETIC_ROBUSTNESS_FINDINGS.md) ·
[artifact](synthetic-robustness-results.json): `paired_paths`, seed **6006**,
**504** rows, min-vol, **zero cost**, stationary versus unseen positive jump.

| Finite-path quantity | Stationary | Unseen jump |
| --- | --- | --- |
| Realized annualized volatility | 8.5462% | 11.3125% |
| Maximum drawdown | −12.1597% | −12.0684% |

The drawdown is slightly less negative despite higher modeled and realized
volatility. Both use the same cost convention and frozen target; drift/trades
can differ. A fixed-target covariance risk calculation and a path's drawdown
answer different questions. One favorable path exception is not regime protection.

Operational checks remain a separate claim: the
[mechanism report](SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md) retains an unsuccessful
individual solver start even though accepted candidates pass independent checks.
Failing starts, failing candidates and missing metrics must be distinguished;
none becomes a reassuring zero. Passing the regression suite establishes tested
software behavior, not lawful data access or investment effectiveness.

## Future comparison scorecard — fill before outcome access

This is an **unfilled, non-aggregated template** for the sample-covariance reference
and a *separately authorized* challenger. It proposes no new candidate or numerical
pass/fail threshold. Apply the existing [Model Evolution Protocol](MODEL_EVOLUTION_PLAN.md)
and preserve its records. Record a versioned comparison ID and preregistration
commit; exact hypothesis/change/failure mode; eligible snapshot and manifest hashes;
training/calibration/validation intervals; decision/publication/revision clocks;
code/environment/RNG/command; owner signoff and fresh-confirmation reservation
status. No dates or confirmation authorization are assigned here.

| Entry for each baseline/challenger comparison | Estimation quality | Decision quality | Forward behavior | Operational trust |
| --- | --- | --- | --- | --- |
| Freeze before evaluation | Estimator, target/intensity if applicable, input audits, units and loss/reference definition | Objective, same universe/constraints, comparators, concentration/sensitivity measures | Same evaluation dates, target resets/drift, execution, initial purchase and cost conventions; outcome definitions | Entitlement, independent verification, as-of/vintage contract, versions/hashes, failure rules, access history and signoff |
| Record baseline and challenger separately | Value/source/unit; PSD/conditioning and data/vintage limitations | Weights/objective, HHI/caps and sensitivity; oracle regret **synthetic only** | Model-assumed risk separate from realized metrics; benchmark and cost alignment | Reproduction result, successful/failed starts/candidates, residuals, missingness and valid/planned denominators |
| Record paired contrasts | Same observations/reference; distinguish diagonal/off-diagonal loss when applicable | Same information/constraints; target distance separate from drifted trades | Identical date/cost basis; disclose different traded amounts and exposures | Same snapshot/clock; keep diagnostics and all attempts, not only accepted outputs |
| Record disconfirming evidence | Worse error, revision/basis uncertainty, null/mixed cases | Worse objective loss/regret; concentration/cap and sensitivity tradeoffs; unchanged targets | Adverse or mixed paths/regimes, sensitivity and limited sample uncertainty | Failures, incomplete rights, chronology violations, consumed or unavailable confirmation |
| Availability and decision note | Observed / uncomputed / blocked / not applicable / structurally unobservable, with reason | Same states; do not replace unavailable oracle metrics with zero | Same states; synthetic outcomes remain labelled and separate | Clear / blocked / unresolved **for each gate**, with evidence and next authorization needed |

“Not applicable” means excluded by the preregistered scope, not unavailable
results hidden after evaluation. “Uncomputed” and “blocked” are not zeros.

Retain both values and paired differences, units, denominators and null/mixed/
disconfirming findings. Use only predeclared summaries; do not pool paired cases
as independent observations. Keep 006-v1 min-vol/local max-Sharpe and equal weight
as references, with SPY for the original empirical comparison. Same eligible
snapshot and clock do not mean every method has identical estimates or trades.

**No composite score, metric weights, invented success thresholds, confidence
bounds or automatic winner.** A diagnostic is not an objective unless explicitly
preregistered as such. Any future decision criterion needs separate authorization
and must be frozen before its evidence is inspected; it cannot be retrofitted to
these examples. Record repeated variants, metric/window selection and stopping
choices. Multiple comparisons and short synthetic samples limit interpretation.
A mixed or inconclusive scorecard is a legitimate outcome.

## Stop / next-evidence decision tree

1. **No approved source or unresolved intended-use rights:** stop empirical claims.
   [DATA_RIGHTS.md](DATA_RIGHTS.md) separates automated access, analysis/retention,
   independent comparison and publication/redistribution. A download, account,
   checkbox, successful test or pending inquiry is not permission. No provider
   contact or retrieval is authorized by this framework.
2. **Source authorized, independent adjustment verification incomplete:** still
   stop performance evaluation. Complete [ADJUSTMENT_REVIEW.md](ADJUSTMENT_REVIEW.md)
   against the same eligible snapshot with equivalent price basis. Coverage or a
   source checking itself is not independent adjustment evidence.
3. **Rights, verification and point-in-time evidence complete:** obtain separate
   evaluation authorization, then freeze the protocol/scorecard before outcomes
   are inspected. Existing runtime source gates require their own reviewed change;
   this document or a filled scorecard cannot enable them. Revisions require new
   snapshots/manifests and explicit restatements, not changed historical claims.
4. **Validation available:** use it to assess the prespecified comparison. If it
   motivates changes, log them as development. Promotion of a revised challenger
   requires a frozen version, fresh previously unseen confirmation and owner
   review. Evidence may justify reject/defer rather than another variant.
5. **Period already consumed or unavailable for a new comparison:** stop fresh-
   confirmation claims for that comparison. Retain/report any first authorized,
   preregistered confirmation result with its access/consumption history; consuming
   the period does not erase that result. The original open-ended **2025+** reserve
   is **not a reuse pool**, including renamed or later subsets. Any performance peek is irreversible consumption; log it, never
   relabel untouched. No fresh dates or reallocation are approved here.

Current status: lawful empirical evaluation remains **blocked**; true-covariance
loss/oracle/known-future-risk fields are additionally **structurally unobservable**
in real markets. All empirical performance and confirmation entries remain
uncomputed. Stop at this framework until a justified new question or lawful
empirical evidence is separately authorized. No model promotion, additional
synthetic variant, market claim, merge, deployment or publication is authorized.

## Read-only verification and limits

The [framework audit](scripts/check_decision_quality.py) checks displayed figures
against committed JSON, exact case selectors, labels, local links and historical
fingerprints. It never fits a model, generates returns, reads market data or
contacts a provider. Run it and the existing checks from the project directory:

```bash
.venv/bin/python scripts/check_decision_quality.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_mechanism_report.py
.venv/bin/python scripts/check_shrinkage_report.py
.venv/bin/python scripts/check_case_study.py
.venv/bin/python scripts/check_model_evolution.py
```

Five-seed constructed Gaussian studies, fixed targets/intensity, short bootstrap
runs and known-truth oracles cannot supply calibrated market uncertainty. The
examples explain distinctions, not probabilities or universal rankings. Metadata
checks cannot prove truthful timestamps, actual entitlement or unseen status;
manual review and unchanged runtime safeguards remain necessary. All prior code,
plans, numeric artifacts, model-evolution records, README and CASE_STUDY are
preserved. The owner's interpretation and publication approval remain separate.

Verification for this documentation-only pass: **200 existing tests passed**;
the framework audit passed **96 assertions / 11 local links**. Existing mechanism,
shrinkage and case-study audits passed **216**, **212** and **135** assertions
respectively (case study: **52 local links/anchors**). The model-evolution checker
remains proposal-only, not cleared for evaluation. No experimental CLI was run.
