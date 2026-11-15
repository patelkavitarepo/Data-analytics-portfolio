# Protocol review 01 · synthetic accounting and timing mechanics

**Status: `DRAFT_NOT_FROZEN`.** This review responds to
[Holmes's synthetic-only accounting checkpoint](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6886452300).
It supplements, rather than freezes or replaces,
[EMPIRICAL_PROTOCOL_DRAFT.md](EMPIRICAL_PROTOCOL_DRAFT.md). Every resolution below
is a reversible prototype convention for owner review. There is no empirical
allocation, optimizer, market return, winner selection or new data-access grant.

The prototype's purpose is to establish whether declared mechanics produce the
declared arithmetic. A passing invented-data test cannot establish executable
trading, market performance, historical information availability or data rights.
The existing ETF protocol/holdout, prior synthetic evidence, published showcase,
strict French parser and hosted raw-data policy remain outside this implementation.

## Review and evidence notation

Each ID below specifies a passing control and a mutation that must fail or
produce the explicitly different result. These are synthetic acceptance cases,
not research-performance thresholds. The test crosswalk identifies the named
assertions; it is not a substitute for the current CI result or a claim of
empirical validation.

“Fail” means reject invalid input with a stable reason, or detect that a mutated
algorithm disagrees with a hand-derived expectation. It does not mean legitimate
adverse portfolio behavior should be suppressed. Retain adverse accounting
results and failure flags when the supplied synthetic inputs remain valid.

## Chronology and evaluation boundaries

| ID | Ambiguity and proposed resolution | Passing control / failing mutation |
| --- | --- | --- |
| A01 | **What is held on d1?** Estimate instructions use observations through month-end `d0` only. Existing weights receive the whole next session `d1` return; instructions execute after that return at d1 close. New weights first receive `d2`. | Distinct invented d1/d2 returns distinguish the allocations. Same-day execution, trading before d1's return or applying targets only on d3 must disagree. |
| A02 | **Who establishes month-end?** `d0` is the last verified session of a complete calendar month, not the last row currently supplied. No weekday inference or lookahead to an unavailable return is permitted. | A reference grid containing the rest of a partial month prevents its earlier last observed row being treated as d0. An arbitrary middle-of-month instruction is rejected. |
| A03 | **First 2021 session.** All rules start with equal-industry allocation at the last 2020 session close. Initial entry cost is charged once, before the first evaluation return. The first d0 instruction cannot change exposure during the first 2021 session. | Identical initial weights/entry charges give identical first-session gross exposure. An optimized first-session allocation or extra artificial entry date fails the chronology check. |
| A04 | **Partial evaluation months.** Use the supplied independently verified calendar to identify valid d0/d1/d2, not a truncated evaluation slice. A short test may start/end mid-month but must not manufacture a rebalance. | A partial-month path without a valid scheduled execution drifts without a trade. Reclassifying its final row as month-end changes the result and must be detected. |
| A05 | **Last boundary and pointless terminal trades.** Candidate resolution: execute an instruction only if d1 and the first eligible new-weight return at d2 are both inside the evaluation interval. Do not pay a terminal rebalance solely for an exposure that never earns an evaluation return. This is an edge-case choice requiring owner review. | An instruction near the final boundary is explicitly marked unexecuted; there is no synthetic 2025 row, terminal liquidation, hidden extension or unexplained final-close fee. |
| A06 | **No same-day information use.** Supplied instructions must identify their information cutoff and execution session. Require every scheduled monthly instruction whose d1 and d2 are in range; never silently move an invalid instruction or carry over weights because a required instruction was omitted. | Correct d0→d1 instruction passes; same-day, reverse-dated, off-grid, duplicate or missing required execution instructions fail. |

The one-full-session lag is an arithmetic rule only. It does not prove that a
current reconstructed French observation existed or was published by d0/d1.
Likewise, a caller's declared instruction timestamp cannot prove that its target
was actually chosen without later information. The prototype consumes fixed
instructions and checks chronology; any future estimator must separately test
its information set, record precommitted inputs/code and prevent future-value
dependence. Altering a later invented return must not alter an earlier ledger
prefix when instructions remain fixed.

## Weight drift and target constraints

| ID | Ambiguity and proposed resolution | Passing control / failing mutation |
| --- | --- | --- |
| A07 | **Equal allocation is monthly.** The baseline resets targets to 10% per industry only at scheduled executions. Between them, asset growth changes weights. | One industry's invented positive return changes its next-session weight. A daily reset to 10% must give a detectably different second-session return. |
| A08 | **Drift equations and budget.** For pre-return weights `w`, asset growth terms are `w_i*(1+r_i)`; their sum is the portfolio gross factor. Normalize these terms once to obtain pretrade drifted weights. | Zero returns preserve weights; deterministic random cases preserve a unit budget and the wealth/return identity. Stale weights or a wrong normalization denominator fail. |
| A09 | **35% target cap versus drift.** Apply the proposed cap to accepted targets, not to every later weight. Report drift exceedances without clipping or an unscheduled trade. | A feasible target can drift above 35%; it remains held until the next valid execution. A supplied one-industry target is rejected, while valid one-industry drift is a distinct diagnostic case. |
| A10 | **Floating budget versus correction.** The prototype requires `math.fsum(target)==1` and strict target bounds; it does not repair targets. Only normalized **drift** may receive a recorded largest-component roundoff residual bounded by `1e-14`. The drift-cap diagnostic uses `0.35+1e-12` to avoid flagging a floating artifact; it does not relax target acceptance. | Feasible equal/fixed targets conserve wealth; wrong length, nonfinite, negative, over-cap or non-unit-budget inputs fail. A residual outside the small drift bound fails rather than becoming a projection. |

For a hand-checkable control, start at ten equal weights and give only the first
industry an invented 100% session return. Gross portfolio growth is `1.1`, its
drifted weight is `2/11`, and each other weight is `1/11`. These are invented
arithmetic expectations, not observed French returns.

Strict exact-sum target acceptance is intentionally narrower than the draft's
future solver feasibility tolerance of `1e-8`. How a future solver's output
would satisfy this accounting interface remains an **unresolved adapter/freeze
decision**, not permission to silently renormalize a failed solution. These
floating conventions are prototype choices, not changes to any frozen study.
The bounded drift correction may use up to eight `nextafter` steps on the
largest component, with lowest index breaking a size tie, until the accurately
summed unit budget is representable. Its recorded net adjustment must remain
within `1e-14`; failure to meet either condition stops the prototype.

## Cost units, trade timing and wealth

| ID | Ambiguity and proposed resolution | Passing control / failing mutation |
| --- | --- | --- |
| A11 | **Cost input units.** The API accepts decimal cost fractions. Under the draft, five basis points means `c=0.0005`, not `5` or `0.05`. Reject nonfinite/negative charges, `c>=1` and nonpositive resulting wealth factors; do not clip them. A valid fraction such as 0.05 means 5%, not five basis points; software cannot infer a caller's intended units. | Zero and stated nonzero fractions pass; invalid domains fail with a reason. A 0.05-for-0.0005 mutation fails the hand-derived fee expectation, even though 0.05 itself is a legal hypothetical fraction. |
| A12 | **Entry q=1 is separate.** Initial establishment buys one dollar of assets per reference dollar, so entry traded-notional proxy is 1. Charge its fee once, before first-session returns. | A flat invented path starts below reference wealth by its entry fee. Repeating entry fees each day or omitting the first fee fails. |
| A13 | **Later q uses d1 drift.** At execution close compute `q=sum(abs(target-pretrade_drift))`, after d1's return. This is different from the change in target weights or the difference from yesterday's weights. | Retargeting the hand example above to equal allocation gives `q=9/55` and half-turnover `9/110`. Using initial equal weights incorrectly gives zero and fails. |
| A14 | **Half-turnover is not the fee base.** Report `q/2` separately; under this convention the fee base is dollars bought plus sold, q. State whether entry's `q/2=0.5` is included in a total or reported separately. Do not present cash-entry half-turnover as a routine fully invested rebalance. | A known q produces fee fraction `c*q`. Charging `c*q/2`, charging buys and sells twice, or changing the convention by rule fails. |
| A15 | **Fee fraction versus fee dollars.** The close fee in wealth units is `c*q` times wealth after the session's gross return, after any entry charge. A reported monetary cost must use that base. | Nonzero returns distinguish a correct close fee from a fee incorrectly based on prior-close wealth. Sum of actual paid fees is not mislabeled as final gross-minus-net wealth drag. |
| A16 | **Daily net factors include the entry charge.** First factor is `(1-c)*(1+R_first)*(1-c*q_first)`. Later factors are `(1+R_day)*(1-c*q_day)`. With no execution, q and the close fee are zero. | Compounding reported net returns reproduces net wealth. Omitting entry from first net return, applying cost before the wrong return, subtracting rather than multiplying fractions, or double charging fails. |
| A17 | **Comparable costs.** Every supplied rule uses the same entry, close, lag and fee units. A baseline rebalance back to 10% is a real hypothetical trade when it differs from drift. There is no exemption merely because the baseline target did not change. Common conventions do not require equal fee dollars when trades or wealth differ. | Identical q and wealth imply equal fees; different actual q correctly changes fees. An exempt baseline or a fee on a no-trade day fails. |
| A18 | **No terminal liquidation.** Final wealth is the held portfolio value at the last permitted close, without a fictional liquidation fee or a post-boundary price. | Extending only the reporting horizon does not manufacture a trade. A terminal cash target or post-2024 observation is rejected rather than silently used. |

This is the draft's target-weight transaction-cost **approximation**. Exact
self-financing trade quantities after costs, cash funding, bid/ask spreads,
slippage, index replication and actual executable prices are not established.
Owner review must decide whether this approximation is sufficient before freezing;
no alternate transaction simulator is fitted to results in this checkpoint.

## Metric estimands and numerical edge cases

| ID | Ambiguity and proposed resolution | Passing control / failing mutation |
| --- | --- | --- |
| A19 | **Maximum drawdown includes reference wealth 1.** Start the high-water mark before entry, rather than at the first already-reduced observed wealth. | A flat path with a nonzero entry fee has drawdown equal to that fee fraction. Starting the peak at first net wealth incorrectly hides it. |
| A20 | **Daily realized volatility.** Use the sample standard deviation of the reported net daily return sequence with `ddof=1`, annualized by `sqrt(252)`. The one-off entry charge therefore belongs in the first return. | A two-return hand calculation distinguishes sample from population variance and exposes omission of the entry charge. With fewer than two observations the metric is undefined, not zero. |
| A21 | **Sharpe reference and undefined cases.** Convert the constant annual-effective 2% by `(1.02)**(1/252)-1`; retain the separately declared 0% sensitivity. Annualized Sharpe is `sqrt(252)*mean(net-rf_daily)/std(net-rf_daily,ddof=1)`. | Constant return/zero variance and insufficient observations produce an explicit undefined result and reason. No historical factor data, division-by-zero finite replacement or infinite “winner” is invented. |
| A22 | **CAGR versus arithmetic return.** Candidate growth uses `product(1+r_net)**(252/N)-1` on the common N-session evaluation. Label it hypothetical and preserve undefined/overflow handling. | Net wealth and net returns give the same growth estimate. Mean daily return times 252 must not be mislabeled geometric growth. |
| A23 | **Simple-return boundaries.** A constituent return of exactly -100% can leave a valid positive portfolio; below -100% is impossible. If total gross portfolio value reaches zero, continued normalized weights are undefined. The prototype fails closed on total wipeout, arithmetic overflow/underflow or cost exhaustion rather than manufacturing a surviving allocation. | One extinguished constituent with other positive holdings passes; an all-held-assets wipeout, return below -1, nonfinite value, numerical exhaustion or impossible fee factor fails explicitly. |
| A24 | **Concentration and reporting.** HHI is `sum(w_i**2)` and effective industry count is its reciprocal. Specify target versus drifted/beginning/end-session weights and the sampling denominator for frequencies. | Equal weights imply HHI 0.1/effective count 10; valid single-industry drift implies 1/1. Reports must not mix target and drift estimands or hide cap exceedances. |

All averages and frequencies need an explicit eligible-date denominator. Entry
events, scheduled rebalances, daily holdings and fallback events are different
populations. Reported aggregate costs and changes must identify which they count.
The prototype's drift concentration/max-weight summaries sample each day's
**pretrade** drifted holdings. Target summaries sample initial equal allocation
plus executed targets only. `fallback_count` counts executed failure instructions;
skipped failures have a separate count. Rebalance q and half-turnover totals
exclude initial entry, whose q=1 and half-turnover=0.5 are separately labelled.

A total wipeout is an accounting-state boundary, not evidence that every
constituent input was invalid. The prototype's fail-closed response must remain
visible as a failure, not a dropped adverse date. A future study would need an
explicit terminal-bankruptcy policy if it should instead retain zero wealth and
100% drawdown without continued weights. A log-wealth implementation could also
extend numerical range, but neither extension is silently introduced here.

## Coverage, estimation windows and instruction failures

| ID | Ambiguity and proposed resolution | Passing control / failing mutation |
| --- | --- | --- |
| A25 | **Reference calendar and data coverage.** `CalendarGrid` receives caller-supplied sessions, coverage bounds and provenance. Pure accounting checks observations against that grid but cannot authenticate it as XNYS. Tests use dates from the independently pinned existing XNYS calendar; this is calendar metadata, not a market-return download. | Against that reference, a missing expected session, duplicate, unsorted/off-grid date or holiday inserted as a weekday fails. No fill, row drop or Mon–Fri replacement is permitted. A dishonest calendar-provenance label is not technically detected. |
| A26 | **60 complete calendar months.** For a d0 in December 2020, the candidate window starts January 1, 2016; advance it by calendar months, not 1,260 rows or `60*21` sessions. Completeness must be established using the reference calendar and its certified boundary coverage. | A hand-built calendar with variable month lengths retains the correct bounds. Row-count approximations and truncation to an incomplete boundary month fail. |
| A27 | **1,000 common observations.** A separate dates-only window selector checks the complete 60-month bounds and minimum count. Insufficient history receives an explicit status; internal missing sessions stop rather than widen/fill. Tiny accounting fixtures need not pretend to supply five years of estimation history. | Exactly 1,000 passes the count check; 999 does not. Insufficient history is a separate reason. Missing sessions and an extended window fail; actual common-cell validity is not established by a dates-only selector. |
| A28 | **Scope and order before value access.** Require strict ten-industry order and development dates only. Reject out-of-scope dates before converting their return tokens; no automatic 2025+ extension. | Reordered/duplicate industries and a post-2024 synthetic poison object fail before any value conversion. Correctly ordered invented rows pass. |
| A29 | **Failure target versus invalid data.** A predeclared failed solver instruction uses the equal-industry target at the same scheduled execution, charging actual turnover and recording the failure. Invalid dates/returns/calendars stop the run; they are not solver failures. | A failed target visibly executes baseline with fee/flag; suppressing the date, changing settings, reusing future targets or silently repairing data fails. |

The accounting prototype consumes predeclared target instructions. It must not
estimate sample means/covariances, solve Markowitz problems or select a strategy.
Window checks can validate mechanics on invented observations; they do not
certify real French coverage or historical publication availability.

## Optimizer conventions requiring paper review

The future candidate **minimum-variance objective is convex** under the declared
linear constraints; a numerical SLSQP success flag still needs feasibility and
objective checks. The separately proposed **local maximum-Sharpe** calculation
must never be relabeled a global optimum or assigned the same guarantee.

The draft proposes fixed `maxiter=1000`, `ftol=1e-12`, feasibility tolerance
`1e-8`, and eleven predetermined local-Sharpe starts: equal allocation plus
one 35% allocation to each industry with 65% divided among the other nine.
These are paper candidates, not implemented optimizations or settings selected
from observed returns. Keep exact dependency/solver/BLAS versions and accounting
tolerances separate in the eventual freeze record.

**A30 — ties:** first find the best valid objective across all returned candidates.
Define the tie set relative to that best value using the proposed absolute
`1e-10` tolerance, rather than chaining pairwise “close” comparisons. Within that
set choose minimum squared distance to equal allocation, then lexicographically
smallest weights in the fixed industry order. A hand-supplied tie with reversed
candidate order must select the same target; a chained near-tie mutation must
not change the winner. This specification chooses among submitted candidates,
not among strategies or empirical winners.

**A31 — failed candidates:** reject nonfinite objectives/weights, nonpositive
estimated portfolio variance, failed convergence and infeasible weights. Do not
repair a failed solution by clipping/normalization, retry new starts after an
unfavorable result or relabel a fallback as an optimized solution. A synthetic
failed instruction must retain its scheduled baseline target, cost and reason.
The accounting layer may validate a failure marker; no solver is run here.

**A32 — zero-turnover and invalid-target differences:** a successful equal target
equal to current drift produces q=0; a declared failed target can also have q=0
but must still count as a failure. A malformed supposedly successful target is
an input error, not an implicit solver-failure permission. Tests must distinguish
all three outcomes instead of inferring success from low turnover.

## Rights, vintage and publication boundaries

**A33 — provenance is not established by a numeric label.** Inputs must be loudly
identified as invented fixtures; that assertion cannot technically prove their
origin or grant rights. There is no connection from the French parser, a file,
an HTTP client, a live workflow or a public plotting/export feature to this
prototype. Private-to-test paths/weights are not a new publication interface.

No repeat HEAD, GET, email or raw-data request belongs to this checkpoint.
`github_actions_scope.json` stays `pending_owner_rights_review` with
`live_enabled=false`. The empirical protocol remains `DRAFT_NOT_FROZEN` and
`performance_cleared=false`. Neither green tests nor the prior HEAD result
answers whether the publisher grant covers transient raw processing on a
third-party GitHub-hosted VM.

Theoretical industry-index allocations are not tradeable ETF returns. Current
French reconstructed history, revisions and the 2025 FIZ→CIZ processing change
do not establish historical point-in-time availability. No real path, underlying
return row or reconstructible combination is exposed. All prior research,
data-permission safeguards, ETF holdout and published synthetic release remain
unchanged.

## Test crosswalk and next decision

The implementation is [synthetic_accounting.py](industry_companion/synthetic_accounting.py).
The crosswalk uses **A** for [test_synthetic_accounting.py](tests/test_synthetic_accounting.py)
and **C** for [test_synthetic_calendar.py](tests/test_synthetic_calendar.py).
Each named test contains a valid control, an expected rejection or an explicit
hand-derived comparison. Check the current PR #12 CI/checkpoint for execution
counts and failures; no run count or empirical outcome is invented here.

| Review IDs | Named synthetic assertions |
| --- | --- |
| A01, A03 | A: `test_first_2021_session_holds_old_weights_and_d2_earns_target`; C: `test_first_2021_and_final_2024_boundaries` |
| A02, A04 | A: `test_partial_observed_month_does_not_become_month_end`; C: `test_month_end_and_lag_use_xnys_not_weekdays`, `test_partial_observed_month_is_not_inferred_month_end` |
| A05, A18 | A: `test_final_d1_without_in_range_d2_has_no_terminal_trade`, `test_final_2024_instruction_never_needs_2025` |
| A06 | A: `test_adversarial_same_day_and_off_by_one_instructions_fail`, `test_monthly_instruction_cannot_be_missing_or_duplicate`, `test_future_returns_and_later_targets_cannot_change_earlier_ledger` |
| A07, A08 | A: `test_drift_is_not_daily_equal_reset`, `test_deterministic_invariants_budget_wealth_and_cash_reconciliation` |
| A09, A10 | A: `test_drift_cap_can_exceed_target_cap_without_forced_trading`, `test_invalid_targets_are_rejected_not_repaired_or_fallback`; invariant test checks budgets and bounded roundoff |
| A11, A12 | A: `test_cost_rate_validation`, `test_entry_cost_first_net_return_and_drawdown_reference` |
| A13–A16 | A: `test_hand_calculated_monthly_q_and_close_cost`, `test_cash_fees_are_not_terminal_wealth_gap`; invariant test checks multiplicative and monetary reconciliation |
| A17 | A: `test_same_entry_convention_for_equal_and_illustrative_targets`; monthly q/cost control also checks baseline costs and a no-trade day |
| A19–A22 | A: `test_entry_cost_first_net_return_and_drawdown_reference`, `test_metrics_use_sample_sd_constant_effective_rf_and_net_path`, `test_undefined_metrics_are_none_with_reason` |
| A23 | A: `test_industry_total_loss_is_valid_if_portfolio_survives`, `test_invalid_or_extinct_return_state_fails_without_echo`, `test_near_total_loss_remains_valid_without_rounding_to_zero`, `test_nonfinite_wealth_fails_closed`, `test_exhausted_close_cost_fails_closed` |
| A24 | A: `test_drift_cap_can_exceed_target_cap_without_forced_trading`, `test_concentration_and_effective_industry_counts_have_hand_oracles` |
| A25–A27 | C: `test_missing_duplicate_nonmonotone_or_weekend_panel_dates_fail`, `test_sixty_complete_calendar_months_and_advancing_window`, `test_history_insufficiency_is_distinct_from_missing_internal_session`, `test_calendar_requires_explicit_scope_identity_and_provenance` |
| A27, A29 | C: `test_insufficient_history_reason_can_feed_a_flagged_target` preserves the window selector's explicit history-insufficiency reason through a scheduled baseline fallback. |
| A28 | A: `test_post_2024_dates_fail_before_return_access`, `test_industry_order_is_fixed`; C: `test_scope_rejection_precedes_any_return_access` |
| A29 | A: `test_failed_instruction_falls_back_with_cost_and_flag` |
| A30, A31 | A: `test_predeclared_candidate_tie_break_is_global_not_chained`, `test_tie_prefers_equal_distance_then_lexicographic_order`, `test_manual_candidate_minimum_and_maximum_objectives_are_distinct`, `test_no_valid_manual_candidate_flags_equal_fallback` |
| A32 | A: `test_zero_turnover_fallback_stays_flagged_despite_equal_wealth`; invalid-target and failed-instruction cases distinguish rejection from fallback |
| A33 | A: `test_synthetic_attestation_required`, `test_engine_has_no_io_output_or_input_mutation`, `test_fixed_industry_order_and_synthetic_summary_labels` |

Future-return prefix causality, exact concentration summaries and a zero-turnover
failure flag were explicitly identified during review and received their own
named assertions, rather than being inferred from adjacent passing cases.

## Numerical defects discovered during synthetic implementation

Four numerical issues were identified and given regression controls:

1. Unnecessary drift-budget adjustment changed an already unit-sum equal vector
   and manufactured q of approximately `2.8e-17` in a zero-return rebalance. That
   is an accounting artifact, not observed economic turnover. The correction
   preserves an already unit-sum ratio vector unchanged; it does **not** round
   every small legitimate trade to zero. Exact zero-turnover assertions in the
   equal-entry and zero-turnover-fallback cases protect this distinction.
2. A complement-only residual correction could still fail the strict full-sum
   budget check in a predetermined seed-7 invariant case, because the rounded
   sum of the other components was itself inexact. The bounded, recorded
   `nextafter` adjustment described above resolves representability without
   repairing a supplied target. The deterministic invariant cases check the
   budget, adjustment bound, compounded net wealth and cash reconciliation.
3. Even with an exact budget, dividing individual asset growth by their sum
   could manufacture tiny allocation changes when all industries had exactly
   the same return. Exact common-return rows now retain the input allocation
   and its common growth factor. This is an algebraic identity, not a threshold
   that suppresses small genuine trades. Six equal/asymmetric-weight controls
   are in [test_accounting_numerical.py](tests/test_accounting_numerical.py).
4. Finite daily states do not guarantee a representable cumulative fee total.
   An engineered high-scale fixture exceeded binary64 aggregate capacity;
   the summary now raises `NONFINITE_AGGREGATE_METRIC`, rather than an untyped
   overflow or invented finite/zero fee result. The same numerical test file
   checks this path using generated invented returns and valid daily states.

These are software-mechanics findings from invented fixtures, not evidence for
an allocation rule, covariance model or market-performance conclusion. They also
leave a genuine methodological question: whether exact-binary target acceptance
and this bounded drift policy are the desired future accounting interface.

The calendar selector establishes dates/counts only. It does not certify a
caller-provided calendar against an independent exchange source or validate
1,000 common historical return rows. The ten-column accounting input validator
is separate; a future estimator/data pipeline must combine these controls before
any fit. Likewise the single-path API reports its cost/risk-free assumptions but
does not implement a multi-strategy comparison harness that enforces identical
costs and evaluation dates across independently invoked runs.

The next owner decision is whether the prototype's explicit boundary, cost,
numerical and reporting conventions match the intended future hypothetical
study. Resolve alternatives before a separate freeze. Raw hosted permission,
real coverage/vintage evidence, any optimization implementation and any future
confirmation registration remain separate later decisions. No launcher change,
merge or deployment is needed for this synthetic-only review.
