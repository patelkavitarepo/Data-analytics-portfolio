"""Mathematical fixtures test methods, not financial hypotheses or real findings."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from daily_study.declines import LeaveOutMedian,Context,reaction,corr,episode_ids,passes,bootstrap_episode,load_returns

ROOT=Path(__file__).resolve().parents[1]


def design():return json.loads((ROOT/'research/declines-D004/design.json').read_text())


def test_exact_leave_out_medians_match_direct_deletion():
    rng=np.random.default_rng(5);a=rng.normal(size=(12,8));a[rng.random(a.shape)<.3]=np.nan;a[0]=np.nan
    helper=LeaveOutMedian(a)
    for excluded in [(),(0,),(2,5),(1,7)]:
        result,count=helper.median(excluded)
        expected=[]
        for row in np.delete(a,excluded,axis=1):
            good=row[np.isfinite(row)];expected.append(np.median(good) if len(good) else np.nan)
        np.testing.assert_allclose(result,expected,equal_nan=True)
        np.testing.assert_array_equal(count,np.isfinite(np.delete(a,excluded,axis=1)).sum(axis=1))
    with pytest.raises(ValueError):helper.median((1,1))


def test_context_excludes_focal_names_and_uses_no_future_row():
    d=design();d['minimum_context_donors']=3
    returns=np.log1p(np.array([[-.02,-.02,-.02,0.,0.],[0.,0.,0.,0.,0.]]))
    context=Context(returns,d)
    assert context.states()[1].tolist()==[True,False]
    assert not context.states((0,))[1][0]
    assert not context.states((0,1))[1][0]
    altered=returns.copy();altered[1]=-100
    for before,after in zip(context.states((0,)),Context(altered,d).states((0,))):
        assert before[0]==after[0]


def test_scale_excludes_current_and_future_and_missing_is_not_filled():
    d=design();d['scale_window_sessions']=3;d['scale_minimum_observed_returns']=2
    r=pd.DataFrame({'A':[.01,.02,.03,.04,.05]})
    z,_,scale=reaction(r,d)
    assert scale.iloc[2,0]==pytest.approx(.015)
    changed=r.copy();changed.iloc[2,0]=9
    assert reaction(changed,d)[2].iloc[2,0]==scale.iloc[2,0]
    changed=r.copy();changed.iloc[4,0]=9
    pd.testing.assert_frame_equal(reaction(changed,d)[0].iloc[:4],z.iloc[:4])
    changed=r.copy();changed.iloc[0:2]=np.nan
    assert reaction(changed,d)[0].iloc[2].isna().all()


def test_correlation_support_and_candidate_rule_are_not_relaxed():
    x=np.array([1.,2.,3.,np.nan]);y=np.array([2.,4.,6.,8.])
    c,n=corr(x,y,np.ones(4,dtype=bool));assert c==pytest.approx(1) and n==3
    assert np.isnan(corr(x,y,np.array([True,False,False,True]))[0])
    row=dict(ordinary_n=200,decline_n=19,decline_episodes=8,ordinary_signed_corr=.1,
             ordinary_adjusted_corr=.1,decline_adjusted_corr=.9,correlation_change=.8)
    assert not passes(row,design())
    row['decline_n']=20;assert passes(row,design())


def test_episode_resampling_is_deterministic_and_counts_blocks():
    d=design();d['episode_gap_sessions']=2
    x=np.arange(20,dtype=float);y=x**2
    mask=np.zeros(20,dtype=bool);mask[[1,2,6,7,11,12,16,17]]=True
    np.testing.assert_array_equal(episode_ids(np.flatnonzero(mask),2),[0,0,1,1,2,2,3,3])
    first=bootstrap_episode(x,y,mask,d,1);assert first==bootstrap_episode(x,y,mask,d,1)
    assert first['episodes']==4 and first['observations']==8


def test_loader_does_not_read_targets_or_later_relationship_observations(tmp_path):
    d=design()
    for policy in ['narrow','conservative']:
        pd.DataFrame({'date':pd.to_datetime(['2015-12-30','2015-12-31','2016-01-04']),
                      'stock':['A']*3,'log_return':[.01,.02,999.],
                      'provisional_target_5':['INVALID_TARGET_MUST_NOT_BE_READ']*3}).to_parquet(tmp_path/f'{policy}.parquet',index=False)
    frames=load_returns(tmp_path,d)
    for frame in frames.values():
        assert frame.index.max()==pd.Timestamp('2015-12-31')
        assert frame.A.tolist()==[.01,.02]


def test_measurement_variants_preserve_recorded_zero_and_primary_definition():
    from daily_study.decline_diagnostics import response_variants
    d=design();d['scale_window_sessions']=3;d['scale_minimum_observed_returns']=2
    frame=pd.DataFrame({'A':[.01,.02,0.,.03,.04]});before=frame.copy(deep=True)
    variants,_=response_variants(frame,d)
    pd.testing.assert_frame_equal(frame,before)
    pd.testing.assert_frame_equal(variants['log_floor_1e-06'],reaction(frame,d)[0])
    assert np.isfinite(variants['log_floor_1e-08'].iloc[2,0])
    assert variants['linear_abs_return_ratio'].iloc[2,0]==0


def test_descriptive_runner_end_to_end_without_targets_or_later_data(tmp_path,monkeypatch):
    import daily_study.declines as module
    d=design();d['minimum_context_donors']=3;d['scale_window_sessions']=3;d['scale_minimum_observed_returns']=2
    d['minimum_pair_ordinary_observations']=5;d['minimum_pair_decline_observations']=3;d['minimum_pair_decline_episodes']=2
    d['minimum_profile_ordinary_observations']=5;d['minimum_profile_decline_observations']=3
    days=pd.bdate_range('2015-01-05',periods=30);rows=[]
    for k,day in enumerate(days):
        for j,stock in enumerate(['A','B','C','D','E']):
            value=(-.02-.0001*j) if k%5==0 else .001*(j+1)
            rows.append(dict(date=day,stock=stock,log_return=value,provisional_target_5='NOT_READ'))
    for policy in ['narrow','conservative']:pd.DataFrame(rows).to_parquet(tmp_path/f'{policy}.parquet',index=False)
    (tmp_path/'manifest.json').write_text('{}')
    monkeypatch.setattr(module,'verify_run',lambda root:{})
    config=tmp_path/'design.json';config.write_text(json.dumps(d))
    result=module.run(tmp_path,config,tmp_path/'evidence')
    assert result['prediction_models_trained'] is False
    assert result['future_target_columns_read'] is False
    assert result['pair_universe']==10
    assert result['discovery_end']=='2015-02-13'
    assert (tmp_path/'evidence/all_pairs_discovery.parquet').exists()
