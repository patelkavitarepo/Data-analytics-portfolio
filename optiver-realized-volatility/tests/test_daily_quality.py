"""Synthetic fixtures verify audit mechanics; they are never research findings."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from daily_study.targets import session_returns, forward_rv, backward_rv, purged_training_mask
from daily_study.quality import row_flags, investigate, read_raw


def test_five_returns_begin_after_origin_and_require_full_horizon():
    days=pd.bdate_range('2020-01-02',periods=9)
    returns=pd.DataFrame({'A':[0,.1,.2,.3,.4,.5,.6,.7,.8]},index=days)
    result=forward_rv(returns)
    assert result.iloc[0,0]==pytest.approx(np.sqrt(.1**2+.2**2+.3**2+.4**2+.5**2))
    assert result.iloc[1,0]==pytest.approx(np.sqrt(.2**2+.3**2+.4**2+.5**2+.6**2))
    assert result.iloc[-5:].isna().all().all()
    changed=returns.copy();changed.iloc[0]=999
    pd.testing.assert_frame_equal(result,forward_rv(changed))


def test_absent_session_never_bridged():
    close=pd.DataFrame({'A':[100,101,np.nan,103,104,105,106,107,108]},index=pd.bdate_range('2020-01-02',periods=9))
    returns=session_returns(close)
    assert returns.iloc[2:4].isna().all().all()
    assert np.isnan(forward_rv(returns).iloc[0,0])
    # Removing the missing row would create a false one-session return. We never do that.
    assert session_returns(close.dropna()).iloc[2,0]==pytest.approx(np.log(103/101))


def test_bad_price_blocks_both_adjacent_returns_and_no_partial_history():
    close=pd.DataFrame({'A':[100,101,102,np.nan,104,105,106,107]},index=pd.bdate_range('2020-01-02',periods=8))
    result=session_returns(close)
    assert result.iloc[3:5].isna().all().all()
    assert backward_rv(result,lookback=3).iloc[5:7].isna().all().all()


def test_purge_uses_label_end_not_just_origin_and_whole_dates():
    origins=pd.to_datetime(['2020-01-02','2020-01-03','2020-01-03','2020-01-06'])
    ends=pd.to_datetime(['2020-01-07','2020-01-08','2020-01-08','2020-01-09'])
    mask=purged_training_mask(origins,ends,'2020-01-08')
    assert mask.tolist()==[True,False,False,False]


def test_flags_mark_both_repetitions_without_choosing_correct_date():
    raw=pd.DataFrame({'Name':['A']*3,'date':pd.to_datetime(['2020-01-02','2020-01-03','2020-01-06']),
                      'open':[100,100,100],'high':[102,102,102],'low':[99,99,99],
                      'close':[101,101,50],'volume':[1000,1100,1200]})
    before=raw.copy(deep=True)
    flags=row_flags(raw)
    assert flags.repeated_ohlc.tolist()==[True,True,False]
    assert not flags.repeated_ohlcv.any()
    assert flags.ohlc_contradiction.tolist()==[False,False,True]
    pd.testing.assert_frame_equal(raw,before)


def test_audit_preserves_raw_and_produces_only_investigation_outputs(tmp_path):
    days=pd.bdate_range('2020-02-03',periods=10)
    raw=pd.DataFrame({'date':days.strftime('%Y-%m-%d'),'Name':['SYNTHETIC']*10,
                      'open':np.arange(100,110,dtype=float),'high':np.arange(101,111,dtype=float),
                      'low':np.arange(99,109,dtype=float),'close':np.arange(100.5,110.5,dtype=float),'volume':1000})
    path=tmp_path/'raw.csv';raw.to_csv(path,index=False);before=path.read_bytes()
    evidence=tmp_path/'evidence.json';evidence.write_text(json.dumps({'events':[]}))
    output=tmp_path/'audit'
    result=investigate(path,evidence,output,enforce_hash=False)
    assert path.read_bytes()==before
    assert result['models_trained'] is False and result['prices_corrected']==0
    assert result['rule_effects'][0]['valid_five_session_targets']==5
    assert (output/'case-studies.svg').is_file()
    assert not (output/'cleaned.csv').exists()
    with pytest.raises(ValueError): investigate(path,evidence,output,enforce_hash=False)
    with pytest.raises(ValueError): investigate(path,evidence,tmp_path/'other')


def test_duplicate_identifiers_fail_instead_of_guessing(tmp_path):
    raw=pd.DataFrame({'date':['2020-01-02']*2,'Name':['A']*2,'open':[1,1],
                      'high':[1,1],'low':[1,1],'close':[1,1],'volume':[1,1]})
    file=tmp_path/'bad.csv';raw.to_csv(file,index=False)
    with pytest.raises(ValueError):read_raw(file)
