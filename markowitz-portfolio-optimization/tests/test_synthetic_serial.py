"""Independent synthetic v3: algorithm validity, isolation, missingness and audit trail."""
import copy
import json
import socket

import numpy as np
import pandas as pd
import pytest

from markowitz import synthetic as lab
from markowitz import synthetic_serial as study


def fake_fit(training, *args):
    w = pd.DataFrame({s: np.full(6, 1/6) for s in lab.STRATEGIES}, index=lab.ASSETS)
    diag = {s: dict(success=True, checked_violation=0., solver=dict(attempts=[], success=True)) for s in lab.STRATEGIES}
    return None, None, w, diag


def test_predeclared_grid_and_paired_generation():
    assert study.SEEDS == (6006, 6007, 6008, 6009, 6010)
    assert study.PHIS == (0., .5) and study.DRAWS == 15 and study.BLOCK_LENGTH == 5
    a = study.training_sample(6006, 0.)
    b = study.training_sample(6006, .5)
    pd.testing.assert_frame_equal(b, study.training_sample(6006, .5))
    assert not a.equals(b)
    # Same innovations and independent stationary initialization, exact recurrence.
    rng = np.random.default_rng(np.random.SeedSequence(6006).spawn(3)[0])
    z = rng.standard_normal((505, 7))
    e = (np.sqrt(.35)*z[:, :1]+np.sqrt(.65)*z[:, 1:])*lab.ANNUAL_VOLS/np.sqrt(252)
    np.testing.assert_allclose(a.to_numpy()-lab.ANNUAL_MEANS/252, e[1:], atol=1e-17)
    x = b.to_numpy()-lab.ANNUAL_MEANS/252
    np.testing.assert_allclose(x[0], .5*e[0]+np.sqrt(.75)*e[1], atol=1e-17)
    np.testing.assert_allclose(x[1:], .5*x[:-1]+np.sqrt(.75)*e[2:], atol=1e-17)
    with pytest.raises(ValueError): study.training_sample(6005, 0)
    with pytest.raises(ValueError): study.training_sample(6006, .9)


def test_stationary_marginals_scales_correlations_and_lag_tolerance():
    # Large deterministic synthetic validation fixture, not an optimization seed search.
    rng = np.random.default_rng(31001)
    z = rng.standard_normal((100001, 7))
    e = (np.sqrt(.35)*z[:, :1]+np.sqrt(.65)*z[:, 1:])*lab.ANNUAL_VOLS/np.sqrt(252)
    for phi in study.PHIS:
        x = study.stationary_ar(e, phi)
        np.testing.assert_allclose(x.std(axis=0)*np.sqrt(252), lab.ANNUAL_VOLS, rtol=.02)
        np.testing.assert_allclose(np.corrcoef(x.T), np.full((6,6), .35)+.65*np.eye(6), atol=.02)
        assert np.abs(x.mean(axis=0)/(lab.ANNUAL_VOLS/np.sqrt(252))).max() < .02
        for i in range(6):
            assert abs(np.corrcoef(x[1:, i], x[:-1, i])[0,1]-phi) < .02
    with pytest.raises(ValueError): study.stationary_ar(e, 1.)
    with pytest.raises(ValueError): study.stationary_ar(np.full((5,6), np.nan), .5)


def test_circular_order_wrap_truncate_length_and_rng_pairing():
    starts = np.full(504, 503, dtype=int)
    ids = study.sample_indices(starts, 'circular_mbb')
    assert len(ids) == 504
    np.testing.assert_array_equal(ids[:10], [503,0,1,2,3]*2)
    np.testing.assert_array_equal(ids[-4:], [503,0,1,2])
    np.testing.assert_array_equal(study.sample_indices(starts, 'iid'), starts)
    # Block length one is exactly the IID algorithm for the same starts.
    np.testing.assert_array_equal(study.sample_indices(starts, 'circular_mbb', 1), starts)
    first = study.resampling_starts(6006)
    np.testing.assert_array_equal(first, study.resampling_starts(6006))
    assert not np.array_equal(first, study.resampling_starts(6007))
    assert first.shape == (15,504) and first.min() >= 0 and first.max() < 504
    with pytest.raises(ValueError): study.sample_indices(starts.astype(float), 'iid')
    with pytest.raises(ValueError): study.sample_indices(starts, 'unknown')
    with pytest.raises(ValueError): study.sample_indices(starts, 'circular_mbb', 0)


def test_complete_vectors_training_only_indices_and_no_network(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('No future/network/provider access')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(lab, 'construct', forbidden)
    monkeypatch.setattr(lab, 'bootstrap', forbidden)
    from markowitz import synthetic_robustness as previous
    monkeypatch.setattr(previous, 'future_paths', forbidden)
    training = study.training_sample(6006, .5)
    captured = []
    def capture(sample, *args):
        captured.append(sample.copy())
        return fake_fit(sample)
    monkeypatch.setattr(lab, 'fit', capture)
    result = study.analyze_training(training, 6006, .5)
    assert len(captured) == 31 and len(result['index_records']) == 30
    for sample, record in zip(captured[1:], result['index_records']):
        ids = np.array(record['source_indices'])
        assert ids.min() >= 0 and ids.max() < 504
        expected = training.iloc[ids].reset_index(drop=True)
        expected.index.name = 'synthetic_step'
        pd.testing.assert_frame_equal(sample, expected)
        assert study.digest(ids.astype('<i8').tobytes()) == record['sample_index_sha256']
    future = pd.DataFrame(np.ones((252,6)), columns=lab.ASSETS, index=pd.RangeIndex(504,756, name='synthetic_step'))
    with pytest.raises(ValueError): study.analyze_training(future, 6006, .5)
    # External future mutation cannot enter the training-only interface or its outputs.
    future.iloc[:] = -0.9
    repeated = study.analyze_training(training, 6006, .5)
    pd.testing.assert_frame_equal(result['summary'], repeated['summary'])
    pd.testing.assert_frame_equal(result['log'], repeated['log'])
    assert result['manifest'] == repeated['manifest']


def test_failures_reference_missing_denominators_and_constraint_logs(monkeypatch):
    calls = 0
    def failing(sample, *args):
        nonlocal calls
        _, _, w, d = fake_fit(sample)
        calls += 1
        if calls == 1:  # Reference missing, valid bootstrap targets still have concentration.
            w = w.drop(columns='max_sharpe')
            d['max_sharpe'] = dict(success=False, checked_violation=np.nan, solver=None, error='reference unavailable')
        elif calls == 2:
            w = w.drop(columns='min_vol')
            d['min_vol'] = dict(success=False, checked_violation=.2,
                solver=dict(attempts=[dict(success=False)]), error='injected constraint rejection')
        return None, None, w, d
    monkeypatch.setattr(lab, 'fit', failing)
    r = study.analyze_training(study.training_sample(6006, 0.), 6006, 0.)
    bad = r['log'].query("method == 'iid' and strategy == 'min_vol' and draw == 0").iloc[0]
    assert not bad.success and pd.isna(bad.HHI) and pd.isna(bad.half_L1)
    assert bad.checked_violation == .2 and bad.failed_solver_starts == 1
    summary = r['summary'].set_index(['method','strategy'])
    assert summary.loc[('iid','min_vol'), 'successful_draws'] == 14
    assert summary.loc[('iid','min_vol'), 'failed_draws'] == 1
    assert summary.loc[('iid','min_vol'), 'valid_distance_draws'] == 14
    assert summary.loc[('iid','max_sharpe'), 'successful_draws'] == 15
    assert summary.loc[('iid','max_sharpe'), 'valid_distance_draws'] == 0
    assert pd.isna(summary.loc[('iid','max_sharpe'), 'mean_half_L1'])
    assert pd.isna(summary.loc[('iid','max_sharpe'), 'target_HHI'])
    assert summary.loc[('iid','max_sharpe'), 'bootstrap_mean_effective_number'] == pytest.approx(6.)
    paired = study.paired_differences(r['summary'])
    assert paired.query("strategy == 'max_sharpe'").material_difference.iloc[0] is None
    # All candidates missing -> missing diagnostics, not reassuring zeros.
    empty = r['log'].copy()
    empty['success'] = False
    empty['half_L1'] = np.nan
    all_bad = study.summarize_draws(empty, pd.DataFrame())
    assert all_bad.mean_half_L1.isna().all() and (all_bad.successful_draws == 0).all()
    assert all_bad.bootstrap_mean_HHI.isna().all()
    truncated = study.summarize_draws(r['log'].iloc[1:], pd.DataFrame())
    assert truncated.unrecorded_draws.sum() == 1
    with pytest.raises(ValueError): study.summarize_draws(pd.concat([r['log'], r['log']]), pd.DataFrame())


def test_aggregation_counts_and_materiality(monkeypatch):
    monkeypatch.setattr(lab, 'fit', fake_fit)
    r = study.analyze_training(study.training_sample(6006, 0.), 6006, 0.)
    summary = r['summary']
    summary.loc[(summary.method=='circular_mbb') & (summary.strategy=='min_vol'), 'mean_half_L1'] = .03
    pairs = study.paired_differences(summary)
    assert pairs.query("strategy=='min_vol'").material_difference.iloc[0]
    assert not pairs.query("strategy=='equal_weight'").material_difference.iloc[0]
    frame = pd.DataFrame(dict(seed=[6006,6007,6008], phi=[.5]*3, value=[.1,.3,np.nan]))
    a = study.across_seeds(frame, ['phi'], ['value']).iloc[0]
    assert a.valid_seeds == 2 and a.planned_seeds == 5 and a.recorded_seeds == 3
    assert a['median'] == .2 and a['minimum'] == .1 and a['maximum'] == .3
    with pytest.raises(ValueError): study.across_seeds(pd.concat([frame,frame]), ['phi'], ['value'])
    with pytest.raises(ValueError): study.paired_differences(pd.concat([summary,summary]))


def test_report_preserved_hashes_labels_indices_and_failure_counts(tmp_path):
    report = study.load_report()
    assert len(report['manifest']['cases']) == 10
    tables = report['tables']
    assert len(tables['summary']) == 60 and len(tables['bootstrap_log']) == 900
    assert len(tables['resampling_indices']) == 300
    assert all(row['Evidence'] == lab.WARNING for rows in tables.values() for row in rows)
    # Generator regimes share the exact same starts/method index streams, not samples.
    hashes = {}
    for case in report['manifest']['cases']:
        key = case['seed']
        if key in hashes: assert hashes[key] == case['starts_sha256']
        hashes[key] = case['starts_sha256']
    for record in tables['resampling_indices']:
        source = study.resampling_starts(record['seed'])[record['draw']]
        np.testing.assert_array_equal(record['source_indices'], study.sample_indices(source, record['method']))
    for row in tables['bootstrap_log']:
        if row['success']:
            w = np.array([row[s] for s in lab.ASSETS])
            assert w.sum() == pytest.approx(1, abs=1e-7) and w.max() <= .35+1e-7
            assert row['cap_count'] == study.concentration(w)['cap_count']
            if row['strategy'] == 'equal_weight': assert row['half_L1'] == 0
    for mutation in ('label', 'case', 'hash'):
        bad = copy.deepcopy(report)
        if mutation == 'label': bad['tables']['summary'][0]['Evidence'] = 'empirical'
        elif mutation == 'case': bad['manifest']['cases'].pop()
        else: bad['manifest']['preserved_sha256']['synthetic-default-summary.json'] = 'bad'
        path = tmp_path/'bad.json'
        path.write_text(json.dumps(bad))
        with pytest.raises(ValueError): study.load_report(path)
