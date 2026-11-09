"""Every observation below is a synthetic mathematical fixture, not market evidence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from optiver.features import BOOK, TRADE, book_features, features_for_stock, realized_volatility
from optiver.metrics import rmspe
from optiver.explore import conditional_similarity, read_manifest, run


def book():
    return pd.DataFrame({'time_id':[7,7,9,9], 'seconds_in_bucket':[10,590,0,500],
                         'bid_price1':[99.,100.,199.,200.], 'ask_price1':[101.,102.,201.,202.],
                         'bid_price2':[98.,99.,198.,199.], 'ask_price2':[102.,103.,202.,203.],
                         'bid_size1':[10,10,10,10], 'ask_size1':[10,10,10,10],
                         'bid_size2':[5,5,5,5], 'ask_size2':[5,5,5,5]})


def trades():
    return pd.DataFrame({'time_id':[7,7], 'seconds_in_bucket':[20,590],
                         'price':[100.,101.], 'size':[20,40], 'order_count':[2,2]})


def test_rv_and_no_cross_window_returns():
    features = book_features(book().sample(frac=1, random_state=2), 1).set_index('time_id')
    assert features.loc[7,'mid_rv'] == pytest.approx(np.log(101/100))
    assert features.loc[9,'mid_rv'] == pytest.approx(np.log(201/200))
    assert features.loc[7,'observed_seconds'] == 590
    assert features.loc[7,'spread_time_mean'] == pytest.approx((580*.02 + 10*(2/101))/590)
    assert np.isnan(features.loc[7,'late_mid_rv'])
    assert np.isnan(realized_volatility([1]))


def test_no_trade_semantics():
    features = features_for_stock(book(),trades(),1).set_index('time_id')
    assert features.loc[7,'mean_order_size'] == 15
    assert features.loc[9,'no_recorded_trades'] == 1
    assert features.loc[9,'trade_volume'] == 0
    assert np.isnan(features.loc[9,'trade_rv'])


@pytest.mark.parametrize('case',['duplicate','crossed','seconds','nonfinite','negative_size'])
def test_bad_book_rejected(case):
    data = book()
    if case == 'duplicate': data = pd.concat([data,data.iloc[:1]])
    if case == 'crossed': data.loc[0,'bid_price1']=103
    if case == 'seconds': data.loc[0,'seconds_in_bucket']=600
    if case == 'nonfinite': data.loc[0,'ask_price1']=np.inf
    if case == 'negative_size': data.loc[0,'ask_size1']=-1
    with pytest.raises(ValueError): book_features(data,1)


def test_zero_depth_not_silently_imputed():
    data=book()
    data.loc[:1,['ask_size1','bid_size1']]=0
    result=book_features(data,1).set_index('time_id')
    assert result.loc[7,'zero_depth_rows']==2
    assert np.isnan(result.loc[7,'wap_rv'])
    assert np.isfinite(result.loc[7,'mid_rv'])


def test_rmspe():
    assert rmspe([1,2],[1.1,1.8]) == pytest.approx(.1)
    with pytest.raises(ValueError): rmspe([0],[1])
    with pytest.raises(ValueError): rmspe([1],[-1])


def test_discovery_manifest_approval(tmp_path):
    path=tmp_path/'manifest.json'
    path.write_text(json.dumps({'time_ids':[7]}))
    with pytest.raises(ValueError): read_manifest(path)
    path.write_text(json.dumps({'approval':'lead-approved','decision_id':'SYNTHETIC-TEST','time_ids':[7]}))
    assert read_manifest(path)['time_ids']==[7]


def test_context_is_explicit_and_support_counted():
    data=pd.DataFrame({'stock_id':[1,1,1,2,2,2], 'time_id':[1,2,3,1,2,3],
                       'mid_rv':[1.,2.,4.,2.,4.,8.]})
    corr,counts=conditional_similarity(data,[1,2,3],3)
    assert corr.loc[1,2]==pytest.approx(1)
    assert counts.loc[1,2]==3
    corr,_=conditional_similarity(data,[1,2],3)
    assert np.isnan(corr.loc[1,2])


def test_private_pipeline_does_not_read_targets_or_other_windows(tmp_path):
    root=tmp_path/'input'
    for kind in ['book_train.parquet','trade_train.parquet']:
        (root/kind/'stock_id=1').mkdir(parents=True)
    book().to_parquet(root/'book_train.parquet/stock_id=1/part.parquet',index=False)
    trades().to_parquet(root/'trade_train.parquet/stock_id=1/part.parquet',index=False)
    (root/'train.csv').write_text('THIS IS NOT VALID CSV: TARGET ACCESS MUST NOT OCCUR')
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'approval':'lead-approved','decision_id':'SYNTHETIC-TEST','time_ids':[7]}))
    audit=run(root,manifest,tmp_path/'output')
    actual=pd.read_parquet(tmp_path/'output/features.parquet')
    assert actual.time_id.tolist()==[7]
    assert 'target' not in actual
    assert audit['labels_read'] is False
    assert audit['stock_window_rows']==1
    assert (tmp_path/'output/stock_volatility.html').exists()
    with pytest.raises(ValueError): run(root,manifest,tmp_path/'output')


def test_dashboard_absent_data_is_honest():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
    assert not app.exception
    assert not app.metric
    assert 'No empirical findings' in app.warning[0].value
