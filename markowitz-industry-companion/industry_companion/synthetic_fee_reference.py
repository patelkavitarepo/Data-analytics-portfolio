"""Opt-in rational reference for invented self-financing fee fixtures only.

This alternative does not change the default accounting prototype. The model
charges c per dollar bought AND sold, fully invests post-fee wealth, and solves
x + c*sum(abs(x*t-p)) = 1. It estimates no executable index-replication cost.

Inputs are exact Fractions/Decimals/integers, or floats interpreted by their
decimal repr. Ten weights must sum exactly one under that convention. No budget
repair occurs, and stress vectors are not restricted to the draft 35% cap.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
import math

SYNTHETIC='invented_synthetic_fixture'
ABSOLUTE_TOLERANCE=Fraction(1,10**36)
RELATIVE_TOLERANCE=Fraction(1,10**28)


class FeeReferenceError(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def _require(condition,code):
    if not condition:
        raise FeeReferenceError(code)


def _fraction(value):
    _require(not isinstance(value,bool),'REFERENCE_NUMBER_REQUIRED')
    if isinstance(value,float):
        _require(math.isfinite(value),'REFERENCE_FINITE_NUMBER_REQUIRED')
        result=Fraction(str(value))
    elif isinstance(value,Decimal):
        _require(value.is_finite(),'REFERENCE_FINITE_NUMBER_REQUIRED')
        _require(value.is_zero() or abs(value.adjusted())<=1000,'REFERENCE_INPUT_PRECISION_LIMIT')
        result=Fraction(value)
    elif isinstance(value,(int,Fraction)):
        result=Fraction(value)
    else:
        raise FeeReferenceError('REFERENCE_NUMBER_REQUIRED')
    _require(result.numerator.bit_length()<=8192 and result.denominator.bit_length()<=8192,
             'REFERENCE_INPUT_PRECISION_LIMIT')
    return result


def _cost(cost_rate,evidence_kind):
    _require(evidence_kind==SYNTHETIC,'EXPLICIT_INVENTED_FIXTURE_REQUIRED')
    cost=_fraction(cost_rate)
    _require(0<=cost<1,'REFERENCE_COST_OUT_OF_RANGE')
    return cost


def _weights(values):
    _require(isinstance(values,(tuple,list)) and len(values)==10,'TEN_REFERENCE_WEIGHTS_REQUIRED')
    values=tuple(_fraction(v) for v in values)
    _require(all(0<=v<=1 for v in values),'REFERENCE_WEIGHT_BOUNDS')
    _require(sum(values)==1,'EXACT_REFERENCE_BUDGET_REQUIRED')
    return values


@dataclass(frozen=True,repr=False)
class FeeReference:
    wealth_ratio: Fraction
    fee_fraction: Fraction
    wealth_loss_fraction: Fraction
    traded_notional: Fraction
    proxy_wealth_ratio: Fraction
    proxy_fee_fraction: Fraction
    proxy_traded_notional: Fraction
    residual: Fraction
    bracket_low: Fraction
    bracket_high: Fraction
    iterations: int
    cost_rate: Fraction
    model: str
    evidence_kind: str=field(default=SYNTHETIC,init=False)
    protocol_status: str=field(default='DRAFT_NOT_FROZEN',init=False)
    performance_cleared: bool=field(default=False,init=False)

    @property
    def bracket_width(self):return self.bracket_high-self.bracket_low

    @property
    def root_error_bound(self):return self.bracket_width/2

    @property
    def wealth_ratio_difference(self):return self.wealth_ratio-self.proxy_wealth_ratio

    @property
    def proxy_feasible(self):return self.proxy_wealth_ratio>0

    def __repr__(self):
        return 'SyntheticFeeReference(values=redacted, certified_bracket=True, performance_cleared=False)'


def _result(x,volume,proxy_volume,cost,low,high,iterations,model):
    fee=cost*volume
    proxy_fee=cost*proxy_volume
    return FeeReference(x,fee,1-x,volume,1-proxy_fee,proxy_fee,proxy_volume,
                        x+fee-1,low,high,iterations,cost,model)


def exact_entry(cost_rate,*,evidence_kind):
    """Entry from cash: x invested, fee c*x, exact ratio x=1/(1+c)."""
    cost=_cost(cost_rate,evidence_kind)
    x=1/(1+cost)
    return _result(x,x,Fraction(1),cost,x,x,0,'exact_entry_from_cash')


def exact_rebalance(pretrade,target,cost_rate,*,evidence_kind,max_iterations=2048):
    """Certify a unique monotone root; no solver, observed returns or I/O.

    For normalized nonnegative p,t and 0<=c<1, F(0)=c-1<0, F(1)>=0.
    Its slope is bounded between 1-c and 1+c, so the root is unique. Rational
    bisection preserves a mathematical bracket without rounded-residual claims.
    Both retained wealth and the small wealth loss receive relative precision;
    if the bounded iteration budget cannot certify it, the function fails.
    """
    cost=_cost(cost_rate,evidence_kind)
    p,t=_weights(pretrade),_weights(target)
    _require(type(max_iterations) is int and 1<=max_iterations<=4096,'REFERENCE_ITERATION_BUDGET_REQUIRED')
    proxy_volume=sum(abs(a-b) for a,b in zip(t,p))
    def volume(x):return sum(abs(x*a-b) for a,b in zip(t,p))
    def equation(x):return x+cost*volume(x)-1
    if cost==0 or proxy_volume==0:
        return _result(Fraction(1),volume(Fraction(1)),proxy_volume,cost,
                       Fraction(1),Fraction(1),0,'exact_all_in_assets_rebalance')
    low,high=Fraction(0),Fraction(1)
    for iteration in range(1,max_iterations+1):
        mid=(low+high)/2
        residual=equation(mid)
        if residual==0:
            return _result(mid,volume(mid),proxy_volume,cost,mid,mid,iteration,'exact_all_in_assets_rebalance')
        if residual<0:
            low=mid
        else:
            high=mid
        width=high-low
        if (low>0 and high<1 and width<=ABSOLUTE_TOLERANCE
                and width<=RELATIVE_TOLERANCE*min(low,1-high)):
            mid=(low+high)/2
            return _result(mid,volume(mid),proxy_volume,cost,low,high,iteration,'exact_all_in_assets_rebalance')
    raise FeeReferenceError('ROOT_PRECISION_NOT_CERTIFIED')
