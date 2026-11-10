"""Verified, read-only research snapshot for the dashboard; never trains models."""
import json
from pathlib import Path

import pandas as pd

from daily_study.quality import sha256

SOURCE_SHA256='6aea253cd19de60b568143991aaf1fa482456565c389205658d236e595e716cf'


def load_snapshot(directory):
    root=Path(directory)
    manifest=json.loads((root/'manifest.json').read_text())
    if manifest.get('source_sha256')!=SOURCE_SHA256:
        raise ValueError('Results must identify the approved real Plotly snapshot')
    if manifest.get('protected_period_observations_loaded') is not False:
        raise ValueError('Protected-period isolation not established')
    hashes=json.loads((root/'bundle_hashes.json').read_text())
    for name,expected in hashes.items():
        if Path(name).name!=name or sha256(root/name)!=expected:
            raise ValueError(f'Result file integrity failure: {name}')
    # Avoid background Arrow I/O surviving a short-lived CLI process teardown.
    predictions=pd.read_parquet(root/'predictions.parquet',use_threads=False,pre_buffer=False)
    if predictions.date.max()>pd.Timestamp('2015-12-31') or predictions.date.min()<pd.Timestamp('2015-01-01'):
        raise ValueError('Dashboard permits 2015 internal evaluation only')
    if predictions.target_end.dropna().max()>pd.Timestamp('2015-12-31'):
        raise ValueError('A target extends into the reserved evaluation period')
    required=['manifest.json','selected_settings.json','scores.json','coverage.json','subgroups.json',
              'cohort.json','uncertainty.json','failure_cases.json','metric_integrity.json','loss_concentration.json']
    result={Path(name).stem:json.loads((root/name).read_text()) for name in required}
    result['predictions']=predictions
    result['fits']=pd.read_parquet(root/'evaluation_fits.parquet',use_threads=False,pre_buffer=False)
    return result


def return_path(directory,policy,stock,origin,target_end):
    if policy not in ['narrow','conservative'] or pd.Timestamp(target_end)>pd.Timestamp('2015-12-31'):
        raise ValueError('Unsupported policy/period')
    frame=pd.read_parquet(Path(directory)/f'{policy}_evaluation_returns.parquet',columns=[stock],use_threads=False,pre_buffer=False)
    path=frame.loc[(frame.index>pd.Timestamp(origin))&(frame.index<=pd.Timestamp(target_end)),stock]
    if len(path)!=5 or path.isna().any():
        raise ValueError('Five genuine complete target returns required')
    return path
