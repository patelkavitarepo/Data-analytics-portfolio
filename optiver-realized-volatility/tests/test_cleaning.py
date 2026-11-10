"""Transparent synthetic tests, never market evidence or prediction performance."""
import json
import numpy as np
import pandas as pd
import pytest
import exchange_calendars as xc
from daily_study.clean import policy_layers,ledger_rows,target_cause_links,build,verify_run
from daily_study.quality import sha256


def fixture():
    sessions=xc.get_calendar('XNYS',start='2020-02-01',end='2020-03-01').sessions_in_range('2020-02-03','2020-02-28').tz_localize(None)
    rows=[]
    for stock in ['A','B']:
        for i,day in enumerate(sessions):
            p=100.+i+(50 if stock=='B' and i>=4 else 0)
            rows.append(dict(Name=stock,date=day,open=p,high=p+1,low=p-1,close=p+.5,volume=1000+i))
    raw=pd.DataFrame(rows).sort_values(['Name','date']).reset_index(drop=True)
    ai=raw[raw.Name=='A'].index
    raw.loc[ai[10],['open','high','low','close','volume']]=raw.loc[ai[5],['open','high','low','close','volume']].to_numpy()
    raw.loc[ai[8],'close']=1000.
    raw.loc[ai[2],'open']=np.nan
    raw.loc[raw[(raw.Name=='B')&(raw.date==sessions[5])].index,'volume']=0
    evidence={'events':[
        dict(id='TEST-ACTION',stock='B',date=str(sessions[12].date()),category='verified_action_boundary',note='synthetic distribution',sources=[]),
        dict(id='TEST-SHOCK',stock='B',date=str(sessions[4].date()),category='documented_market_move',note='synthetic shock',sources=[])]}
    return sessions,raw,evidence


def test_policy_specific_masks_preserve_source_and_shock():
    days,raw,evidence=fixture();original=raw.copy(deep=True)
    _,present,flags,action,protected,layers=policy_layers(raw,days,evidence)
    pd.testing.assert_frame_equal(raw,original)
    assert layers['narrow']['price_mask'].to_numpy().sum()==1
    assert layers['conservative']['price_mask'].to_numpy().sum()==3
    assert layers['narrow']['close'].loc[days[5],'A']==105.5
    assert np.isnan(layers['conservative']['close'].loc[days[5],'A'])
    assert np.isnan(layers['conservative']['close'].loc[days[10],'A'])
    for name in ['narrow','conservative']:
        assert np.isfinite(layers[name]['returns'].loc[days[4],'B'])
        assert np.isnan(layers[name]['returns'].loc[days[12],'B'])
        assert layers[name]['close'].loc[days[2],'A']==102.5
        assert not layers[name]['range_ok'].loc[days[2],'A']
        assert layers[name]['volume'].loc[days[5],'B']==0
    assert np.isfinite(layers['error_only_reference']['returns'].loc[days[12],'B'])


def test_every_policy_target_loss_has_ledger_cause_and_timing():
    days,raw,evidence=fixture();_,_,flags,_,_,layers=policy_layers(raw,days,evidence)
    ledger=ledger_rows(raw,days,flags,evidence)
    repeated=[r for r in ledger if r['rule']=='repeated_ohlc']
    assert sum(r['requires_future_session_at_observation'] for r in repeated)==1
    assert repeated[0]['earliest_detection_session_if_delivered']==str(days[10].date())
    assert not any(r['point_in_time_delivery_verified'] for r in ledger)
    for name in ['error_only_reference','narrow','conservative']:
        lost=layers['raw_reference']['target'].notna()&layers[name]['target'].isna()
        links=target_cause_links(lost,days,ledger,name)
        assert len(links)==lost.to_numpy().sum()
        assert all(r['cause_ids'] for r in links)
        assert not any('missing_ohlc' in c for r in links for c in r['cause_ids'])
        if name=='error_only_reference':assert not any('TEST-ACTION' in r['cause_ids'] for r in links)


def test_action_at_origin_does_not_contaminate_future_target():
    days,raw,evidence=fixture();_,_,flags,_,_,layers=policy_layers(raw,days,evidence)
    assert np.isfinite(layers['narrow']['target'].loc[days[12],'B'])
    assert np.isnan(layers['narrow']['target'].loc[days[11],'B'])


def test_clean_artifacts_are_traceable_and_source_immutable(tmp_path):
    _,raw,evidence=fixture();source=tmp_path/'source.csv';raw.to_csv(source,index=False)
    ev=tmp_path/'ev.json';ev.write_text(json.dumps(evidence));before=source.read_bytes()
    out=tmp_path/'clean';manifest=build(source,ev,out,enforce_hash=False)
    assert source.read_bytes()==before
    assert manifest['source_sha256']==manifest['source_sha256_after']==sha256(source)
    assert manifest['models_trained'] is False and manifest['prices_replaced']==0
    hashes=json.loads((out/'artifact_hashes.json').read_text())
    assert all(sha256(out/name)==value for name,value in hashes.items())
    for name in ['narrow','conservative']:
        view=pd.read_parquet(out/f'{name}.parquet')
        assert int(view.provisional_target_5.notna().sum())==next(r['available_targets'] for r in manifest['policy_summaries'] if r['policy']==name)
        assert view.loc[view.provisional_target_5.notna(),'target_reason_codes'].eq(0).all()
    assert verify_run(out,source)['version']=='D003-v1'
    with pytest.raises(ValueError):build(source,ev,out,enforce_hash=False)
    (out/'ledger.jsonl').write_text('tampered')
    with pytest.raises(ValueError):verify_run(out,source)
