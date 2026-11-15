"""Invented endpoint-convention oracles; no default ledger changes or markets."""
from datetime import date
from fractions import Fraction as F

import pytest

from industry_companion.audit import expected_sessions
from industry_companion.synthetic_accounting import (
    CalendarGrid, EQUAL, make_instruction, simulate,
)


def endpoint_reference(wealth, pretrade, target, cost, *, has_d2, policy):
    """Test-private exact-rational oracle for the existing approximate fee rule."""
    assert policy in ('skip_without_d2', 'continuing_strategy')
    if not has_d2 and policy == 'skip_without_d2':
        return wealth, F(0), 'SKIPPED_NO_IN_RANGE_EFFECTIVE_SESSION'
    q=sum(abs(t-p) for p,t in zip(pretrade,target))
    fee=wealth*cost*q
    return wealth-fee,fee,'EXECUTED_AT_D1_CLOSE'


@pytest.fixture(scope='module')
def calendar():
    return CalendarGrid(expected_sessions(),date(2016,1,1),date(2024,12,31),
                        provenance='Pinned XNYS dates; invented endpoint fixtures')


def test_no_d2_alternatives_change_wealth_only_by_the_terminal_fee(calendar):
    c=F(1,2000)
    p=(F(2,11),)+(F(1,11),)*9
    t=(F(1,10),)*10
    before=(1-c)*F(11,10)
    skipped=endpoint_reference(before,p,t,c,has_d2=False,policy='skip_without_d2')
    continuing=endpoint_reference(before,p,t,c,has_d2=False,policy='continuing_strategy')
    assert skipped==(F('1.09945'),F(0),'SKIPPED_NO_IN_RANGE_EFFECTIVE_SESSION')
    assert continuing[0]==F('1.099360045') and continuing[1]==F('0.000089955')
    assert skipped[0]-continuing[0]==continuing[1]
    dates=(date(2021,1,29),date(2021,2,1))
    instruction=make_instruction(calendar,dates[0],weights=EQUAL)
    ledger=simulate(calendar=calendar,dates=dates,returns=((0.,)*10,(1.,)+(0.,)*9),
                    instructions=(instruction,),cost_rate=float(c),
                    evidence_kind='invented_synthetic_fixture')
    assert ledger.days[-1].wealth==pytest.approx(float(skipped[0]))
    assert ledger.days[-1].rebalance_q==ledger.days[-1].rebalance_fee==0
    # Preserve the original stored reason; the review status adds a namespace,
    # not a retrospective default implementation change.
    assert ledger.skipped_instructions[0].reason=='NO_IN_RANGE_EFFECTIVE_SESSION'


def test_d2_in_range_executes_the_legitimate_trade_under_both_policies(calendar):
    c=F(1,2000)
    p=(F(2,11),)+(F(1,11),)*9
    t=(F(1,10),)*10
    for policy in ('skip_without_d2','continuing_strategy'):
        wealth,fee,status=endpoint_reference((1-c)*F(11,10),p,t,c,has_d2=True,policy=policy)
        assert wealth==F('1.099360045') and fee==F('0.000089955')
        assert status=='EXECUTED_AT_D1_CLOSE'
    dates=(date(2021,1,29),date(2021,2,1),date(2021,2,2))
    ledger=simulate(calendar=calendar,dates=dates,
                    returns=((0.,)*10,(1.,)+(0.,)*9,(0.,)*10),
                    instructions=(make_instruction(calendar,dates[0],weights=EQUAL),),
                    cost_rate=float(c),evidence_kind='invented_synthetic_fixture')
    assert ledger.days[1].target_executed and ledger.days[1].rebalance_q>0
    assert ledger.days[-1].wealth==pytest.approx(float(wealth))
    assert not ledger.skipped_instructions


def test_endpoint_choice_can_reverse_terminal_value_order_without_a_new_return():
    p=(F(1,10),)*10
    target=(F(7,20),)+(F(13,180),)*9
    assert sum(abs(t-w) for t,w in zip(target,p))==F(1,2)
    a=F(1);b=F('1.0001');c=F(1,2000)
    a_skip=endpoint_reference(a,p,p,c,has_d2=False,policy='skip_without_d2')[0]
    b_skip=endpoint_reference(b,p,target,c,has_d2=False,policy='skip_without_d2')[0]
    a_continue=endpoint_reference(a,p,p,c,has_d2=False,policy='continuing_strategy')[0]
    b_continue=endpoint_reference(b,p,target,c,has_d2=False,policy='continuing_strategy')[0]
    assert b_skip>a_skip and b_continue<a_continue
    assert b_continue==F('0.999849975')


def test_skipped_failure_keeps_status_and_no_terminal_liquidation(calendar):
    dates=(date(2024,12,30),date(2024,12,31))
    instruction=make_instruction(calendar,dates[-1],weights=None,failure_reason='SOLVER_FAILED')
    assert instruction.d1 is instruction.d2 is None
    ledger=simulate(calendar=calendar,dates=dates,returns=((0.,)*10,)*2,
                    instructions=(instruction,),evidence_kind='invented_synthetic_fixture')
    assert ledger.summary()['terminal_wealth']==pytest.approx(.9995)
    assert ledger.summary()['fallback_count']==0 and ledger.summary()['skipped_failure_count']==1
    assert ledger.skipped_instructions[0].failure_reason=='SOLVER_FAILED'
    assert all(d.rebalance_fee==0 for d in ledger.days)
