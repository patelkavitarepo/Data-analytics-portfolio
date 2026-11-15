"""Invented solver-shaped vectors only: no optimizer or historical observations."""
import itertools
import math
import random
from fractions import Fraction

import pytest

from industry_companion.synthetic_budget_reference import (
    BudgetReferenceError, INDUSTRIES, adapt_synthetic_budget,
)

LABEL = 'invented_synthetic_fixture'
EQUAL = (0.1,) * 10
BINARY_EQUAL = (0.125,) * 8 + (0., 0.)
EPS = 2 ** -28


def adapt(weights, policy='strict', **kwargs):
    return adapt_synthetic_budget(weights, policy=policy, solver_success=True,
                                  evidence_kind=LABEL, **kwargs)


@pytest.mark.parametrize('policy', ['strict', 'canonicalize'])
def test_exact_feasible_vectors_remain_bitwise_unchanged(policy):
    for vector in (EQUAL, BINARY_EQUAL, (.35, .35, .3) + (0.,) * 7):
        decision = adapt(vector, policy)
        assert decision.accepted and decision.status == 'ACCEPTED_EXACT'
        assert decision.accepted_weights == vector
        assert decision.corrections == (0.,) * 10 and decision.max_correction == 0
        assert not decision.used_fallback and not decision.canonicalized
        assert decision.original_residual == 0


@pytest.mark.parametrize('sign', [-1, 1])
def test_competing_policies_have_an_explicit_near_feasible_counterexample(sign):
    original = (BINARY_EQUAL[0] + sign * EPS,) + BINARY_EQUAL[1:]
    strict = adapt(original, 'strict')
    canonical = adapt(original, 'canonicalize')
    assert not strict.accepted and strict.used_fallback
    assert strict.reason == 'INEXACT_ACCOUNTING_BUDGET'
    assert canonical.accepted and canonical.canonicalized
    assert canonical.accepted_weights == BINARY_EQUAL
    assert canonical.original_residual == -sign * EPS
    assert canonical.corrections[0] == -sign * EPS
    assert canonical.corrections[1:] == (0.,) * 9
    assert canonical.max_correction == EPS
    assert math.fsum(canonical.accepted_weights) == 1.0
    assert original[0] != BINARY_EQUAL[0]  # Input never mutated.


def test_spare_capacity_skips_already_capped_industries():
    original = (.35, .35, .3 - EPS) + (0.,) * 7
    decision = adapt(original, 'canonicalize')
    assert decision.accepted
    assert decision.corrections[:2] == (0., 0.)
    assert decision.corrections[2] > 0
    assert all(0 <= value <= .35 for value in decision.accepted_weights)
    assert math.fsum(decision.accepted_weights) == 1.0


def test_removal_skips_zero_holdings_in_fixed_industry_order():
    original = (0., .125 + EPS) + (.125,) * 7 + (0.,)
    decision = adapt(original, 'canonicalize')
    assert decision.accepted
    assert decision.corrections[0] == 0 and decision.corrections[1] == -EPS
    assert decision.accepted_weights == (0.,) + (.125,) * 8 + (0.,)


@pytest.mark.parametrize('vector', [
    (.35,) * 10, (0.,) * 10, (1.,) + (0.,) * 9,
    (-1e-12,) + (.125,) * 8 + (1e-12,),
    (.35000000000000003, .35, .29999999999999993) + (0.,) * 7,
    (float('nan'),) + EQUAL[1:], (float('inf'),) + EQUAL[1:],
    (True,) + EQUAL[1:], ('PRIVATEPOISON',) + EQUAL[1:],
    EQUAL[:-1], EQUAL + (0.,), None,
])
@pytest.mark.parametrize('policy', ['strict', 'canonicalize'])
def test_infeasible_inputs_are_not_clipped_or_made_successful(vector, policy):
    decision = adapt(vector, policy)
    assert not decision.accepted and decision.used_fallback
    assert decision.accepted_weights is None and not decision.canonicalized
    assert decision.reason
    assert 'PRIVATEPOISON' not in repr(decision)


@pytest.mark.parametrize('success', [False, None, 0, 1, 'true'])
def test_only_literal_solver_success_is_eligible(success):
    decision = adapt_synthetic_budget(EQUAL, policy='canonicalize', solver_success=success,
                                      evidence_kind=LABEL)
    assert not decision.accepted and decision.reason == 'SOLVER_NOT_SUCCESSFUL'
    assert decision.accepted_weights is None


@pytest.mark.parametrize('sign', [-1, 1])
def test_budget_outside_declared_tolerance_never_enters_canonicalization(sign):
    original = (BINARY_EQUAL[0] + sign * 2 ** -26,) + BINARY_EQUAL[1:]
    decision = adapt(original, 'canonicalize')
    assert not decision.accepted
    assert decision.reason == 'BUDGET_OUTSIDE_FEASIBILITY_TOLERANCE'


@pytest.mark.parametrize('tolerance', [-1e-8, 1.0001e-8, float('nan'), float('inf'), True, '0.0001'])
def test_invalid_policy_parameters_are_rejected(tolerance):
    with pytest.raises(BudgetReferenceError):
        adapt(EQUAL, 'canonicalize', budget_tolerance=tolerance)


def test_zero_budget_tolerance_is_an_explicit_exact_only_envelope():
    assert adapt(EQUAL, 'canonicalize', budget_tolerance=0).accepted
    near = (BINARY_EQUAL[0] - EPS,) + BINARY_EQUAL[1:]
    decision = adapt(near, 'canonicalize', budget_tolerance=0)
    assert not decision.accepted and decision.reason == 'BUDGET_OUTSIDE_FEASIBILITY_TOLERANCE'


@pytest.mark.parametrize('seed', [7, 29, 101, 313, 2026])
def test_deterministic_small_residual_invariants(seed):
    rng = random.Random(seed)
    for _ in range(20):
        original = list(BINARY_EQUAL)
        index = rng.randrange(8)
        original[index] += rng.choice((-1, 1)) * rng.randrange(1, 9) * 2 ** -31
        decision = adapt(original, 'canonicalize')
        repeat = adapt(original, 'canonicalize')
        assert decision == repeat and decision.accepted
        assert math.fsum(decision.accepted_weights) == 1.0
        assert all(0 <= weight <= .35 for weight in decision.accepted_weights)
        assert decision.max_correction <= 1e-8
        assert math.fsum(abs(delta) for delta in decision.corrections) <= abs(decision.original_residual) + 8*math.ulp(1.)
        assert all(after-before == delta for after,before,delta in zip(decision.accepted_weights, original, decision.corrections))


def test_candidate_batch_order_does_not_change_each_individual_decision():
    candidates = [BINARY_EQUAL,
                  (BINARY_EQUAL[0]-EPS,) + BINARY_EQUAL[1:],
                  (BINARY_EQUAL[0]+EPS,) + BINARY_EQUAL[1:]]
    expected = {candidate: adapt(candidate, 'canonicalize') for candidate in candidates}
    for permutation in itertools.permutations(candidates):
        assert {candidate: adapt(candidate, 'canonicalize') for candidate in permutation} == expected
    # This is batch-order independence, not a claim that changing industry
    # identities/order leaves the fixed-index correction allocation unchanged.


@pytest.mark.parametrize('seed', [7,29,101,313,2026])
def test_nonbinary_simplex_candidates_keep_independently_rechecked_budgets(seed):
    rng=random.Random(seed)
    for _ in range(20):
        raw=[rng.uniform(.5,1.5) for _ in range(10)]
        total=math.fsum(raw)
        candidate=[value/total for value in raw]
        candidate[0]+=rng.choice((-1,1))*1e-9
        decision=adapt(candidate,'canonicalize')
        assert decision.accepted
        assert math.fsum(decision.accepted_weights)==1.0
        assert all(0<=value<=.35 for value in decision.accepted_weights)
        assert decision.max_correction<=1e-8


@pytest.mark.parametrize('order', [INDUSTRIES[::-1],INDUSTRIES[:-1],('Other',)*10])
def test_fixed_industry_identity_is_not_an_unlabelled_permutation(order):
    with pytest.raises(BudgetReferenceError,match='STRICT_INDUSTRY_ORDER_REQUIRED'):
        adapt(EQUAL,'canonicalize',industry_order=order)


def test_explicit_synthetic_origin_and_policy_are_required():
    with pytest.raises(BudgetReferenceError):
        adapt_synthetic_budget(EQUAL, policy='canonicalize', solver_success=True,
                               evidence_kind='historical_market')
    with pytest.raises(BudgetReferenceError):
        adapt(EQUAL, 'renormalize_everything')


def test_reference_is_pure_and_summary_is_explicitly_unfrozen(monkeypatch, tmp_path, capsys):
    import builtins
    monkeypatch.chdir(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError('Budget reference must perform no file I/O')
    monkeypatch.setattr(builtins, 'open', forbidden)
    original = list((BINARY_EQUAL[0]-EPS,) + BINARY_EQUAL[1:])
    snapshot = original[:]
    decision = adapt(original, 'canonicalize')
    assert original == snapshot and list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ('', '')
    summary = decision.summary()
    assert summary['owner_status'] == 'OWNER_REVIEW_PENDING'
    assert summary['performance_cleared'] is False
    assert summary['evidence_kind'] == 'synthetic_budget_reference'
    assert all(key not in summary for key in ('weights','accepted_weights','corrections'))
    assert 'redacted' in repr(decision)


@pytest.mark.parametrize('policy', ['strict','canonicalize'])
@pytest.mark.parametrize('case,reason', [
    ('negative_underflow','CANDIDATE_BOUND_VIOLATION'),
    ('positive_underflow','CANDIDATE_PRECISION_LOSS'),
    ('above_cap_rounds_to_cap','CANDIDATE_BOUND_VIOLATION'),
])
def test_raw_real_domain_and_positive_support_survive_float_boundary(policy,case,reason):
    tiny=Fraction(1,10**1000)
    vector=list(BINARY_EQUAL)
    if case=='negative_underflow':vector[8]=-tiny
    elif case=='positive_underflow':vector[8]=tiny
    else:
        vector=list((.35,.35,.3)+(0.,)*7)
        vector[0]=Fraction.from_float(.35)+tiny
    assert math.fsum(float(value) for value in vector)==1
    decision=adapt(vector,policy)
    assert not decision.accepted and decision.used_fallback
    assert decision.reason==reason and decision.accepted_weights is None


@pytest.mark.parametrize('policy',['strict','canonicalize'])
def test_representable_fraction_inputs_record_validated_binary64_values(policy):
    vector=tuple(Fraction.from_float(value) for value in BINARY_EQUAL)
    decision=adapt(vector,policy)
    assert decision.accepted and decision.accepted_weights==BINARY_EQUAL
    assert all(type(value) is float for value in decision.original_weights)


@pytest.mark.parametrize('policy',['strict','canonicalize'])
def test_exact_decimal_cap_is_not_silently_granted_extra_binary_capacity(policy):
    # Binary64 .35 lies just below exact 7/20. This proposal's raw-domain check
    # conservatively uses the actual binary64 cap, not a new decimal cap.
    vector=(Fraction(7,20),.35,.3)+(0.,)*7
    decision=adapt(vector,policy)
    assert not decision.accepted and decision.reason=='CANDIDATE_BOUND_VIOLATION'


def test_opt_in_budget_adapter_does_not_replace_current_strict_default():
    from industry_companion.synthetic_accounting import ScoredCandidate, select_predeclared_target
    near=(BINARY_EQUAL[0]-EPS,)+BINARY_EQUAL[1:]
    candidate=(ScoredCandidate(near,1.),)
    assert select_predeclared_target(candidate).used_fallback
    assert adapt(near,'canonicalize').accepted
    assert select_predeclared_target(candidate).used_fallback


@pytest.mark.parametrize('tolerance', [
    -Fraction(1,10**1000), Fraction(1,10**1000),
    Fraction.from_float(1e-8)+Fraction(1,10**1000),
], ids=['negative_rounds_zero','positive_rounds_zero','above_max_rounds_down'])
def test_tolerance_original_domain_is_not_changed_by_conversion(tolerance):
    with pytest.raises(BudgetReferenceError,match='INVALID_BUDGET_TOLERANCE'):
        adapt(EQUAL,'canonicalize',budget_tolerance=tolerance)
