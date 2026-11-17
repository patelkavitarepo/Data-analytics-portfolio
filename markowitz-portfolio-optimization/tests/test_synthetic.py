"""Constructed evidence only. No expected financial-market results asserted."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest
from markowitz import synthetic as lab
from markowitz.analytics import Candidate
from markowitz.research import PROTOCOL, metrics


@pytest.fixture
def config():
    return lab.LabConfig(seed=6006, train_steps=126, future_steps=63, bootstrap_draws=3)


@pytest.mark.parametrize('name', lab.SCENARIOS)
def test_seeded_scenarios_reproducible_positive_covariance_and_disjoint_steps(name, config):
    a, b = lab.construct(name, config), lab.construct(name, config)
    pd.testing.assert_frame_equal(a.training, b.training)
    pd.testing.assert_frame_equal(a.future, b.future)
    assert a.training.index.max() < a.future.index.min()
    assert not isinstance(a.training.index, pd.DatetimeIndex)
    assert set(a.training.columns).isdisjoint({'SPY', 'QQQ', 'TLT'})
    assert np.linalg.eigvalsh(a.train_covariance).min() > 0
    assert np.linalg.eigvalsh(a.future_covariance).min() > 0
    assert np.isfinite(a.training).all(axis=None) and (a.training > -1).all(axis=None)
    other = lab.construct(name, lab.LabConfig(seed=6007, train_steps=126, future_steps=63, bootstrap_draws=3))
    assert not a.training.equals(other.training)


def corr(cov):
    return cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))


def test_scenario_design_is_exact_and_explicit(config):
    base = lab.construct('baseline', config)
    np.testing.assert_allclose(corr(base.train_covariance)[np.triu_indices(6, 1)], .35)
    spike = lab.construct('correlation_spike', config)
    np.testing.assert_allclose(corr(spike.train_covariance)[np.triu_indices(6, 1)], .85)
    np.testing.assert_allclose(np.diag(spike.train_covariance), np.diag(base.train_covariance))
    shock = lab.construct('volatility_shock', config)
    assert shock.train_covariance[0, 0] == pytest.approx(base.train_covariance[0, 0] * 9)
    np.testing.assert_allclose(corr(shock.train_covariance), corr(base.train_covariance))
    mean = lab.construct('mean_estimation_error', config)
    pd.testing.assert_frame_equal(mean.training, base.training)
    pd.testing.assert_frame_equal(mean.future, base.future)
    np.testing.assert_array_equal(mean.mean_bias, [.08, -.04, 0, 0, 0, 0])
    flip = lab.construct('correlation_sign_flip', config)
    pd.testing.assert_frame_equal(flip.training, base.training)
    assert corr(flip.future_covariance)[0, 3] == pytest.approx(-.35)
    assert corr(flip.future_covariance)[0, 1] == pytest.approx(.35)
    assert not flip.future.equals(base.future)


def test_mean_bias_changes_only_estimator_mean_not_covariance(config):
    base, error = lab.construct('baseline', config), lab.construct('mean_estimation_error', config)
    mu0, cov0, weights0, _ = lab.fit(base.training, base.mean_bias)
    mu1, cov1, weights1, _ = lab.fit(error.training, error.mean_bias)
    np.testing.assert_allclose(mu1 - mu0, error.mean_bias)
    pd.testing.assert_frame_equal(cov0, cov1)
    np.testing.assert_allclose(weights0['min_vol'], weights1['min_vol'], atol=1e-8)
    assert np.abs(weights0['max_sharpe'] - weights1['max_sharpe']).sum() > .01


def test_future_mutation_cannot_change_fitted_or_bootstrap_weights(config):
    a = lab.construct('baseline', config)
    b = deepcopy(a)
    b.future.loc[:, :] = -.1
    r1, r2 = lab.analyze(a, config), lab.analyze(b, config)
    pd.testing.assert_frame_equal(r1['weights'], r2['weights'])
    pd.testing.assert_frame_equal(r1['estimated'], r2['estimated'])
    pd.testing.assert_frame_equal(r1['bootstrap']['summary'], r2['bootstrap']['summary'])
    pd.testing.assert_frame_equal(r1['bootstrap']['log'], r2['bootstrap']['log'])
    assert r1['manifest']['training_sha256'] == r2['manifest']['training_sha256']
    assert r1['manifest']['future_sha256'] != r2['manifest']['future_sha256']
    assert not r1['realized'].equals(r2['realized'])
    b.future.index -= 1
    with pytest.raises(ValueError, match='disjoint'):
        lab.analyze(b, config)


def test_constraints_cost_comparability_and_reproducible_bootstrap(config):
    result = lab.run('baseline', config)
    weights = result['weights']
    np.testing.assert_allclose(weights.sum(), 1, atol=1e-7)
    assert weights.min().min() >= -1e-7 and weights.max().max() <= config.cap + 1e-7
    np.testing.assert_allclose(weights['equal_weight'], 1 / 6)
    assert result['estimated'].loc['equal_weight', 'target_HHI'] == pytest.approx(1 / 6)
    assert result['realized'].groupby('strategy')['cost_bps'].apply(list).tolist() == [[0., 10.]] * 3
    for strategy in lab.STRATEGIES:
        free = result['paths'][strategy, 0.]
        costly = result['paths'][strategy, 10.]
        assert costly.index.equals(free.index)
        assert np.prod(1 + costly) <= np.prod(1 + free)
    again = lab.bootstrap(lab.construct('baseline', config).training, np.zeros(6), config)
    pd.testing.assert_frame_equal(result['bootstrap']['log'], again['log'])
    assert len(again['log']) == config.bootstrap_draws * 3
    assert again['summary']['successful_draws'].eq(config.bootstrap_draws).all()
    assert again['summary'].loc['equal_weight', 'mean_L1'] == pytest.approx(0)
    assert all(len(frame) == config.bootstrap_draws for frame in again['samples'].values())


def test_stability_distances_known_values_and_empty_draws():
    result = lab.instability([[.5, .5], [.6, .4]], [.5, .5])
    assert result['mean_L1'] == pytest.approx(.1)
    assert result['mean_half_L1_reallocation'] == pytest.approx(.05)
    assert result['p95_L1'] == pytest.approx(.19)
    assert result['mean_asset_weight_std'] == pytest.approx(np.sqrt(.005))
    assert np.isnan(lab.instability(np.empty((0, 2)), [.5, .5])['mean_L1'])
    with pytest.raises(ValueError):
        lab.instability([[np.nan, .5]], [.5, .5])


def test_solver_failure_not_zero_imputed_or_published(config, monkeypatch):
    original = lab.optimize
    def fail(mu, cov, cap, objective, annual_rf):
        if objective == 'max_sharpe':
            raise ValueError('SYNTHETIC forced local-solver failure')
        return original(mu, cov, cap, objective, annual_rf)
    monkeypatch.setattr(lab, 'optimize', fail)
    result = lab.run('baseline', config)
    assert 'max_sharpe' not in result['weights']
    assert 'max_sharpe' not in result['realized']['strategy'].values
    assert result['bootstrap']['summary'].loc['max_sharpe', 'failed_draws'] == config.bootstrap_draws
    assert np.isnan(result['bootstrap']['summary'].loc['max_sharpe', 'mean_L1'])
    failed = result['bootstrap']['log'].query('strategy == "max_sharpe"')
    assert failed['success'].eq(False).all() and failed['error'].str.contains('forced').all()
    assert failed['failed_solver_starts'].isna().all()  # No fabricated count when solver details were unavailable.
    assert failed['checked_violation'].isna().all()  # Not reported by failed solver, never invented as zero.
    json.dumps(lab.json_safe(result['manifest']), allow_nan=False)


def test_independent_constraint_recheck_rejects_false_success(config, monkeypatch):
    monkeypatch.setattr(lab, 'optimize', lambda *args: Candidate(np.array([1., 0, 0, 0, 0, 0]), {'success': True, 'attempts': []}))
    result = lab.run('baseline', config)
    assert list(result['weights']) == ['equal_weight']
    assert result['manifest']['diagnostics']['min_vol']['checked_violation'] == pytest.approx(.65)
    assert result['bootstrap']['log'].query('strategy != "equal_weight"')['success'].eq(False).all()


def test_path_drift_costs_and_metrics_match_hand_calculation():
    future = pd.DataFrame([[.2, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
    result = lab.path_returns(future, [.5, .5, 0, 0, 0, 0], cost_bps=10, rebalance_every=1)
    assert result['return'].iloc[0] == pytest.approx(.999 * 1.1 - 1)
    assert result['gross_traded_notional'].iloc[1] == pytest.approx(2 * (.6 / 1.1 - .5))
    r = pd.Series([-.1, .1, -.1])
    actual, reference = lab.path_metrics(r, .02), metrics(r, .02)
    assert actual['max_drawdown'] == pytest.approx(-.109)
    assert actual['CAGR'] == pytest.approx(reference['annualized_return_CAGR'])
    assert actual['volatility'] == pytest.approx(reference['annualized_volatility'])
    assert actual['sharpe'] == pytest.approx(reference['sharpe'])


@pytest.mark.parametrize('overrides', [{'bootstrap_draws': 31}, {'bootstrap_draws': 1}, {'cap': .1},
                                     {'cap': float('nan')}, {'train_steps': 1261}, {'seed': -1},
                                     {'future_steps': 0}, {'train_steps': True}, {'annual_rf': -1}])
def test_computation_bounds_and_infeasible_settings(overrides):
    with pytest.raises(ValueError):
        lab.construct(config=lab.LabConfig(**overrides))


def test_no_provider_calls_or_empirical_protocol_mutation(config, monkeypatch):
    import socket
    import markowitz.data
    import markowitz.verification
    frozen = deepcopy(PROTOCOL)
    def forbidden(*args, **kwargs):
        pytest.fail('Synthetic lab must not access providers, empirical evaluation or permission gates')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(markowitz.data, 'download_prices', forbidden)
    monkeypatch.setattr(markowitz.verification, 'verify_source', forbidden)
    monkeypatch.setattr('markowitz.research.evaluate', forbidden)
    result = lab.run('baseline', config)
    assert result['manifest']['warning'] == lab.WARNING
    assert PROTOCOL == frozen
    assert lab.labeled(result['weights'])['Evidence'].eq(lab.WARNING).all()
    assert result['manifest']['training_steps'] == [0, config.train_steps - 1]
    assert result['manifest']['future_steps'][0] == config.train_steps
