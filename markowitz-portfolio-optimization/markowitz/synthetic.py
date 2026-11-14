"""Constructed optimizer fragility experiments. No provider, ETF or holdout inputs.

Scenario steps are ordinal simulation time, not historical trading dates.
Only analytics.py is shared with the empirical optimizer; its protocol is untouched.
"""
from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import version

import numpy as np
import pandas as pd

from .analytics import DAYS, moments, optimize, portfolio_stats, risk_free_daily

WARNING = 'SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
ASSETS = tuple(f'Synthetic {letter}' for letter in 'ABCDEF')
SCENARIOS = {
    'baseline': 'Moderate positive correlation (0.35) in training and later path.',
    'correlation_spike': 'Correlation 0.85 in BOTH training and later path: a controlled regime comparison, not an unforeseen shock.',
    'volatility_shock': 'Asset A volatility triples in BOTH training and later path: a controlled assumption change.',
    'mean_estimation_error': 'Baseline draws; add +8 percentage points/year to estimated mean A and -4 to B. Covariance and later path are unchanged.',
    'correlation_sign_flip': 'Baseline training; at the first later step, cross-group correlation changes from +0.35 to -0.35. No refit after the unseen flip.',
}
STRATEGIES = ('min_vol', 'max_sharpe', 'equal_weight')
ANNUAL_MEANS = np.array([.06, .07, .08, .09, .10, .11])
ANNUAL_VOLS = np.array([.10, .13, .16, .19, .22, .25])


@dataclass(frozen=True)
class LabConfig:
    seed: int = 6006
    train_steps: int = 504
    future_steps: int = 252
    bootstrap_draws: int = 20
    cap: float = .35
    annual_rf: float = .02

    def validate(self):
        for name, low, high in (('seed', 0, 2**32 - 1), ('train_steps', 126, 1260),
                                ('future_steps', 21, 504), ('bootstrap_draws', 2, 30)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or not low <= value <= high:
                raise ValueError(f'{name} must be an integer in [{low}, {high}]')
        if not np.isfinite(self.cap) or not 1 / len(ASSETS) <= self.cap <= 1:
            raise ValueError('Infeasible synthetic cap: six assets require cap >= 1/6 and <= 1')
        risk_free_daily(self.annual_rf)


@dataclass
class Scenario:
    name: str
    training: pd.DataFrame
    future: pd.DataFrame
    train_covariance: np.ndarray
    future_covariance: np.ndarray
    mean_bias: np.ndarray


def covariance(rho=.35, signs=None, vols=None):
    """One-factor construction: PSD by design, with positive idiosyncratic risk."""
    if not np.isfinite(rho) or not 0 <= rho < 1:
        raise ValueError('Factor correlation must be in [0, 1)')
    signs = np.ones(6) if signs is None else np.asarray(signs, float)
    vols = ANNUAL_VOLS if vols is None else np.asarray(vols, float)
    if signs.shape != (6,) or not np.isin(signs, [-1, 1]).all() or vols.shape != (6,) or not np.isfinite(vols).all() or (vols <= 0).any():
        raise ValueError('Need six signs (+/-1) and finite positive volatilities')
    correlation = (1 - rho) * np.eye(6) + rho * np.outer(signs, signs)
    return correlation * np.outer(vols, vols)


def _draw(innovations, rho, signs, vols):
    daily = (np.sqrt(rho) * innovations[:, :1] * signs +
             np.sqrt(1 - rho) * innovations[:, 1:]) * vols / np.sqrt(DAYS)
    daily += ANNUAL_MEANS / DAYS
    # Gaussian tails are unbounded; never silently clip an invalid simple return.
    if (daily <= -1).any():
        raise ValueError('Constructed Gaussian draw <= -100%; choose another seed; no clipping applied')
    return daily


def construct(name='baseline', config=LabConfig()):
    config.validate()
    if name not in SCENARIOS:
        raise ValueError('Unknown synthetic scenario')
    streams = np.random.SeedSequence(config.seed).spawn(3)
    z_train = np.random.default_rng(streams[0]).standard_normal((config.train_steps, 7))
    z_future = np.random.default_rng(streams[1]).standard_normal((config.future_steps, 7))
    rho = .85 if name == 'correlation_spike' else .35
    vols = ANNUAL_VOLS.copy()
    if name == 'volatility_shock':
        vols[0] *= 3
    signs = np.ones(6)
    future_signs = np.array([1, 1, 1, -1, -1, -1]) if name == 'correlation_sign_flip' else signs
    bias = np.array([.08, -.04, 0, 0, 0, 0]) if name == 'mean_estimation_error' else np.zeros(6)
    training = pd.DataFrame(_draw(z_train, rho, signs, vols), columns=ASSETS,
                            index=pd.RangeIndex(config.train_steps, name='synthetic_step'))
    future = pd.DataFrame(_draw(z_future, rho, future_signs, vols), columns=ASSETS,
                          index=pd.RangeIndex(config.train_steps, config.train_steps + config.future_steps, name='synthetic_step'))
    return Scenario(name, training, future, covariance(rho, signs, vols),
                    covariance(rho, future_signs, vols), bias)


def _validate_training(training):
    if tuple(training.columns) != ASSETS or len(training) < 126 or not training.index.equals(pd.RangeIndex(len(training), name='synthetic_step')):
        raise ValueError('Training must be six synthetic assets on ordinal steps 0..n-1 (>=126)')
    if not np.isfinite(training.to_numpy()).all() or (training <= -1).any(axis=None):
        raise ValueError('Training simple returns must be finite and > -1')


def training_hash(training):
    return hashlib.sha256(training.to_csv(float_format='%.17g').encode()).hexdigest()


def fit(training, mean_bias, cap=.35, annual_rf=.02):
    """Training-only estimates; no future/path object accepted by this function."""
    _validate_training(training)
    bias = np.asarray(mean_bias, float)
    if bias.shape != (6,) or not np.isfinite(bias).all() or not 1 / 6 <= cap <= 1:
        raise ValueError('Invalid synthetic mean bias or infeasible cap')
    mu, cov = moments(training)
    mu = mu + bias  # Explicit estimator error, never a hidden change to generated truth.
    weights, diagnostics = {}, {}
    for strategy in STRATEGIES:
        violation = np.nan
        solver = None
        try:
            if strategy == 'equal_weight':
                w = np.full(6, 1 / 6)
                solver = {'success': True, 'method': 'fixed equal weights', 'starts': 0, 'attempts': []}
            else:
                candidate = optimize(mu, cov, cap, strategy, annual_rf)
                w = np.asarray(candidate.weights, float)
                solver = candidate.diagnostics
            if w.shape != (6,) or not np.isfinite(w).all():
                raise ValueError('Invalid returned weight vector')
            violation = float(max(abs(w.sum() - 1), max(0., -w.min(), w.max() - cap)))
            if not solver['success'] or violation > 1e-7:
                raise ValueError('Rejected solver/constraint failure; no weights or path metrics published')
            weights[strategy] = w
            diagnostics[strategy] = {'success': True, 'checked_violation': violation, 'solver': solver}
        except (ValueError, np.linalg.LinAlgError) as exc:
            diagnostics[strategy] = {'success': False, 'checked_violation': violation,
                                     'solver': solver, 'error': str(exc)}
    return mu, cov, pd.DataFrame(weights, index=ASSETS), diagnostics


def instability(samples, reference):
    """L1 target distance, half-L1 reallocation, and cross-draw dispersion.

    These are estimator diagnostics, not path trading costs or confidence bands.
    """
    a, ref = np.asarray(samples, float), np.asarray(reference, float)
    if a.ndim != 2 or a.shape[1:] != ref.shape or not np.isfinite(a).all() or not np.isfinite(ref).all():
        raise ValueError('Finite draw × asset weights and a matching reference required')
    if not len(a):
        return {'mean_L1': np.nan, 'p95_L1': np.nan, 'max_L1': np.nan,
                'mean_half_L1_reallocation': np.nan, 'mean_asset_weight_std': np.nan}
    l1 = np.abs(a - ref).sum(axis=1)
    return {'mean_L1': float(l1.mean()), 'p95_L1': float(np.quantile(l1, .95)),
            'max_L1': float(l1.max()), 'mean_half_L1_reallocation': float(.5 * l1.mean()),
            'mean_asset_weight_std': float(a.std(axis=0, ddof=1).mean()) if len(a) > 1 else np.nan}


def bootstrap(training, mean_bias, config=LabConfig()):
    """IID row bootstrap of training ONLY; common row indices across strategies.

    Bounds: <=30 draws, <=1260 observations, 6 assets, <=7 local Sharpe starts
    per draw. Original checked solver retains its 1000-iteration/start limit.
    """
    config.validate()
    _validate_training(training)
    if len(training) != config.train_steps:
        raise ValueError('Training length must match the logged config')
    _, _, reference, base_diagnostics = fit(training, mean_bias, config.cap, config.annual_rf)
    stream = np.random.SeedSequence(config.seed).spawn(3)[2]
    rng = np.random.default_rng(stream)
    samples = {strategy: [] for strategy in STRATEGIES}
    logs, solver_details = [], []
    for draw in range(config.bootstrap_draws):
        ids = rng.integers(0, len(training), size=len(training))
        sample = training.iloc[ids].reset_index(drop=True)
        sample.index.name = 'synthetic_step'
        _, _, weights, diagnostics = fit(sample, mean_bias, config.cap, config.annual_rf)
        solver_details.append({'draw': draw, 'diagnostics': diagnostics})
        for strategy in STRATEGIES:
            diag = diagnostics[strategy]
            if diag['success']:
                samples[strategy].append(weights[strategy].to_numpy())
            attempts = (diag.get('solver') or {}).get('attempts', [])
            logs.append({'draw': draw, 'strategy': strategy, 'success': diag['success'],
                'checked_violation': diag['checked_violation'],
                'failed_solver_starts': sum(not attempt['success'] for attempt in attempts) if diag.get('solver') is not None else None,
                'error': diag.get('error', ''),
                'sample_index_sha256': hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()})
    rows, distributions = {}, {}
    for strategy in STRATEGIES:
        a = np.array(samples[strategy], float).reshape(-1, 6)
        distributions[strategy] = pd.DataFrame(a, columns=ASSETS)
        stability = instability(a, reference[strategy]) if strategy in reference else instability(np.empty((0, 6)), np.zeros(6))
        rows[strategy] = dict(successful_draws=len(a), failed_draws=config.bootstrap_draws - len(a),
                              reference_available=strategy in reference, **stability)
    return {'summary': pd.DataFrame(rows).T, 'samples': distributions, 'log': pd.DataFrame(logs),
        'metadata': {'warning': WARNING, 'method': 'IID bootstrap, contemporaneous training rows with replacement',
            'seed': config.seed, 'rng_stream': 2, 'draws': config.bootstrap_draws,
            'training_steps': [0, len(training) - 1], 'training_sha256': training_hash(training),
            'base_diagnostics': base_diagnostics, 'draw_diagnostics': solver_details}}


def path_returns(future, target, cost_bps=0., rebalance_every=21):
    """Illustrative later-path trading: drift between fixed 21-step target resets."""
    a, w = np.asarray(future, float), np.asarray(target, float).copy()
    if a.ndim != 2 or not len(a) or a.shape[1] != 6 or w.shape != (6,) or not np.isfinite(a).all() or (a <= -1).any():
        raise ValueError('Invalid synthetic path')
    if not np.isfinite(w).all() or (w < -1e-7).any() or not np.isclose(w.sum(), 1):
        raise ValueError('Invalid target')
    if not np.isfinite(cost_bps) or not 0 <= cost_bps <= 100 or not isinstance(rebalance_every, int) or rebalance_every < 1:
        raise ValueError('Invalid cost or rebalance interval')
    target = w.copy()
    result, trades = [], []
    for step, r in enumerate(a):
        traded = 0.
        if step % rebalance_every == 0:
            traded = 1. if step == 0 else float(np.abs(target - w).sum())
            w = target.copy()
        gross = 1 + w @ r
        result.append((1 - traded * cost_bps / 10000) * gross - 1)
        trades.append(traded)
        w *= (1 + r) / gross
    return pd.DataFrame({'return': result, 'gross_traded_notional': trades}, index=future.index)


def path_metrics(returns, annual_rf):
    r = pd.Series(returns, dtype=float)
    if len(r) < 2 or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError('Need two valid simple returns')
    wealth = (1 + r).cumprod()
    dd = wealth / wealth.cummax().clip(lower=1) - 1
    vol = float(r.std(ddof=1) * np.sqrt(DAYS))
    return {'CAGR': float(np.expm1(np.log1p(r).sum() * DAYS / len(r))), 'volatility': vol,
        'sharpe': float((r.mean() - risk_free_daily(annual_rf)) * DAYS / vol) if vol > 1e-12 else np.nan,
        'cumulative_return': float(wealth.iloc[-1] - 1), 'max_drawdown': float(dd.min())}


def analyze(scenario, config=LabConfig()):
    config.validate()
    _validate_training(scenario.training)
    expected_future = pd.RangeIndex(config.train_steps, config.train_steps + config.future_steps, name='synthetic_step')
    if len(scenario.training) != config.train_steps or not scenario.future.index.equals(expected_future) or tuple(scenario.future.columns) != ASSETS:
        raise ValueError('Synthetic training and future steps must be disjoint, contiguous and match config')
    mu, cov, weights, diagnostics = fit(scenario.training, scenario.mean_bias, config.cap, config.annual_rf)
    baseline = construct('baseline', config)
    _, _, baseline_weights, _ = fit(baseline.training, baseline.mean_bias, config.cap, config.annual_rf)
    estimated, changes, realized = {}, {}, []
    paths = {}
    for strategy in weights:
        w = weights[strategy].to_numpy()
        stats = portfolio_stats(w, mu, cov, config.annual_rf)
        estimated[strategy] = dict(estimated_arithmetic_return=stats['expected_return'],
            estimated_volatility=stats['volatility'], estimated_sharpe=stats['sharpe'],
            target_HHI=float(w @ w), max_target_weight=float(w.max()),
            constructed_future_volatility=float(np.sqrt(w @ scenario.future_covariance @ w)))
        if strategy in baseline_weights:
            changes[strategy] = w - baseline_weights[strategy].to_numpy()
        for cost in (0., 10.):
            bt = path_returns(scenario.future, w, cost)
            paths[(strategy, cost)] = bt['return']
            realized.append(dict(strategy=strategy, cost_bps=cost,
                gross_traded_notional=float(bt['gross_traded_notional'].sum()),
                **path_metrics(bt['return'], config.annual_rf)))
    robust = bootstrap(scenario.training, scenario.mean_bias, config)
    manifest = {'warning': WARNING, 'version': '006-synthetic-lab-v1', 'config': asdict(config),
        'scenario': scenario.name, 'scenario_description': SCENARIOS[scenario.name], 'assets': ASSETS,
        'assumed_true_annual_means': ANNUAL_MEANS.tolist(), 'assumed_estimator_mean_bias': scenario.mean_bias.tolist(),
        'assumed_training_covariance': scenario.train_covariance.tolist(), 'assumed_future_covariance': scenario.future_covariance.tolist(),
        'training_sha256': training_hash(scenario.training), 'future_sha256': training_hash(scenario.future),
        'training_steps': [0, config.train_steps - 1],
        'future_steps': [config.train_steps, config.train_steps + config.future_steps - 1],
        'generator': 'Gaussian one-factor plus independent idiosyncratic normals; PCG64/SeedSequence streams 0=train, 1=future, 2=bootstrap',
        'rebalancing': 'every 21 synthetic steps, before return; drift between resets; initial gross trade = 1',
        'costs': '0 and 10 bps per gross traded notional; proportional multiplicative approximation',
        'versions': {name: version(name) for name in ('numpy', 'pandas', 'scipy')},
        'diagnostics': diagnostics, 'bootstrap': robust['metadata']}
    return {'weights': weights, 'changes_from_baseline': pd.DataFrame(changes, index=ASSETS),
        'estimated': pd.DataFrame(estimated).T, 'realized': pd.DataFrame(realized),
        'paths': paths, 'bootstrap': robust, 'manifest': manifest}


def run(name='baseline', config=LabConfig()):
    return analyze(construct(name, config), config)


def labeled(table):
    """Persistent provenance carried inside every UI/download table."""
    result = table.copy()
    result.insert(0, 'Evidence', WARNING)
    return result


def json_safe(value):
    """Strict JSON: unavailable diagnostics are null, never invented zeros."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_safe(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


def main():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=WARNING)
    parser.add_argument('--scenario', choices=[*SCENARIOS, 'all'], default='baseline')
    parser.add_argument('--seed', type=int, default=6006)
    parser.add_argument('--draws', type=int, default=20)
    parser.add_argument('--output', type=Path, default=Path('work/synthetic'))
    args = parser.parse_args()
    config = LabConfig(seed=args.seed, bootstrap_draws=args.draws)
    config.validate()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in (SCENARIOS if args.scenario == 'all' else [args.scenario]):
        result = run(name, config)
        payload = {'manifest': result['manifest'], 'tables': {key: labeled(result[key]).reset_index().to_dict(orient='records')
            for key in ('weights', 'changes_from_baseline', 'estimated', 'realized')},
            'bootstrap_summary': labeled(result['bootstrap']['summary']).reset_index().to_dict(orient='records'),
            'bootstrap_log': labeled(result['bootstrap']['log']).to_dict(orient='records')}
        (args.output / f'SYNTHETIC_{name}.json').write_text(json.dumps(json_safe(payload), indent=2, allow_nan=False))
        print(f'{WARNING} | {name} | saved seeded diagnostics to {args.output}')


if __name__ == '__main__':
    main()
