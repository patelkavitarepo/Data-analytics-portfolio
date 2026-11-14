"""Annualized moments, constrained SLSQP candidates, and checked frontier."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize

DAYS = 252


def risk_free_daily(annual):
    if not np.isfinite(annual) or annual <= -1:
        raise ValueError('Risk-free effective annual assumption must exceed -100%')
    return np.expm1(np.log1p(annual) / DAYS)


def moments(returns):
    a = np.asarray(returns, dtype=float)
    if a.ndim != 2 or a.shape[0] < 2 or not np.isfinite(a).all() or (a <= -1).any():
        raise ValueError('At least two rows of finite simple returns > -1 required')
    return returns.mean() * DAYS, returns.cov(ddof=1) * DAYS


def portfolio_stats(weights, mu, cov, annual_rf=0.):
    w = np.asarray(weights)
    variance = float(w @ np.asarray(cov) @ w)
    vol = np.sqrt(max(0., variance))
    mean = float(w @ np.asarray(mu))
    excess = mean - DAYS * risk_free_daily(annual_rf)
    return {'expected_return': mean, 'volatility': vol, 'sharpe': excess / vol if vol > 1e-12 else np.nan}


@dataclass
class Candidate:
    weights: np.ndarray
    diagnostics: dict


def validate_problem(mu, cov, cap):
    mu, cov = np.asarray(mu, float), np.asarray(cov, float)
    n = len(mu)
    if n < 2 or not np.isfinite(cap) or not 0 < cap <= 1 or n * cap < 1 - 1e-10:
        raise ValueError('Infeasible universe/cap: need at least two assets and n × cap >= 1')
    if mu.ndim != 1 or cov.shape != (n, n) or not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise ValueError('Invalid moment dimensions or nonfinite values')
    if not np.allclose(cov, cov.T, atol=1e-10) or np.linalg.eigvalsh(cov).min() < -1e-10:
        raise ValueError('Covariance must be symmetric positive semidefinite')
    if np.linalg.eigvalsh(cov).min() < 1e-12:
        raise ValueError('Singular/degenerate covariance; choose a different universe or more observations')
    return mu, cov


def optimize(mu, cov, cap=.35, objective='min_vol', annual_rf=0., target=None):
    mu, cov = validate_problem(mu, cov, cap)
    if objective not in ('min_vol', 'max_sharpe'):
        raise ValueError('Unknown objective')
    n = len(mu)
    constraints = [{'type': 'eq', 'fun': lambda w: w.sum() - 1}]
    if target is not None:
        if not np.isfinite(target):
            raise ValueError('Nonfinite target')
        constraints.append({'type': 'eq', 'fun': lambda w: w @ mu - target})
    rf = DAYS * risk_free_daily(annual_rf)
    def loss(w):
        var = float(w @ cov @ w)
        return var if objective == 'min_vol' else -(w @ mu - rf) / np.sqrt(max(var, 1e-16))
    # Fixed deterministic starts for Sharpe; a local candidate, no global claim.
    starts = [np.full(n, 1 / n)]
    if objective == 'max_sharpe':
        for i in range(n):
            w = np.full(n, (1 - cap) / (n - 1))
            w[i] = cap
            starts.append(w)
    accepted = []
    attempts = []
    for start in starts:
        result = minimize(loss, start, method='SLSQP', bounds=[(0, cap)] * n,
            constraints=constraints, options={'ftol': 1e-12, 'maxiter': 1000})
        w = result.x
        violation = max(abs(w.sum() - 1), max(0., -w.min(), w.max() - cap),
                        abs(w @ mu - target) if target is not None else 0.)
        ok = bool(result.success and np.isfinite(w).all() and np.isfinite(loss(w)) and violation <= 1e-7)
        diag = {'success': ok, 'solver_success': bool(result.success), 'message': str(result.message),
            'iterations': int(result.nit), 'max_constraint_violation': float(violation),
            'objective_value': float(loss(w)), 'objective': objective}
        attempts.append(diag)
        if ok:
            accepted.append((loss(w), w, diag))
    if not accepted:
        raise ValueError(f'No valid optimization candidate: {attempts}')
    _, w, diag = min(accepted, key=lambda item: item[0])
    diag = dict(diag, starts=len(starts), accepted_starts=len(accepted), attempts=attempts,
                covariance_condition=float(np.linalg.cond(cov)))
    return Candidate(w, diag)


def frontier(mu, cov, cap=.35, points=35):
    mu, cov = validate_problem(mu, cov, cap)
    if points < 2:
        raise ValueError('Need at least two frontier points')
    gm = optimize(mu, cov, cap)
    upper = linprog(-mu, A_eq=[np.ones(len(mu))], b_eq=[1], bounds=[(0, cap)] * len(mu), method='highs')
    if not upper.success:
        raise ValueError('Could not determine feasible target interval')
    rows, failures = [], []
    for target in np.linspace(gm.weights @ mu, upper.x @ mu, points):
        try:
            candidate = optimize(mu, cov, cap, target=target)
            rows.append(dict(target=target, **portfolio_stats(candidate.weights, mu, cov),
                             violation=candidate.diagnostics['max_constraint_violation']))
        except ValueError as exc:
            failures.append({'target': float(target), 'error': str(exc)})
    return pd.DataFrame(rows), failures
