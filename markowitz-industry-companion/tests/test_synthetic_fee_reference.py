"""Independent rational hand oracles for invented proportional-cost cases only."""
from decimal import Decimal
from fractions import Fraction as F
import math
import random

import pytest

from industry_companion.synthetic_fee_reference import (
    ABSOLUTE_TOLERANCE, RELATIVE_TOLERANCE, FeeReferenceError,
    exact_entry, exact_rebalance,
)

KIND='invented_synthetic_fixture'
EQUAL=(F(1,10),)*10
FIRST=(F(1),)+(F(0),)*9
SECOND=(F(0),F(1))+(F(0),)*8


def check_oracle(result,oracle):
    assert result.bracket_low<=oracle<=result.bracket_high
    assert abs(result.wealth_ratio-oracle)<=result.root_error_bound
    assert result.bracket_width==result.bracket_high-result.bracket_low
    assert result.residual==result.wealth_ratio+result.fee_fraction-1
    assert abs(result.residual)<=2*result.root_error_bound
    assert result.wealth_loss_fraction==1-result.wealth_ratio
    assert result.performance_cleared is False
    assert result.protocol_status=='DRAFT_NOT_FROZEN'
    assert result.evidence_kind==KIND


@pytest.mark.parametrize('cost',[F(0),F(1,2000),F(1,10),F(3,4)])
def test_exact_initial_entry_is_all_in_assets_not_proxy_reference_dollars(cost):
    result=exact_entry(cost,evidence_kind=KIND)
    check_oracle(result,1/(1+cost))
    assert result.traded_notional==result.wealth_ratio
    assert result.fee_fraction==cost*result.wealth_ratio
    assert result.proxy_wealth_ratio==1-cost
    assert result.wealth_ratio_difference==cost*cost/(1+cost)


@pytest.mark.parametrize('cost',[F(0),F(1,2000),F(1,4),F(3,4)])
def test_disjoint_trade_has_independent_closed_form_and_proxy_counterexample(cost):
    result=exact_rebalance(FIRST,SECOND,cost,evidence_kind=KIND)
    check_oracle(result,(1-cost)/(1+cost))
    assert result.proxy_wealth_ratio==1-2*cost
    assert result.proxy_feasible is (cost<F(1,2))
    assert result.wealth_ratio>0


@pytest.mark.parametrize('cost',[F(0),F(1,2000),F(1,4),F(999,1000)])
def test_unchanged_targets_have_no_cost_even_under_stress(cost):
    result=exact_rebalance(EQUAL,EQUAL,cost,evidence_kind=KIND)
    assert result.wealth_ratio==result.proxy_wealth_ratio==1
    assert result.fee_fraction==result.traded_notional==result.residual==0
    assert result.iterations==0


def test_zero_cost_retargeting_does_not_charge_notional():
    result=exact_rebalance(FIRST,EQUAL,F(0),evidence_kind=KIND)
    assert result.wealth_ratio==1 and result.fee_fraction==0
    assert result.traded_notional==F(9,5)


def test_proxy_can_understate_fees_with_all_targets_inside_35_percent_cap():
    p=(F(35,100),F(15,100))+(F(1,16),)*8
    t=(F(30,100),F(20,100))+(F(1,16),)*8
    c=F(1,2000)
    result=exact_rebalance(p,t,c,evidence_kind=KIND)
    check_oracle(result,(1-F(7,10)*c)/(1-F(3,5)*c))
    assert result.proxy_traded_notional==F(1,10)
    assert result.wealth_ratio<result.proxy_wealth_ratio
    assert result.fee_fraction>result.proxy_fee_fraction
    # Same pretrade wealth and same later invented growth: this comparison's
    # terminal-wealth difference is adverse to the exact model, unlike the
    # separate entry-plus-doubled-industry fixture below.
    starting_wealth,later_growth=F(3,2),F(11,10)
    assert starting_wealth*later_growth*result.wealth_ratio < starting_wealth*later_growth*result.proxy_wealth_ratio


def test_proxy_can_overstate_fees_for_doubled_industry_back_to_equal():
    p=(F(2,11),)+(F(1,11),)*9
    c=F(1,2000)
    result=exact_rebalance(p,EQUAL,c,evidence_kind=KIND)
    check_oracle(result,(1+F(7,11)*c)/(1+F(4,5)*c))
    assert result.proxy_traded_notional==F(9,55)
    assert result.wealth_ratio>result.proxy_wealth_ratio
    assert result.fee_fraction<result.proxy_fee_fraction


def test_paired_three_session_fixture_final_wealth_difference_is_not_a_market_result():
    c=F(1,2000)
    entry=exact_entry(c,evidence_kind=KIND)
    rebalance=exact_rebalance((F(2,11),)+(F(1,11),)*9,EQUAL,c,evidence_kind=KIND)
    exact_wealth=entry.wealth_ratio*F(11,10)*rebalance.wealth_ratio
    oracle=F(1,1)/(1+c)*F(11,10)*(1+F(7,11)*c)/(1+F(4,5)*c)
    proxy=(1-c)*F(11,10)*(1-c*F(9,55))
    assert abs(exact_wealth-oracle)<=F(11,10)*rebalance.root_error_bound
    assert proxy==F('1.099360045') and exact_wealth>proxy


@pytest.mark.parametrize('cost',[F(1,10**80),1-F(1,10**80),F(5,10**324)])
def test_extreme_costs_certify_both_wealth_and_small_fee_precision(cost):
    result=exact_rebalance(FIRST,SECOND,cost,evidence_kind=KIND)
    check_oracle(result,(1-cost)/(1+cost))
    assert result.bracket_width<=ABSOLUTE_TOLERANCE
    assert result.bracket_width<=RELATIVE_TOLERANCE*min(result.bracket_low,1-result.bracket_high)


def test_precision_limit_is_a_failure_not_a_false_root_certificate():
    with pytest.raises(FeeReferenceError,match='ROOT_PRECISION_NOT_CERTIFIED'):
        exact_rebalance(FIRST,SECOND,F(1,2000),evidence_kind=KIND,max_iterations=1)


@pytest.mark.parametrize('seed',[5,19,47,101,2026])
def test_exact_equation_brackets_and_paired_reproducibility(seed):
    rng=random.Random(seed)
    def vector():
        integers=[rng.randrange(1,100) for _ in range(10)]
        total=sum(integers)
        return tuple(F(i,total) for i in integers)
    p,t=vector(),vector()
    c=F(rng.randrange(1,500),1000)
    first=exact_rebalance(p,t,c,evidence_kind=KIND)
    second=exact_rebalance(p,t,c,evidence_kind=KIND)
    assert first==second
    def equation(x):return x+c*sum(abs(x*a-b) for a,b in zip(t,p))-1
    assert equation(first.bracket_low)<=0<=equation(first.bracket_high)
    assert first.fee_fraction==c*first.traded_notional
    assert first.proxy_fee_fraction==c*sum(abs(a-b) for a,b in zip(t,p))
    assert abs(first.residual)<=2*first.root_error_bound
    # Strict monotonicity's lower slope bound also implies a unique root.
    low,high=F(1,4),F(3,4)
    assert equation(high)-equation(low)>=(1-c)*(high-low)>0


def test_wealth_scaling_industry_permutation_and_cost_monotonicity():
    p=(F(35,100),F(15,100))+(F(1,16),)*8
    t=(F(30,100),F(20,100))+(F(1,16),)*8
    result=exact_rebalance(p,t,F(1,2000),evidence_kind=KIND)
    permuted=exact_rebalance(p[::-1],t[::-1],F(1,2000),evidence_kind=KIND)
    assert result==permuted
    for wealth in (F(1,1000),F(1),F(10**12)):
        assert wealth*result.wealth_ratio+wealth*result.fee_fraction-wealth==wealth*result.residual
        assert wealth*result.fee_fraction==result.cost_rate*(wealth*result.traded_notional)
    costs=(F(0),F(1,2000),F(1,100),F(1,4))
    references=[exact_rebalance(p,t,c,evidence_kind=KIND) for c in costs]
    assert all(a.bracket_low>b.bracket_high for a,b in zip(references,references[1:]))


@pytest.mark.parametrize('iterations',[0,-1,True,4097])
def test_invalid_iteration_budget_fails_explicitly(iterations):
    with pytest.raises(FeeReferenceError,match='REFERENCE_ITERATION_BUDGET_REQUIRED'):
        exact_rebalance(FIRST,SECOND,F(1,2000),evidence_kind=KIND,max_iterations=iterations)


@pytest.mark.parametrize('cost',[-1,1,2,float('nan'),float('inf'),True,'0.01'])
def test_invalid_cost_inputs_are_rejected_with_safe_codes(cost):
    with pytest.raises(FeeReferenceError) as error:
        exact_entry(cost,evidence_kind=KIND)
    assert '0.01' not in str(error.value) and 'nan' not in str(error.value)


@pytest.mark.parametrize('weights',[(F(1),)*10,(-F(1),F(2))+(F(0),)*8,
    (F(1),)*9,(float('nan'),)+(F(0),)*9,(True,)+(F(0),)*9,
    (Decimal('.1'),)*9+(Decimal('.1000000000000000000001'),)])
def test_no_silent_budget_or_bound_repair(weights):
    with pytest.raises(FeeReferenceError):
        exact_rebalance(weights,EQUAL,F(1,2000),evidence_kind=KIND)


def test_explicit_synthetic_origin_and_redacted_results_no_output(capsys):
    with pytest.raises(FeeReferenceError):exact_entry(F(1,2000),evidence_kind='historical')
    result=exact_rebalance(EQUAL,FIRST,Decimal('.0005'),evidence_kind=KIND)
    assert 'redacted' in repr(result)
    assert capsys.readouterr()==('','')


def test_float_input_policy_is_decimal_repr_without_renormalization():
    result=exact_rebalance((.1,)*10,(.1,)*10,.0005,evidence_kind=KIND)
    assert result.wealth_ratio==1
    # A binary64 fsum budget can differ from the explicit decimal-repr budget.
    near=(.35,)+(.65/9,)*9
    assert math.fsum(near)==1
    with pytest.raises(FeeReferenceError):exact_rebalance(near,EQUAL,.0005,evidence_kind=KIND)
