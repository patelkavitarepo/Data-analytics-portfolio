"""Predeclared focused synthetic investigation; additive to synthetic lab v1.

SYNTHETIC DATA — NOT EMPIRICAL RESULTS. No provider or empirical-protocol inputs.
See SYNTHETIC_ROBUSTNESS_PLAN.md; declare this grid before generating outcomes.
"""

SEEDS = (6006, 6007, 6008, 6009, 6010)
WINDOWS = (126, 504)
TRAIN_POOL = 504
FUTURE_STEPS = 252
DRAWS = 10
CAP = .35
ANNUAL_RF = .02
CAP_TOLERANCE = 1e-7
VERSION = '006-synthetic-robustness-v2'

from dataclasses import asdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import synthetic as lab

PREDECLARATION_COMMIT = '6231b6ca9b8e9d914f65dc0e8ecf24259307986c'
PLAN = {
    'version': VERSION, 'warning': lab.WARNING, 'seeds': list(SEEDS), 'windows': list(WINDOWS),
    'training_pool': TRAIN_POOL, 'future_steps': FUTURE_STEPS, 'bootstrap_draws': DRAWS,
    'cap': CAP, 'annual_rf': ANNUAL_RF, 'cap_tolerance': CAP_TOLERANCE,
    'training_correlation': .35, 'stationary_future_correlation': .35, 'jump_future_correlation': .85,
    'training_window_rule': 'nested trailing windows ending at original step 503',
    'future_rule': 'same stream-1 innovations across scenarios and windows; original steps 504..755',
    'aggregation': 'median, minimum, maximum across five seeds separately by window/strategy/cost; no confidence interval',
    'cost_bps': [0., 10.], 'rebalancing_steps': 21,
}


def _validate_case(seed, window):
    if seed not in SEEDS or window not in WINDOWS:
        raise ValueError('Case outside predeclared seeds 6006..6010 and windows 126/504')


def training_sample(seed, window):
    """Generate only training; no future object or covariance argument is accepted."""
    _validate_case(seed, window)
    stream = np.random.SeedSequence(seed).spawn(3)[0]
    z = np.random.default_rng(stream).standard_normal((TRAIN_POOL, 7))
    pool = lab._draw(z, .35, np.ones(6), lab.ANNUAL_VOLS)
    return pd.DataFrame(pool[-window:], columns=lab.ASSETS,
                        index=pd.RangeIndex(window, name='synthetic_step'))


def future_paths(seed):
    """Future is independent of training-window length; paired latent innovations."""
    if seed not in SEEDS:
        raise ValueError('Future seed outside predeclared grid')
    stream = np.random.SeedSequence(seed).spawn(3)[1]
    z = np.random.default_rng(stream).standard_normal((FUTURE_STEPS, 7))
    index = pd.RangeIndex(TRAIN_POOL, TRAIN_POOL + FUTURE_STEPS, name='synthetic_step')
    return {name: pd.DataFrame(lab._draw(z, rho, np.ones(6), lab.ANNUAL_VOLS),
                               columns=lab.ASSETS, index=index)
            for name, rho in [('stationary_baseline', .35), ('unseen_positive_jump', .85)]}


def concentration(weights):
    w = np.asarray(weights, float)
    if w.shape != (6,) or not np.isfinite(w).all() or (w < -CAP_TOLERANCE).any() or abs(w.sum() - 1) > CAP_TOLERANCE or w.max() > CAP + CAP_TOLERANCE:
        raise ValueError('Invalid constrained target for concentration diagnostics')
    hhi = float(w @ w)
    count = int(np.count_nonzero(np.abs(w - CAP) <= CAP_TOLERANCE))
    return {'HHI': hhi, 'effective_number': 1 / hhi, 'max_weight': float(w.max()),
            'cap_count': count, 'any_cap_binding': bool(count)}


def train_case(seed, window):
    """Fit and bootstrap completely before constructing/evaluating future paths."""
    training = training_sample(seed, window)
    config = lab.LabConfig(seed=seed, train_steps=window, future_steps=FUTURE_STEPS,
                           bootstrap_draws=DRAWS, cap=CAP, annual_rf=ANNUAL_RF)
    mu, cov, weights, diagnostics = lab.fit(training, np.zeros(6), CAP, ANNUAL_RF)
    robust = lab.bootstrap(training, np.zeros(6), config)
    fit_id = hashlib.sha256(json.dumps({'training_hash': lab.training_hash(training),
        'config': asdict(config)}, sort_keys=True).encode()).hexdigest()
    logs = robust['log'].copy()
    logs.insert(0, 'window', window)
    logs.insert(0, 'seed', seed)
    for strategy in lab.STRATEGIES:
        frame = robust['samples'][strategy]
        successful_rows = logs.index[(logs['strategy'] == strategy) & logs['success']]
        if len(successful_rows) != len(frame):
            raise ValueError('Bootstrap successful-draw mapping mismatch')
        for row_id, (_, sample) in zip(successful_rows, frame.iterrows()):
            for key, value in concentration(sample).items():
                logs.loc[row_id, key] = value
            for asset, weight in sample.items():
                logs.loc[row_id, f'weight_{asset}'] = weight
    target_rows = []
    for strategy in lab.STRATEGIES:
        diag = diagnostics[strategy]
        row = {'seed': seed, 'window': window, 'strategy': strategy,
               'fit_success': diag['success'], 'fit_error': diag.get('error', ''),
               'checked_violation': diag['checked_violation'],
               'fit_id': fit_id, 'bootstrap_reuse_id': fit_id + ':iid-stream-2',
               'training_sha256': lab.training_hash(training)}
        for field, value in robust['summary'].loc[strategy].items():
            row['bootstrap_' + field] = value
        sample_stats = logs.loc[(logs['strategy'] == strategy) & logs['success']]
        for name, field in [('cap_binding_incidence', 'any_cap_binding'), ('mean_cap_count', 'cap_count'),
                            ('mean_HHI', 'HHI'), ('mean_effective_number', 'effective_number'),
                            ('mean_max_weight', 'max_weight')]:
            row['bootstrap_' + name] = float(pd.to_numeric(sample_stats[field]).mean()) if field in sample_stats and len(sample_stats) else np.nan
        if diag['success']:
            w = weights[strategy].to_numpy()
            row.update(concentration(w))
            row.update({f'weight_{asset}': float(weight) for asset, weight in zip(lab.ASSETS, w)})
            stats = lab.portfolio_stats(w, mu, cov, ANNUAL_RF)
            row.update({'estimated_volatility': stats['volatility'], 'estimated_sharpe': stats['sharpe'],
                        'estimated_arithmetic_return': stats['expected_return']})
        target_rows.append(row)
    return {'weights': weights, 'targets': pd.DataFrame(target_rows), 'bootstrap_log': logs,
        'manifest': {'seed': seed, 'window': window, 'draws': DRAWS,
            'training_source_positions': [TRAIN_POOL - window, TRAIN_POOL - 1],
            'training_reindexed_positions': [0, window - 1], 'future_source_positions': [TRAIN_POOL, TRAIN_POOL + FUTURE_STEPS - 1],
            'training_sha256': lab.training_hash(training), 'fit_id': fit_id,
            'bootstrap_reuse_id': fit_id + ':iid-stream-2', 'fit_diagnostics': diagnostics,
            'bootstrap_full_details': robust['metadata']}}


def evaluate_case(trained, paths):
    """Only evaluate frozen targets here; this function performs no optimization."""
    expected = pd.RangeIndex(TRAIN_POOL, TRAIN_POOL + FUTURE_STEPS, name='synthetic_step')
    if set(paths) != {'stationary_baseline', 'unseen_positive_jump'}:
        raise ValueError('Need both paired future conditions')
    for frame in paths.values():
        if not frame.index.equals(expected) or tuple(frame.columns) != lab.ASSETS or not np.isfinite(frame.to_numpy()).all() or (frame <= -1).any(axis=None):
            raise ValueError('Future data must be valid returns on disjoint source steps 504..755')
    seed, window = trained['manifest']['seed'], trained['manifest']['window']
    risks, paired_paths = [], []
    cov_base, cov_jump = lab.covariance(.35), lab.covariance(.85)
    for strategy in lab.STRATEGIES:
        good = strategy in trained['weights']
        common = {'seed': seed, 'window': window, 'strategy': strategy, 'available': good,
                  'fit_id': trained['manifest']['fit_id'], 'bootstrap_reuse_id': trained['manifest']['bootstrap_reuse_id']}
        risk = dict(common, paired_target_L1=np.nan, baseline_known_volatility=np.nan,
                    jump_known_volatility=np.nan, known_volatility_ratio=np.nan)
        if good:
            base_target = trained['weights'][strategy].to_numpy().copy()
            jump_target = base_target.copy()  # No informed refit; equality is intentional.
            vb = float(np.sqrt(base_target @ cov_base @ base_target))
            vj = float(np.sqrt(jump_target @ cov_jump @ jump_target))
            risk.update(paired_target_L1=float(np.abs(jump_target - base_target).sum()),
                        baseline_known_volatility=vb, jump_known_volatility=vj, known_volatility_ratio=vj/vb)
        risks.append(risk)
        for cost in PLAN['cost_bps']:
            row = dict(common, cost_bps=cost)
            if good:
                for name, target in [('stationary_baseline', base_target), ('unseen_positive_jump', jump_target)]:
                    bt = lab.path_returns(paths[name], target, cost, PLAN['rebalancing_steps'])
                    for metric, value in lab.path_metrics(bt['return'], ANNUAL_RF).items():
                        row[f'{name}_{metric}'] = value
                    row[f'{name}_gross_traded_notional'] = float(bt['gross_traded_notional'].sum())
                for metric in ('CAGR', 'volatility', 'sharpe', 'max_drawdown', 'cumulative_return'):
                    row[f'jump_minus_baseline_{metric}'] = row[f'unseen_positive_jump_{metric}'] - row[f'stationary_baseline_{metric}']
                row['jump_realized_vol_higher'] = row['jump_minus_baseline_volatility'] > 0
                row['jump_drawdown_more_negative'] = row['jump_minus_baseline_max_drawdown'] < 0
            paired_paths.append(row)
    return {'paired_risk': pd.DataFrame(risks), 'paired_paths': pd.DataFrame(paired_paths),
            'future_hashes': {name: lab.training_hash(frame) for name, frame in paths.items()}}


def run_case(seed, window):
    trained = train_case(seed, window)
    evaluated = evaluate_case(trained, future_paths(seed))
    return {**trained, **evaluated}


def aggregate(frame, groups, metrics):
    """Descriptive across-seed summaries; missing/failed values keep valid counts."""
    rows = []
    for keys, group in frame.groupby(groups, dropna=False, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        if group['seed'].duplicated().any():
            raise ValueError('Aggregate cannot double-count paired futures as independent seeds')
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors='coerce').dropna() if metric in group else pd.Series(dtype=float)
            rows.append(dict(zip(groups, keys), metric=metric, planned_seed_count=len(SEEDS),
                recorded_seed_count=len(group), valid_seed_count=len(values),
                median=float(values.median()) if len(values) else np.nan,
                minimum=float(values.min()) if len(values) else np.nan,
                maximum=float(values.max()) if len(values) else np.nan))
    return pd.DataFrame(rows)


def window_changes(targets):
    rows = []
    for seed in SEEDS:
        for strategy in lab.STRATEGIES:
            pair = targets[(targets['seed'] == seed) & (targets['strategy'] == strategy)].set_index('window')
            good = all(window in pair.index and pair.loc[window, 'fit_success'] for window in WINDOWS)
            row = {'seed': seed, 'strategy': strategy, 'available': good}
            if good:
                short, long = pair.loc[126], pair.loc[504]
                row['half_L1_short_vs_long'] = .5 * sum(abs(short[f'weight_{a}'] - long[f'weight_{a}']) for a in lab.ASSETS)
                for metric in ('HHI', 'effective_number', 'cap_count', 'bootstrap_mean_half_L1_reallocation'):
                    row['short_' + metric] = short[metric]
                    row['long_' + metric] = long[metric]
                    row['short_minus_long_' + metric] = short[metric] - long[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def run_grid():
    cases = [run_case(seed, window) for seed in SEEDS for window in WINDOWS]
    tables = {key: pd.concat([case[key] for case in cases], ignore_index=True)
              for key in ('targets', 'paired_risk', 'paired_paths', 'bootstrap_log')}
    tables['window_changes'] = window_changes(tables['targets'])
    target_metrics = ['HHI', 'effective_number', 'max_weight', 'cap_count',
        'bootstrap_mean_half_L1_reallocation', 'bootstrap_mean_asset_weight_std',
        'bootstrap_cap_binding_incidence', 'bootstrap_mean_cap_count', 'bootstrap_mean_HHI',
        'bootstrap_successful_draws', 'bootstrap_failed_draws']
    tables['aggregate_targets'] = aggregate(tables['targets'], ['window', 'strategy'], target_metrics)
    tables['aggregate_risk'] = aggregate(tables['paired_risk'], ['window', 'strategy'],
        ['paired_target_L1', 'baseline_known_volatility', 'jump_known_volatility', 'known_volatility_ratio'])
    path_metrics = [f'{condition}_{metric}' for condition in ('stationary_baseline', 'unseen_positive_jump', 'jump_minus_baseline')
                    for metric in ('volatility', 'max_drawdown', 'sharpe', 'CAGR')]
    tables['aggregate_paths'] = aggregate(tables['paired_paths'], ['window', 'strategy', 'cost_bps'], path_metrics)
    tables['aggregate_window_changes'] = aggregate(tables['window_changes'], ['strategy'],
        ['half_L1_short_vs_long', 'short_minus_long_HHI', 'short_minus_long_cap_count',
         'short_minus_long_bootstrap_mean_half_L1_reallocation'])
    direction_rows = []
    for keys, frame in tables['paired_paths'].groupby(['window', 'strategy', 'cost_bps']):
        valid = frame.loc[frame['available']]
        direction_rows.append(dict(zip(['window', 'strategy', 'cost_bps'], keys),
            planned_seeds=len(SEEDS), available_seeds=len(valid),
            jump_realized_vol_higher_count=int(valid['jump_realized_vol_higher'].sum()) if len(valid) else 0,
            jump_drawdown_more_negative_count=int(valid['jump_drawdown_more_negative'].sum()) if len(valid) else 0))
    tables['realized_direction_counts'] = pd.DataFrame(direction_rows)
    root = Path(__file__).resolve().parents[1]
    logs = tables['bootstrap_log']
    manifest = {'warning': lab.WARNING, 'plan': PLAN, 'predeclaration_commit': PREDECLARATION_COMMIT,
        'predeclaration_sha256': hashlib.sha256((root / 'SYNTHETIC_ROBUSTNESS_PLAN.md').read_bytes()).hexdigest(),
        'preserved_lab_summary_sha256': hashlib.sha256((root / 'synthetic-default-summary.json').read_bytes()).hexdigest(),
        'true_annual_means': lab.ANNUAL_MEANS.tolist(), 'true_annual_volatilities': lab.ANNUAL_VOLS.tolist(),
        'versions': {name: version(name) for name in ('numpy', 'pandas', 'scipy')},
        'case_manifests': [{key: value for key, value in case['manifest'].items() if key != 'bootstrap_full_details'} |
                           {'future_hashes': case['future_hashes']} for case in cases],
        'counts': {'planned_training_cases': len(SEEDS)*len(WINDOWS), 'fitted_strategy_rows': len(tables['targets']),
            'fit_failures': int((~tables['targets']['fit_success']).sum()),
            'fit_known_failed_solver_starts': sum(not a['success'] for case in cases
                for diag in case['manifest']['fit_diagnostics'].values()
                for a in (diag.get('solver') or {}).get('attempts', [])),
            'bootstrap_strategy_rows': len(logs), 'bootstrap_failed_candidates': int((~logs['success']).sum()),
            'known_failed_solver_starts': int(logs['failed_solver_starts'].sum()),
            'unknown_solver_start_counts': int(logs['failed_solver_starts'].isna().sum()),
            'max_checked_bootstrap_violation': float(logs['checked_violation'].max())}}
    return {'manifest': manifest, 'tables': tables,
            'full_bootstrap_diagnostics': [case['manifest']['bootstrap_full_details'] for case in cases]}


def export_report(result):
    return lab.json_safe({'manifest': result['manifest'],
        'tables': {key: lab.labeled(frame).to_dict(orient='records') for key, frame in result['tables'].items()}})



def load_report(path=None):
    """Read the bounded, committed synthetic report without refitting or networking."""
    root = Path(__file__).resolve().parents[1]
    path = root / 'synthetic-robustness-results.json' if path is None else Path(path)
    result = json.loads(path.read_text())
    manifest = result['manifest']
    if manifest.get('warning') != lab.WARNING or manifest.get('plan') != PLAN:
        raise ValueError('Report does not match the predeclared synthetic grid')
    if manifest.get('predeclaration_sha256') != hashlib.sha256((root / 'SYNTHETIC_ROBUSTNESS_PLAN.md').read_bytes()).hexdigest():
        raise ValueError('Predeclaration changed: preserve/version the plan before regenerating')
    if manifest.get('preserved_lab_summary_sha256') != hashlib.sha256((root / 'synthetic-default-summary.json').read_bytes()).hexdigest():
        raise ValueError('Original synthetic baseline artifact changed')
    pairs = [(case['seed'], case['window']) for case in manifest['case_manifests']]
    if len(pairs) != len(SEEDS)*len(WINDOWS) or set(pairs) != {(seed, window) for seed in SEEDS for window in WINDOWS}:
        raise ValueError('Report must retain every predeclared seed/window exactly once')
    for rows in result['tables'].values():
        if any(row.get('Evidence') != lab.WARNING for row in rows):
            raise ValueError('Every exported table row must retain the synthetic evidence label')
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=lab.WARNING + ' | fixed predeclared robustness grid')
    parser.add_argument('--output', type=Path, default=Path('work/synthetic-robustness-v2'))
    args = parser.parse_args()
    result = run_grid()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'SYNTHETIC_robustness_report.json').write_text(json.dumps(export_report(result), indent=2, allow_nan=False))
    (args.output / 'SYNTHETIC_full_solver_diagnostics.json').write_text(json.dumps(lab.json_safe({
        'warning': lab.WARNING, 'plan': PLAN, 'details': result['full_bootstrap_diagnostics']}), indent=2, allow_nan=False))
    print(lab.WARNING)
    print(json.dumps(result['manifest']['counts'], indent=2))
    print(f'Fixed grid saved to {args.output}; all seeds/windows retained. No provider input or empirical conclusion.')


if __name__ == '__main__':
    main()
