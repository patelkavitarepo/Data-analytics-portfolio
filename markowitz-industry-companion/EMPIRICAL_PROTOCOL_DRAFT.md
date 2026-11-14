# Industry companion empirical protocol · version 0.1

**Status: `DRAFT_NOT_FROZEN` — owner review required.**

This is a prospective discussion draft responding to
[Holmes's checkpoint](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6870252210).
Every methodological choice below is **unfrozen**. Specific candidate settings
make the proposal reviewable; they are not instructions to run an experiment.
No real returns, optimizer, backtest, parameter search or confirmation-period
inspection was used to prepare this document. No empirical finding is claimed.
The original ETF study, its holdout, all synthetic evidence and the published
showcase remain separate and unchanged.

## Research question and permitted input

For a hypothetical allocation across ten US equity industries, how do a fixed
equal-industry allocation and two constrained Markowitz rules differ in later
volatility, drawdown, concentration, allocation changes and operational failures?
Return and Sharpe comparisons are secondary. There is no guaranteed improvement
or preselected winner, and no synthetic result establishes an empirical answer.

The proposed source is the Kenneth French **10 Industry Portfolios [Daily]**
archive, with the ten columns fixed by [PROJECT_PLAN.md](PROJECT_PLAN.md):
NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils and Other. Primary
observations are **value-weighted stock returns within each industry**. The
baseline assigns **10% of portfolio wealth to each of those ten industries**;
this is not the source's equal-weighted-within-industry table. That separately
labelled table remains a coverage-audit panel and optional future research,
never an automatic substitute or another unregistered performance comparison.

These are SIC-assigned industry portfolios, not ten stocks, ETFs, adjusted-price
series or necessarily executable instruments. US equity industries also provide
less asset-class diversification than the original eight-ETF study. Reported
index returns do not establish replication costs, availability or implementable
trading at those returns. No SPY, T-bill series, factor returns or other dataset
is brought into scope by this proposal.

## Time separation and protection against repeated validation

| Role | Candidate period | Permitted purpose after separate authorization |
| --- | --- | --- |
| Initial estimation | 2016-01-01 through 2020-12-31 | Fit the first scheduled allocation; establish diagnostics without examining later strategy outcomes |
| Development comparison | 2021-01-01 through 2024-12-31 | One registered paired comparison of the fixed rules and sensitivities |
| Future confirmation | **Unassigned, unexamined and unauthorized** | Requires a distinct sealed registration and explicit owner instruction |

All companion development data remain bounded by **2016-01-01 through
2024-12-31**. The existing parser excludes other return tokens before numerical
conversion. A possible 2025+ companion confirmation must not be inferred from
this draft or borrowed from the ETF holdout reservation. Neither later dates
nor confirmation outcomes may be accessed to select these settings.

The candidate primary estimator uses **60 complete calendar months** of daily
development returns ending at the previous month-end information cutoff. For
the first allocation, that is January 2016–December 2020. The next month drops
January 2016 and adds January 2021; subsequent windows advance by one month.
Require at least **1,000 common valid daily observations** across all ten
industries, with no imputation or industry removal. This minimum is a proposed
data-sufficiency rule, not an outcome-based threshold or a verified sample count.

An expanding window starting in January 2016 is an alternative for owner review,
not an additional setting to run and select after seeing validation results.
The rolling candidate limits the age of observations but discards information;
expanding estimation reduces that discard while potentially adapting more
slowly to changed correlations. The synthetic investigations motivate asking
this question, not selecting a window from market evidence that is unavailable.

Predetermined monthly refits may use earlier 2021–2024 observations once those
dates precede that refit's cutoff. This is walk-forward updating under a fixed
rule, not permission to tune settings on completed validation performance.
Freeze the protocol hash, code/dependency versions, data vintage and comparison
ledger before inspecting any strategy outcomes. Preserve the first complete
comparison, every failure and all sensitivities. Later proposals must identify
already-inspected validation dates as development evidence; they cannot relabel
the same period as a fresh holdout. No empirical champion is promoted by this
draft, and no synthetic exploratory study is inserted into an empirical registry.

## Candidate strategies and estimation assumptions

All strategies use the same date grid, hypothetical execution convention and
cost scenarios. At scheduled target formation, require
`sum(weights)=1`, `0 <= weight_i <= 0.35`, no short positions and no leverage.
The **35% per-industry cap is feasible with ten industries**: the 10% baseline
is feasible and aggregate capacity is 350%. It is a proposed concentration
control, not an empirically optimal limit. It applies to targets at rebalancing;
market drift between rebalances can exceed it and must be reported.

| Rule | Candidate definition |
| --- | --- |
| Equal-industry baseline | Reset each industry target to 10% at each scheduled rebalance |
| Constrained minimum variance | Minimize `w' Sigma w` subject to the same constraints |
| Explicitly **local** maximum Sharpe | Maximize `(mu' w - rf_daily) / sqrt(w' Sigma w)` numerically under the same constraints; do not label the result a global optimum |

Use decimal daily simple returns, arithmetic sample means and the sample
covariance matrix with `ddof=1` on the same trailing window. No covariance
shrinkage, expected-return adjustment, asset screening or estimator choice is
implicitly imported from the synthetic studies. Those remain alternatives for
a separately registered comparison. A sample covariance is noisy; expected means
are especially unstable, and the local Sharpe objective can exploit that noise.

Candidate numerical implementation is deterministic SciPy SLSQP, with fixed
`maxiter=1000`, `ftol=1e-12` and feasibility tolerance `1e-8`. Minimum variance
starts at equal allocation. Local Sharpe uses eleven fixed feasible starts:
equal allocation and one start for each industry with 35% in that industry and
the remaining 65% split equally across the other nine. No randomized search or
extra starts after an unfavorable outcome. Reject nonfinite inputs/objectives,
nonpositive estimated portfolio variance, failed convergence and infeasible
weights rather than silently clipping or renormalizing a failed solution.

Among valid local candidates, choose the highest estimated Sharpe. Candidate
tie convention: objectives within absolute `1e-10` are numerical ties; choose
the solution closest in squared Euclidean distance to equal allocation, then
the lexicographically smallest weight vector in the fixed column order. Apply
the analogous tie rule to minimum variance if multiple returned solutions are
considered. These are proposed numerical conventions, not material-performance
thresholds. Exact solver/library/BLAS versions and reproducibility tolerances
must be settled in the freeze record and tested before outcomes are inspected.
The convex variance objective and the locally solved Sharpe objective must not
be described as having the same optimization guarantees.

If a scheduled fit has insufficient samples or no valid solver candidate,
execute the equal-industry target at that rebalance, charge its actual scenario
turnover cost, and retain a failure flag/reason. Do not drop the date, reuse a
future estimate, widen a window or retry different settings. Data-integrity
failures stop the whole study for reviewed correction; they are not optimizer
fallback events. Report fallback frequency prominently so an apparently stable
strategy is not mistaken for a successful optimization when it mostly used the
baseline. No failure-frequency success threshold is invented here.

## Information timing and hypothetical execution

Candidate rebalancing is monthly, based on the last **verified XNYS session**
of each month. Define that session as `d0`. Use only development observations
dated at or before `d0`. Form targets after its close, retain the existing
portfolio throughout the next XNYS session `d1`, execute the hypothetical
rebalance at `d1` close, and apply the new targets starting with the daily return
for `d2`. No return dated `d1` or `d2` enters the estimate formed at `d0`.
The implementation must test date boundaries and the one-full-session lag.

For a common start, initialize every rule to the same equal-industry allocation
at the last 2020 session close. All receive the same first 2021 session return;
the first optimized targets take effect only after the prescribed lag. Record
an identical initial acquisition-cost convention for every rule. Before the
final development date, do not simulate an execution or return that requires
post-2024 observations; do not liquidate after the boundary using a future price.

Between rebalances, weights drift with simple returns and no external flows.
For beginning-of-session weights `w`, gross daily portfolio return is the
weighted sum of that day's industry returns, and subsequent weights are
proportional to `w_i * (1 + r_i)`. Equal allocation is rebalanced monthly as well,
not silently maintained at 10% every day. Record cap exceedances due to drift.
These equations define a theoretical index-allocation experiment; there is no
claim that industry portfolios can actually be bought at the assumed closes.

A one-session lag removes same-observation arithmetic leakage but **does not
establish historical publication availability**. The current reconstructed
archive may have been unavailable or different on the simulated decision date.
The timing assumption must retain that limitation rather than certify a
point-in-time backtest.

## Risk-free and hypothetical costs

Proposed primary risk-free assumption is a **constant annual effective 2%**,
converted as `rf_daily = (1.02) ** (1/252) - 1`. A predeclared **0%** sensitivity
uses the same rule with zero. No historical risk-free dataset is implied.
This is an excess-return reference for Sharpe, not a financed cash asset in the
fully invested portfolio. The sensitivity changes local-Sharpe optimization and
Sharpe reporting; it does not change equal/minimum-variance target definitions.

Proposed primary hypothetical cost is **5 basis points per dollar bought or
sold**; fixed sensitivity scenarios are **0, 10 and 25 basis points**. These
numbers are assumptions for robustness, not fees estimated from industry-index
replication or claims about executable markets. Do not choose a preferred cost
scenario after inspecting performance.

At an execution close, use pretrade drifted weights `w_minus` and target weights
`w_target`. Define traded-notional proxy `q = sum(abs(w_target - w_minus))` and
report conventional turnover `q/2` separately. Deduct a wealth fraction `c*q`
once at that close, then set target weights; do not charge it twice or confuse
one-way dollars with half-turnover. Include initial establishment with `q=1`
and no artificial terminal liquidation. Use reference wealth 1 immediately
before initial entry: the first evaluation return includes its one-off entry
cost and first-session return, plus any scheduled rebalance cost at that close.
Thus its net growth factor is `(1-c) * (1+R_first) * (1-c*q_first)`; subsequent
daily factors are `(1+R_day) * (1-c*q_day)`, with `q_day=0` off execution dates.
This keeps the initial charge in both the net return sequence and wealth totals.
This target-weight cost model ignores
the small feedback of fees on exact trade notionals and all real implementation
frictions; it is a fully stated approximation, not a transaction simulator.
Compare all rules on the same cost convention and retain both gross and net
aggregate results if future publication is authorized.

## Evidence hierarchy and reporting plan

The following is a reporting order, not a weighted score, pass/fail threshold or
automatic winner-selection rule. Report each predeclared strategy/scenario,
including adverse outcomes and ambiguous differences, on identical dates.

1. **Later portfolio behavior:** realized net daily volatility annualized by
   `sqrt(252)` using `ddof=1`, and maximum peak-to-trough drawdown of compounded
   net wealth. Report the full 2021–2024 comparison and its calendar-year slices;
   four development years remain one observed path, not independent replications.
2. **Decision quality:** target and drift concentration (`sum(w_i**2)` and its
   reciprocal effective industry count), largest weight, binding-target-cap
   frequency, drift cap exceedances, allocation L1 changes, traded notional and
   half-turnover, estimated risk, and its relationship to later realized risk.
   A noisy subsequent month is not a definitive true-risk measurement. Track
   fallback frequency, reasons and determinism alongside allocation diagnostics.
3. **Secondary return summaries:** geometric annual growth
   `product(1+r_net) ** (252/N) - 1` over `N` common evaluation sessions, and
   `sqrt(252) * mean(r_net-rf_daily) / std(r_net-rf_daily, ddof=1)` for annualized
   Sharpe. Report undefined metrics as
   undefined with a reason; never replace zero-volatility or failed cases with
   favorable numerical values. Keep the assumed risk-free reference visible.
4. **Operational reliability:** parser/calendar status, common observation dates,
   code/data hashes, current permission status, solver feasibility/convergence,
   reproducibility and all corrections. Operational validity is necessary even
   when a performance number looks attractive.

Estimation accuracy, decision quality and forward behavior are different claims.
Unlike constructed synthetic experiments, empirical **true covariance and a
theoretical oracle allocation are unobserved**. Lower realized volatility alone
does not prove a covariance estimator was more accurate. Lower concentration or
turnover need not improve drawdown or returns; improved in-sample objectives may
fail later. No performance-significance test, resampling choice or materiality
threshold is silently added. If uncertainty intervals are desired, their method,
dependence assumptions and multiplicity treatment need review before freezing.

Any eventual public output must respect the no-raw-redistribution restriction.
Publish only reviewed aggregates/visuals within the grant; do not publish the
archive, individual industry return rows or combinations of daily paths/weights
that reconstruct the underlying panel. No empirical outputs are produced by
this documentation checkpoint.

## Vintage, permissions and unresolved interpretation

Schema/session completeness is not economic accuracy or historical availability.
Current French history can be revised, and the documented **2025 FIZ→CIZ** change
can affect reconstructed earlier observations. Archive/member hashes identify
bytes, not a historical information set. An independently entitled historical
vintage comparison would be a separate study. Retain
`point_in_time_verified=false`; no performance clearance follows from a HEAD
response, synthetic CI, this draft or a successful coverage audit.

Professor French's described grant covers limited Python collection, private
educational use/retention and publication of derived findings, with **no raw
redistribution** and possible rescission. The exact open question is whether
**transient raw licensed-archive processing on a third-party GitHub-hosted VM**
falls within that grant. Memory-only handling and read-only workflow permissions
do not answer it. The committed hosted policy remains
`pending_owner_rights_review`, `live_enabled=false`.

[GitHub Actions product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
require the hosted job to remain related to the repository's software
development/testing. A bounded ingestion-software preflight serves that purpose;
those terms do not grant rights to third-party market data or approve future
general research computation. [Hosted-runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
also places execution on GitHub/cloud-provider infrastructure, not an
owner-controlled local computer. Neither document resolves the publisher-scope
ambiguity. If the owner cannot establish coverage from the permission evidence,
publisher clarification is needed before raw hosted processing. Do not send a
new licensing message, publish correspondence or self-enable the gate.

## Owner decisions and the exact next checkpoint

The immediate next checkpoint is **only** the reviewed manual HEAD preflight:
after owner approval/installation of the separate pinned launcher, run one
owner-invoked HEAD request, record its coarse status and timestamp, then stop.
Success establishes neither GET access nor dataset rights/quality; 405 is
inconclusive. No archive or return observations are needed for that checkpoint.

In parallel, review the candidate windows, rolling-versus-expanding estimator,
minimum samples, 35% cap, local solver/tie/fallback rules, one-session timing,
constant risk-free assumption, cost scenarios and metric hierarchy above.
Resolve any publication/reconstruction and reproducibility requirements. This
document remains `DRAFT_NOT_FROZEN` until an explicit reviewed version is sealed.

Only after hosted scope is genuinely resolved and the owner separately
authorizes it may a **coverage/schema audit alone** be proposed through the
existing protected route. After that evidence is reviewed, separately freeze
the empirical protocol/code/environment **before strategy outcome inspection**
and request explicit instruction for optimization. No step automatically grants
the next. The ETF holdout, post-2024 companion values and synthetic release are
outside all currently authorized work.
