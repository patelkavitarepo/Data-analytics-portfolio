import numpy as np
import pandas as pd
import pytest
from markowitz.analytics import moments, optimize, frontier, portfolio_stats, risk_free_daily


def problem():
    return np.array([.04, .08, .12, .16]), np.diag([.01, .02, .03, .04])


def test_moments_sample_covariance_annualization():
    r = pd.DataFrame({'A': [.01, -.02, .03], 'B': [-.01, .01, .02]})
    mu, cov = moments(r)
    np.testing.assert_allclose(mu, np.mean(r, axis=0) * 252)
    np.testing.assert_allclose(cov, np.cov(r.to_numpy().T, ddof=1) * 252)


def test_objective_and_risk_free_scaling():
    mu, cov = problem()
    w = np.full(4, .25)
    s = portfolio_stats(w, mu, cov, .03)
    assert s['expected_return'] == pytest.approx(.1)
    assert s['volatility'] == pytest.approx(np.sqrt(.1 / 16))
    assert s['sharpe'] == pytest.approx((.1 - risk_free_daily(.03) * 252) / s['volatility'])
    assert (1 + risk_free_daily(.03)) ** 252 == pytest.approx(1.03)


@pytest.mark.parametrize('objective', ['min_vol', 'max_sharpe'])
def test_constraints_and_objective_improvement(objective):
    mu, cov = problem()
    c = optimize(mu, cov, .35, objective)
    assert c.diagnostics['success'] and c.diagnostics['max_constraint_violation'] < 1e-7
    assert c.weights.sum() == pytest.approx(1)
    assert np.all(c.weights >= -1e-8) and np.all(c.weights <= .35 + 1e-8)
    equal = portfolio_stats(np.full(4, .25), mu, cov)
    optimized = portfolio_stats(c.weights, mu, cov)
    if objective == 'min_vol':
        assert optimized['volatility'] <= equal['volatility']
    else:
        assert optimized['sharpe'] >= equal['sharpe']


def test_known_analytic_minimum_variance_solution():
    mu, cov = problem()
    result = optimize(mu, cov, 1.)
    expected = 1 / np.diag(cov)
    expected /= expected.sum()
    np.testing.assert_allclose(result.weights, expected, atol=2e-6)


@pytest.mark.parametrize('cap', [.2, 0, 1.1, np.nan])
def test_infeasible_bounds(cap):
    mu, cov = problem()
    with pytest.raises(ValueError):
        optimize(mu, cov, cap)


def test_exactly_binding_feasibility():
    mu, cov = problem()
    c = optimize(mu, cov, .25)
    np.testing.assert_allclose(c.weights, .25)


def test_frontier_feasible_efficient_branch():
    mu, cov = problem()
    curve, failures = frontier(mu, cov, points=12)
    assert not failures and len(curve) == 12
    np.testing.assert_allclose(curve['expected_return'], curve['target'], atol=1e-7)
    assert (curve['violation'] < 1e-7).all()
    assert (curve['volatility'].diff().dropna() >= -1e-7).all()
    with pytest.raises(ValueError, match='No valid'):
        optimize(mu, cov, target=10.)


def test_invalid_covariance_and_returns():
    mu, cov = problem()
    cov[0, 0] = -1
    with pytest.raises(ValueError, match='semidefinite'):
        optimize(mu, cov)
    with pytest.raises(ValueError, match='Singular'):
        optimize(mu, np.zeros((4, 4)))
    with pytest.raises(ValueError):
        moments(pd.DataFrame([[.1, np.nan], [.2, .1]]))


def test_failed_solver_points_never_included(monkeypatch):
    import markowitz.analytics as a
    original = a.optimize
    def fail_targets(*args, **kwargs):
        if kwargs.get('target') is not None:
            raise ValueError('forced solver failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(a, 'optimize', fail_targets)
    curve, failures = a.frontier(*problem(), points=5)
    assert curve.empty and len(failures) == 5
