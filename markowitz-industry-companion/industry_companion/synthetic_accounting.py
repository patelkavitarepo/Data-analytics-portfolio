"""Pure accounting mechanics for explicitly invented fixtures, not market evidence.

No loader, optimizer, CLI, networking, files or source-parser integration exists.
Calendar provenance and synthetic origin are caller assertions, not independent
verification. Candidate conventions remain DRAFT_NOT_FROZEN.
"""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
import math
from numbers import Real
import statistics
from types import MappingProxyType

INDUSTRIES = ('NoDur', 'Durbl', 'Manuf', 'Enrgy', 'HiTec', 'Telcm', 'Shops', 'Hlth', 'Utils', 'Other')
EQUAL = (0.1,) * 10
START, END = date(2016, 1, 1), date(2024, 12, 31)
CAP, CAP_EPS, ROUND_EPS, TIE_EPS = 0.35, 1e-12, 1e-14, 1e-10
SYNTHETIC = 'invented_synthetic_fixture'
FAILURES = {'SOLVER_FAILED', 'INSUFFICIENT_HISTORY', 'INSUFFICIENT_SAMPLES', 'NO_VALID_CANDIDATE'}


class AccountingError(ValueError):
    """Stable code only, never source values or private ledger contents."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise AccountingError(code)


def _number(value):
    _require(isinstance(value, Real) and not isinstance(value, bool), 'FINITE_NUMBER_REQUIRED')
    try:
        value = float(value)
    except (ValueError, OverflowError):
        raise AccountingError('FINITE_NUMBER_REQUIRED') from None
    _require(math.isfinite(value), 'FINITE_NUMBER_REQUIRED')
    return value


def _finite_sum(values):
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError):
        raise AccountingError('NONFINITE_AGGREGATE_METRIC') from None
    _require(math.isfinite(result), 'NONFINITE_AGGREGATE_METRIC')
    return result


def _day(value):
    _require(type(value) is date and START <= value <= END, 'DEVELOPMENT_DATE_REQUIRED')
    return value


@dataclass(frozen=True, repr=False)
class CalendarGrid:
    sessions: tuple
    coverage_start: date
    coverage_end: date
    name: str = 'XNYS'
    provenance: str = ''
    _ends: tuple = field(init=False, repr=False)
    _positions: object = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        _day(self.coverage_start); _day(self.coverage_end)
        _require(self.coverage_start <= self.coverage_end, 'CALENDAR_COVERAGE')
        _require(self.name == 'XNYS' and isinstance(self.provenance, str) and bool(self.provenance.strip()), 'CALENDAR_PROVENANCE_REQUIRED')
        sessions = tuple(self.sessions)
        _require(bool(sessions), 'EMPTY_CALENDAR')
        for d in sessions:
            _day(d)
            _require(self.coverage_start <= d <= self.coverage_end and d.weekday() < 5, 'CALENDAR_SESSION')
        _require(all(a < b for a, b in zip(sessions, sessions[1:])), 'CALENDAR_CHRONOLOGY')
        object.__setattr__(self, 'sessions', sessions)
        ends = {}
        for d in sessions:
            first = date(d.year, d.month, 1)
            last = date(d.year, d.month, monthrange(d.year, d.month)[1])
            if self.coverage_start <= first and self.coverage_end >= last:
                ends[d.year, d.month] = d
        object.__setattr__(self, '_ends', tuple(ends.values()))
        object.__setattr__(self, '_positions', MappingProxyType({d: i for i, d in enumerate(sessions)}))

    def __repr__(self):
        return 'ExplicitCalendarGrid(name=XNYS, independently_verified=False)'


def _panel_dates(calendar, dates):
    _require(isinstance(calendar, CalendarGrid), 'EXPLICIT_CALENDAR_REQUIRED')
    dates = tuple(dates)
    _require(bool(dates), 'EMPTY_EVALUATION')
    for d in dates:
        _day(d)  # All date/scope checks precede touching return tokens.
    _require(all(a < b for a, b in zip(dates, dates[1:])), 'PANEL_CHRONOLOGY')
    expected = tuple(d for d in calendar.sessions if dates[0] <= d <= dates[-1])
    _require(dates == expected, 'MISSING_OR_NON_SESSION_DATE')
    return dates


def _month_ends(calendar):
    return calendar._ends


def _lag(calendar, d0):
    _day(d0)
    _require(d0 in _month_ends(calendar), 'COMPLETE_MONTH_END_REQUIRED')
    i = calendar._positions[d0]
    d1 = calendar.sessions[i + 1] if i + 1 < len(calendar.sessions) else None
    d2 = calendar.sessions[i + 2] if i + 2 < len(calendar.sessions) else None
    return d1, d2


def required_decisions(calendar, dates):
    dates = _panel_dates(calendar, dates)
    result = []
    for d0 in _month_ends(calendar):
        d1, d2 = _lag(calendar, d0)
        if d1 is not None and d2 is not None and dates[0] <= d1 and d2 <= dates[-1]:
            result.append(d0)
    return tuple(result)


def _weights(values, *, capped):
    values = tuple(_number(v) for v in values)
    _require(len(values) == 10 and all(0 <= w <= (CAP if capped else 1) for w in values), 'INVALID_WEIGHT_BOUNDS')
    # Accounting does not silently repair optimizer output accepted at 1e-8.
    _require(math.fsum(values) == 1.0, 'EXACT_WEIGHT_BUDGET_REQUIRED')
    return values


def _returns(values):
    values = tuple(_number(v) for v in values)
    _require(len(values) == 10 and all(r >= -1 for r in values), 'INVALID_SIMPLE_RETURNS')
    return values


@dataclass(frozen=True, repr=False)
class TargetInstruction:
    d0: date
    d1: date | None
    d2: date | None
    information_cutoff: date
    weights: tuple | None
    failure_reason: str | None = None


def make_instruction(calendar, d0, *, weights=EQUAL, failure_reason=None):
    d1, d2 = _lag(calendar, d0)
    if weights is None:
        _require(isinstance(failure_reason, str) and failure_reason in FAILURES, 'DECLARED_FAILURE_REQUIRED')
    else:
        _require(failure_reason is None, 'CONTRADICTORY_TARGET_INSTRUCTION')
        weights = _weights(weights, capped=True)
    return TargetInstruction(d0, d1, d2, d0, weights, failure_reason)


@dataclass(frozen=True, repr=False)
class ScoredCandidate:
    weights: tuple
    score: float
    valid: bool = True


@dataclass(frozen=True, repr=False)
class TargetChoice:
    weights: tuple
    used_fallback: bool
    reason: str | None


def select_predeclared_target(candidates, *, objective='local_sharpe'):
    """Tie-rule test using supplied invented scores; never fit or solve anything."""
    _require(objective in ('local_sharpe', 'min_variance'), 'UNKNOWN_OBJECTIVE')
    valid = []
    for candidate in candidates:
        _require(isinstance(candidate, ScoredCandidate), 'CANDIDATE_REQUIRED')
        if candidate.valid is not True:
            continue
        try:
            w = _weights(candidate.weights, capped=True)
            score = _number(candidate.score)
            if objective == 'min_variance' and score <= 0:
                continue
            valid.append((score, w))
        except AccountingError:
            continue
    if not valid:
        return TargetChoice(EQUAL, True, 'NO_VALID_CANDIDATE')
    best = (max if objective == 'local_sharpe' else min)(score for score, _ in valid)
    pool = [w for score, w in valid if abs(score - best) <= TIE_EPS]
    chosen = min(pool, key=lambda w: (math.fsum((v - 0.1) ** 2 for v in w), w))
    return TargetChoice(chosen, False, None)


def drift_weights(weights, returns):
    weights, returns = _weights(weights, capped=False), _returns(returns)
    if all(r == returns[0] for r in returns):
        gross = 1 + returns[0]
        _require(gross > 0, 'PORTFOLIO_DEPLETED_OR_NONFINITE')
        return weights, gross, 0.0  # Exact common factors cannot change allocation.
    assets = tuple(w * (1 + r) for w, r in zip(weights, returns))
    try:
        gross = math.fsum(assets)
    except OverflowError:
        raise AccountingError('NONFINITE_ACCOUNTING_STATE') from None
    _require(math.isfinite(gross) and gross > 0, 'PORTFOLIO_DEPLETED_OR_NONFINITE')
    drifted = [v / gross for v in assets]
    # Normalize ratios only; never alter a supplied target. Assign roundoff to
    # the largest holding (lowest index on ties), recording the tiny adjustment.
    largest = max(range(10), key=lambda i: drifted[i])
    before = drifted[largest]
    if math.fsum(drifted) != 1.0:
        drifted[largest] = 1.0 - math.fsum(v for i, v in enumerate(drifted) if i != largest)
        # The rounded sum of the other nine is itself inexact. Move at most a
        # few ULPs so the correctly rounded full sum is exactly the unit budget.
        for _ in range(8):
            total = math.fsum(drifted)
            if total == 1.0:
                break
            drifted[largest] = math.nextafter(drifted[largest], math.inf if total < 1.0 else 0.0)
    adjustment = drifted[largest] - before
    _require(abs(adjustment) <= ROUND_EPS and math.fsum(drifted) == 1.0,
             'UNREPRESENTABLE_WEIGHT_BUDGET')
    return _weights(drifted, capped=False), gross, adjustment


@dataclass(frozen=True, repr=False)
class TrainingWindow:
    window_start: date
    window_end: date
    dates: tuple
    sufficient: bool
    reason: str | None


def has_minimum_samples(count):
    _require(type(count) is int and count >= 0, 'OBSERVATION_COUNT_REQUIRED')
    return count >= 1000


def training_window(calendar, available_dates, d0):
    """Date selection only: 60 complete calendar months, no return fitting."""
    dates = _panel_dates(calendar, available_dates)
    _lag(calendar, d0)
    _require(d0 in dates, 'MISSING_TRAINING_CUTOFF')
    index = d0.year * 12 + d0.month - 1 - 59
    year, month = divmod(index, 12)
    first = date(year, month + 1, 1)
    selected = tuple(d for d in dates if first <= d <= d0)
    if first < START or first < calendar.coverage_start:
        return TrainingWindow(first, d0, selected, False, 'INSUFFICIENT_HISTORY')
    expected = tuple(d for d in calendar.sessions if first <= d <= d0)
    if not selected or selected[0] != expected[0]:
        return TrainingWindow(first, d0, selected, False, 'INSUFFICIENT_HISTORY')
    _require(selected == expected, 'INCOMPLETE_TRAINING_WINDOW')
    sufficient = has_minimum_samples(len(selected))
    return TrainingWindow(first, d0, selected, sufficient, None if sufficient else 'INSUFFICIENT_SAMPLES')


@dataclass(frozen=True, repr=False)
class DayState:
    date: date
    start_weights: tuple
    pretrade_weights: tuple
    end_weights: tuple
    gross_factor: float
    gross_return: float
    net_factor: float
    net_return: float
    wealth: float
    entry_q: float
    entry_fee: float
    rebalance_q: float
    rebalance_half_turnover: float
    rebalance_fee: float
    cost_fraction: float
    gross_pnl: float
    used_fallback: bool
    drift_cap_exceeded: bool
    roundoff_adjustment: float
    target_executed: bool
    failure_reason: str | None


@dataclass(frozen=True, repr=False)
class SkippedInstruction:
    d0: date
    reason: str = 'NO_IN_RANGE_EFFECTIVE_SESSION'
    failure_reason: str | None = None


@dataclass(frozen=True, repr=False)
class Ledger:
    days: tuple = field(repr=False)
    skipped_instructions: tuple = field(repr=False)
    cost_rate: float

    def __repr__(self):
        return f'InventedAccountingLedger(rows={len(self.days)}, values=redacted, performance_cleared=False)'

    def summary(self, *, rf_annual=0.02):
        rf = _number(rf_annual)
        _require(rf > -1, 'INVALID_RISK_FREE_ASSUMPTION')
        rf_daily = math.expm1(math.log1p(rf) / 252)
        returns = tuple(d.net_return for d in self.days)
        n = len(returns)
        volatility = sharpe = None
        vol_reason = sharpe_reason = 'INSUFFICIENT_OBSERVATIONS'
        if n >= 2:
            try:
                sd = statistics.stdev(returns)
                volatility = sd * math.sqrt(252)
                _require(math.isfinite(volatility), 'METRIC_OVERFLOW')
                vol_reason = None
                if sd == 0:
                    sharpe_reason = 'ZERO_SAMPLE_VOLATILITY'
                else:
                    sharpe = math.sqrt(252) * (math.fsum(returns) / n - rf_daily) / sd
                    _require(math.isfinite(sharpe), 'METRIC_OVERFLOW')
                    sharpe_reason = None
            except (AccountingError, OverflowError):
                volatility = sharpe = None
                vol_reason = sharpe_reason = 'NUMERICAL_OVERFLOW'
        try:
            growth = math.expm1(math.log(self.days[-1].wealth) * 252 / n)
            _require(math.isfinite(growth), 'METRIC_OVERFLOW')
            growth_reason = None
        except (AccountingError, OverflowError):
            growth, growth_reason = None, 'NUMERICAL_OVERFLOW'
        peak, drawdown = 1.0, 0.0
        for d in self.days:
            peak = max(peak, d.wealth)
            drawdown = max(drawdown, 1 - d.wealth / peak)
        concentrations = tuple(math.fsum(w*w for w in d.pretrade_weights) for d in self.days)
        targets = (EQUAL,) + tuple(d.end_weights for d in self.days if d.target_executed)
        target_concentrations = tuple(math.fsum(w*w for w in target) for target in targets)
        return dict(evidence_kind='synthetic_accounting_validation', protocol_status='DRAFT_NOT_FROZEN',
                    performance_cleared=False, point_in_time_verified=False, sessions=n,
                    terminal_wealth=self.days[-1].wealth, max_drawdown=drawdown,
                    realized_volatility=volatility, volatility_reason=vol_reason,
                    annualized_sharpe=sharpe, sharpe_reason=sharpe_reason,
                    geometric_annual_growth=growth, growth_reason=growth_reason,
                    rf_annual=rf, rf_daily=rf_daily, cost_rate=self.cost_rate,
                    total_entry_fee=_finite_sum(d.entry_fee for d in self.days),
                    total_rebalance_fee=_finite_sum(d.rebalance_fee for d in self.days),
                    total_rebalance_q=_finite_sum(d.rebalance_q for d in self.days),
                    total_half_turnover=_finite_sum(d.rebalance_half_turnover for d in self.days),
                    entry_traded_notional=1.0, entry_half_turnover=0.5,
                    fallback_count=sum(d.used_fallback for d in self.days),
                    fallback_reasons={reason: sum(d.failure_reason == reason for d in self.days)
                                      for reason in sorted(FAILURES)},
                    skipped_failure_count=sum(d.failure_reason is not None for d in self.skipped_instructions),
                    drift_cap_exceedance_count=sum(d.drift_cap_exceeded for d in self.days),
                    skipped_instruction_count=len(self.skipped_instructions),
                    max_weight=max(max(d.pretrade_weights) for d in self.days),
                    max_concentration=max(concentrations),
                    min_effective_industry_count=min(1/h for h in concentrations),
                    max_target_weight=max(max(target) for target in targets),
                    max_target_concentration=max(target_concentrations),
                    min_target_effective_industry_count=min(1/h for h in target_concentrations),
                    max_roundoff_adjustment=max(abs(d.roundoff_adjustment) for d in self.days))


def simulate(*, calendar, dates, returns, instructions, evidence_kind,
             cost_rate=0.0005, industry_order=INDUSTRIES):
    """Invented paths only. Private ledger is deliberately absent from any CLI."""
    _require(evidence_kind == SYNTHETIC, 'EXPLICIT_INVENTED_FIXTURE_REQUIRED')
    dates = _panel_dates(calendar, dates)
    _require(tuple(industry_order) == INDUSTRIES, 'STRICT_INDUSTRY_ORDER_REQUIRED')
    cost = _number(cost_rate)
    _require(0 <= cost < 1, 'INVALID_COST_RATE')
    rows = tuple(returns)
    _require(len(rows) == len(dates), 'RETURN_DATE_LENGTH')
    rows = tuple(_returns(row) for row in rows)
    instructions = tuple(instructions)
    decisions, execution, skipped = [], {}, []
    for instruction in instructions:
        _require(isinstance(instruction, TargetInstruction), 'TARGET_INSTRUCTION_REQUIRED')
        d1, d2 = _lag(calendar, instruction.d0)
        _require((instruction.d1, instruction.d2) == (d1, d2)
                 and instruction.information_cutoff == instruction.d0, 'INVALID_EXECUTION_CHRONOLOGY')
        _require(not decisions or decisions[-1] < instruction.d0, 'DUPLICATE_OR_UNORDERED_INSTRUCTION')
        decisions.append(instruction.d0)
        if instruction.weights is None:
            _require(isinstance(instruction.failure_reason, str) and instruction.failure_reason in FAILURES, 'DECLARED_FAILURE_REQUIRED')
            target = EQUAL
        else:
            _require(instruction.failure_reason is None, 'CONTRADICTORY_TARGET_INSTRUCTION')
            target = _weights(instruction.weights, capped=True)
        _require(instruction.d0 <= dates[-1] and (d1 is None or d1 >= dates[0]), 'OUTSIDE_EVALUATION_INSTRUCTION')
        if d2 is None or d2 > dates[-1]:
            skipped.append(SkippedInstruction(instruction.d0, failure_reason=instruction.failure_reason))
        else:
            _require(d1 in dates and d2 in dates, 'INVALID_EXECUTION_CHRONOLOGY')
            execution[d1] = (target, instruction.weights is None, instruction.failure_reason)
    _require(set(required_decisions(calendar, dates)) <= set(decisions), 'MISSING_MONTHLY_INSTRUCTION')
    days, wealth, weights = [], 1.0, EQUAL
    for i, (day, row) in enumerate(zip(dates, rows)):
        start = weights
        pretrade, gross, adjustment = drift_weights(start, row)
        entry_fee = cost if i == 0 else 0.0
        base = wealth - entry_fee
        before_fee = base * gross
        target, failed, failure_reason = execution.get(day, (None, False, None))
        q = math.fsum(abs(a - b) for a, b in zip(target, pretrade)) if target is not None else 0.0
        fraction = cost * q
        _require(fraction < 1, 'TRANSACTION_COST_EXHAUSTS_WEALTH')
        close_fee = before_fee * fraction
        factor = (1 - cost if i == 0 else 1.0) * gross * (1 - fraction)
        net_return = factor - 1
        next_wealth = before_fee * (1 - fraction)
        _require(all(math.isfinite(v) and v > 0 for v in (base, before_fee, factor, next_wealth)),
                 'NONFINITE_OR_DEPLETED_WEALTH')
        _require(math.isclose(1 + net_return, factor, rel_tol=1e-12, abs_tol=0), 'UNREPRESENTABLE_NET_RETURN')
        days.append(DayState(day, start, pretrade, target if target is not None else pretrade,
                             gross, gross - 1, factor, net_return, next_wealth,
                             1.0 if i == 0 else 0.0, entry_fee, q, q / 2, close_fee,
                             fraction, base * (gross - 1), failed,
                             any(w > CAP + CAP_EPS for w in pretrade), adjustment,
                             target is not None, failure_reason))
        wealth, weights = next_wealth, days[-1].end_weights
    return Ledger(tuple(days), tuple(skipped), cost)
