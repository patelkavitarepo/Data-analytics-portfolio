"""Invented accounting scenarios only: no French observations or fitted models.

Dates use a pinned local XNYS calendar solely for chronology. Every numeric
return and candidate score below is invented, including adversarial values.
"""
from dataclasses import replace
from datetime import date, datetime
from fractions import Fraction
import io
import itertools
import math
import random
import re
import statistics
import subprocess

import pytest

from industry_companion import synthetic_accounting as accounting
from industry_companion.audit import expected_sessions
from industry_companion.parser import INDUSTRIES


@pytest.fixture(scope='module')
def calendar():
    return accounting.CalendarGrid(
        tuple(expected_sessions()), date(2016, 1, 1), date(2024, 12, 31),
        name='XNYS', provenance='Pinned exchange-calendars 4.11.1; dates only; invented returns')


def toy_dates(calendar, start=date(2021, 1, 5), end=date(2021, 1, 7)):
    return tuple(day for day in calendar.sessions if start <= day <= end)


def zero_rows(dates):
    return tuple((0.,) * 10 for _ in dates)


def equal_schedule(calendar, dates):
    return tuple(accounting.make_instruction(calendar, d0, weights=accounting.EQUAL)
                 for d0 in accounting.required_decisions(calendar, dates))


def run(calendar, *, dates=None, returns=None, instructions=None, cost_rate=0., **kwargs):
    dates = toy_dates(calendar) if dates is None else tuple(dates)
    returns = zero_rows(dates) if returns is None else returns
    instructions = equal_schedule(calendar, dates) if instructions is None else tuple(instructions)
    return accounting.simulate(calendar=calendar, dates=dates, returns=returns,
        instructions=instructions, cost_rate=cost_rate,
        evidence_kind='invented_synthetic_fixture', **kwargs)


def illustrative_target(first=.35):
    return (first,) + ((1-first)/9,) * 9


def test_fixed_industry_order_and_synthetic_summary_labels(calendar):
    assert accounting.INDUSTRIES == INDUSTRIES and len(accounting.EQUAL) == 10
    summary = run(calendar).summary()
    assert summary['protocol_status'] == 'DRAFT_NOT_FROZEN'
    assert summary['performance_cleared'] is False and summary['point_in_time_verified'] is False
    assert 'synthetic' in summary['evidence_kind']
    assert all(key not in summary for key in ('returns', 'weights', 'days', 'wealth_path'))


def test_drift_is_not_daily_equal_reset(calendar):
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    ledger = run(calendar, dates=dates, returns=((1.,)+(0.,)*9, (.1,)+(0.,)*9))
    first, second = ledger.days
    assert first.gross_factor == pytest.approx(1.1)
    assert first.pretrade_weights[0] == pytest.approx(float(Fraction(2, 11)))
    assert first.end_weights == first.pretrade_weights
    assert second.start_weights == first.end_weights
    assert second.gross_factor == pytest.approx(float(Fraction(56, 55)))
    assert second.wealth == pytest.approx(1.12)
    assert second.wealth != pytest.approx(1.1*1.01)
    assert all(day.rebalance_q == 0 for day in ledger.days)


def test_first_2021_session_holds_old_weights_and_d2_earns_target(calendar):
    dates = (date(2021, 1, 4), date(2021, 1, 5))
    target = illustrative_target()
    instruction = accounting.make_instruction(calendar, date(2020, 12, 31), weights=target)
    ledger = run(calendar, dates=dates, returns=((1.,)+(0.,)*9, (1.,)+(0.,)*9),
                 instructions=(instruction,))
    d1, d2 = ledger.days
    assert instruction.d1 == dates[0] and instruction.d2 == dates[1]
    assert d1.start_weights == accounting.EQUAL
    assert d1.gross_factor == pytest.approx(1.1)
    assert d1.end_weights == target and d2.start_weights == target
    assert d2.gross_factor == pytest.approx(1.35)
    assert d2.wealth == pytest.approx(1.485)
    assert d1.target_executed and not d2.target_executed
    summary = ledger.summary()
    assert summary['max_target_weight'] == .35
    assert summary['max_target_concentration'] == pytest.approx(math.fsum(w*w for w in target))
    assert summary['min_target_effective_industry_count'] == pytest.approx(1/math.fsum(w*w for w in target))
    assert summary['max_weight'] > summary['max_target_weight']


def test_hand_calculated_monthly_q_and_close_cost(calendar):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 2))
    c = .0005
    ledger = run(calendar, dates=dates,
        returns=((0.,)*10, (1.,)+(0.,)*9, (0.,)*10), cost_rate=c)
    first, d1, d2 = ledger.days
    q = float(Fraction(9, 55))
    expected_close_fee = (1-c)*1.1*c*q
    expected_terminal = (1-c)*1.1*(1-c*q)
    assert first.entry_q == 1 and first.entry_fee == pytest.approx(c)
    assert d1.pretrade_weights[0] == pytest.approx(float(Fraction(2, 11)))
    assert d1.rebalance_q == pytest.approx(q)
    assert d1.rebalance_half_turnover == pytest.approx(q/2)
    assert d1.cost_fraction == pytest.approx(c*q)
    assert d1.rebalance_fee == pytest.approx(expected_close_fee, rel=2e-13, abs=1e-16)
    assert d1.net_factor == pytest.approx(1.1*(1-c*q))
    assert d1.end_weights == accounting.EQUAL
    assert d2.rebalance_q == d2.rebalance_fee == d2.entry_fee == 0
    assert d2.wealth == pytest.approx(expected_terminal, rel=2e-14, abs=1e-15)
    summary = ledger.summary()
    assert summary['total_rebalance_q'] == pytest.approx(q)
    assert summary['total_half_turnover'] == pytest.approx(q/2)
    assert summary['entry_traded_notional'] == 1 and summary['entry_half_turnover'] == .5


@pytest.mark.parametrize('c', [0., .0005, .0025])
def test_entry_cost_first_net_return_and_drawdown_reference(calendar, c):
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    ledger = run(calendar, dates=dates, cost_rate=c)
    first, second = ledger.days
    assert first.net_factor == pytest.approx(1-c)
    assert first.net_return == pytest.approx(-c)
    assert second.net_return == 0 and second.entry_q == 0
    assert second.wealth == pytest.approx(1-c)
    summary = ledger.summary()
    assert summary['terminal_wealth'] == pytest.approx(1-c)
    assert summary['max_drawdown'] == pytest.approx(c)
    assert summary['realized_volatility'] == pytest.approx(c/math.sqrt(2)*math.sqrt(252))
    assert summary['total_entry_fee'] == pytest.approx(c)


def test_cash_fees_are_not_terminal_wealth_gap(calendar):
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    ledger = run(calendar, dates=dates, returns=((0.,)*10, (.1,)*10), cost_rate=.01)
    fees = math.fsum(d.entry_fee+d.rebalance_fee for d in ledger.days)
    assert ledger.days[-1].wealth == pytest.approx(1.089)
    assert fees == pytest.approx(.01)
    assert 1.1-ledger.days[-1].wealth != pytest.approx(fees)
    assert 1+math.fsum(d.gross_pnl-d.entry_fee-d.rebalance_fee for d in ledger.days) == pytest.approx(1.089)


def test_same_entry_convention_for_equal_and_illustrative_targets(calendar):
    dates = (date(2021, 1, 4), date(2021, 1, 5))
    baseline = run(calendar, dates=dates, cost_rate=.0005)
    manual = run(calendar, dates=dates, cost_rate=.0005, instructions=(
        accounting.make_instruction(calendar, date(2020, 12, 31), weights=illustrative_target()),))
    assert baseline.days[0].entry_q == manual.days[0].entry_q == 1
    assert baseline.days[0].entry_fee == manual.days[0].entry_fee == .0005
    assert baseline.days[0].rebalance_q == 0
    assert manual.days[0].rebalance_q > 0


def test_final_d1_without_in_range_d2_has_no_terminal_trade(calendar):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 1))
    instruction = accounting.make_instruction(calendar, date(2021, 1, 29), weights=accounting.EQUAL)
    ledger = run(calendar, dates=dates, returns=((0.,)*10, (1.,)+(0.,)*9),
                 instructions=(instruction,), cost_rate=.0005)
    final = ledger.days[-1]
    assert final.end_weights[0] == pytest.approx(float(Fraction(2, 11)))
    assert final.rebalance_q == final.rebalance_fee == 0
    assert len(ledger.skipped_instructions) == 1


def test_final_2024_instruction_never_needs_2025(calendar):
    dates = toy_dates(calendar, date(2024, 12, 30), date(2024, 12, 31))
    instruction = accounting.make_instruction(calendar, date(2024, 12, 31), weights=accounting.EQUAL)
    assert instruction.d1 is instruction.d2 is None
    ledger = run(calendar, dates=dates, instructions=(instruction,), cost_rate=.0005)
    assert ledger.days[-1].rebalance_q == ledger.days[-1].rebalance_fee == 0
    assert ledger.days[-1].wealth == pytest.approx(.9995)
    assert len(ledger.skipped_instructions) == 1


@pytest.mark.parametrize('field,mutated', [
    ('d1', date(2021, 1, 29)), ('d1', date(2021, 2, 2)),
    ('d2', date(2021, 2, 1)), ('d2', date(2021, 2, 3)),
    ('information_cutoff', date(2021, 2, 1)),
])
def test_adversarial_same_day_and_off_by_one_instructions_fail(calendar, field, mutated):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 2))
    instruction = accounting.make_instruction(calendar, date(2021, 1, 29), weights=accounting.EQUAL)
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, instructions=(replace(instruction, **{field: mutated}),))


def test_monthly_instruction_cannot_be_missing_or_duplicate(calendar):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 2))
    instruction = accounting.make_instruction(calendar, date(2021, 1, 29), weights=accounting.EQUAL)
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, instructions=())
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, instructions=(instruction, instruction))


def test_partial_observed_month_does_not_become_month_end(calendar):
    dates = toy_dates(calendar, date(2021, 1, 26), date(2021, 1, 28))
    assert accounting.required_decisions(calendar, dates) == ()
    assert all(day.rebalance_q == 0 for day in run(calendar, dates=dates).days)
    with pytest.raises(accounting.AccountingError):
        accounting.make_instruction(calendar, date(2021, 1, 28), weights=accounting.EQUAL)


@pytest.mark.parametrize('reason', ['SOLVER_FAILED', 'INSUFFICIENT_SAMPLES', 'NO_VALID_CANDIDATE'])
def test_failed_instruction_falls_back_with_cost_and_flag(calendar, reason):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 2))
    instruction = accounting.make_instruction(calendar, date(2021, 1, 29), weights=None, failure_reason=reason)
    ledger = run(calendar, dates=dates, returns=((0.,)*10, (1.,)+(0.,)*9, (0.,)*10),
                 instructions=(instruction,), cost_rate=.0005)
    d1 = ledger.days[1]
    assert d1.used_fallback and d1.end_weights == accounting.EQUAL
    assert d1.rebalance_q == pytest.approx(float(Fraction(9, 55)))
    assert d1.rebalance_fee > 0 and ledger.summary()['fallback_count'] == 1
    assert d1.failure_reason == reason and d1.target_executed
    assert ledger.summary()['fallback_reasons'][reason] == 1
    assert sum(ledger.summary()['fallback_reasons'].values()) == 1


def test_skipped_failed_target_is_reported_without_executed_fallback(calendar):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 1))
    instruction = accounting.make_instruction(calendar, date(2021, 1, 29),
        weights=None, failure_reason='SOLVER_FAILED')
    ledger = run(calendar, dates=dates, instructions=(instruction,), cost_rate=.0005)
    summary = ledger.summary()
    assert summary['fallback_count'] == 0 and summary['skipped_failure_count'] == 1
    assert summary['fallback_reasons']['SOLVER_FAILED'] == 0
    assert all(not d.target_executed and d.rebalance_q == 0 for d in ledger.days)


@pytest.mark.parametrize('weights', [(1.,)+(0.,)*9, (-.1,)+(.1,)*8+(.3,),
    (0.,)*10, (.1,)*9+(.1000000000000001,), (.1,)*9,
    (float('nan'),)+(.1,)*9])
def test_invalid_targets_are_rejected_not_repaired_or_fallback(calendar, weights):
    with pytest.raises(accounting.AccountingError):
        instruction = accounting.make_instruction(calendar, date(2020, 12, 31), weights=weights)
        run(calendar, dates=(date(2021, 1, 4), date(2021, 1, 5)), instructions=(instruction,))


def test_drift_cap_can_exceed_target_cap_without_forced_trading(calendar):
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    ledger = run(calendar, dates=dates, returns=((0.,)+(-1.,)*9, (0.,)*10))
    first = ledger.days[0]
    assert first.end_weights == (1.,)+(0.,)*9
    assert first.drift_cap_exceeded and first.rebalance_q == 0
    assert ledger.summary()['drift_cap_exceedance_count'] >= 1


def test_concentration_and_effective_industry_counts_have_hand_oracles(calendar):
    equal = run(calendar).summary()
    assert equal['max_concentration'] == pytest.approx(.1)
    assert equal['min_effective_industry_count'] == pytest.approx(10.)
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    concentrated = run(calendar, dates=dates, returns=((0.,)+(-1.,)*9, (0.,)*10)).summary()
    assert concentrated['max_concentration'] == 1.
    assert concentrated['min_effective_industry_count'] == 1.
    assert concentrated['max_weight'] == 1.


def test_zero_turnover_fallback_stays_flagged_despite_equal_wealth(calendar):
    dates = (date(2021, 1, 4), date(2021, 1, 5))
    valid = run(calendar, dates=dates, cost_rate=.0005)
    failed = accounting.make_instruction(calendar, date(2020, 12, 31),
        weights=None, failure_reason='SOLVER_FAILED')
    fallback = run(calendar, dates=dates, instructions=(failed,), cost_rate=.0005)
    assert [d.wealth for d in fallback.days] == [d.wealth for d in valid.days]
    assert fallback.days[0].rebalance_q == fallback.days[0].rebalance_fee == 0
    assert fallback.days[0].used_fallback and not valid.days[0].used_fallback
    assert fallback.summary()['fallback_count'] == 1
    assert valid.summary()['fallback_count'] == 0


def test_future_returns_and_later_targets_cannot_change_earlier_ledger(calendar):
    dates = toy_dates(calendar, date(2021, 1, 5), date(2021, 3, 5))
    rows = zero_rows(dates)
    baseline = run(calendar, dates=dates, returns=rows, cost_rate=.0005)
    future_shock = tuple((.5,)*10 if d == date(2021, 2, 3) else row
                        for d, row in zip(dates, rows))
    shocked = run(calendar, dates=dates, returns=future_shock, cost_rate=.0005)
    assert tuple(d for d in baseline.days if d.date < date(2021, 2, 3)) == tuple(
        d for d in shocked.days if d.date < date(2021, 2, 3))
    later_instructions = tuple(accounting.make_instruction(calendar, d0,
        weights=illustrative_target() if d0 == date(2021, 2, 26) else accounting.EQUAL)
        for d0 in accounting.required_decisions(calendar, dates))
    later_target = run(calendar, dates=dates, returns=rows,
        instructions=later_instructions, cost_rate=.0005)
    assert tuple(d for d in baseline.days if d.date < date(2021, 3, 1)) == tuple(
        d for d in later_target.days if d.date < date(2021, 3, 1))
    d1_base = next(d for d in baseline.days if d.date == date(2021, 3, 1))
    d1_target = next(d for d in later_target.days if d.date == date(2021, 3, 1))
    assert d1_base.start_weights == d1_target.start_weights
    assert d1_base.gross_factor == d1_target.gross_factor
    assert d1_base.end_weights != d1_target.end_weights
    d2 = next(d for d in later_target.days if d.date == date(2021, 3, 2))
    assert d2.start_weights == illustrative_target()


def test_industry_total_loss_is_valid_if_portfolio_survives(calendar):
    ledger = run(calendar, dates=(date(2021, 1, 5),), returns=((-1.,)+(0.,)*9,))
    assert ledger.days[0].gross_factor == pytest.approx(.9)
    assert ledger.days[0].end_weights[0] == 0
    assert ledger.days[0].wealth == pytest.approx(.9)


@pytest.mark.parametrize('returns', [(-1.,)*10, (-1.0000001,)+(0.,)*9,
    (float('nan'),)+(0.,)*9, (float('inf'),)+(0.,)*9, (True,)+(0.,)*9,
    ('PRIVATEPOISON',)+(0.,)*9, (0.,)*9])
def test_invalid_or_extinct_return_state_fails_without_echo(calendar, returns):
    with pytest.raises(accounting.AccountingError) as error:
        run(calendar, dates=(date(2021, 1, 5),), returns=(returns,))
    assert re.fullmatch(r'[A-Z][A-Z0-9_]+', str(error.value))
    assert 'PRIVATEPOISON' not in str(error.value)


def test_near_total_loss_remains_valid_without_rounding_to_zero(calendar):
    r = -1.+2**-52
    ledger = run(calendar, dates=(date(2021, 1, 5),), returns=((r,)*10,))
    assert ledger.days[0].wealth > 0
    assert ledger.days[0].gross_factor == pytest.approx(2**-52)


def test_nonfinite_wealth_fails_closed(calendar):
    dates = toy_dates(calendar, end=date(2021, 1, 6))
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, returns=((1e308,)*10, (1e308,)*10))


def test_positive_wealth_underflow_fails_instead_of_fabricating_weights(calendar):
    dates = toy_dates(calendar, date(2021, 1, 5), date(2021, 2, 5))
    almost_wiped_out = -1.+2**-52
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, returns=((almost_wiped_out,)*10,)*len(dates))


def test_exhausted_close_cost_fails_closed(calendar):
    dates = toy_dates(calendar, date(2021, 1, 29), date(2021, 2, 2))
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, returns=((0.,)*10, (0.,)+(-1.,)*9, (0.,)*10), cost_rate=.8)


@pytest.mark.parametrize('c', [-.0001, 1., float('nan'), float('inf'), True])
def test_cost_rate_validation(calendar, c):
    with pytest.raises(accounting.AccountingError):
        run(calendar, cost_rate=c)


@pytest.mark.parametrize('dates', [
    (date(2021, 1, 5), date(2021, 1, 5)),
    (date(2021, 1, 6), date(2021, 1, 5)),
    (date(2021, 1, 5), date(2021, 1, 7)),
    (date(2021, 1, 9),), (datetime(2021, 1, 5),), (),
])
def test_date_grid_is_strict_and_has_no_missing_or_invented_sessions(calendar, dates):
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=dates, instructions=())


def test_post_2024_dates_fail_before_return_access(calendar):
    class Poison:
        def __iter__(self): raise AssertionError('Prospective return tokens accessed')
        def __len__(self): raise AssertionError('Prospective return tokens accessed')
    with pytest.raises(accounting.AccountingError):
        run(calendar, dates=(date(2025, 1, 2),), returns=Poison(), instructions=())


@pytest.mark.parametrize('order', [INDUSTRIES[::-1], INDUSTRIES[:-1], ('Other',)*10])
def test_industry_order_is_fixed(calendar, order):
    with pytest.raises(accounting.AccountingError):
        run(calendar, industry_order=order)


def test_synthetic_attestation_required(calendar):
    with pytest.raises(accounting.AccountingError):
        accounting.simulate(calendar=calendar, dates=toy_dates(calendar),
            returns=zero_rows(toy_dates(calendar)), instructions=(), evidence_kind='historical_market')


@pytest.mark.parametrize('weights,reason', [(None, None), (accounting.EQUAL, 'SOLVER_FAILED'),
    (None, 'PRIVATEPOISON')])
def test_inconsistent_or_unrecognized_failure_instruction_is_not_silent(calendar, weights, reason):
    with pytest.raises(accounting.AccountingError) as error:
        instruction = accounting.make_instruction(calendar, date(2020, 12, 31),
            weights=weights, failure_reason=reason)
        run(calendar, dates=(date(2021, 1, 4), date(2021, 1, 5)), instructions=(instruction,))
    assert 'PRIVATEPOISON' not in str(error.value)


@pytest.mark.parametrize('reason', [['PRIVATEPOISON'], {'PRIVATEPOISON': True}])
def test_unhashable_failure_reason_has_safe_typed_error(calendar, reason):
    with pytest.raises(accounting.AccountingError) as constructor_error:
        accounting.make_instruction(calendar, date(2020, 12, 31), weights=None, failure_reason=reason)
    instruction = accounting.make_instruction(calendar, date(2020, 12, 31),
        weights=None, failure_reason='SOLVER_FAILED')
    with pytest.raises(accounting.AccountingError) as simulation_error:
        run(calendar, dates=(date(2021, 1, 4), date(2021, 1, 5)),
            instructions=(replace(instruction, failure_reason=reason),))
    for error in (constructor_error, simulation_error):
        assert re.fullmatch(r'[A-Z][A-Z0-9_]+', str(error.value))
        assert 'PRIVATEPOISON' not in str(error.value)


def test_standalone_drift_has_budget_identity_without_target_cap_repair():
    drifted, factor, residual = accounting.drift_weights(accounting.EQUAL, (0.,)+(-1.,)*9)
    assert factor == pytest.approx(.1)
    assert drifted == (1.,)+(0.,)*9 and math.fsum(drifted) == 1
    assert abs(residual) <= 1e-14


@pytest.mark.parametrize('rf', [-1., -2., float('nan'), float('inf'), True])
def test_risk_free_is_one_finite_effective_annual_scalar(calendar, rf):
    with pytest.raises(accounting.AccountingError):
        run(calendar).summary(rf_annual=rf)


def test_metrics_use_sample_sd_constant_effective_rf_and_net_path(calendar):
    dates = toy_dates(calendar)
    ledger = run(calendar, dates=dates, returns=((.01,)*10, (-.02,)*10, (.03,)*10), cost_rate=.0005)
    net = [day.net_return for day in ledger.days]
    summary = ledger.summary(rf_annual=.02)
    rf = (1.02)**(1/252)-1
    sd = statistics.stdev(net)
    expected_sharpe = math.sqrt(252)*(statistics.mean(net)-rf)/sd
    assert summary['rf_daily'] == pytest.approx(rf, abs=2e-16)
    assert summary['realized_volatility'] == pytest.approx(sd*math.sqrt(252))
    assert summary['annualized_sharpe'] == pytest.approx(expected_sharpe)
    expected_wealth = (1-.0005)*1.01*.98*1.03
    assert summary['terminal_wealth'] == pytest.approx(expected_wealth)
    assert summary['geometric_annual_growth'] == pytest.approx(expected_wealth**(252/3)-1)
    zero_rf = ledger.summary(rf_annual=0.)
    assert zero_rf['terminal_wealth'] == summary['terminal_wealth']
    assert zero_rf['realized_volatility'] == summary['realized_volatility']
    assert zero_rf['annualized_sharpe'] > summary['annualized_sharpe']


def test_undefined_metrics_are_none_with_reason(calendar):
    one = run(calendar, dates=(date(2021, 1, 5),)).summary()
    assert one['realized_volatility'] is None and one['volatility_reason']
    assert one['annualized_sharpe'] is None and one['sharpe_reason']
    constant = run(calendar).summary()
    assert constant['realized_volatility'] == 0
    assert constant['annualized_sharpe'] is None and constant['sharpe_reason']


@pytest.mark.parametrize('seed', [7, 29, 101, 313, 2026])
@pytest.mark.parametrize('c', [0., .0005, .0025])
def test_deterministic_invariants_budget_wealth_and_cash_reconciliation(calendar, seed, c):
    rng = random.Random(seed)
    dates = toy_dates(calendar, date(2021, 1, 5), date(2021, 3, 5))
    rows = tuple(tuple(rng.uniform(-.4, .7) for _ in range(10)) for _ in dates)
    ledger = run(calendar, dates=dates, returns=rows, cost_rate=c)
    repeat = run(calendar, dates=dates, returns=rows, cost_rate=c)
    assert ledger.days == repeat.days
    for day in ledger.days:
        assert math.fsum(day.start_weights) == pytest.approx(1., abs=1e-15)
        assert math.fsum(day.pretrade_weights) == pytest.approx(1., abs=1e-15)
        assert math.fsum(day.end_weights) == pytest.approx(1., abs=1e-15)
        assert all(w >= 0 for w in day.end_weights)
        assert abs(day.roundoff_adjustment) <= 1e-14
        assert day.net_factor == pytest.approx(1+day.net_return, rel=2e-15)
    terminal = ledger.days[-1].wealth
    assert math.prod(day.net_factor for day in ledger.days) == pytest.approx(terminal, rel=2e-13)
    assert 1+math.fsum(d.gross_pnl-d.entry_fee-d.rebalance_fee for d in ledger.days) == pytest.approx(terminal, rel=2e-13)
    assert ledger.summary()['terminal_wealth'] == terminal


def test_engine_has_no_io_output_or_input_mutation(calendar, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    rows = [[0.] * 10 for _ in toy_dates(calendar)]
    original = [row[:] for row in rows]
    def forbidden(*args, **kwargs): raise AssertionError('Pure accounting performed I/O')
    monkeypatch.setattr(io, 'open', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    ledger = run(calendar, returns=rows)
    ledger.summary()
    assert rows == original and list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ('', '')
    assert 'redacted' in repr(ledger).casefold()
    assert '[0.' not in repr(ledger.days[0])


def test_predeclared_candidate_tie_break_is_global_not_chained():
    a = accounting.ScoredCandidate(illustrative_target(.35), 1.)
    b = accounting.ScoredCandidate(illustrative_target(.2), 1.-.75e-10)
    c = accounting.ScoredCandidate(accounting.EQUAL, 1.-1.5e-10)
    for candidates in itertools.permutations((a, b, c)):
        chosen = accounting.select_predeclared_target(candidates, objective='local_sharpe')
        assert chosen.weights == b.weights and not chosen.used_fallback


def test_tie_prefers_equal_distance_then_lexicographic_order():
    a_weights = (.2, 0.)+(.1,)*8
    b_weights = (0., .2)+(.1,)*8
    a = accounting.ScoredCandidate(a_weights, 2.)
    b = accounting.ScoredCandidate(b_weights, 2.)
    chosen = accounting.select_predeclared_target((a, b), objective='local_sharpe')
    assert chosen.weights == b_weights
    equal = accounting.ScoredCandidate(accounting.EQUAL, 2.)
    assert accounting.select_predeclared_target((a, b, equal), objective='local_sharpe').weights == accounting.EQUAL


def test_manual_candidate_minimum_and_maximum_objectives_are_distinct():
    low = accounting.ScoredCandidate(accounting.EQUAL, 1.)
    high = accounting.ScoredCandidate(illustrative_target(), 3.)
    assert accounting.select_predeclared_target((low, high), objective='min_variance').weights == low.weights
    assert accounting.select_predeclared_target((low, high), objective='local_sharpe').weights == high.weights


@pytest.mark.parametrize('score', [0., -1.])
def test_nonpositive_variance_score_is_not_a_valid_manual_candidate(score):
    candidate = accounting.ScoredCandidate(illustrative_target(), score)
    chosen = accounting.select_predeclared_target((candidate,), objective='min_variance')
    assert chosen.weights == accounting.EQUAL and chosen.used_fallback


def test_zero_sharpe_score_is_valid_when_variance_validity_is_declared():
    candidate = accounting.ScoredCandidate(illustrative_target(), 0., valid=True)
    chosen = accounting.select_predeclared_target((candidate,), objective='local_sharpe')
    assert chosen.weights == candidate.weights and not chosen.used_fallback


@pytest.mark.parametrize('candidates', [(),
    (accounting.ScoredCandidate(accounting.EQUAL, 1., valid=False),),
    (accounting.ScoredCandidate(accounting.EQUAL, float('nan')),),
    (accounting.ScoredCandidate((1.,)+(0.,)*9, 10.),),
])
def test_no_valid_manual_candidate_flags_equal_fallback(candidates):
    chosen = accounting.select_predeclared_target(candidates, objective='local_sharpe')
    assert chosen.weights == accounting.EQUAL and chosen.used_fallback and chosen.reason
