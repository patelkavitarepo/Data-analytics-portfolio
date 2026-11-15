"""Invented cross-convention counterexamples; no default integration or markets."""
from datetime import date
import math

import pytest

from industry_companion.audit import expected_sessions
from industry_companion.synthetic_accounting import CalendarGrid
from industry_companion.synthetic_budget_reference import adapt_synthetic_budget
from industry_companion.synthetic_fee_reference import FeeReferenceError, exact_rebalance
from industry_companion.synthetic_ruin_reference import absorbing_ruin_reference

LABEL='invented_synthetic_fixture'
EPS=2**-28
TINY=2**-40


@pytest.mark.parametrize('direction', ['remove_support','add_support'])
def test_small_certified_budget_correction_can_change_a_ruin_classification(direction):
    if direction=='remove_support':
        original=(TINY,.125+EPS-TINY)+(.125,)*7+(0.,)
        alternative=(TINY,.125-TINY)+(.125,)*7+(0.,)
        expected_ruin=True
    else:
        original=(0.,.125-EPS)+(.125,)*7+(0.,)
        alternative=(0.,)+(.125,)*8+(0.,)
        expected_ruin=False
    proposal=adapt_synthetic_budget(original,policy='canonicalize',solver_success=True,evidence_kind=LABEL)
    strict=adapt_synthetic_budget(original,policy='strict',solver_success=True,evidence_kind=LABEL)
    assert proposal.accepted and proposal.max_correction<=1e-8
    assert not strict.accepted and strict.used_fallback
    assert math.fsum(proposal.accepted_weights)==math.fsum(alternative)==1
    assert max(abs(a-b) for a,b in zip(original,alternative))<=EPS
    assert all(0<=w<=.35 for w in alternative)
    calendar=CalendarGrid(expected_sessions(),date(2016,1,1),date(2024,12,31),
                          provenance='Pinned calendar dates; invented cross-convention loss fixture')
    def result(weights):
        return absorbing_ruin_reference(calendar=calendar,dates=(date(2021,1,5),),
            returns=((0.,)+(-1.,)*9,),initial_weights=weights,evidence_kind=LABEL).summary()
    fixed_index=result(proposal.accepted_weights)
    support_preserving=result(alternative)
    assert fixed_index['ruin_occurred'] is expected_ruin
    assert support_preserving['ruin_occurred'] is not expected_ruin
    assert (fixed_index['terminal_wealth']==0) is expected_ruin
    assert fixed_index['performance_cleared'] is support_preserving['performance_cleared'] is False


def test_binary_budget_acceptance_is_not_an_exact_rational_input_adapter():
    # Both references deliberately state different input-number conventions.
    # Do not silently normalize one to make composition appear successful.
    vector=(.35,)+(.65/9,)*9
    accepted=adapt_synthetic_budget(vector,policy='strict',solver_success=True,evidence_kind=LABEL)
    assert accepted.accepted and math.fsum(vector)==1
    with pytest.raises(FeeReferenceError,match='EXACT_REFERENCE_BUDGET_REQUIRED'):
        exact_rebalance((.1,)*10,accepted.accepted_weights,.0005,evidence_kind=LABEL)


def test_rounded_drawdown_or_total_return_is_not_a_bankruptcy_classifier():
    calendar=CalendarGrid(expected_sessions(),date(2016,1,1),date(2024,12,31),
                          provenance='Pinned calendar dates; invented near-loss precision fixture')
    r=-1+2**-52
    result=absorbing_ruin_reference(calendar=calendar,dates=(date(2021,1,5),date(2021,1,6)),
                                    returns=((r,)*10,)*2,evidence_kind=LABEL).summary()
    assert result['terminal_wealth']==2**-104 and result['ruin_occurred'] is False
    assert result['terminal_total_return']==-1 and result['max_drawdown']==1
    # Those displayed binary64 metrics rounded to their boundary. Positive
    # wealth and the explicit exact-loss predicate remain the classification.
