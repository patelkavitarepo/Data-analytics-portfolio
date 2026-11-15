"""Opt-in, unfrozen budget-boundary alternatives for invented solver-shaped inputs.

No optimization, return data, loaders, I/O or default-ledger integration exists.
Strict policy rejects any inexact accounting budget. Canonicalize is a competing
proposal that changes already feasible inputs; it requires owner review before
adoption and is deliberately not called by the existing accounting prototype.
"""
from dataclasses import dataclass, field
import math
from numbers import Real

CAP = 0.35
MAX_BUDGET_TOLERANCE = 1e-8
ROUND_ALLOWANCE = 8 * math.ulp(1.0)
SYNTHETIC = 'invented_synthetic_fixture'
INDUSTRIES = ('NoDur', 'Durbl', 'Manuf', 'Enrgy', 'HiTec', 'Telcm', 'Shops', 'Hlth', 'Utils', 'Other')


class BudgetReferenceError(ValueError):
    """Stable configuration code only, never an offending weight/vector."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, repr=False)
class BudgetDecision:
    policy: str
    status: str
    reason: str | None
    accepted: bool
    used_fallback: bool
    canonicalized: bool
    original_weights: tuple | None = field(repr=False)
    accepted_weights: tuple | None = field(repr=False)
    original_residual: float | None
    corrections: tuple | None = field(repr=False)
    max_correction: float | None
    l1_correction: float | None
    budget_tolerance: float

    def __repr__(self):
        return (f'SyntheticBudgetDecision(policy={self.policy}, status={self.status}, '
                'values=redacted, owner_review_pending=True)')

    def summary(self):
        return dict(evidence_kind='synthetic_budget_reference',
                    owner_status='OWNER_REVIEW_PENDING', performance_cleared=False,
                    policy=self.policy, status=self.status, reason=self.reason,
                    accepted=self.accepted, used_fallback=self.used_fallback,
                    canonicalized=self.canonicalized,
                    original_residual=self.original_residual,
                    max_correction=self.max_correction, l1_correction=self.l1_correction,
                    budget_tolerance=self.budget_tolerance, bound_tolerance=0.0,
                    roundoff_allowance=ROUND_ALLOWANCE)


def _candidate_values(weights):
    if not isinstance(weights, (tuple, list)) or len(weights) != 10:
        return None, 'INVALID_CANDIDATE_SHAPE'
    values = []
    for value in weights:
        if not isinstance(value, Real) or isinstance(value, bool):
            return None, 'NONFINITE_OR_NONREAL_CANDIDATE'
        if value != value or value == math.inf or value == -math.inf:
            return None, 'NONFINITE_OR_NONREAL_CANDIDATE'
        # Check the supplied domain first: a tiny negative can cast to -0.0,
        # and a high-precision above-cap value can round down to binary CAP.
        if not 0.0 <= value <= CAP:
            return None, 'CANDIDATE_BOUND_VIOLATION'
        try:
            number = float(value)
        except (ValueError, OverflowError):
            return None, 'NONFINITE_OR_NONREAL_CANDIDATE'
        if not math.isfinite(number):
            return None, 'NONFINITE_OR_NONREAL_CANDIDATE'
        if not 0.0 <= number <= CAP:
            return None, 'CANDIDATE_BOUND_VIOLATION'
        if value > 0 and number == 0:
            return None, 'CANDIDATE_PRECISION_LOSS'
        values.append(number)
    return tuple(values), None


def adapt_synthetic_budget(weights, *, policy='strict', solver_success,
                           evidence_kind, budget_tolerance=MAX_BUDGET_TOLERANCE,
                           industry_order=INDUSTRIES):
    """Independently validate first; never convert failed/infeasible input to success.

    Only the budget gets a tolerance. Even a tiny negative or above-cap input is
    rejected, rather than clipped under a solver's bound tolerance. Canonicalize
    moves budget residual in fixed industry-index order through spare capacity
    (or positive holdings for removal). Two bounded sweeps are permitted; an
    independently unverified exact budget/correction bound is a rejection.

    Batch ordering cannot affect a single candidate's result. Reordering the
    industry vector changes identities and may change where correction occurs.
    Literal solver_success=True is only an assertion supplied by the caller,
    not proof that a real solver ran or that its objective is valid.

    Reported original_weights/residuals describe the validated binary64 point,
    not a lossless arbitrary-precision input. Raw-domain checks precede casts;
    casts that erase positive support are rejected. CAP is the actual binary64
    0.35 boundary, conservatively not extended to exact rational 7/20.
    """
    if evidence_kind != SYNTHETIC:
        raise BudgetReferenceError('EXPLICIT_INVENTED_FIXTURE_REQUIRED')
    if policy not in ('strict', 'canonicalize'):
        raise BudgetReferenceError('UNKNOWN_BUDGET_POLICY')
    if not isinstance(industry_order, (tuple, list)) or tuple(industry_order) != INDUSTRIES:
        raise BudgetReferenceError('STRICT_INDUSTRY_ORDER_REQUIRED')
    if not isinstance(budget_tolerance, Real) or isinstance(budget_tolerance, bool):
        raise BudgetReferenceError('INVALID_BUDGET_TOLERANCE')
    if not 0.0 <= budget_tolerance <= MAX_BUDGET_TOLERANCE:
        raise BudgetReferenceError('INVALID_BUDGET_TOLERANCE')
    try:
        tolerance = float(budget_tolerance)
    except (ValueError, OverflowError):
        raise BudgetReferenceError('INVALID_BUDGET_TOLERANCE') from None
    if not math.isfinite(tolerance) or not 0.0 <= tolerance <= MAX_BUDGET_TOLERANCE:
        raise BudgetReferenceError('INVALID_BUDGET_TOLERANCE')
    if budget_tolerance > 0 and tolerance == 0:
        raise BudgetReferenceError('INVALID_BUDGET_TOLERANCE')

    def reject(reason, original=None, residual=None, corrections=None):
        maximum = max(map(abs, corrections)) if corrections is not None else None
        l1 = math.fsum(map(abs, corrections)) if corrections is not None else None
        return BudgetDecision(policy, 'REJECTED', reason, False, True, False,
                              original, None, residual, corrections, maximum, l1, tolerance)

    if solver_success is not True:
        return reject('SOLVER_NOT_SUCCESSFUL')
    original, error = _candidate_values(weights)
    if error is not None:
        return reject(error)
    residual = 1.0 - math.fsum(original)
    if abs(residual) > tolerance:
        return reject('BUDGET_OUTSIDE_FEASIBILITY_TOLERANCE', original, residual)
    if residual == 0.0:
        return BudgetDecision(policy, 'ACCEPTED_EXACT', None, True, False, False,
                              original, original, residual, (0.,) * 10, 0., 0., tolerance)
    if policy == 'strict':
        return reject('INEXACT_ACCOUNTING_BUDGET', original, residual)

    adjusted = list(original)
    for _ in range(2):
        for index in range(10):
            remaining = 1.0 - math.fsum(adjusted)
            if remaining == 0.0:
                break
            current = adjusted[index]
            if remaining > 0.0 and current < CAP:
                # This bounds a correction of an input already checked feasible;
                # it is not clipping an out-of-bounds supplied candidate.
                updated = min(CAP, current + min(remaining, CAP - current))
                if updated == current:
                    updated = math.nextafter(current, math.inf)
            elif remaining < 0.0 and current > 0.0:
                updated = max(0.0, current - min(-remaining, current))
                if updated == current:
                    updated = math.nextafter(current, 0.0)
            else:
                continue
            if 0.0 <= updated <= CAP:
                adjusted[index] = updated
        if math.fsum(adjusted) == 1.0:
            break

    candidate = tuple(adjusted)
    corrections = tuple(after - before for after, before in zip(candidate, original))
    maximum = max(map(abs, corrections))
    l1 = math.fsum(map(abs, corrections))
    # Recheck independently, after the algorithm, rather than assuming its
    # construction proves feasibility. No proposed bound tolerance is relaxed.
    certified = (
        all(math.isfinite(w) and 0.0 <= w <= CAP for w in candidate)
        and math.fsum(candidate) == 1.0
        and maximum <= tolerance
        and l1 <= abs(residual) + ROUND_ALLOWANCE
        and abs(math.fsum(corrections) - residual) <= ROUND_ALLOWANCE
    )
    if not certified:
        return reject('CANONICALIZATION_NOT_CERTIFIED', original, residual, corrections)
    return BudgetDecision(policy, 'ACCEPTED_CANONICALIZED', None, True, False, True,
                          original, candidate, residual, corrections, maximum, l1, tolerance)
