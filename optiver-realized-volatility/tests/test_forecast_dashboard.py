"""Read-only UI and snapshot checks use the bundled, actual 2015 run."""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from daily_study.forecast_snapshot import load_snapshot,return_path
from daily_study.quality import sha256

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'research/forecast-D008/results'


def test_bundled_real_snapshot_is_discovery_only_and_failure_path_reconstructs():
    snapshot=load_snapshot(BUNDLE)
    pred=snapshot['predictions']
    assert pred.date.min()>=pd.Timestamp('2015-01-01') and pred.date.max()<=pd.Timestamp('2015-12-31')
    case=snapshot['failure_cases'][0]
    path=return_path(BUNDLE,case['policy'],case['stock'],case['date'],case['target_end'])
    assert np.sqrt(path.pow(2).sum())==pytest.approx(case['actual'])
    with pytest.raises(ValueError):return_path(BUNDLE,'narrow','AAPL','2015-12-31','2016-01-08')


def test_snapshot_rejects_tampered_artifact(tmp_path):
    shutil.copytree(BUNDLE,tmp_path/'snapshot')
    path=tmp_path/'snapshot/scores.json';path.write_text(path.read_text()+' ')
    with pytest.raises(ValueError,match='integrity failure'):load_snapshot(tmp_path/'snapshot')


def test_hash_consistent_snapshot_still_rejects_protected_dates(tmp_path):
    shutil.copytree(BUNDLE,tmp_path/'snapshot');root=tmp_path/'snapshot'
    frame=pd.read_parquet(root/'predictions.parquet');frame.loc[0,'date']=pd.Timestamp('2016-01-04')
    frame.to_parquet(root/'predictions.parquet',index=False)
    hashes=json.loads((root/'bundle_hashes.json').read_text());hashes['predictions.parquet']=sha256(root/'predictions.parquet')
    (root/'bundle_hashes.json').write_text(json.dumps(hashes))
    with pytest.raises(ValueError,match='2015 internal'):load_snapshot(root)


def test_dashboard_filters_empty_selection_and_never_trains(monkeypatch):
    from sklearn.linear_model import Ridge
    monkeypatch.setattr(Ridge,'fit',lambda *a,**k: (_ for _ in ()).throw(AssertionError('UI must never train')))
    app=AppTest.from_file(str(ROOT/'forecast_app.py'),default_timeout=60).run()
    assert not app.exception and not app.error and len(app.metric)==3
    next(r for r in app.radio if r.label=='Cleaning policy').set_value('narrow').run()
    assert not app.exception
    next(r for r in app.radio if r.label=='Metric shown in model cards').set_value('MAE').run()
    assert all('pp' in m.value for m in app.metric)
    next(r for r in app.radio if r.label=='Stock scope').set_value('Selected stocks').run()
    next(m for m in app.multiselect if m.label=='Selected stocks').set_value([]).run()
    assert not app.exception and any('at least one stock' in item.value for item in app.info)
