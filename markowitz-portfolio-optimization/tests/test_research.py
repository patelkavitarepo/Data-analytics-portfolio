import numpy as np
import pandas as pd
import pytest
from markowitz.research import backtest, evaluate, evaluate_validation, metrics, split_dates, wealth_and_drawdown


def test_date_boundaries(historical_returns):
    parts = split_dates(historical_returns)
    assert parts['train'].index.max() < pd.Timestamp('2023-01-01')
    assert parts['validation'].index.min() >= pd.Timestamp('2023-01-01')
    assert parts['validation'].index.max() < pd.Timestamp('2025-01-01')
    assert parts['holdout'].index.min() >= pd.Timestamp('2025-01-01')
    assert sum(map(len, parts.values())) == len(historical_returns)


def test_future_mutation_never_changes_earlier_weights(historical_returns):
    assets = list(historical_returns.columns)
    original = evaluate(historical_returns, assets)
    altered = historical_returns.copy()
    altered.loc['2025':] = -.5
    changed = evaluate(altered, assets)
    for period in original:
        pd.testing.assert_frame_equal(original[period]['weights'], changed[period]['weights'])
    pd.testing.assert_frame_equal(original['validation']['returns'], changed['validation']['returns'])
    altered = historical_returns.copy()
    altered.loc['2023':] = .01
    # Validation estimation never sees any validation prices/returns.
    changed = evaluate_validation(altered, assets)
    pd.testing.assert_frame_equal(original['validation']['weights'], changed['validation']['weights'])


def test_holdout_never_fit_or_required_in_validation_mode(historical_returns):
    validation_only = evaluate_validation(historical_returns.loc[:'2024'], list(historical_returns.columns))
    assert list(validation_only) == ['validation']
    assert validation_only['validation']['fit_end'] < '2023-01-01'


def test_identical_benchmark_dates_and_cost_assumptions(historical_returns):
    assets = list(historical_returns.columns)
    out = evaluate(historical_returns, assets, cost_bps=10)
    for period, result in out.items():
        r = result['returns']
        assert r.notna().all().all()
        assert r.index.equals(split_dates(historical_returns)[period].index)
        expected = historical_returns.loc[r.index, 'SPY'].copy()
        expected.iloc[0] = (1 - .001) * (1 + expected.iloc[0]) - 1
        np.testing.assert_allclose(r['SPY'], expected)
        assert result['turnover']['SPY'].sum() == pytest.approx(1.)
        assert result['metrics'].loc['SPY', 'concentration_HHI'] == 1.
        assert result['weights'].loc[:, ['min_vol', 'max_sharpe']].max().max() <= .35 + 1e-7


def test_monthly_rebalance_has_drift_and_no_daily_reset():
    r = pd.DataFrame([[.1, 0], [0, .1], [.1, 0]],
                     index=pd.to_datetime(['2024-01-30', '2024-01-31', '2024-02-01']))
    out = backtest(r, [.5, .5])
    assert out['return'].iloc[0] == pytest.approx(.05)
    assert out['return'].iloc[1] == pytest.approx(.1 * .5 / 1.05)
    assert out['return'].iloc[2] == pytest.approx(.05)
    assert out['traded_notional'].iloc[1] == 0
    assert out['traded_notional'].iloc[2] == pytest.approx(0., abs=1e-12)


def test_costs_multiplicative_and_gross_notional():
    r = pd.DataFrame([[.2, 0], [0, 0]], index=pd.to_datetime(['2024-01-31', '2024-02-01']))
    out = backtest(r, [.5, .5], cost_bps=10)
    assert out['return'].iloc[0] == pytest.approx(.999 * 1.1 - 1)
    traded = 2 * (.6 / 1.1 - .5)
    assert out['traded_notional'].iloc[1] == pytest.approx(traded)
    assert out['return'].iloc[1] == pytest.approx(-traded * .001)


def test_metrics_known_values_initial_drawdown_and_cagr():
    r = pd.Series([-.1, .1, -.1])
    wealth, dd = wealth_and_drawdown(r)
    assert wealth.iloc[-1] == pytest.approx(.891)
    assert dd.iloc[0] == pytest.approx(-.1)
    m = metrics(r, 0.)
    assert m['max_drawdown'] == pytest.approx(-.109)
    assert m['annualized_return_CAGR'] == pytest.approx(.891 ** (252 / 3) - 1)
    assert m['annualized_volatility'] == pytest.approx(r.std(ddof=1) * np.sqrt(252))
    assert m['sharpe'] == pytest.approx(r.mean() / r.std(ddof=1) * np.sqrt(252))


def test_insufficient_data_bad_dates_and_missing_values(historical_returns):
    with pytest.raises(ValueError, match='training'):
        evaluate(historical_returns.loc['2023':], list(historical_returns.columns))
    with pytest.raises(ValueError, match='sorted'):
        split_dates(historical_returns.iloc[::-1])
    with pytest.raises(ValueError):
        backtest(pd.DataFrame([[np.nan, 0]], index=pd.to_datetime(['2024-01-02'])), [.5, .5])
    with pytest.raises(ValueError):
        metrics([-.1, -1.])


def test_evaluation_rejects_skipped_market_intervals(historical_returns):
    with pytest.raises(ValueError, match='Missing or non-session'):
        evaluate(historical_returns.drop(historical_returns.index[100]), list(historical_returns.columns))


def test_insufficient_holdout_never_runs_optimization(historical_returns, monkeypatch):
    truncated = pd.concat([historical_returns.loc[:'2024'], historical_returns.loc['2025':].iloc[:59]])
    def forbidden(*args, **kwargs):
        pytest.fail('Optimization must not run before holdout length check')
    monkeypatch.setattr('markowitz.research.optimize', forbidden)
    with pytest.raises(ValueError, match='>=60'):
        evaluate(truncated, list(truncated.columns))


def test_exactly_sixty_holdout_sessions(historical_returns):
    truncated = pd.concat([historical_returns.loc[:'2024'], historical_returns.loc['2025':].iloc[:60]])
    result = evaluate(truncated, list(truncated.columns))
    assert len(result['holdout']['returns']) == 60
