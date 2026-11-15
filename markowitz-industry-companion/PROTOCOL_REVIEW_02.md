# Protocol review 02 · four accounting decisions

**Decision status: `OWNER_REVIEW_PENDING`. Protocol: `DRAFT_NOT_FROZEN`.**

Responds to [Holmes's review 02](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6886993363).
All inputs and numerical results here are **invented mathematical fixtures**.
They establish no market performance, source accuracy, executable index costs or
data-use rights. The [existing prototype](industry_companion/synthetic_accounting.py),
empirical protocol, parser, raw policy and workflows are unchanged. None of the
alternatives below is adopted by this review.

## Recommendations and owner decisions

| Decision | Recommendation for review | Still requires owner selection/freeze |
| --- | --- | --- |
| Fee definition | If `c` means cost per actual dollar bought/sold with fully invested post-fee targets, prefer the exact self-financing equation for eventual accounting. Retain the present proxy unchanged and explicitly approximate. | Which economic convention is intended, including entry, numerical representation/precision and model limitations? Do not choose using market outcomes. |
| Final boundary | Retain the proposed study-specific skip when no in-range d2 exists; record the unexecuted instruction and failure status. | Is the reporting horizon a bounded study or a continuing strategy that still trades at its final close? Apply the chosen rule to every comparator. |
| Solver budget | Retain strict rejection A in the current default. B demonstrates a possible audited adapter, but is **not ready for production adoption**: its fixed-index corrections can alter exposure support. | Reject/fallback versus a revised support-aware correction, exact tolerances, deterministic allocation of residual and independent objective re-evaluation. |
| Genuine ruin | Favor an explicit absorbing zero-wealth outcome for verified exact total loss, preserving the common evaluation horizon. Do not convert numerical/input failures into ruin. | Lifecycle/event reporting, full-horizon ratio/growth policies, data-quality precedence and any separately labelled prefix statistics. Current strict default remains unchanged. |

The references are pure, opt-in functions requiring the invented-fixture label.
They provide no loader, CLI, optimizer, dashboard/export, workflow mode or data
pipeline. Detailed vectors/marks have redacted representations. Label checks are
caller assertions, not independent proof of input origin.

## 1. Proxy versus exact self-financing fees

For nonnegative pre-trade weights `p` and post-fee target weights `t`, each with
sum one, and symmetric cost `0 <= c < 1` per dollar bought **and** sold, let `x`
be post-cost wealth divided by pre-trade wealth. Actual trade amounts per
pre-trade dollar are `x*t_i-p_i`; the reference equation is

```text
x + c * sum(abs(x*t_i - p_i)) = 1,      0 < x <= 1.
```

The existing proxy uses `q=sum(abs(t-p))`, fee fraction `c*q`, and wealth ratio
`1-c*q`. It computes volume before accounting for how fees shrink the target
portfolio. It is an approximation, not necessarily a conservative fee estimate.
From cash, exact entry instead has `x+c*x=1`, or `x=1/(1+c)`; proxy entry is
`1-c`. The model ignores asymmetric spreads, taxes, lots, market impact and
instrument availability. Neither cost rule calibrates replication of French
industry returns or makes those portfolios executable.

If instead `c*q` is deliberately defined as a target-weight turnover penalty,
it is that chosen abstract penalty, not an erroneous implementation of it. The
word “approximation” here concerns interpreting it as actual traded-dollar fees.
The owner must select the intended definition before choosing an equation.

### Existence, precision and independent oracles

Define `F(x)=x+c*sum(abs(x*t-p))-1`. Its endpoint values are `F(0)=c-1<0` and
`F(1)>=0`. The absolute-value volume function is Lipschitz with constant one,
so `F` increases with slope bounded between `1-c` and `1+c`. Thus the root is
unique in `(0,1]` under these assumptions. This is a fixed accounting equation,
not a portfolio optimizer.

[synthetic_fee_reference.py](industry_companion/synthetic_fee_reference.py)
uses exact rational bisection. Successful results carry a bracket containing the
root, width, half-width root error bound and exact equation residual. A midpoint
is a **certified approximation**, not an algebraically exact root unless its
residual is zero. `fee_fraction=c*actual_volume` and `wealth_loss_fraction=1-x`
can differ by the reported nonzero residual; it is not hidden as exact equality.

Certification requires width at most `1e-36` **and** relative width at most
`1e-28` times both retained wealth's positive lower bound and fee-loss's positive
lower bound. The latter avoids claiming a precise tiny fee from a coarse root
near one. Zero-cost/no-trade and entry closed forms avoid a zero-relative-bound
problem. The default iteration limit is 2,048; inability to certify produces
`ROOT_PRECISION_NOT_CERTIFIED`, not a plausible-looking root. Resource/input
precision limits are declared reference limits, not financial thresholds.

Inputs use exact Fractions/Decimals or floats interpreted by their decimal
representation. Ten weights must sum exactly one under that convention; no
normalization is performed. This differs from the old binary `math.fsum`
budget convention. A vector can pass the latter and fail rational input
validation; the cross-reference regression preserves this incompatibility.
Future integration must explicitly choose a representation/adapter rather than
silently repairing weights to make the references compose.

### Synthetic results: retain both signs and adverse stress cases

The fractions below are independent closed-form oracles. Bisection results are
checked against them within their certified brackets.

| Invented control | Exact model oracle | Existing proxy | Consequence |
| --- | --- | --- | --- |
| Zero cost or unchanged target | Wealth ratio 1 | Wealth ratio 1 | No fictitious trade fee. |
| Entry from cash, `c=0.0005` | `2000/2001`, about `0.999500249875062469` | `0.9995` | Exact retains about `2.49875062469e-7` more wealth per initial dollar. |
| Drift `(2/11,1/11,...,1/11)` to ten equal weights, `c=0.0005` | `x=(1+7c/11)/(1+4c/5)=110035/110044`, about `0.999918214532368871` | `0.999918181818181818` | Exact fee is lower; ratio difference is `9/275110000`, about `3.27141870525e-8`. |
| Same three-session toy as review 01, including entry and a 1.1 gross factor | Final wealth `5501750/5004501`, about `1.099360355807701907` | `1.099360045` | Difference about `3.10807701907e-7`; not the sum of cash-fee differences, because wealth compounds. |
| `p=(0.35,0.15,0.0625×8)`, `t=(0.30,0.20,0.0625×8)`, `c=0.0005` | `x=(1-0.7c)/(1-0.6c)=19993/19994`, about `0.999949984995498650` | `0.99995` | Exact fee is **higher**; proxy overstates retained wealth by about `1.50045013504e-8`. Both vectors meet the candidate cap. |
| Disjoint holdings, `c=0.75` | `(1-c)/(1+c)=1/7`, positive | `1-2c=-0.5`, infeasible | The proxy's exhausted-cost failure is not economic bankruptcy; the exact model remains defined. This is an engineered stress, not a plausible fee estimate. |

At small costs these examples differ by terms of second order, but their signs
and financial interpretations are not interchangeable. Small numerical examples
do not establish universal economic immateriality, particularly over repeated
trades or near a numerical boundary. Keep the proxy's unfavorable cases; select
the definition before any outcome inspection. Do not replace the default now.

## 2. Final-close trade without a subsequent in-range return

Two defensible conventions answer different questions:

- **Bounded study:** skip a d1-close instruction if no in-range d2 return can be
  earned. This matches the present prototype and Holmes's provisional preference.
- **Continuing strategy:** execute every scheduled in-range d1-close trade even
  at the reporting endpoint. Its fee is real under that hypothetical continuing
  policy, although the resulting exposure earns no measured later return.

Neither is a terminal liquidation. Neither permits post-2024 data. If d1 itself
is outside the study, no in-range trade exists under either rule. The full 2024
December boundary remains closed; the finite endpoint examples below use valid
earlier XNYS sessions, not an invented 2025 return.

The test-private rational oracle in
[test_boundary_conventions.py](tests/test_boundary_conventions.py) compares both
policies without changing the default ledger. At the final d1 in the doubled-
industry toy, skip gives `1.09945`; continuing gives `1.099360045`. Their gap is
the single proxy close fee `0.000089955`. Adding a valid d2 makes both policies
execute the legitimate d1 trade. Failed/skipped instructions remain explicit;
the existing stored reason `NO_IN_RANGE_EFFECTIVE_SESSION` is unchanged. This
review labels that policy status `SKIPPED_NO_IN_RANGE_EFFECTIVE_SESSION`.

A counterexample shows the interpretation matters: let invented pre-fee terminal
wealths be 1 and 1.0001. With a zero-turnover first portfolio and `q=0.5` in the
second at 5 bp, skip preserves their ordering; continuing gives the second
`0.999849975`, reversing it without any new return. This is an endpoint-policy
effect, not evidence selecting a strategy or justifying whichever rule looks best.

**Recommendation:** retain skip for this bounded study, preserve the instruction
and failure status, charge no phantom terminal fee or liquidation, and freeze
the same endpoint convention for every rule. Owner selection is still required;
ongoing-fund interpretation would justify a different convention.

## 3. Solver tolerance versus exact accounting budget

No solver is implemented or run. The references consume invented solver-shaped
vectors and a literal caller `solver_success=True` assertion, which is not proof
of convergence or an acceptable objective.

[synthetic_budget_reference.py](industry_companion/synthetic_budget_reference.py)
offers explicit competing policies:

| Policy | Admission and behavior |
| --- | --- |
| A: strict | Require independently valid ten-column inputs, exact binary `math.fsum(w)==1`, strict nonnegative/35% bounds and declared solver success. Reject inexact candidates with a fallback status. This preserves the existing accounting principle. |
| B: canonicalize proposal | First require those same strict bounds and success flag, plus budget residual at most `1e-8`. Only then redistribute the budget residual in fixed industry-index order, using spare capacity or removable positive holdings. Record original residual, every correction, maximum and L1 correction. Independently recheck exact budget, bounds and correction limits; reject if uncertified. |

B uses **zero bound tolerance**: even a tiny negative or above-cap input is
rejected, not clipped. The proposed `1e-8` tolerance applies only to budget.
Its at-most-two sweeps and roundoff allowance are explicit algorithmic limits.
Maximum correction cannot exceed the chosen budget tolerance; L1 correction and
sum-of-corrections are checked against original residual plus `8*ulp(1)`.
An already exact vector remains bitwise unchanged. Failed flags, nonfinite
values, wrong signs, excessive residuals and all-cap infeasible vectors cannot
be made successful. With ten 35%-capped weights, aggregate capacity is 3.5;
there is no feasible unit-budget all-cap/no-capacity case under these settings.

The adapter is a binary64 proposal. Original-domain bounds are checked before
conversion, and positive values that convert to zero are rejected rather than
silently losing support. Reported “original” weights/residuals refer to the
validated binary point before canonicalization, not a lossless arbitrary-
precision record. Higher-precision values just outside the binary cap cannot be
rounded down into admission. This is another reason to freeze a numeric
interface rather than implicitly compose the different references.

Independent review caught a cast-first defect in the new proposal: tiny
negative/above-cap values could round into admission, and a tiny positive
holding could disappear before its correction was recorded. Raw-domain and
positive-support guards now precede admission, with regressions for both
policies and tolerance parameters. These are corrections to the isolated
reference; the old ledger and its behavior are unchanged.

The binary toy `(0.125×8,0,0)` with its first weight perturbed by
`±2^-28` has residual magnitude `3.725290298461914e-9`. A rejects; B restores the
exact vector and records that correction. Batch permutation tests establish
candidate-order independence. This is **not** coordinate-permutation invariance:
reordering industry identities is disallowed and fixed-index correction can
assign residual to a different holding than another allocation rule would.

### Counterexample: a small correction can change exposure support

Let `epsilon=2^-28` and `delta=2^-40` (about `9.09494701773e-13`). Under B's
fixed-index rule:

- An oversummed vector `(delta,0.125+epsilon-delta,0.125×7,0)` loses its first
  positive holding while eliminating the residual.
- An undersummed vector `(0,0.125-epsilon,0.125×7,0)` gains a new first holding.

Both corrections pass the proposed numerical size and bound checks. Alternative
unit-budget vectors within the same correction bound can preserve original
support. In a separate invented one-session loss where only the first industry
survives, the two choices produce opposite ruin classifications. These controls
are in [test_reference_interactions.py](tests/test_reference_interactions.py).
They show that a small norm bound is not proof of equivalent risk or objective,
not that either synthetic allocation is a research winner.

**Recommendation:** retain A in the current default. Before any adoption of B,
review a support-aware correction rule (for example, remove from a large
holding and add to an already positive holding with capacity), retest it, and
re-evaluate the objective/variance on the final vector. Such a revision is not
implemented here. B is an explicit change to the no-repair principle, not
routine normalization. Strict A can also increase fallback frequency, changing
the effective strategy toward its baseline. Neither policy is economically
neutral merely because its numerical rule is deterministic.

## 4. Genuine total loss versus numerical/input failure

The current strict prototype remains unchanged. A separate
[synthetic_ruin_reference.py](industry_companion/synthetic_ruin_reference.py)
tests an absorbing-zero alternative for fixed initial holdings and natural
drift. It is not an alternate rebalancing engine; optional cost factors are
abstract multiplicative stresses, not either fee model above.

Genuine extinction is established **before floating multiplication**: every
strictly positive held asset must have an exact supplied simple return of -1.
A zero-weight asset need not lose 100%. One lost asset with another surviving
holding does not bankrupt the portfolio. A genuine event records wealth 0,
net return -1, no surviving weights and reference-peak drawdown 1. Every later
evaluation date remains present with wealth 0, return/weights `None`, no trade,
cost or restart. This retains an adverse full-horizon result without inventing
post-ruin zero returns from the undefined ratio `0/0`.

Classification must use the explicit exact-loss event, **not rounded metrics**.
Two invented common returns `-1+2^-52` leave positive wealth `2^-104`, but binary
`wealth/initial-1` and drawdown can round to -1 and 1 while `ruin_occurred=false`.
The cross-reference test retains this counterexample; boundary-looking summary
numbers alone do not prove genuine extinction.

The whole provided grid, returns and cost-factor tail are validated first.
Invalid tail data therefore produce an input failure rather than allowing early
ruin to conceal bad observations. This precedence is explicit; a production
policy reporting both a validated prefix event and later data fault would need
separate design. Dates are restricted before value access, with no 2025+ input.

The alternative separates invalid/below--1/nonfinite inputs, cost exhaustion,
arithmetic overflow/underflow and return precision loss. Counterexamples include
a near-total loss `-1+2^-52` that remains positive, a surviving tiny holding whose
product or normalized weight underflows, and `Fraction(-1+2^-60)` rounding to
float -1. None may be relabelled economic bankruptcy. Finite huge positive
inputs that overflow binary64 have a numerical code; literal infinity and
original returns below -1 remain invalid input. The tests retain all cases.

### Comparing terminated and surviving hypothetical portfolios

Compare terminal wealth and drawdown on the same full evaluation grid, keeping
the ruin flag/date and number of absorbed dates visible. Do not drop the losing
portfolio, shorten only its period or compare an unlabelled prefix Sharpe against
survivors' full-horizon Sharpe. Any later prefix diagnostic must state its period
and censoring and remain separate from a common-horizon comparison.

The narrow reference intentionally does **not report** annualized volatility,
Sharpe or geometric growth. With an absorbed tail, a complete daily return
sequence does not exist. If ruin occurs on the last date, the sequence can be
complete and a sample ratio can be calculable; the reference's omission is a
policy, not a claim of mathematical undefinedness. Terminal total return -1 is
reported. Terminal-value geometric growth of -100% over a fixed horizon can
also be defined without fabricated daily returns; whether to report it is an
unresolved owner choice. Do not impute post-ruin returns to obtain Sharpe.

**Recommendation:** preserve genuine ruin as an adverse absorbing outcome in any
future chosen policy, separate all input/numerical failure types, and review
metric omissions/censoring before freeze. No actual bankruptcy or market finding
is claimed, and the old strict behavior is not replaced.

## Reproducibility, status and next checkpoint

Every fixture is invented, with deterministic hand/property oracles and no
source observations, optimizer, files or network effects. New tests compare
alternatives and preserve counterexamples; old tests/default behavior remain.
Local verification completed with **508 passing tests**: the existing **323**,
**45** fee-reference cases, **74** budget cases, **58** ruin cases, **4** endpoint
cases and **4** interaction cases. The complete suite, both safety/workflow
guards (including optimized-Python validation), and actionlint v1.7.7 pass.
All previous experimental evidence is preserved. Test examples include exact
hand oracles, certified root brackets, deterministic property cases and rejected
input/precision boundaries. GitHub CI evidence is added after its run is verified.

Owner review should select the fee definition, horizon interpretation, budget
interface and ruin reporting policy. If another synthetic iteration is wanted,
the highest-priority open interface is support-preserving budget correction and
consistent binary/rational transport with independent objective checks. That
revision has not been implemented or approved. Do not select conventions based
on unavailable market outcomes or automatically freeze this document.

Hosted raw-data scope stays `pending_owner_rights_review`, `live_enabled=false`.
No historical returns, HEAD/GET, publisher email, live mode, launcher PR, public
release, PR merge or deployment is part of this task. The original ETF holdout,
all previous evidence and the published synthetic showcase remain untouched.
