"""Independent predeclared v3 synthetic serial-dependence study.
SYNTHETIC DATA — NOT EMPIRICAL RESULTS.
"""
SEEDS = (6006, 6007, 6008, 6009, 6010)
PHIS = (0., .5)
TRAIN_STEPS = 504
DRAWS = 15
BLOCK_LENGTH = 5
CAP = .35
ANNUAL_RF = .02
MATERIALITY = .02
VERSION = '006-synthetic-serial-v3'

import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import synthetic as lab
from .synthetic_robustness import concentration

PREDECLARATION_COMMIT = 'dd77e94'
METHODS = ('iid', 'circular_mbb')
ROOT = Path(__file__).resolve().parents[1]
PRESERVED = ('markowitz/synthetic.py', 'markowitz/synthetic_robustness.py',
    'synthetic-default-summary.json', 'synthetic-robustness-results.json',
    'SYNTHETIC_ROBUSTNESS_PLAN.md', 'markowitz/analytics.py', 'markowitz/research.py',
    'markowitz/data.py', 'markowitz/source_policy.py', 'markowitz/verification.py')
PLAN = dict(version=VERSION, seeds=list(SEEDS), phis=list(PHIS), training_steps=TRAIN_STEPS,
    draws=DRAWS, methods=list(METHODS), block_length=BLOCK_LENGTH, cap=CAP,
    annual_rf=ANNUAL_RF, materiality_half_L1=MATERIALITY,
    initialization='exact stationary Gaussian; no burn-in',
    resampling='complete vectors; circular 5-row blocks, last block truncated; shared stream-2 starts',
    generator_stream=0, unused_reserved_stream=1, resampling_stream=2)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stationary_ar(innovations, phi):
    """First centered row initializes stationary state; remaining rows are innovations.

    Input rows independently have covariance C. Output covariance C, lag k phi**k C.
    This pure recurrence accepts no future, optimization or provider object.
    """
    z = np.asarray(innovations, float)
    if not np.isfinite(phi) or abs(phi) >= 1 or z.ndim != 2 or len(z) < 2 or z.shape[1] != 6 or not np.isfinite(z).all():
        raise ValueError('Finite six-vector innovations and stationary |phi| < 1 required')
    result = np.empty_like(z[1:])
    state = z[0].copy()
    for t, epsilon in enumerate(z[1:]):
        state = phi * state + np.sqrt(1 - phi**2) * epsilon
        result[t] = state
    return result


def training_sample(seed, phi):
    if seed not in SEEDS or phi not in PHIS:
        raise ValueError('Outside predeclared seed/phi grid')
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[0])
    z = rng.standard_normal((TRAIN_STEPS + 1, 7))
    centered = (np.sqrt(.35)*z[:, :1] + np.sqrt(.65)*z[:, 1:]) * lab.ANNUAL_VOLS / np.sqrt(lab.DAYS)
    a = stationary_ar(centered, phi) + lab.ANNUAL_MEANS / lab.DAYS
    return pd.DataFrame(a, columns=lab.ASSETS, index=pd.RangeIndex(TRAIN_STEPS, name='synthetic_step'))


def resampling_starts(seed):
    if seed not in SEEDS:
        raise ValueError('Outside predeclared seeds')
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[2])
    return rng.integers(0, TRAIN_STEPS, size=(DRAWS, TRAIN_STEPS))


def sample_indices(starts, method, block_length=BLOCK_LENGTH):
    """Complete-vector indices; circular blocks preserve order internally, not at joins."""
    a = np.asarray(starts)
    if a.shape != (TRAIN_STEPS,) or not np.issubdtype(a.dtype, np.integer) or (a < 0).any() or (a >= TRAIN_STEPS).any():
        raise ValueError('Exactly 504 valid training indices required')
    if not isinstance(block_length, int) or not 1 <= block_length <= TRAIN_STEPS:
        raise ValueError('Invalid block length')
    if method == 'iid':
        return a.copy()
    if method != 'circular_mbb':
        raise ValueError('Unknown resampling method')
    count = (TRAIN_STEPS + block_length - 1) // block_length
    return ((a[:count, None] + np.arange(block_length)) % TRAIN_STEPS).ravel()[:TRAIN_STEPS]


def checked_training(training):
    lab._validate_training(training)
    if len(training) != TRAIN_STEPS:
        raise ValueError('Only the 504-row ordinal training sample is accepted')


def solver_fields(diag):
    solver = diag.get('solver')
    attempts = solver.get('attempts', []) if solver is not None else None
    return dict(success=bool(diag['success']), checked_violation=diag['checked_violation'],
        failed_solver_starts=sum(not a['success'] for a in attempts) if attempts is not None else None,
        error=diag.get('error', ''))


def summarize_draws(log, references):
    """Successful draws only; explicit missing reference and dispersion denominators."""
    rows = []
    for method in METHODS:
        for strategy in lab.STRATEGIES:
            subset = log.loc[(log.method == method) & (log.strategy == strategy)]
            if subset.draw.duplicated().any() or not subset.draw.isin(range(DRAWS)).all():
                raise ValueError('Duplicate or out-of-range bootstrap draw')
            valid = subset.loc[subset.success]
            available = strategy in references
            distances = valid.half_L1.dropna()
            row = dict(method=method, strategy=strategy, planned_draws=DRAWS,
                recorded_draws=len(subset), unrecorded_draws=DRAWS-len(subset),
                successful_draws=len(valid), failed_draws=len(subset)-len(valid),
                reference_available=available, valid_distance_draws=len(distances),
                mean_half_L1=distances.mean(), sd_half_L1=distances.std(ddof=1),
                p05_half_L1=distances.quantile(.05), p50_half_L1=distances.quantile(.5),
                p95_half_L1=distances.quantile(.95),
                mean_asset_weight_std=valid[list(lab.ASSETS)].std(ddof=1).mean() if len(valid) >= 2 else np.nan,
                known_failed_solver_starts=subset.failed_solver_starts.sum(min_count=1),
                unknown_solver_start_counts=int(subset.failed_solver_starts.isna().sum()),
                max_checked_violation=subset.checked_violation.max())
            for metric in ('HHI', 'effective_number', 'max_weight', 'cap_count', 'any_cap_binding'):
                row['bootstrap_mean_' + metric] = valid[metric].mean()
                row['target_' + metric] = concentration(references[strategy])[metric] if available else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def analyze_training(training, seed, phi):
    """Training-only interface. No future data, future covariance, or empirical source."""
    checked_training(training)
    if seed not in SEEDS or phi not in PHIS:
        raise ValueError('Outside predeclared seed/phi grid')
    _, _, references, base_diag = lab.fit(training, np.zeros(6), CAP, ANNUAL_RF)
    starts = resampling_starts(seed)
    logs, indices, full_diagnostics = [], [], []
    for method in METHODS:
        for draw, source in enumerate(starts):
            ids = sample_indices(source, method)
            sample = training.iloc[ids].reset_index(drop=True)
            sample.index.name = 'synthetic_step'
            _, _, weights, diagnostics = lab.fit(sample, np.zeros(6), CAP, ANNUAL_RF)
            index_hash = digest(ids.astype('<i8').tobytes())
            indices.append(dict(seed=seed, phi=phi, method=method, draw=draw,
                sample_index_sha256=index_hash, source_indices=ids.tolist(),
                block_starts=source[:101].tolist() if method == 'circular_mbb' else None))
            full_diagnostics.append(dict(method=method, draw=draw, diagnostics=diagnostics))
            for strategy in lab.STRATEGIES:
                row = dict(seed=seed, phi=phi, method=method, draw=draw, strategy=strategy,
                    sample_index_sha256=index_hash, half_L1=np.nan, **solver_fields(diagnostics[strategy]))
                # All missing metrics retained on failed candidates; never zero-imputed.
                row.update({m: np.nan for m in ('HHI', 'effective_number', 'max_weight', 'cap_count', 'any_cap_binding', *lab.ASSETS)})
                if row['success']:
                    w = weights[strategy].to_numpy()
                    row.update(concentration(w))
                    row.update(dict(zip(lab.ASSETS, w)))
                    if strategy in references:
                        row['half_L1'] = .5 * float(np.abs(w - references[strategy]).sum())
                logs.append(row)
    log = pd.DataFrame(logs)
    summary = summarize_draws(log, references)
    summary.insert(0, 'phi', phi)
    summary.insert(0, 'seed', seed)
    return dict(summary=summary, log=log, index_records=indices,
        manifest=dict(seed=seed, phi=phi, training_sha256=lab.training_hash(training),
            training_steps=[0, TRAIN_STEPS-1], reference_weights=references.to_dict(),
            reference_diagnostics=base_diag, starts_sha256=digest(starts.astype('<i8').tobytes()),
            sample_lag1=[training.iloc[:, i].autocorr(1) for i in range(6)],
            sample_annual_means=(training.mean()*lab.DAYS).tolist(),
            sample_annual_vols=(training.std()*np.sqrt(lab.DAYS)).tolist(),
            sample_correlation=training.corr().to_numpy().tolist()),
        full_diagnostics=full_diagnostics)


def paired_differences(summary):
    keys = ['seed', 'phi', 'strategy']
    left = summary.loc[summary.method == 'iid'].set_index(keys)
    right = summary.loc[summary.method == 'circular_mbb'].set_index(keys)
    if left.index.has_duplicates or right.index.has_duplicates or not left.index.equals(right.index):
        raise ValueError('Each method must have exactly one matched seed/phi/strategy')
    result = pd.DataFrame(index=left.index)
    for metric in ('mean_half_L1', 'p95_half_L1', 'mean_asset_weight_std',
                   'bootstrap_mean_HHI', 'bootstrap_mean_effective_number', 'bootstrap_mean_any_cap_binding'):
        result['iid_' + metric] = left[metric]
        result['mbb_' + metric] = right[metric]
        result['delta_' + metric] = right[metric] - left[metric]
    result['material_difference'] = [bool(abs(x) >= MATERIALITY) if pd.notna(x) else None for x in result.delta_mean_half_L1]
    return result.reset_index()


def across_seeds(frame, groups, metrics):
    rows = []
    for key, group in frame.groupby(groups, sort=True):
        if group.seed.duplicated().any():
            raise ValueError('Do not pool repeated seeds/paired methods')
        for metric in metrics:
            a = group[metric].dropna()
            rows.append(dict(zip(groups, key), metric=metric, planned_seeds=len(SEEDS),
                recorded_seeds=len(group), valid_seeds=len(a), median=a.median(), minimum=a.min(), maximum=a.max()))
    return pd.DataFrame(rows)


def run_grid():
    cases = [analyze_training(training_sample(seed, phi), seed, phi) for seed in SEEDS for phi in PHIS]
    summary = pd.concat([c['summary'] for c in cases], ignore_index=True)
    log = pd.concat([c['log'] for c in cases], ignore_index=True)
    paired = paired_differences(summary)
    indices = pd.DataFrame([row for c in cases for row in c['index_records']])
    counts = dict(training_cases=len(cases), reference_failures=sum(not d['success'] for c in cases for d in c['manifest']['reference_diagnostics'].values()),
        reference_known_failed_solver_starts=sum(not a['success'] for c in cases for d in c['manifest']['reference_diagnostics'].values() for a in (d.get('solver') or {}).get('attempts', [])),
        bootstrap_strategy_rows=len(log), failed_candidates=int((~log.success).sum()),
        known_failed_solver_starts=int(log.failed_solver_starts.sum()),
        unknown_solver_start_counts=int(log.failed_solver_starts.isna().sum()),
        max_checked_violation=float(log.checked_violation.max()))
    return dict(manifest=dict(warning=lab.WARNING, plan=PLAN, predeclaration_commit=PREDECLARATION_COMMIT,
        predeclaration_sha256=digest((ROOT/'SYNTHETIC_SERIAL_PLAN.md').read_bytes()),
        preserved_sha256={p: digest((ROOT/p).read_bytes()) for p in PRESERVED},
        true_annual_means=lab.ANNUAL_MEANS.tolist(), true_annual_marginal_covariance=lab.covariance(.35, np.ones(6), lab.ANNUAL_VOLS).tolist(),
        versions={p: version(p) for p in ('numpy', 'pandas', 'scipy')}, counts=counts,
        cases=[c['manifest'] for c in cases]),
        tables=dict(summary=summary, paired_differences=paired, bootstrap_log=log, resampling_indices=indices,
            aggregate_methods=across_seeds(summary, ['phi', 'strategy', 'method'],
                ['mean_half_L1', 'p95_half_L1', 'bootstrap_mean_HHI', 'bootstrap_mean_effective_number', 'bootstrap_mean_any_cap_binding']),
            aggregate_differences=across_seeds(paired, ['phi', 'strategy'],
                ['delta_mean_half_L1', 'delta_p95_half_L1', 'delta_bootstrap_mean_HHI', 'delta_bootstrap_mean_any_cap_binding'])),
        full_diagnostics=[dict(seed=c['manifest']['seed'], phi=c['manifest']['phi'], details=c['full_diagnostics']) for c in cases])


def export_report(result):
    return lab.json_safe(dict(manifest=result['manifest'], tables={k: lab.labeled(v).to_dict(orient='records') for k, v in result['tables'].items()}))


def load_report(path=None):
    report = json.loads((ROOT/'synthetic-serial-results.json' if path is None else Path(path)).read_text())
    manifest = report['manifest']
    if manifest.get('warning') != lab.WARNING or manifest.get('plan') != PLAN:
        raise ValueError('Invalid synthetic serial report plan/label')
    if manifest['predeclaration_sha256'] != digest((ROOT/'SYNTHETIC_SERIAL_PLAN.md').read_bytes()):
        raise ValueError('Predeclared serial plan changed')
    if set(manifest['preserved_sha256']) != set(PRESERVED) or any(digest((ROOT/p).read_bytes()) != h for p, h in manifest['preserved_sha256'].items()):
        raise ValueError('Earlier results or frozen safeguards changed')
    pairs = [(c['seed'], c['phi']) for c in manifest['cases']]
    if len(pairs) != 10 or set(pairs) != {(s, p) for s in SEEDS for p in PHIS}:
        raise ValueError('All predeclared cases required exactly once')
    if any(row.get('Evidence') != lab.WARNING for rows in report['tables'].values() for row in rows):
        raise ValueError('Every row must carry the synthetic evidence label')
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=lab.WARNING + ' | fixed serial-dependence grid')
    parser.add_argument('--output', type=Path, default=Path('work/synthetic-serial-v3'))
    args = parser.parse_args()
    result = run_grid()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'SYNTHETIC_serial_report.json').write_text(json.dumps(export_report(result), indent=2, allow_nan=False))
    (args.output/'SYNTHETIC_serial_full_solver_diagnostics.json').write_text(json.dumps(lab.json_safe(dict(warning=lab.WARNING,
        plan=PLAN, details=result['full_diagnostics'])), indent=2, allow_nan=False))
    print(lab.WARNING)
    print(json.dumps(result['manifest']['counts'], indent=2))
    print(f'All predeclared cases retained in {args.output}; no empirical performance evaluated.')


if __name__ == '__main__':
    main()
