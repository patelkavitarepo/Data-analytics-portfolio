"""Synthetic fixtures validate timing/support logic, never financial hypotheses."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from daily_study.declines import Context
from daily_study.feasibility import (stress_states, measurements, potential_context,
    episode_support, marginal_bootstrap, pair_count_summary, synthetic_precision,
    load_inputs, wilson_width, run)
from daily_study.feasibility import verify_inputs
from daily_study.quality import sha256

ROOT = Path(__file__).resolve().parents[1]


def context_design():
    value = json.loads((ROOT/'research/declines-D004/design.json').read_text())
    value['minimum_context_donors'] = 3
    return value


def test_historical_threshold_never_uses_current_or_future_and_retains_zeros():
    data = pd.DataFrame({'A':[0., .01, .02, .04, 0., .2]})
    result = stress_states(data, 3, .9, 1)
    assert result['threshold'][3, 0] == pytest.approx(.018)
    assert result['stress'][3, 0]
    assert result['valid'][4, 0] and not result['stress'][4, 0]
    changed = data.copy(); changed.iloc[3, 0] = 9
    assert stress_states(changed, 3, .9, 1)['threshold'][3, 0] == result['threshold'][3, 0]
    changed = data.copy(); changed.iloc[5, 0] = 9
    np.testing.assert_array_equal(stress_states(changed, 3, .9, 1)['stress'][:5], result['stress'][:5])
    assert not result['valid'][:3].any()


def test_missing_is_unknown_coverage_has_ceil_and_zero_threshold_is_flagged():
    data = pd.DataFrame({'A':[.01, np.nan, .02, .03, np.nan, .2]})
    full, partial = stress_states(data, 3, .9, 1), stress_states(data, 3, .9, .66)
    assert not full['valid'][3, 0] and partial['valid'][3, 0]
    assert not partial['valid'][4, 0] and not partial['stress'][4, 0]
    zero = stress_states(pd.DataFrame({'A':[0., 0., 0., .1]}), 3, .9, 1)
    assert zero['zero_threshold'][3, 0] and not zero['valid'][3, 0]
    assert not stress_states(data, 3, .9, .8)['valid'][3, 0]  # ceil(2.4)=3


def test_measurements_are_backward_only_range_guarded_and_do_not_bridge_gaps():
    r = pd.DataFrame({'A':[.01, -.02, .03, .04, .05, np.nan, .06]})
    fields = {'log_return':r, 'range_features_eligible':pd.DataFrame({'A':[True]*6+[False]})}
    raw = {'high':pd.DataFrame({'A':[2.]*7}), 'low':pd.DataFrame({'A':[1.]*7})}
    value = measurements(fields, raw)
    assert value['backward_five_rv'].iloc[4, 0] == pytest.approx(np.sqrt((r.iloc[:5, 0]**2).sum()))
    assert value['backward_five_rv'].iloc[5:, 0].isna().all()
    assert value['intraday_range'].iloc[6].isna().all()
    assert value['downside_magnitude'].iloc[0, 0] == 0


def test_vectorized_pair_context_is_exact_and_excludes_both_focal_names():
    rng = np.random.default_rng(7)
    returns = rng.normal(-.01, .02, (40, 7))
    returns[rng.random(returns.shape)<.1] = np.nan
    context = Context(returns, context_design())
    pairs = potential_context(context, np.arange(7))
    for k, (i, j) in enumerate(zip(pairs['i'], pairs['j'])):
        _, decline, _, median = context.states((int(i), int(j)))
        full = np.zeros(40, bool); full[pairs['dates']] = pairs['decline'][:, k]
        np.testing.assert_array_equal(full, decline)
        np.testing.assert_allclose(pairs['median'][:, k], median[pairs['dates']], equal_nan=True)


def test_episodes_are_defined_before_stock_missingness_and_no_event_bootstrap_warns():
    mask = np.array([True, True, False, False, False, True])
    valid = np.ones((6, 2), bool); valid[1, 0] = False
    stressed = np.zeros((6, 2), bool); stressed[0, 0] = True
    blocks = episode_support(valid, stressed, mask, pd.bdate_range('2015-01-01', periods=6), 1)
    assert blocks['calendar_blocks'] == 2
    assert blocks['event_blocks'].tolist() == [1, 0]
    width, undefined = marginal_bootstrap(blocks['totals'], blocks['events'], 1, repetitions=100)
    assert width[1] == 0 and undefined[1] == 0  # misleading without the no-event flag
    assert marginal_bootstrap(blocks['totals'], blocks['events'], 1, 100)[0].tolist() == width.tolist()


def test_support_has_no_scores_and_severity_counterfactual_uses_no_joint_outcomes():
    # Same stratum marginals, different co-occurrence: counterfactual must agree.
    pair = dict(dates=np.arange(8), i=np.array([0]), j=np.array([1]),
                decline=np.ones((8, 1), bool), median=np.array([[-.01]]*4+[[-.03]]*4))
    states = dict(valid=np.ones((8, 2), bool),
                  stress=np.array([[1,1],[0,0],[0,0],[0,0],[1,1],[1,1],[1,1],[0,0]], bool))
    first = pair_count_summary(states, pair, -.02, 1)
    states['stress'][:, 1] = [0,1,0,0,0,1,1,1]
    second = pair_count_summary(states, pair, -.02, 1)
    assert first['severity_mixture_null_lift'] == second['severity_mixture_null_lift']
    assert first['joint_stress_dates'] != second['joint_stress_dates']
    assert 'CVR' not in first and 'score' not in first and 'rank' not in first


def write_inputs(path):
    days = list(pd.bdate_range('2015-01-01', periods=30))+[pd.Timestamp('2016-01-04')]
    rows = []
    for t, day in enumerate(days):
        for j in range(5):
            rows.append(dict(date=day, stock=f'S{j}', log_return=999 if day.year == 2016 else (-.03 if t%3 == 0 else .001*(j+1)),
                range_features_eligible=True, price_reason_codes=0, return_reason_codes=0,
                provisional_target_5='POISON_TARGET', high=2., low=1., source_present=True))
    frame = pd.DataFrame(rows)
    for policy in ['narrow', 'conservative']:
        frame.drop(columns=['high', 'low', 'source_present']).to_parquet(path/f'{policy}.parquet', index=False)
    frame[['date','stock','high','low','source_present']].to_parquet(path/'aligned_raw.parquet', index=False)
    (path/'manifest.json').write_text('{"source_sha256":"synthetic"}')
    (path/'artifact_hashes.json').write_text(json.dumps({name:sha256(path/name) for name in
        ['manifest.json', 'narrow.parquet', 'conservative.parquet', 'aligned_raw.parquet']}))


def test_audit_refuses_altered_cleaning_inputs(tmp_path):
    write_inputs(tmp_path)
    assert len(verify_inputs(tmp_path)) == 4
    (tmp_path/'manifest.json').write_text('{"altered":true}')
    with pytest.raises(ValueError, match='hash mismatch'):verify_inputs(tmp_path)


def test_loader_projects_only_authorized_columns_and_discovery_dates(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    design = json.loads((ROOT/'research/feasibility-D006/design.json').read_text())
    original = pd.read_parquet
    calls = []
    def spy(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)
    monkeypatch.setattr(pd, 'read_parquet', spy)
    panels, raw = load_inputs(tmp_path, design)
    assert len(calls) == 3
    for call in calls:
        assert 'provisional_target_5' not in call['columns'] and 'filters' in call
    assert panels['narrow']['log_return'].index.max() < pd.Timestamp('2016-01-01')
    assert panels['narrow']['log_return'].max().max() < 999


def test_runner_end_to_end_excludes_later_targets_and_refuses_overwrite(tmp_path, monkeypatch):
    import daily_study.feasibility as module
    write_inputs(tmp_path)
    d = json.loads((ROOT/'research/feasibility-D006/design.json').read_text())
    d.update(history_sessions=[3,5], quantiles=[.9], history_coverage_fractions=[1.], measurements=['absolute_return'])
    context = tmp_path/'context-design.json'; context.write_text(json.dumps(context_design()))
    d['context_design'] = str(context)
    config = tmp_path/'design.json'; config.write_text(json.dumps(d))
    monkeypatch.setattr(module, 'plot_evidence', lambda *args:None)
    manifest = run(tmp_path, config, tmp_path/'output')
    assert manifest['later_relationship_observations_read'] is False
    assert manifest['models_trained'] is False and manifest['pair_cvr_computed'] is False
    assert manifest['reference_candidates_ranked'] is False
    assert manifest['pair_universe'] == 10
    with pytest.raises(ValueError):run(tmp_path, config, tmp_path/'output')


def test_synthetic_precision_is_repeatable_labeled_and_not_empirical_inference():
    a = synthetic_precision([2,1,3,1], 9, repetitions=100)
    assert a == synthetic_precision([2,1,3,1], 9, repetitions=100)
    assert a[-1]['population_pooled_lift'] > 1
    assert a[-2]['population_pooled_lift'] == pytest.approx(1)
    assert all('SYNTHETIC' in s['label'] for s in a)
    assert np.isnan(wilson_width(0))
    assert wilson_width(200) < wilson_width(20)
