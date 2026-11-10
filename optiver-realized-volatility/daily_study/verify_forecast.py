"""Independently replay actual forecasts/labels and scores without fitting models."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from daily_study.quality import sha256
from daily_study.declines import write_json


def verify(run):
    root=Path(run)
    for name,digest in json.loads((root/'output_hashes.json').read_text()).items():
        if Path(name).name!=name or sha256(root/name)!=digest:
            raise ValueError(f'Artifact hash mismatch: {name}')
    pred=pd.read_parquet(root/'predictions.parquet');fits=pd.read_parquet(root/'fits.parquet')
    if not (pd.to_datetime(fits.train_target_end_max)<pd.to_datetime(fits.validation_start)).all():
        raise ValueError('Immature label entered a fit')
    tuning=pd.read_parquet(root/'tuning_predictions.parquet')
    if not (tuning.target_end<pd.Timestamp('2015-01-02')).all():
        raise ValueError('Tuning label entered 2015 evaluation')
    counts={'replayed_model_forecasts':0,'reconstructed_targets':0,'reconstructed_baselines':0}
    maximum=0.
    fit_lookup=fits.set_index('fit_id')
    for model in ['M1','M2']:
        for fit_id,block in pred[pred[model].notna()].groupby('fit_'+model):
            fit=fit_lookup.loc[fit_id]
            features=json.loads(fit.features)
            standardized=(block[features].to_numpy()-np.array(json.loads(fit.means)))/np.array(json.loads(fit.scales))
            replay=np.exp(standardized@np.array(json.loads(fit.coefficients))+fit.intercept)
            delta=np.max(np.abs(replay-block[model].to_numpy()))
            maximum=max(maximum,float(delta))
            np.testing.assert_allclose(replay,block[model],rtol=1e-11,atol=1e-13)
            counts['replayed_model_forecasts']+=len(block)
    for policy in ['narrow','conservative']:
        returns=pd.read_parquet(root/f'{policy}_discovery_returns.parquet')
        assert returns.index.max()<=pd.Timestamp('2015-12-31')
        matrix=returns.to_numpy();t=len(matrix);expected=np.full(matrix.shape,np.nan)
        # Independent array construction, not the production target utility.
        squared=np.zeros((t-5,matrix.shape[1]))
        for h in range(1,6):squared+=matrix[h:t-5+h]**2
        expected[:t-5]=np.sqrt(squared)
        baseline=np.full(matrix.shape,np.nan)
        windows=np.lib.stride_tricks.sliding_window_view(matrix**2,20,axis=0)
        baseline[19:]=np.sqrt(5/20*windows.sum(axis=-1))
        baseline[-5:]=np.nan
        block=pred[pred.policy==policy]
        i=returns.index.get_indexer(block.date);j=returns.columns.get_indexer(block.stock)
        np.testing.assert_allclose(block.actual,expected[i,j],rtol=1e-12,atol=1e-14,equal_nan=True)
        np.testing.assert_allclose(block.M0,baseline[i,j],rtol=1e-12,atol=1e-14,equal_nan=True)
        counts['reconstructed_targets']+=int(block.actual.notna().sum())
        counts['reconstructed_baselines']+=int(block.M0.notna().sum())
    scores=pd.read_json(root/'scores.json');headline=scores[scores.scope=='headline']
    for _,row in headline.iterrows():
        data=pred[(pred.policy==row.policy)&pred.headline]
        y=data.actual.to_numpy();forecast=data[row.model].to_numpy();e=forecast-y
        direct=dict(mae=np.abs(e).mean(),rmse=np.sqrt((e**2).mean()),bias=e.mean(),rmspe=np.sqrt(((e[y>0]/y[y>0])**2).mean()))
        for name,value in direct.items():
            # Public JSON intentionally serializes decimal scores at pandas' precision.
            if not np.isclose(value,row[name],rtol=0,atol=1e-9):
                raise ValueError(f'Independent metric disagreement: {name}')
    return dict(**counts,maximum_prediction_replay_absolute_difference=maximum,
        independent_headline_metric_records_verified=len(headline),all_fit_labels_mature=True,
        tuning_labels_precede_2015=True,protected_period_loaded=False,
        models_refitted=False,source='Actual discovery-only run, no synthetic portfolio evidence')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=verify(args.run);write_json(Path(args.output),result);print(json.dumps(result,indent=2))
