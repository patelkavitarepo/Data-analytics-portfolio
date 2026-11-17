"""Frozen protocol. Estimation windows precede every evaluation return."""
import numpy as np
import pandas as pd

from .analytics import DAYS, moments, optimize, risk_free_daily
from .data import sessions

PROTOCOL = {
    'version': '006-v1', 'train': ['2016-01-01', '2022-12-31'],
    'validation': ['2023-01-01', '2024-12-31'], 'holdout_start': '2025-01-01',
    'covariance': 'sample ddof=1', 'rebalancing': 'first session monthly, before daily return',
    'selection': 'none; compare both prespecified objectives; no winner selected',
    'default_cap': .35, 'default_rf_effective_annual': .02, 'cost_sensitivity_bps': 10.,
}


def split_dates(returns):
    if not isinstance(returns.index, pd.DatetimeIndex) or not returns.index.is_monotonic_increasing or returns.index.has_duplicates:
        raise ValueError('Unique sorted dated returns required')
    return {'train': returns.loc['2016-01-01':'2022-12-31'],
            'validation': returns.loc['2023-01-01':'2024-12-31'],
            'holdout': returns.loc['2025-01-01':]}


def backtest(returns, target, cost_bps=0.):
    """Drifting buy-and-hold weights between monthly target resets.

    Rebalance using prior-close holdings, then earn today's return. Costs are
    bps times gross traded notional / NAV (sum absolute changes, not half).
    Initial investment is one unit traded from cash, charged for every strategy.
    This close-execution approximation excludes spread/slippage beyond flat costs.
    """
    a = np.asarray(returns, float)
    w = np.asarray(target, float)
    if a.ndim != 2 or len(a) == 0 or a.shape[1] != len(w) or not np.isfinite(a).all() or (a <= -1).any():
        raise ValueError('Invalid returns')
    if not isinstance(returns.index, pd.DatetimeIndex) or returns.index.has_duplicates or not returns.index.is_monotonic_increasing:
        raise ValueError('Unique sorted dates required')
    if not np.isfinite(w).all() or (w < 0).any() or not np.isclose(w.sum(), 1):
        raise ValueError('Invalid target weights')
    if not np.isfinite(cost_bps) or not 0 <= cost_bps < 10000:
        raise ValueError('Invalid costs')
    target = w.copy()
    out, trades = [], []
    previous_month = None
    for date, r in zip(returns.index, a):
        month = (date.year, date.month)
        traded = 0.
        if month != previous_month:
            traded = 1. if previous_month is None else float(np.abs(target - w).sum())
            w = target.copy()
        cost = traded * cost_bps / 10000
        if cost >= 1:
            raise ValueError('Transaction costs exhaust capital')
        gross = 1 + w @ r
        out.append((1 - cost) * gross - 1)
        trades.append(traded)
        w = w * (1 + r) / gross
        previous_month = month
    return pd.DataFrame({'return': out, 'traded_notional': trades}, index=returns.index)


def wealth_and_drawdown(returns):
    wealth = (1 + returns).cumprod()
    # Include inception NAV=1 so an immediate loss is a drawdown.
    peaks = wealth.cummax().clip(lower=1.)
    return wealth, wealth / peaks - 1


def metrics(returns, annual_rf=0.):
    r = pd.Series(returns, dtype=float)
    if len(r) < 2 or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError('At least two finite returns > -1 required')
    wealth, dd = wealth_and_drawdown(r)
    vol = float(r.std(ddof=1) * np.sqrt(DAYS))
    return {'annualized_return_CAGR': float(np.expm1(np.log1p(r).sum() * DAYS / len(r))),
        'annualized_volatility': vol,
        'sharpe': float((r.mean() - risk_free_daily(annual_rf)) * DAYS / vol) if vol > 1e-12 else np.nan,
        'cumulative_return': float(wealth.iloc[-1] - 1), 'max_drawdown': float(dd.min()),
        'observations': len(r)}


def evaluate(returns, assets, cap=.35, annual_rf=.02, cost_bps=0., include_holdout=True):
    if 'SPY' not in returns or len(set(assets)) != len(assets) or not set(assets).issubset(returns.columns):
        raise ValueError('Need SPY benchmark and unique selected assets')
    parts = split_dates(returns)
    if returns.empty or not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError('Complete finite return history required')
    expected = sessions(returns.index.min(), returns.index.max())
    if not returns.index.equals(expected):
        raise ValueError('Missing or non-session return dates; evaluation cannot skip market intervals')
    # Minimum one trading year estimation, sixty days evaluation; no fabricated short samples.
    if len(parts['train']) < DAYS or len(parts['validation']) < 60 or (include_holdout and len(parts['holdout']) < 60):
        raise ValueError('Need >=252 training and >=60 validation/holdout observations')
    output = {}
    for period in (('validation', 'holdout') if include_holdout else ('validation',)):
        fit = parts['train'] if period == 'validation' else pd.concat([parts['train'], parts['validation']])
        test = parts[period]
        if fit.index.max() >= test.index.min():
            raise ValueError('Time leakage: fitting must precede evaluation')
        mu, cov = moments(fit[assets])
        candidates = {name: optimize(mu, cov, cap, name, annual_rf) for name in ('min_vol', 'max_sharpe')}
        weights = {name: pd.Series(c.weights, index=assets) for name, c in candidates.items()}
        weights['equal_weight'] = pd.Series(1 / len(assets), index=assets)
        weights['SPY'] = pd.Series({'SPY': 1.})
        results, records, turnovers = {}, {}, {}
        for name, w in weights.items():
            full = w.reindex(returns.columns, fill_value=0.)
            bt = backtest(test, full, cost_bps)
            results[name] = bt['return']
            records[name] = dict(metrics(bt['return'], annual_rf), concentration_HHI=float((w ** 2).sum()),
                max_target_weight=float(w.max()), gross_traded_notional=float(bt['traded_notional'].sum()))
            turnovers[name] = bt['traded_notional']
        output[period] = {'returns': pd.DataFrame(results), 'metrics': pd.DataFrame(records).T,
            'weights': pd.DataFrame(weights).fillna(0.), 'turnover': pd.DataFrame(turnovers),
            'diagnostics': {n: c.diagnostics for n, c in candidates.items()},
            'fit_start': str(fit.index.min().date()), 'fit_end': str(fit.index.max().date()),
            'test_start': str(test.index.min().date()), 'test_end': str(test.index.max().date())}
    return output


def evaluate_validation(returns, assets, cap=.35, annual_rf=.02, cost_bps=0.):
    return evaluate(returns.loc[:'2024-12-31'], assets, cap, annual_rf, cost_bps, include_holdout=False)
