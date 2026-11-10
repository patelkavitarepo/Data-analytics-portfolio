"""Synthetic fixtures test forecasting integrity; never portfolio findings."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from daily_study.forecast import (read_panels, own_features, market_features, build_frames,
    training_rows, fit_predict, metrics, grouped_frames, tune, run)
from daily_study.forecast_analysis import outcome_band, loss_concentration, paired_block_uncertainty
from daily_study.quality import sha256

ROOT=Path(__file__).resolve().parents[1]


def design():
    value=json.loads((ROOT/'research/forecast-D008/design.json').read_text())
    value.update(minimum_market_donors=2,minimum_training_origins=12,ridge_alphas=[.1,1.])
    return value


def test_features_stop_at_origin_and_target_starts_next_session():
    d=design();dates=pd.bdate_range('2014-01-01',periods=80)
    r=pd.DataFrame({'A':np.linspace(-.02,.03,80),'B':np.linspace(.03,-.02,80),'C':np.repeat(.01,80)},index=dates)
    out=own_features(r);changed=r.copy();changed.iloc[70:]=100
    later=own_features(changed)
    for key in out:pd.testing.assert_frame_equal(out[key].iloc[:70],later[key].iloc[:70])
    assert out['rv20'].iloc[60,0]==pytest.approx(np.sqrt(5/20*(r.iloc[41:61,0]**2).sum()))
    assert out['return5'].iloc[60,0]==pytest.approx(r.iloc[56:61,0].sum())
    assert out['rv60'].iloc[:59].isna().all().all()
    panels={p:{'log_return':r,'price_reason_codes':r*0,'return_reason_codes':r*0} for p in ['narrow','conservative']}
    frame=build_frames(panels,d)['narrow'];point=frame[(frame.date==dates[60])&(frame.stock=='A')].iloc[0]
    assert point.actual==pytest.approx(np.sqrt((r.iloc[61:66,0]**2).sum()))
    assert point.target_end==dates[65]
    assert frame[frame.date==dates[-1]].actual.isna().all()


def test_market_features_exclude_focal_stock_and_share_conservative_donors():
    d=design();r=pd.DataFrame([[.01,.02,-.03],[.01,.02,-.03]],columns=list('ABC'))
    market,count=market_features(r,d)
    assert market['market_return'].iloc[0,0]==pytest.approx(-.005)
    assert market['market_down_breadth'].iloc[0,0]==.5
    assert count[0,0]==2
    changed=r.copy();changed.A=100
    other,_=market_features(changed,d)
    for key in market:np.testing.assert_allclose(market[key].A,other[key].A,equal_nan=True)


def test_missing_observations_are_not_imputed_and_degenerate_downside_share_is_unknown():
    r=pd.DataFrame({'A':[0.]*65})
    f=own_features(r)
    assert f['rv20'].iloc[-1,0]==0
    assert np.isnan(f['downside_share20'].iloc[-1,0])
    r.iloc[60]=np.nan;f=own_features(r)
    assert f['rv20'].iloc[-1].isna().all()


def test_training_purge_removes_unmatured_zero_and_missing_feature_rows():
    d=design();dates=pd.bdate_range('2014-06-20',periods=10)
    frame=pd.DataFrame({'date':dates,'target_end':dates+pd.offsets.BDay(5),'actual':1.})
    for name in d['own_features']+d['market_features']:frame[name]=.1
    train=training_rows(frame,'2014-07-01',d)
    assert (train.target_end<pd.Timestamp('2014-07-01')).all()
    assert len(train)==2
    frame.loc[0,'actual']=0;frame.loc[1,'rv5']=np.nan
    assert training_rows(frame,'2014-07-01',d).empty


def test_scaler_and_log_model_are_train_only_positive_and_replayable():
    train=pd.DataFrame(dict(date=pd.to_datetime(['2014-01-02','2014-01-03','2014-01-06']),
        target_end=pd.to_datetime(['2014-01-09','2014-01-10','2014-01-13']),x=[0.,1.,2.],actual=np.exp(np.array([0.,.1,.2]))))
    valid=pd.DataFrame({'x':[10.,20.],'actual':[9999.,9999.]})
    pred,record=fit_predict(train,valid,['x'],1.,'2014-02-01','fixture')
    assert json.loads(record['means'])==[1.]
    replay=np.exp(record['intercept']+((valid.x.to_numpy()-1)/json.loads(record['scales'])[0])*json.loads(record['coefficients'])[0])
    np.testing.assert_allclose(pred,replay)
    assert (pred>0).all()
    valid.actual=-999
    np.testing.assert_allclose(fit_predict(train,valid,['x'],1.,'2014-02-01','fixture')[0],pred)
    with pytest.raises(ValueError):fit_predict(train,valid,['x'],1.,'2014-01-10','fixture')


def test_rmspe_can_worsen_while_mae_and_rmse_improve_without_per_row_rank_reversal():
    y=np.array([.001,.1]);baseline=np.array([.002,.08]);model=np.array([.004,.099])
    a,b=metrics(y,baseline),metrics(y,model)
    assert b['mae']<a['mae'] and b['rmse']<a['rmse'] and b['rmspe']>a['rmspe']
    np.testing.assert_array_equal(np.abs(model-y)<np.abs(baseline-y),
                                 np.abs((model-y)/y)<np.abs((baseline-y)/y))


def test_zero_targets_remain_in_absolute_metrics_and_small_targets_are_not_clipped():
    result=metrics([0,.01],[.005,.02])
    assert result['n']==2 and result['positive_targets']==1 and result['zero_targets']==1
    assert result['rmspe']==1 and result['mae']==pytest.approx(.0075)
    result=metrics([1e-9],[.01])
    assert result['n']==1 and result['rmspe']>1e6
    assert metrics([0],[.1])['rmspe'] is None


def test_loss_concentration_retains_all_cases_and_bands_are_frozen_training_cuts():
    frame=pd.DataFrame(dict(date=pd.bdate_range('2015-01-02',periods=3),stock=['A']*3,actual=[1e-6,.1,.2],M0=[.01,.1,.2],M1=[.01,.1,.2],M2=[.01,.1,.2]))
    out=loss_concentration(frame)
    assert all(r['removed_from_headline'] is False for r in out)
    assert out[0]['sum_squared_percentage_error_share']==1
    cuts={str(q):q for q in [.1,.25,.5,.75,.9]}
    assert outcome_band([0,.05,.95,np.nan],cuts).tolist()==['zero','positive ≤2014 q10','above 2014 q90','unknown']


def test_joint_date_bootstrap_does_not_invent_precision_from_duplicate_stocks():
    d=design();dates=pd.bdate_range('2015-01-02',periods=50);rows=[]
    for policy in ['narrow','conservative']:
        for t,day in enumerate(dates):rows.append(dict(policy=policy,date=day,session_pos=t,stock='A',headline=True,actual=1.,M0=1+.1*np.sin(t),M1=1+.2*np.sin(t),M2=1+.15*np.sin(t)))
    frame=pd.DataFrame(rows);one=paired_block_uncertainty(frame,d)
    duplicated=pd.concat([frame,frame.assign(stock='B')],ignore_index=True)
    two=paired_block_uncertainty(duplicated,d)
    for a,b in zip(one,two):
        for key in ['point_difference','descriptive_95pct_low','descriptive_95pct_high']:
            assert a[key]==pytest.approx(b[key])


def write_fixture(root):
    dates=pd.bdate_range('2013-02-08','2016-01-05');names=list('ABCD');rng=np.random.default_rng(12)
    values=rng.normal(0,.01,(len(dates),4));values[dates<pd.Timestamp('2015-01-01'),3]=np.nan
    values[(dates>='2015-02-02')&(dates<='2015-02-13'),0]=0
    values[dates>pd.Timestamp('2015-12-31')]=9999
    for policy in ['narrow','conservative']:
        a=values.copy()
        if policy=='conservative':a[np.flatnonzero(dates==pd.Timestamp('2015-05-01'))[0],1]=np.nan
        frame=pd.DataFrame(dict(date=np.repeat(dates,len(names)),stock=np.tile(names,len(dates)),log_return=a.ravel(),
            price_reason_codes=0,return_reason_codes=0,provisional_target_5='POISON_DO_NOT_READ'))
        frame.to_parquet(root/f'{policy}.parquet',index=False)
    (root/'aligned_raw.parquet').write_bytes(b'Only hash-verified; not parsed by forecasting')
    (root/'manifest.json').write_text('{"source_sha256":"SYNTHETIC_FIXTURE_NOT_MARKET_DATA"}')
    (root/'artifact_hashes.json').write_text(json.dumps({name:sha256(root/name) for name in ['manifest.json','narrow.parquet','conservative.parquet','aligned_raw.parquet']}))


def test_projected_loader_excludes_targets_and_all_protected_rows(tmp_path,monkeypatch):
    write_fixture(tmp_path);d=design();calls=[];original=pd.read_parquet
    def spy(*args,**kwargs):calls.append(kwargs);return original(*args,**kwargs)
    monkeypatch.setattr(pd,'read_parquet',spy)
    panels=read_panels(tmp_path,d)
    assert len(calls)==2
    for call in calls:
        assert 'provisional_target_5' not in call['columns'] and 'filters' in call
    assert panels['narrow']['log_return'].index.max()==pd.Timestamp('2015-12-31')
    assert panels['narrow']['log_return'].max().max()<9999


def test_tuning_cannot_use_2015_targets_or_late_2014_unmatured_labels(tmp_path):
    write_fixture(tmp_path);d=design();frames=build_frames(read_panels(tmp_path,d),d)
    first=tune(grouped_frames(frames),d)
    assert (first[2].target_end<pd.Timestamp('2015-01-02')).all()
    altered={p:f.copy() for p,f in frames.items()}
    for f in altered.values():f.loc[f.target_end>=pd.Timestamp('2015-01-02'),'actual']=1e100
    second=tune(grouped_frames(altered),d)
    assert first[0]==second[0]
    pd.testing.assert_frame_equal(first[1],second[1])


def test_complete_runner_purges_training_preserves_zero_and_fixes_cohort(tmp_path,monkeypatch):
    import daily_study.forecast_analysis as analysis
    write_fixture(tmp_path);d=design();config=tmp_path/'design.json';config.write_text(json.dumps(d))
    monkeypatch.setattr(analysis,'plot_results',lambda *args:None)
    manifest=run(tmp_path,config,tmp_path/'result')
    assert manifest['protected_period_observations_loaded'] is False
    predictions=pd.read_parquet(tmp_path/'result/predictions.parquet')
    assert predictions.date.max()<=pd.Timestamp('2015-12-31')
    assert not predictions.loc[predictions.stock=='D','cohort_eligible'].any()
    assert predictions.loc[predictions.stock=='D','M0'].notna().any()
    assert predictions.loc[predictions.stock=='D','M1'].isna().all()
    assert predictions.loc[~predictions.horizon_within_discovery,['M0','M1','M2']].isna().all().all()
    assert predictions[(predictions.actual==0)&predictions.headline].shape[0]>0
    fits=pd.read_parquet(tmp_path/'result/fits.parquet')
    assert (pd.to_datetime(fits.train_target_end_max)<pd.to_datetime(fits.validation_start)).all()
    scores=pd.read_json(tmp_path/'result/scores.json');headline=scores[scores.scope=='headline']
    assert headline.n.nunique()==1 and headline.zero_targets.min()>0
    assert (headline.positive_targets+headline.zero_targets==headline.n).all()
    with pytest.raises(ValueError):run(tmp_path,config,tmp_path/'result')
