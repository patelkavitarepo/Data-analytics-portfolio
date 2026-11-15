# Synthetic portfolio accounting and timing checkpoint

Implements [Holmes's synthetic-only assignment](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6886452300).
**All returns, targets, candidate scores and accounting outcomes below are invented
test fixtures. They are not empirical market evidence or strategy findings.**
The empirical protocol remains `DRAFT_NOT_FROZEN`; `performance_cleared=false`.

## Implementation and verification

[synthetic_accounting.py](industry_companion/synthetic_accounting.py) contains
pure standard-library functions for explicit date grids, ten-column simple
returns and predetermined target instructions. It has no data loader, file or
network effects, optimizer, CLI, dashboard, export path or workflow integration.
A synthetic-origin acknowledgement is required; it is a caller assertion, not
a cryptographic proof of origin. Detailed ledgers have redacted representations
and are inspected only in tests; safe summaries are explicitly synthetic.

The local suite has **323 passing tests**: the previous **208**, **99** accounting
cases, **9** date/window cases and **7** additional numerical controls. Fixtures
use pinned local XNYS calendar metadata, not market observations. Existing
network prohibition remains active. The safety guard additionally restricts the
accounting module to its pure standard-library imports and rejects I/O/dynamic
execution calls. No workflow, launcher, source parser, numerical source audit,
raw policy or published showcase is changed by this implementation.

[GitHub CI run 43659044460](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43659044460)
confirmed **323 tests**, both safety guards and the original synthetic-only CLI
at `cc894acd2e8e185d97e5f8c11a5efe5bdf9f337d`. The logs were checked; no
artifacts were produced. Local actionlint v1.7.7 also passes unchanged workflows.

The tests cover monthly d0/d1/d2 chronology, first-2021 exposure, drift rather
than daily resets, target cap versus drift exceedance, common entry convention,
traded notional/half-turnover, post-return close fees, net wealth, missing dates,
partial/final periods, 60 complete calendar months, the 1,000-count rule,
post-2024 poison rejection before value access, numerical extinction/overflow,
sample metrics, fallback flags and manual-score tie rules. Five predetermined
seeds crossed with three cost settings give **15 deterministic invariant cases**
checking budget, reproducibility, multiplicative wealth and cash reconciliation.
No covariance, expected returns or portfolio weights were fitted.

## Hand-calculated controls actually checked

| Invented control | Expected and observed test result |
| --- | --- |
| Equal weights; one industry doubles | Gross factor 1.1; that industry's drifted weight is `2/11`, the other nine are `1/11` each. |
| Rebalance those holdings back to equal | Traded-notional proxy `q=9/55`; half-turnover `9/110`. Neither quantity is silently substituted for the other. |
| Three-session fixture: initial zero returns, then one industry doubles on d1, then zero returns; cost rate 5 bp | Entry fee `0.0005`; d1 close fee `0.000089955`; terminal wealth `1.099360045`, matching `(1-0.0005)*1.1*(1-0.0005*9/55)` within floating-point tolerance. |
| Two zero-return sessions, entry cost 5 bp | First net return `-0.0005`; second zero; final wealth `0.9995`; daily-close drawdown `0.0005` against reference wealth 1. |
| Initial fee 1%, then a later common 10% gain | Actual fee is `0.01`; terminal wealth `1.089`. The `0.011` gross/net wealth gap includes foregone compounding and is not the cash fee. |
| One surviving industry after the other nine lose 100% | Valid positive-wealth drift can reach 100% in one holding: HHI 1/effective count 1. A new 100% target is rejected by the candidate 35% target cap. |
| Constant net-return sequence without costs | Realized volatility can be zero; Sharpe is undefined with an explicit reason, not infinite or a fabricated finite winner. |
| Declared solver failure with unchanged equal target | Zero traded notional/fee can coexist with a failure flag; identical wealth alone does not prove solver success. |

These controls validate arithmetic only. Annualizing a short toy sequence is a
formula check, not an estimate of a market strategy's performance. Reporting
uses net daily returns (`ddof=1`), constant annual-effective 2% converted daily,
reference-1 daily-close drawdown and explicit undefined/overflow reasons.

## Findings, counterexamples and limits

Tests/review exposed and corrected four numerical issues: unnecessary unit-budget
adjustment created false tiny zero-return turnover; complement-only correction
could reject a valid seed-7 path; equal common returns could drift through
division roundoff; and cumulative fee sums could overflow despite finite daily
states. Regression controls retain the counterexamples. Drift adjustments are
bounded/recorded; supplied targets are not repaired and genuine tiny trades are
not discarded by a turnover threshold. See [PROTOCOL_REVIEW_01.md](PROTOCOL_REVIEW_01.md)
for the **33-item ambiguity/test crosswalk** and exact numerical conventions.

Important unresolved choices remain: skipping a final trade with no in-range d2;
the hypothetical `c*q` fee proxy versus exact self-financing trade costs; strict
binary64 target budgets versus a future solver's `1e-8` feasibility tolerance;
and handling true bankruptcy separately from invalid observations/numerical
exhaustion. Calendar provenance, actual common-return validation and an estimator's
information set need independent future checks. The prototype checks declared
instruction chronology, not whether an external caller secretly chose targets
using future data. No estimator, SLSQP fit, empirical comparison harness or
point-in-time availability proof has been implemented.

## Source status and next review

The owner's completed [HEAD run 43656997583](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43656997583)
was independently checked: `REACHABLE_HEAD_2XX`, 208 tests, no artifacts. That
proves only the observed HEAD route, not GET success, raw-data rights, archive
quality or historical vintage. **No new HEAD/GET, source bytes, licensing email,
live workflow or launcher PR was requested by this task.** Raw hosted policy
remains `pending_owner_rights_review`, `live_enabled=false`; no correspondence
or raw observations are published.

Next review should accept or revise the explicit mechanics above while keeping
the protocol unfrozen. A useful separately authorized synthetic follow-up would
compare the fee proxy with a self-financing cost equation on predetermined
invented cases; it has not been run here. Resolve the target-budget/solver
interface and terminal-boundary choices before implementing any optimizer.
Hosted raw-data permission remains a separate owner evidence/clarification
question. Nothing here enables it, freezes a study or authorizes an empirical run.
Original ETF research/holdout, earlier evidence and the published synthetic
showcase remain untouched. No PR merge or deployment is part of this checkpoint.
