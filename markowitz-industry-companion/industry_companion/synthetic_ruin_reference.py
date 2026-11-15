"""Opt-in absorbing-zero alternative for invented fixtures; defaults unchanged.

This narrow reference supports a fixed initial allocation and natural drift,
not a strategy/optimizer or a replacement for the existing strict ledger.
Optional cost factors are abstract multiplicative stresses, not a fee model.
The whole provided panel is validated even when an earlier row causes ruin.
"""
from dataclasses import dataclass, field
import math
from numbers import Real

from .synthetic_accounting import (
    AccountingError, EQUAL, INDUSTRIES, _panel_dates, _weights, drift_weights,
)

SYNTHETIC = 'invented_synthetic_fixture'


class RuinReferenceError(ValueError):
    """Typed classification, never an offending value or detailed path."""
    def __init__(self, code):
        self.code=code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise RuinReferenceError(code)


def _scalar(value, code):
    _require(isinstance(value,Real) and not isinstance(value,bool),code)
    try:
        result=float(value)
    except OverflowError:
        raise RuinReferenceError('NUMERICAL_OVERFLOW_NOT_RUIN') from None
    except ValueError:
        raise RuinReferenceError(code) from None
    _require(math.isfinite(result),code)
    return result


def _sequence(values, code):
    try:
        return tuple(values)
    except TypeError:
        raise RuinReferenceError(code) from None


def _row(values):
    values=_sequence(values,'INVALID_RETURN_INPUT')
    _require(len(values)==10,'INVALID_RETURN_INPUT')
    # Check the supplied Real as well: Fraction(-1 +/- tiny) can convert to
    # float(-1) and must not manufacture a genuine loss or hide invalid input.
    _require(all(isinstance(value,Real) and not isinstance(value,bool) for value in values),
             'INVALID_RETURN_INPUT')
    _require(all(value>=-1 for value in values),'INVALID_RETURN_INPUT')
    row=tuple(_scalar(value,'INVALID_RETURN_INPUT') for value in values)
    _require(all(not(converted==-1 and original!=-1) for original,converted in zip(values,row)),
             'NUMERICAL_RETURN_PRECISION_NOT_RUIN')
    return row


def _positive_state(value):
    if not math.isfinite(value):
        raise RuinReferenceError('NUMERICAL_OVERFLOW_NOT_RUIN')
    if value<=0:
        raise RuinReferenceError('NUMERICAL_UNDERFLOW_NOT_RUIN')
    return value


@dataclass(frozen=True,repr=False)
class RuinMark:
    date: object
    wealth: float
    net_return: float | None
    weights: tuple | None
    state: str
    applied_cost_factor: float | None


@dataclass(frozen=True,repr=False)
class RuinLedger:
    marks: tuple=field(repr=False)
    initial_wealth: float
    ruin_date: object | None
    max_drawdown: float

    def __repr__(self):
        return f'SyntheticRuinReference(rows={len(self.marks)}, values=redacted, owner_review_pending=True)'

    def summary(self):
        absorbed=sum(mark.state=='ABSORBED_NO_RETURN' for mark in self.marks)
        ratio=self.marks[-1].wealth/self.initial_wealth
        _require(math.isfinite(ratio),'NUMERICAL_OVERFLOW_NOT_RUIN')
        return dict(evidence_kind='synthetic_absorbing_ruin_reference',
            decision_status='OWNER_REVIEW_PENDING',protocol_status='DRAFT_NOT_FROZEN',
            performance_cleared=False,point_in_time_verified=False,
            terminal_wealth=self.marks[-1].wealth,terminal_total_return=ratio-1,
            max_drawdown=self.max_drawdown,ruin_occurred=self.ruin_date is not None,
            ruin_date=self.ruin_date.isoformat() if self.ruin_date is not None else None,
            evaluation_sessions=len(self.marks),observed_return_sessions=len(self.marks)-absorbed,
            absorbed_sessions=absorbed,full_horizon_return_sequence_available=absorbed==0,
            annualized_sharpe=None,realized_volatility=None,
            daily_metric_reason=('NOT_REPORTED_ABSORBED_TAIL' if absorbed else
                                 'NOT_REPORTED_BY_TERMINAL_REFERENCE_POLICY'),
            geometric_annual_growth=None,growth_reason='NOT_REPORTED_BY_TERMINAL_REFERENCE_POLICY',
            trades_executed=0)


def absorbing_ruin_reference(*,calendar,dates,returns,evidence_kind,
                            initial_weights=EQUAL,initial_wealth=1.,cost_factors=None,
                            industry_order=INDUSTRIES):
    """Hold/drift invented assets; exact market extinction becomes absorbing zero.

    All supplied rows/factors are validated before any transition. Later valid
    rows are retained as absorbed dates with return/weights=None, never filled
    with fictitious zero returns. No ratio metric is calculated by this narrow
    reference: omission is an explicit policy, not mathematical undefinedness
    when the event happens on the last date. No files/network/source bridge.
    """
    _require(evidence_kind==SYNTHETIC,'EXPLICIT_INVENTED_FIXTURE_REQUIRED')
    try:
        dates=_panel_dates(calendar,dates)
    except (AccountingError,TypeError):
        raise RuinReferenceError('INVALID_DATE_GRID') from None
    _require(_sequence(industry_order,'STRICT_INDUSTRY_ORDER_REQUIRED')==INDUSTRIES,
             'STRICT_INDUSTRY_ORDER_REQUIRED')
    rows=_sequence(returns,'INVALID_RETURN_INPUT')
    _require(len(rows)==len(dates),'RETURN_DATE_LENGTH')
    rows=tuple(_row(row) for row in rows)
    raw_weights=_sequence(initial_weights,'INVALID_INITIAL_WEIGHTS')
    try:
        weights=_weights(raw_weights,capped=False)
    except (AccountingError,TypeError):
        raise RuinReferenceError('INVALID_INITIAL_WEIGHTS') from None
    _require(all(0<=value<=1 for value in raw_weights),'INVALID_INITIAL_WEIGHTS')
    _require(not any(original>0 and converted==0 for original,converted in zip(raw_weights,weights)),
             'NUMERICAL_UNDERFLOW_NOT_RUIN')
    _require(isinstance(initial_wealth,Real) and not isinstance(initial_wealth,bool)
             and initial_wealth>0,'INVALID_INITIAL_WEALTH')
    wealth=_scalar(initial_wealth,'INVALID_INITIAL_WEALTH')
    if initial_wealth>0 and wealth==0:
        raise RuinReferenceError('NUMERICAL_UNDERFLOW_NOT_RUIN')
    _require(wealth>0,'INVALID_INITIAL_WEALTH')
    initial=wealth
    factors=(1.,)*len(dates) if cost_factors is None else _sequence(cost_factors,'INVALID_COST_FACTOR')
    _require(len(factors)==len(dates),'COST_DATE_LENGTH')
    raw_factors=factors
    # Establish the original mathematical domain before conversion: a huge
    # finite negative return is invalid, while a valid huge positive return
    # can instead fail binary64 representation. Costs outside (0,1] are inputs.
    for original in raw_factors:
        _require(isinstance(original,Real) and not isinstance(original,bool),'INVALID_COST_FACTOR')
        if original==0:
            raise RuinReferenceError('COST_EXHAUSTION_NOT_RUIN')
        _require(0<original<=1,'INVALID_COST_FACTOR')
    factors=tuple(_scalar(factor,'INVALID_COST_FACTOR') for factor in raw_factors)
    for factor in factors:
        if factor==0:
            raise RuinReferenceError('NUMERICAL_UNDERFLOW_NOT_RUIN')
    marks=[]
    ruin_date=None
    peak=initial
    max_drawdown=0.
    for day,row,cost_factor in zip(dates,rows,factors):
        if ruin_date is not None:
            marks.append(RuinMark(day,0.,None,None,'ABSORBED_NO_RETURN',None))
            continue
        # Establish economic extinction from exact input/support, before any
        # floating multiplication can confuse a numerical zero with total loss.
        genuine=all(r==-1 for w,r in zip(weights,row) if w>0)
        if genuine:
            ruin_date=day
            wealth=0.
            weights=None
            max_drawdown=1.
            marks.append(RuinMark(day,0.,-1.,None,'RUIN_EVENT',None))
            continue
        assets=tuple(w*(1+r) for w,r in zip(weights,row))
        if any(w>0 and r>-1 and asset==0 for w,r,asset in zip(weights,row,assets)):
            raise RuinReferenceError('NUMERICAL_UNDERFLOW_NOT_RUIN')
        if not all(math.isfinite(asset) for asset in assets):
            raise RuinReferenceError('NUMERICAL_OVERFLOW_NOT_RUIN')
        try:
            gross=math.fsum(assets)
        except OverflowError:
            raise RuinReferenceError('NUMERICAL_OVERFLOW_NOT_RUIN') from None
        _positive_state(gross)
        if any(asset>0 and asset/gross==0 for asset in assets):
            raise RuinReferenceError('NUMERICAL_UNDERFLOW_NOT_RUIN')
        try:
            next_weights,gross,_adjustment=drift_weights(weights,row)
        except AccountingError:
            raise RuinReferenceError('NUMERICAL_WEIGHT_STATE_NOT_RUIN') from None
        before_cost=_positive_state(wealth*gross)
        wealth=_positive_state(before_cost*cost_factor)
        factor=_positive_state(gross*cost_factor)
        net=factor-1
        if not math.isclose(1+net,factor,rel_tol=1e-12,abs_tol=0):
            raise RuinReferenceError('NUMERICAL_RETURN_PRECISION_NOT_RUIN')
        weights=next_weights
        peak=max(peak,wealth)
        max_drawdown=max(max_drawdown,1-wealth/peak)
        marks.append(RuinMark(day,wealth,net,weights,'ACTIVE',cost_factor))
    return RuinLedger(tuple(marks),initial,ruin_date,max_drawdown)
