# Owner decision record 03 · accounting conventions

**Status: `AWAITING_OWNER_APPROVAL`.**

| Record field | Current value |
| --- | --- |
| Authority requested | Research owner approval of explicitly named accounting conventions and integration conditions |
| Owner approval | **NOT RECORDED** for any recommendation below |
| Empirical protocol | `DRAFT_NOT_FROZEN`; unchanged |
| Empirical validation | **None**; all accounting evidence uses invented fixtures |
| Hosted raw-data scope | `pending_owner_rights_review`, `live_enabled=false`; unchanged |

This record responds to [Holmes's Review 03](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6897736229).
Holmes's recommendation is scientific advice, **not owner approval**, an
implementation instruction or a protocol freeze. A green CI run has none of
those meanings either. This documentation checkpoint changes no accounting
engine, reference function, policy, workflow or empirical protocol.

## Four separate statuses

| Convention | Recommended | Owner-approved | Implemented now | Empirically validated |
| --- | --- | --- | --- | --- |
| Fees | Exact self-financing as candidate primary; named proxy sensitivity | No | Exact mathematical reference only; default ledger still uses the proxy | No |
| Endpoint | Bounded-study skip when no in-range d2 exists | No | Tested prototype behavior; not an approved research convention | No |
| Solver output | Strict reject/fallback; do not adopt canonicalization B | No | Strict budget/target checks and fallback mechanics; no integrated solver/numeric-serialization wrapper | No |
| Genuine ruin | Absorbing zero-wealth event with explicit missing post-ruin ratios | No | Isolated fixed-holding reference; default ledger still fails closed on depletion | No |

“Implemented” refers to the specific component named, not a completed integrated
research engine. “Synthetic tests passed” never means empirically validated.

## D1 · Fee definition and role of the proxy

**Recommendation:** interpret `c` as cost per actual dollar bought **or** sold,
with fully invested post-cost target weights. For pre-trade weights `p`, targets
`t` and remaining wealth ratio `x`, the candidate primary equation is:

```text
x + c * sum(abs(x*t_i - p_i)) = 1,     0 < x <= 1, 0 <= c < 1.
cash entry: x = 1/(1+c).
```

Retain `c*q`, where `q=sum(abs(t-p))`, as a separately named
**turnover-penalty proxy** for a prospectively declared sensitivity/comparison.
It is not uniformly conservative. If the owner intends a purely abstract
target-weight penalty, that proxy is a legitimate alternative primary definition;
select and label its role before outcomes, not according to which looks better.

Existing evidence: in the same invented three-session fixture, the exact-model
closed-form oracle gives approximately `1.099360355807701907`, versus proxy
`1.099360045`. Another fully cap-feasible fixture gives exact retained ratio
`19993/19994`, approximately `0.999949984995498650`, below proxy `0.99995`.
These opposite signs preclude a universal conservative-proxy claim. The rational
reference certifies a root bracket or fails; it does not prove ledger integration.

If approved, the later versioned specification would lock the economic fee
basis, cash-entry rule, primary/sensitivity roles, d1-close placement and the
same conventions across comparators. Cost values/sensitivities in the empirical
draft are **not approved by this record**. Numerical representation, precision,
failure propagation and composition still need the integration gate below.
These remain abstract costs for hypothetical non-tradeable industry allocations,
not calibrated executable trading charges.

## D2 · Common end-of-horizon convention

**Recommendation:** skip a d1-close target when no in-range d2 return exists.
Preserve the predeclared target/failure record; charge no terminal rebalancing or
liquidation. If d2 is within the common comparison grid, execute and charge
normally after d1's return. Apply identically to every candidate strategy.

The alternative is a continuing-strategy horizon that pays for its scheduled
final-close trade despite having no later measured exposure. That is a different
question, not necessarily incorrect accounting. In an invented endpoint example,
wealth `1.0001` with `q=0.5` becomes `0.999849975` after a 5 bp close fee; a
zero-turnover portfolio at 1 does not change. Endpoint policy alone reverses
their ordering. Do not choose the rule from outcome rankings.

If approved, lock the common date-grid/eligibility rule, fee-call ordering and
skipped-instruction/failure accounting. The decision status is
`SKIPPED_NO_IN_RANGE_EFFECTIVE_SESSION`; the current stored prototype reason
`NO_IN_RANGE_EFFECTIVE_SESSION` is not renamed here. A skipped failure must not
be counted as an executed fallback. No extension, future return or synthetic
liquidation is permitted to manufacture d2.

## D3 · Strict solver admission and fallback

**Recommendation:** reject/fallback when solver output fails the accounting
budget or hard target bounds. Do **not** adopt fixed-index canonicalization B.
Record original feasibility residuals, admission/rejection reasons and fallback
counts. A declared solver-success flag is not proof of convergence, valid risk
or acceptable accounting input.

The proposed SLSQP `1e-8` numerical feasibility tolerance and the current exact
binary `math.fsum(weights)==1.0` budget are **not reconciled**. They are different
tests, not interchangeable tolerances. The target constraint remains long-only,
fully invested and at most 35% per industry. The 35% bound applies to target
`t`, **not drifted pre-trade `p`**, which can legitimately exceed it.

Alternatives are explicit strict rejection A, an owner-approved future
support-preserving interface, or redefining the numeric contract prospectively.
No clipping, normalization or hidden switch to B is authorized. The synthetic
evidence shows a correction smaller than `1e-8` can create/remove a tiny holding
and reverse an exact-loss classification. A small norm does not establish
equivalent support, objective or economic behavior. Strict rejection can also
increase baseline fallback frequency; it is not economically neutral.

If approved, lock hard bounds, distinct solver/accounting/serialization checks,
residual definitions, reason taxonomy, deterministic unchanged admission and
same-date equal-industry fallback with applicable fees. An accepted target must
not be changed without a separately approved policy. Record fallback frequency
and reasons even when fallback wealth happens to equal the baseline. Do not
label universal numerical fallback an optimized strategy.

## D4 · Genuine ruin and reporting

**Recommendation:** an exact verified -100% loss of **all positive holdings**
becomes an absorbing zero-wealth event: terminal wealth 0, cumulative terminal
return -100%, reference-peak full-horizon drawdown 100%, and an explicit ruin
date. Retain the common evaluation grid. Subsequent ruined dates have no active
weights, trade, restart or fabricated daily return.

The current strict stop is the unchanged implemented default; the absorbing
alternative is only a narrow fixed-holding/drift reference. Numerical
underflow/overflow, precision loss, invalid inputs and cost exhaustion must
remain distinct failure statuses. Near-total positive wealth can produce
rounded return -1/drawdown 1 without genuine ruin; only the verified event and
wealth state establish the classification.

Full-horizon daily volatility/Sharpe are undefined where post-ruin `0/0` ratios
do not exist. Never fill those dates with zero returns or compare an unlabelled
prefix Sharpe with full-horizon survivors. Final-date ruin can leave a complete
calculable return sequence; the existing reference omits such ratios by policy,
not mathematical necessity. Whether to report them needs explicit selection.
Decide separately whether/how to label -100% **terminal-value geometric growth**;
it does not require inventing daily post-ruin ratios.

If approved, lock event verification, absorbing lifecycle, same-horizon wealth
comparison, failure-code separation, data-quality precedence and metric labels.
Invalid later input currently stops the reference rather than being concealed
by an earlier ruin. Whether a production report should additionally retain an
independently validated prefix event needs design; it is not silently resolved.

## Blocking numeric interface: both p and t, at every rebalance

The binary ledger and exact-fee reference do not currently share an authoritative
numeric-state contract. Binary `math.fsum==1` does not imply that the fee
reference's `Fraction(str(float))` weights sum exactly to one. The existing
`(.35, .65/9, ..., .65/9)` mismatch is a regression, not a transport solution.
Using `Fraction.from_float` alone also need not yield a unit rational sum.

This affects **drift-produced p as well as solver-produced t**. The earlier
paired fee example supplies analytical rational pre-trade weights; multiplying
its scalar ratios does not prove the actual binary drift tuple can pass into
the next exact-fee call. Repeated composition remains unverified.

Before an implementation change, specify the authoritative holdings/weight
representation, serialization in both directions, admission/failure statuses,
and how root/bracket error and any approved rounding propagate through wealth.
Changing a numeric representation is not permission to alter portfolio weights.
No implicit normalization, residual cash allocation, rounding-to-feasibility or
support-changing repair is approved. If strict admission makes representative
nontrivial fixtures universally fall back, stop for prospective owner review
and interface redesign **before freeze**, not after market outcome inspection.

## Minimum additional synthetic integration controls

These are **five planned contracts, not new experiments, not a test-count target,
and not implemented or run in this documentation task**. Reuse the existing
hand fixtures and component regressions; use no historical returns, optimizer,
random search, new scenario sweep or market-derived threshold. Predetermine
expected admission classes once the numeric contract is selected.

| ID | Fixed scope | Measurable acceptance condition |
| --- | --- | --- |
| I1 Admission and serialization | One small table: equal, dyadic, cap-boundary, known nonbinary mismatch, actual drift output, `±2^-28` residual, failed flag and invalid-bound cases | Independently record solver feasibility, exact accounting budget and fee-serialization admission for **both p and t**. Accept unchanged or reject with the expected reason; no B/correction. Genuine drift cap exceedance is not target infeasibility. Valid interior/boundary controls must reach the intended path; universal fallback is a stop, not success. |
| I2 Ledger composition | One predetermined tiny rational path, exact entry and **two scheduled rebalances**, at zero and the existing 5 bp toy cost | Independent holdings/trade-dollar oracles verify self-financing, fee dollars, compounded wealth and entry cost in the first net return. Use actual output p from the preceding state, not a separately substituted analytical tuple. Accepted targets remain unchanged; every transition retains the selected budgets. |
| I3 Strict rejection to fallback | Reuse one near-feasible solver-shaped rejection and an admitted control on the same schedule | The rejection executes equal-industry fallback on the same d1, charges the selected fees and records original residual, reason and count. Zero turnover does not erase failure status. The admitted control is not mislabelled fallback; identical baseline wealth does not certify solver success. |
| I4 Certified precision/failure propagation | Reuse an existing nontrivial certified fee root and its forced precision-limit failure | Bound composed wealth against independent exact oracles using the root interval plus the **prospectively specified** serialization/arithmetic error bound. Distinguish that bound from `1e-8` solver tolerance. Uncertified roots or unapproved conversions stop cleanly; no zero-fee substitution, hidden normalization or fabricated valid ledger. |
| I5 Endpoint fee admission | Existing no-d2/d2-present pair, including a skipped failed instruction | The skipped rebalance must not call the rebalance-fee routine, trade or charge a close fee; keep target/failure metadata. Common initial-entry cost still applies if this is the first evaluation session. With in-range d2, execute once after d1's return with the correct close fee and new exposure timing. Reuse existing boundary tests instead of a fresh horizon campaign. |

Component coverage already exists for root uniqueness/brackets, fee signs,
input boundaries, canonicalizer support risks and genuine-versus-numerical ruin.
Do not duplicate those campaigns. The new need is the **joint admission/state
contract**, residual/fallback trace and error propagation. Passing these controls
would validate a chosen synthetic implementation only, not an eventual real
solver, historical point-in-time data or market performance.

A rejected solver **target** may invoke the declared same-date fallback. An
unserializable pre-trade **state**, or an uncertified fee root, instead stops the
integration: switching to a fallback target cannot establish what the held
portfolio or its transaction costs were. Do not hide these failures in solver
fallback counts.

No new numerical acceptance threshold is invented by this record. Existing
reference precision constants are evidence about that reference, not automatic
production tolerances. Owner-approved representation/error assumptions must
precede an integration certificate. A proposal unable to state them is blocked.

## Evidence and approval boundary

This task adds documentation only: no new test cases, reference behavior or
experimental results. Rerunning the existing regression suite checks the change;
it does not execute I1–I5 or close the numeric-interface blocker.

Evidence baseline: [Review 02](PROTOCOL_REVIEW_02.md), code
`c4186c63b087cc71b85321b5e8e9e66db298b668`, and
[CI run 43716462607](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43716462607):
**508 existing synthetic tests**, guards passed, no artifacts. Key controls are
in [fee tests](tests/test_synthetic_fee_reference.py),
[budget tests](tests/test_synthetic_budget_reference.py),
[ruin tests](tests/test_synthetic_ruin_reference.py),
[endpoint tests](tests/test_boundary_conventions.py) and
[interaction tests](tests/test_reference_interactions.py). Their scope and
limitations remain as recorded; no new findings are asserted here.

The owner may approve, amend or reject each recommendation. A later approval
record must identify the owner, this record's exact version/commit, choices,
conditions and outstanding blockers. None is prefilled or inferred. Accounting
convention approval alone does not adopt code, complete the numeric integration,
freeze the whole empirical protocol or authorize an empirical run. Any later
implementation and versioned freeze require explicit instruction and review.

## Independent source/permission gates and next checkpoint

Raw French processing stays disabled. HEAD `REACHABLE_HEAD_2XX` establishes
neither GET success/permission nor authority for a third-party GitHub-hosted VM
to handle raw bytes. No new HEAD/GET, original correspondence, historical returns,
2025+ observation inspection or licensing email is part of this checkpoint.
Publisher clarification is permitted **only on explicit owner instruction**;
an authorized owner-controlled non-GitHub raw-data route remains an alternative.
Never infer rights from mathematical approval or CI.

Before any eventual empirical work, independently resolve permitted processing
and retention, genuine source/schema/coverage/vintage evidence, point-in-time
limitations and a separately approved frozen protocol/code/environment. Preserve
no-raw-redistribution safeguards. No benchmark/ETF/factor rights are added.

**Next checkpoint:** owner review of D1–D4 and the numeric-contract blocker. Then,
only if separately instructed, implement the minimum I1–I5 integration controls
in isolation under the chosen contract. If admission/composition cannot be
certified, return a blocker and prospective redesign proposal; do not loosen
checks or start exploratory research. PR #12 stays draft, the original ETF study
and holdout and the published synthetic showcase remain untouched, and no PR
merge, launcher change, deployment or release is authorized.
