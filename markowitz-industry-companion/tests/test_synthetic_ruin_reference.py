"""Invented loss/ruin controls only; no historical observations or trade fit."""
from datetime import date, datetime
from fractions import Fraction
import io
import math
import subprocess

import pytest

from industry_companion.audit import expected_sessions
from industry_companion.synthetic_accounting import AccountingError, CalendarGrid, simulate
from industry_companion import synthetic_ruin_reference as ruin


@pytest.fixture(scope='module')
def calendar():
    return CalendarGrid(expected_sessions(), date(2016, 1, 1), date(2024, 12, 31),
                        provenance='Pinned XNYS calendar dates only; invented ruin fixtures')


DATES = (date(2021, 1, 5), date(2021, 1, 6), date(2021, 1, 7))
SYNTHETIC = 'invented_synthetic_fixture'


def run(calendar, rows, **kwargs):
    dates = kwargs.pop('dates', DATES[:len(rows)])
    return ruin.absorbing_ruin_reference(calendar=calendar, dates=dates,
        returns=rows, evidence_kind=SYNTHETIC, **kwargs)


def test_exact_ruin_is_an_adverse_absorbing_outcome(calendar):
    ledger = run(calendar, ((.1,) * 10, (-1.,) * 10, (100.,) * 10))
    before, event, after = ledger.marks
    assert before.wealth == pytest.approx(1.1) and before.state == 'ACTIVE'
    assert event.wealth == 0 and event.net_return == -1 and event.weights is None
    assert event.state == 'RUIN_EVENT'
    assert after.wealth == 0 and after.net_return is None and after.weights is None
    assert after.state == 'ABSORBED_NO_RETURN'
    assert after.applied_cost_factor is None
    summary = ledger.summary()
    assert summary['terminal_wealth'] == 0 and summary['max_drawdown'] == 1
    assert summary['terminal_total_return'] == -1
    assert summary['ruin_date'] == DATES[1].isoformat()
    assert summary['evaluation_sessions'] == 3
    assert summary['observed_return_sessions'] == 2 and summary['absorbed_sessions'] == 1
    assert summary['annualized_sharpe'] is None and summary['realized_volatility'] is None
    assert summary['daily_metric_reason'] == 'NOT_REPORTED_ABSORBED_TAIL'
    assert summary['full_horizon_return_sequence_available'] is False
    assert summary['performance_cleared'] is False
    assert summary['protocol_status'] == 'DRAFT_NOT_FROZEN'
    assert summary['decision_status'] == 'OWNER_REVIEW_PENDING'
    assert summary['trades_executed'] == 0
    assert all(key not in summary for key in ('returns','marks','weights','wealth_path'))


def test_current_strict_ledger_is_preserved_as_a_distinct_convention(calendar):
    rows = ((-1.,) * 10, (0.,) * 10)
    with pytest.raises(AccountingError):
        simulate(calendar=calendar, dates=DATES[:2], returns=rows,
                 instructions=(), cost_rate=0., evidence_kind=SYNTHETIC)
    alternative = run(calendar, rows)
    assert alternative.summary()['terminal_wealth'] == 0
    assert alternative.summary()['ruin_occurred'] is True


def test_one_extinguished_industry_is_not_portfolio_ruin(calendar):
    ledger = run(calendar, ((-1.,) + (0.,) * 9, (0.,) * 10))
    assert ledger.marks[0].wealth == pytest.approx(.9)
    assert ledger.marks[0].weights[0] == 0
    assert not ledger.summary()['ruin_occurred']
    assert ledger.summary()['terminal_total_return'] == pytest.approx(-.1)
    assert ledger.summary()['max_drawdown'] == pytest.approx(.1)


def test_zero_weight_nonlosers_cannot_rescue_a_fully_lost_invested_portfolio(calendar):
    initial = (1.,) + (0.,) * 9
    ledger = run(calendar, ((-1.,) + (100.,) * 9,), initial_weights=initial)
    assert ledger.summary()['ruin_occurred'] and ledger.marks[0].net_return == -1
    assert ledger.summary()['terminal_wealth'] == 0


def test_zero_holdings_before_ruin_are_not_invented_survivors(calendar):
    ledger = run(calendar, ((0.,) + (-1.,) * 9, (-1.,) + (0.,) * 9, (1.,) * 10))
    assert ledger.marks[0].weights == (1.,) + (0.,) * 9
    assert ledger.marks[1].state == 'RUIN_EVENT'
    assert ledger.marks[2].net_return is None


def test_near_total_loss_is_not_exact_economic_ruin(calendar):
    r = -1. + 2**-52
    ledger = run(calendar, ((r,) * 10,), cost_factors=(1.,))
    assert ledger.marks[0].wealth == 2**-52
    assert ledger.marks[0].state == 'ACTIVE'
    assert ledger.marks[0].weights is not None
    assert ledger.summary()['ruin_occurred'] is False


def test_real_conversion_must_not_round_a_genuine_survivor_into_exact_loss(calendar):
    r=Fraction(-1)+Fraction(1,2**60)
    assert r>-1 and float(r)==-1
    with pytest.raises(ruin.RuinReferenceError,match='NUMERICAL_RETURN_PRECISION_NOT_RUIN'):
        run(calendar, ((r,)*10,))


def test_real_conversion_cannot_hide_a_below_minus_one_input(calendar):
    r=Fraction(-1)-Fraction(1,2**60)
    assert r<-1 and float(r)==-1
    with pytest.raises(ruin.RuinReferenceError,match='INVALID_RETURN_INPUT'):
        run(calendar, ((r,)*10,))


@pytest.mark.parametrize('value,code', [
    (10**1000,'NUMERICAL_OVERFLOW_NOT_RUIN'),
    (Fraction(10**1000,3),'NUMERICAL_OVERFLOW_NOT_RUIN'),
    (-10**1000,'INVALID_RETURN_INPUT'),
    (float('inf'),'INVALID_RETURN_INPUT'),
], ids=['finite_int_overflow','finite_fraction_overflow','negative_domain','literal_infinity'])
def test_finite_conversion_overflow_is_distinct_from_invalid_return_domain(calendar,value,code):
    with pytest.raises(ruin.RuinReferenceError,match=code):
        run(calendar, ((value,)*10,))


@pytest.mark.parametrize('value,code', [
    (Fraction(10**1000,3),'NUMERICAL_OVERFLOW_NOT_RUIN'),
    (-10**1000,'INVALID_INITIAL_WEALTH'),
], ids=['finite_fraction_overflow','negative_domain'])
def test_initial_wealth_original_domain_precedes_representation_failure(calendar,value,code):
    with pytest.raises(ruin.RuinReferenceError,match=code):
        run(calendar, ((0.,)*10,), initial_wealth=value)


@pytest.mark.parametrize('value',[10**1000,-10**1000])
def test_invalid_cost_domain_is_rejected_before_float_conversion(calendar,value):
    with pytest.raises(ruin.RuinReferenceError,match='INVALID_COST_FACTOR'):
        run(calendar, ((0.,)*10,), cost_factors=(value,))


def test_positive_initial_holding_conversion_underflow_is_not_silently_erased(calendar):
    tiny=Fraction(1,10**400)
    with pytest.raises(ruin.RuinReferenceError,match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((0.,)*10,), initial_weights=(tiny,1-tiny)+(0.,)*8)


def test_positive_cost_factor_conversion_underflow_is_not_cost_exhaustion(calendar):
    with pytest.raises(ruin.RuinReferenceError,match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((0.,)*10,), cost_factors=(Fraction(1,10**400),))


def test_positive_initial_wealth_conversion_underflow_is_not_initial_bankruptcy(calendar):
    with pytest.raises(ruin.RuinReferenceError,match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((0.,)*10,), initial_wealth=Fraction(1,10**400))


def test_wealth_underflow_is_not_relabelled_economic_ruin(calendar):
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((-.5,) * 10,), initial_wealth=math.ulp(0.))


def test_asset_underflow_is_rejected_before_it_can_erase_a_positive_holding(calendar):
    tiny = math.ulp(0.)
    initial = (tiny, 1.) + (0.,) * 8
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((-.5, -1.) + (0.,) * 8,), initial_weights=initial)


def test_normalized_holding_underflow_is_not_a_genuine_zero_position(calendar):
    tiny = math.ulp(0.)
    initial = (tiny, 1.) + (0.,) * 8
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((0., 1e308) + (0.,) * 8,), initial_weights=initial)


def test_partial_underflow_cannot_create_a_false_later_exact_ruin(calendar):
    tiny = 1e-320
    initial = (tiny, 1.) + (0.,) * 8
    rows = ((-1.+2**-52, 0.) + (0.,) * 8,
            (0., -1.) + (0.,) * 8)
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, rows, initial_weights=initial)


def test_wealth_overflow_is_a_distinct_numerical_failure(calendar):
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_OVERFLOW_NOT_RUIN'):
        run(calendar, ((1e308,) * 10, (1e308,) * 10))


def test_positive_cost_factor_can_underflow_without_economic_ruin(calendar):
    with pytest.raises(ruin.RuinReferenceError, match='NUMERICAL_UNDERFLOW_NOT_RUIN'):
        run(calendar, ((0.,) * 10,), initial_wealth=math.ulp(0.), cost_factors=(.5,))


def test_cost_exhaustion_is_not_a_total_market_loss(calendar):
    with pytest.raises(ruin.RuinReferenceError, match='COST_EXHAUSTION_NOT_RUIN'):
        run(calendar, ((0.,) * 10,), cost_factors=(0.,))


def test_valid_post_ruin_factors_are_not_charged_and_returns_are_not_filled(calendar):
    ledger = run(calendar, ((-1.,) * 10, (1.,) * 10, (.5,) * 10), cost_factors=(1., .5, .25))
    assert [mark.net_return for mark in ledger.marks] == [-1., None, None]
    assert all(mark.applied_cost_factor is None for mark in ledger.marks)
    assert all(mark.weights is None for mark in ledger.marks)
    assert ledger.summary()['absorbed_sessions'] == 2


@pytest.mark.parametrize('bad', [-1.00001, float('nan'), float('inf'), True, 'PRIVATEPOISON'])
def test_invalid_return_values_stay_input_failures_even_after_an_earlier_ruin(calendar, bad):
    rows = ((-1.,) * 10, (bad,) + (0.,) * 9)
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_RETURN_INPUT') as error:
        run(calendar, rows)
    assert 'PRIVATEPOISON' not in str(error.value)


@pytest.mark.parametrize('factor', [-.1, 1.01, float('nan'), float('inf'), True])
def test_cost_factor_domain_is_explicit(calendar, factor):
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_COST_FACTOR'):
        run(calendar, ((0.,) * 10,), cost_factors=(factor,))


def test_invalid_cost_tail_is_not_silently_omitted_after_ruin(calendar):
    with pytest.raises(ruin.RuinReferenceError, match='COST_EXHAUSTION_NOT_RUIN'):
        run(calendar, ((-1.,) * 10, (1.,) * 10), cost_factors=(1., 0.))


@pytest.mark.parametrize('dates', [
    (date(2021,1,5), date(2021,1,5)),
    (date(2021,1,6), date(2021,1,5)),
    (date(2021,1,5), date(2021,1,7)),
    (date(2021,1,9),), (datetime(2021,1,5),), (),
])
def test_grid_integrity_is_not_weakened_by_optional_ruin_handling(calendar, dates):
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_DATE_GRID'):
        ruin.absorbing_ruin_reference(calendar=calendar, dates=dates,
            returns=((0.,)*10,)*len(dates), evidence_kind=SYNTHETIC)


def test_post_2024_scope_fails_before_return_inspection(calendar):
    class Poison:
        def __iter__(self):raise AssertionError('Future return values accessed')
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_DATE_GRID'):
        ruin.absorbing_ruin_reference(calendar=calendar, dates=(date(2025,1,2),),
            returns=Poison(), evidence_kind=SYNTHETIC)


@pytest.mark.parametrize('weights', [(0.,)*10, (1.,)*10, (-.1,)+(.1,)*9, (.1,)*9])
def test_initial_holdings_must_be_a_valid_explicit_simplex(calendar, weights):
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_INITIAL_WEIGHTS'):
        run(calendar, ((0.,)*10,), initial_weights=weights)


@pytest.mark.parametrize('wealth', [0., -.1, float('inf'), float('nan'), True])
def test_initial_wealth_cannot_masquerade_as_a_new_ruin_event(calendar, wealth):
    with pytest.raises(ruin.RuinReferenceError, match='INVALID_INITIAL_WEALTH'):
        run(calendar, ((0.,)*10,), initial_wealth=wealth)


def test_lengths_order_and_explicit_fixture_label_are_validated(calendar):
    for kwargs, code in [
        ({'returns':((0.,)*9,)}, 'INVALID_RETURN_INPUT'),
        ({'returns':((0.,)*10,)*2}, 'RETURN_DATE_LENGTH'),
        ({'cost_factors':(1.,1.)}, 'COST_DATE_LENGTH'),
        ({'industry_order':('Other',)*10}, 'STRICT_INDUSTRY_ORDER_REQUIRED'),
        ({'evidence_kind':'historical'}, 'EXPLICIT_INVENTED_FIXTURE_REQUIRED'),
    ]:
        options = dict(calendar=calendar, dates=DATES[:1], returns=((0.,)*10,), evidence_kind=SYNTHETIC)
        options.update(kwargs)
        with pytest.raises(ruin.RuinReferenceError, match=code):
            ruin.absorbing_ruin_reference(**options)


def test_full_horizon_comparison_does_not_compare_censored_sharpe(calendar):
    adverse = run(calendar, ((0.,)*10, (-1.,)*10, (.5,)*10))
    survivor = run(calendar, ((0.,)*10, (-.1,)*10, (0.,)*10))
    assert adverse.summary()['evaluation_sessions'] == survivor.summary()['evaluation_sessions'] == 3
    assert adverse.summary()['terminal_wealth'] == 0
    assert survivor.summary()['terminal_wealth'] == pytest.approx(.9)
    assert adverse.summary()['max_drawdown'] == 1
    assert adverse.summary()['annualized_sharpe'] is None
    assert adverse.summary()['observed_return_sessions'] != survivor.summary()['observed_return_sessions']


def test_final_date_ruin_has_no_missing_tail_but_metrics_remain_an_explicit_policy_choice(calendar):
    ledger=run(calendar, ((0.,)*10,(-1.,)*10))
    summary=ledger.summary()
    assert summary['full_horizon_return_sequence_available'] is True
    assert summary['annualized_sharpe'] is None
    assert summary['daily_metric_reason']=='NOT_REPORTED_BY_TERMINAL_REFERENCE_POLICY'
    assert summary['terminal_total_return']==-1
    assert summary['geometric_annual_growth'] is None
    assert summary['growth_reason']=='NOT_REPORTED_BY_TERMINAL_REFERENCE_POLICY'


def test_reference_is_pure_and_detailed_marks_are_not_automatically_exposed(calendar, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    def forbidden(*args,**kwargs):raise AssertionError('Ruin reference performed I/O')
    monkeypatch.setattr(io,'open',forbidden)
    monkeypatch.setattr(subprocess,'run',forbidden)
    rows = [[-1.]*10,[.5]*10]
    original = [row[:] for row in rows]
    ledger = run(calendar, rows)
    summary = ledger.summary()
    assert rows == original and not list(tmp_path.iterdir())
    assert capsys.readouterr() == ('','')
    assert 'redacted' in repr(ledger) and '-1.0' not in repr(ledger.marks[0])
    assert summary['evidence_kind'] == 'synthetic_absorbing_ruin_reference'
