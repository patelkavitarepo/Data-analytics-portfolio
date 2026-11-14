"""Focused synthetic study only; no market observations or estimator-ranking assertions."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from markowitz import synthetic as lab
from markowitz import synthetic_robustness as study


@pytest.fixture(scope='module')
def trained():
    return study.train_case(6006, 126)


def test_exact_predeclared_grid_and_nested_training_preserve_old_baseline():
    assert study.SEEDS == (6006, 6007, 6008, 6009, 6010)
    assert study.WINDOWS == (126, 504) and study.DRAWS == 10
    assert study.CAP == .35 and study.ANNUAL_RF == .02
    long = study.training_sample(6006, 504)
    old = lab.construct('baseline', lab.LabConfig(seed=6006)).training
    pd.testing.assert_frame_equal(long, old)
    short = study.training_sample(6006, 126)
    suffix = long.iloc[-126:].reset_index(drop=True)
    suffix.index.name = 'synthetic_step'
    pd.testing.assert_frame_equal(short, suffix)
    pd.testing.assert_frame_equal(short, study.training_sample(6006, 126))
    assert not short.equals(study.training_sample(6007, 126))
    for seed, window in [(6005, 126), (6011, 504), (6006, 252)]:
        with pytest.raises(ValueError, match='predeclared'):
            study.training_sample(seed, window)


def test_paired_future_innovations_and_covariance_psd():
    paths = study.future_paths(6006)
    base, jump = paths.values()
    old = lab.construct('baseline', lab.LabConfig(seed=6006)).future
    pd.testing.assert_frame_equal(base, old)
    pd.testing.assert_frame_equal(jump, study.future_paths(6006)['unseen_positive_jump'])
    assert base.index.min() == 504 and base.index.max() == 755
    # Eliminate the shared idiosyncratic component: remaining common-factor
    # difference must be identical across assets after volatility normalization.
    b = (base.to_numpy() - lab.ANNUAL_MEANS / 252) * np.sqrt(252) / lab.ANNUAL_VOLS
    j = (jump.to_numpy() - lab.ANNUAL_MEANS / 252) * np.sqrt(252) / lab.ANNUAL_VOLS
    common = j - np.sqrt(.15/.65) * b
    np.testing.assert_allclose(common, np.repeat(common[:, :1], 6, axis=1), atol=1e-12)
    for rho in (.35, .85):
        cov = lab.covariance(rho)
        assert np.linalg.eigvalsh(cov).min() > 0
        np.testing.assert_allclose(np.diag(cov), lab.ANNUAL_VOLS**2)


def test_training_never_reads_future_or_constructed_future_covariance(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Training/bootstrap must not see future paths or constructed future covariance')
    monkeypatch.setattr(study, 'future_paths', forbidden)
    monkeypatch.setattr(lab, 'covariance', forbidden)
    case = study.train_case(6006, 126)
    assert len(case['weights'].columns) == 3
    assert case['manifest']['training_source_positions'] == [378, 503]
    assert case['manifest']['future_source_positions'] == [504, 755]


def test_future_mutation_no_refit_or_bootstrap_change(trained, monkeypatch):
    original = deepcopy(trained)
    paths = study.future_paths(6006)
    first = study.evaluate_case(trained, paths)
    for frame in paths.values():
        frame.loc[:, :] = -.03
    def forbidden(*args, **kwargs):
        pytest.fail('Evaluation must not refit/bootstrap using future paths')
    monkeypatch.setattr(lab, 'fit', forbidden)
    monkeypatch.setattr(lab, 'bootstrap', forbidden)
    second = study.evaluate_case(trained, paths)
    pd.testing.assert_frame_equal(trained['weights'], original['weights'])
    pd.testing.assert_frame_equal(trained['targets'], original['targets'])
    pd.testing.assert_frame_equal(trained['bootstrap_log'], original['bootstrap_log'])
    assert trained['manifest'] == original['manifest']
    pd.testing.assert_frame_equal(first['paired_risk'], second['paired_risk'])
    assert not first['paired_paths'].equals(second['paired_paths'])
    assert first['future_hashes'] != second['future_hashes']
    assert second['paired_risk']['paired_target_L1'].eq(0).all()
    paths['unseen_positive_jump'].index -= 1
    with pytest.raises(ValueError, match='disjoint'):
        study.evaluate_case(trained, paths)


def test_covariance_jump_on_same_targets_and_matched_costs(trained):
    evaluated = study.evaluate_case(trained, study.future_paths(6006))
    for row in evaluated['paired_risk'].to_dict(orient='records'):
        w = trained['weights'][row['strategy']].to_numpy()
        assert row['baseline_known_volatility'] == pytest.approx(np.sqrt(w @ lab.covariance(.35) @ w))
        assert row['jump_known_volatility'] == pytest.approx(np.sqrt(w @ lab.covariance(.85) @ w))
        assert row['known_volatility_ratio'] > 1  # Analytic long-only covariance property, not path-outcome claim.
        assert row['paired_target_L1'] == 0
    frame = evaluated['paired_paths']
    assert len(frame) == 6 and frame['available'].all()
    assert frame.groupby('strategy')['cost_bps'].apply(list).tolist() == [[0., 10.]] * 3
    for strategy in lab.STRATEGIES:
        rows = frame.loc[frame['strategy'] == strategy].set_index('cost_bps')
        for condition in ('stationary_baseline', 'unseen_positive_jump'):
            assert rows.loc[10., f'{condition}_CAGR'] <= rows.loc[0., f'{condition}_CAGR']
        assert rows['fit_id'].nunique() == 1 and rows['bootstrap_reuse_id'].nunique() == 1


def test_cap_count_tolerance_effective_number_and_bootstrap_incidence(trained):
    assert study.concentration(np.full(6, 1/6))['effective_number'] == pytest.approx(6)
    assert study.concentration(np.full(6, 1/6))['cap_count'] == 0
    assert study.concentration([.35-5e-8, .35, .3+5e-8, 0, 0, 0])['cap_count'] == 2
    assert study.concentration([.35-2e-7, .35, .3+2e-7, 0, 0, 0])['cap_count'] == 1
    with pytest.raises(ValueError):
        study.concentration([1, 0, 0, 0, 0, 0])
    for row in trained['targets'].to_dict(orient='records'):
        log = trained['bootstrap_log'].loc[trained['bootstrap_log']['strategy'] == row['strategy']]
        valid = log.loc[log['success']]
        assert len(valid) + row['bootstrap_failed_draws'] == study.DRAWS
        assert row['bootstrap_cap_binding_incidence'] == pytest.approx(valid['any_cap_binding'].astype(float).mean())
        assert row['bootstrap_mean_cap_count'] == pytest.approx(valid['cap_count'].mean())
        assert row['cap_count'] == study.concentration(trained['weights'][row['strategy']])['cap_count']


def test_failure_rows_retained_with_no_fabricated_risk_or_concentration(monkeypatch):
    original = lab.optimize
    def fail(mu, cov, cap, objective, annual_rf):
        if objective == 'max_sharpe':
            raise ValueError('SYNTHETIC forced failure')
        return original(mu, cov, cap, objective, annual_rf)
    monkeypatch.setattr(lab, 'optimize', fail)
    case = study.run_case(6007, 126)
    row = case['targets'].set_index('strategy').loc['max_sharpe']
    assert not row['fit_success'] and row['bootstrap_failed_draws'] == 10
    assert pd.isna(row['HHI']) and pd.isna(row['bootstrap_mean_half_L1_reallocation'])
    assert case['paired_risk'].query('strategy == "max_sharpe"')['available'].eq(False).all()
    assert case['paired_paths'].query('strategy == "max_sharpe"')['available'].eq(False).all()
    failed = case['bootstrap_log'].query('strategy == "max_sharpe"')
    assert len(failed) == 10 and failed['error'].str.contains('forced').all()
    assert failed['failed_solver_starts'].isna().all() and failed['cap_count'].isna().all()
    json.dumps(lab.json_safe(case['manifest']), allow_nan=False)


def test_across_seed_aggregation_keeps_denominators_and_does_not_pool_pairs():
    frame = pd.DataFrame({'seed': study.SEEDS, 'window': [126]*5, 'strategy': ['test']*5,
                          'metric_value': [1., 2., 3., 4., np.nan]})
    summary = study.aggregate(frame, ['window', 'strategy'], ['metric_value']).iloc[0]
    assert summary['median'] == 2.5 and summary['minimum'] == 1 and summary['maximum'] == 4
    assert summary['planned_seed_count'] == summary['recorded_seed_count'] == 5
    assert summary['valid_seed_count'] == 4
    with pytest.raises(ValueError, match='double-count'):
        study.aggregate(pd.concat([frame, frame.iloc[:1]]), ['window', 'strategy'], ['metric_value'])


def test_report_grid_labels_and_preserved_artifact():
    report = study.load_report()
    assert report['manifest']['predeclaration_commit'] == study.PREDECLARATION_COMMIT
    targets = pd.DataFrame(report['tables']['targets'])
    assert len(targets) == 30 and len(targets[['seed','window','strategy']].drop_duplicates()) == 30
    assert set(targets['seed']) == set(study.SEEDS) and set(targets['window']) == set(study.WINDOWS)
    for rows in report['tables'].values():
        assert all(row['Evidence'] == lab.WARNING for row in rows)
    for seed in study.SEEDS:
        manifests = [m for m in report['manifest']['case_manifests'] if m['seed'] == seed]
        assert manifests[0]['future_hashes'] == manifests[1]['future_hashes']


def test_report_validation_rejects_mislabeled_or_missing_cases(tmp_path):
    report = study.load_report()
    for mutate in (lambda r: r['tables']['targets'][0].update(Evidence='market evidence'),
                   lambda r: r['manifest']['case_manifests'].pop()):
        bad = deepcopy(report)
        mutate(bad)
        path = tmp_path / 'bad.json'
        path.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            study.load_report(path)


def test_no_network_provider_or_empirical_calls(monkeypatch):
    import socket
    import markowitz.data
    import markowitz.research
    before = deepcopy(markowitz.research.PROTOCOL)
    def forbidden(*args, **kwargs):
        pytest.fail('Provider or empirical call from synthetic investigation')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(markowitz.data, 'download_prices', forbidden)
    monkeypatch.setattr(markowitz.research, 'evaluate', forbidden)
    case = study.run_case(6010, 126)
    assert len(case['targets']) == 3
    assert markowitz.research.PROTOCOL == before
