"""Approved D008/D009 experiment: three models, discovery only, no peer selection."""
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from daily_study.declines import LeaveOutMedian, write_json
from daily_study.feasibility import verify_inputs
from daily_study.quality import sha256
from daily_study.targets import forward_rv

MODELS = ['M0', 'M1', 'M2']
POLICIES = ['narrow', 'conservative']


def read_panels(root, design):
    if design['discovery_end'] != '2015-12-31' or design['models'] != MODELS:
        raise ValueError('Protected period and approved model set are fixed')
    panels = {}
    for policy in POLICIES:
        data = pd.read_parquet(Path(root)/f'{policy}.parquet',
            columns=['date', 'stock', 'log_return', 'price_reason_codes', 'return_reason_codes'],
            filters=[('date', '>=', pd.Timestamp(design['discovery_start'])),
                     ('date', '<=', pd.Timestamp(design['discovery_end']))])
        panels[policy] = {c:data.pivot(index='date', columns='stock', values=c).sort_index()
                          for c in ['log_return', 'price_reason_codes', 'return_reason_codes']}
    a, b = (panels[p]['log_return'] for p in POLICIES)
    if not a.index.equals(b.index) or not a.columns.equals(b.columns):
        raise ValueError('Policies must share their original session/stock grid')
    if a.index.max() > pd.Timestamp('2015-12-31'):
        raise ValueError('Protected observations in discovery inputs')
    return panels


def own_features(returns):
    squared = returns.pow(2)
    out = {f'rv{n}':np.sqrt((5/n)*squared.rolling(n, min_periods=n).sum()) for n in [5,20,60]}
    out['return1'] = returns
    out['return5'] = returns.rolling(5, min_periods=5).sum()
    out['return20'] = returns.rolling(20, min_periods=20).sum()
    downside = squared.where(returns < 0, 0).where(returns.notna()).rolling(20, min_periods=20).sum()
    denominator = squared.rolling(20, min_periods=20).sum()
    out['downside_share20'] = downside/denominator.where(denominator > 0)
    return out


def market_features(returns, design):
    r = returns.to_numpy()
    valid = np.isfinite(r)
    medians, absolute = LeaveOutMedian(r), LeaveOutMedian(np.abs(r))
    down = valid & (np.expm1(r) <= design['market_decline_simple_return']+1e-12)
    totals = down.sum(axis=1)
    arrays = {key:np.full(r.shape, np.nan) for key in design['market_features'][:3]}
    donors = np.zeros(r.shape, dtype=int)
    for j in range(r.shape[1]):
        median, count = medians.median((j,))
        magnitude, _ = absolute.median((j,))
        enough = count >= design['minimum_market_donors']
        arrays['market_return'][:, j] = np.where(enough, median, np.nan)
        arrays['market_abs_return'][:, j] = np.where(enough, magnitude, np.nan)
        arrays['market_down_breadth'][:, j] = np.where(enough, (totals-down[:, j])/np.maximum(count,1), np.nan)
        donors[:, j] = count
    out = {key:pd.DataFrame(value, index=returns.index, columns=returns.columns) for key,value in arrays.items()}
    out['market_rv20'] = np.sqrt((5/20)*out['market_return'].pow(2).rolling(20,min_periods=20).sum())
    return out, donors


def build_frames(panels, design):
    market, donors = market_features(panels['conservative']['log_return'], design)
    frames = {}
    for policy in POLICIES:
        returns = panels[policy]['log_return']
        dates, names = returns.index, returns.columns
        own = own_features(returns)
        target = forward_rv(returns, design['horizon'])
        target_end = pd.Series(dates, index=dates).shift(-design['horizon'])
        label_reasons=np.zeros(returns.shape,dtype=np.int64)
        for step in range(1,design['horizon']+1):
            label_reasons |= panels[policy]['return_reason_codes'].shift(-step).fillna(64).to_numpy(dtype=np.int64)
        frame = pd.DataFrame(dict(date=np.repeat(dates.to_numpy(),len(names)),
            stock=np.tile(names.to_numpy(),len(dates)),
            session_pos=np.repeat(np.arange(len(dates)),len(names)),
            target_end=np.repeat(target_end.to_numpy(),len(names)),
            actual=target.to_numpy().ravel(), policy=policy,
            label_reason_bits=label_reasons.ravel(),
            price_reason=panels[policy]['price_reason_codes'].to_numpy().ravel(),
            return_reason=panels[policy]['return_reason_codes'].to_numpy().ravel(),
            market_donors=donors.ravel()))
        for key,value in {**own,**market}.items():
            frame[key] = value.to_numpy().ravel()
        frame['origin_market_decline'] = frame.market_down_breadth >= design['market_decline_breadth']
        frames[policy] = frame
    return frames


def finite_features(frame, columns):
    return np.isfinite(frame[columns].to_numpy()).all(axis=1)


def training_rows(frame, before, design):
    before = pd.Timestamp(before)
    eligible = ((frame.date < before) & (frame.target_end < before) &
                frame.actual.notna() & (frame.actual > 0) &
                finite_features(frame, design['own_features']+design['market_features']))
    return frame.loc[eligible]


def training_audit(frame, before, design):
    """Counts overlap; they explain each fit without parsing protected outcomes."""
    history=frame[frame.date<pd.Timestamp(before)]
    mature=history.target_end.notna()&(history.target_end<pd.Timestamp(before))
    return dict(historical_origins=len(history),
        not_yet_matured_labels=int((~mature).sum()),
        missing_historical_targets=int((mature&history.actual.isna()).sum()),
        zero_targets_excluded_from_log_fit=int((mature&(history.actual==0)).sum()),
        own_feature_incomplete=int((~finite_features(history,design['own_features'])).sum()),
        market_feature_incomplete=int((~finite_features(history,design['market_features'])).sum()))


def fit_predict(train, validation, features, alpha, validation_start, fit_id):
    if not len(train) or (train.target_end >= pd.Timestamp(validation_start)).any():
        raise ValueError('Every training label must mature before validation begins')
    if (train.date >= pd.Timestamp(validation_start)).any() or (train.actual <= 0).any():
        raise ValueError('Invalid origin/target in log-response fitting')
    scaler = StandardScaler()
    x = scaler.fit_transform(train[features].to_numpy())
    model = Ridge(alpha=float(alpha), solver='svd').fit(x, np.log(train.actual.to_numpy()))
    with np.errstate(over='raise', invalid='raise', under='raise'):
        predictions = np.exp(model.predict(scaler.transform(validation[features].to_numpy()))) if len(validation) else np.array([])
    if not np.isfinite(predictions).all() or (predictions <= 0).any():
        raise FloatingPointError('Nonfinite/nonpositive forecast; never silently clip or discard it')
    record = dict(fit_id=fit_id, alpha=float(alpha), train_rows=len(train),
        train_origin_min=str(train.date.min().date()), train_origin_max=str(train.date.max().date()),
        train_target_end_max=str(train.target_end.max().date()),
        validation_start=str(pd.Timestamp(validation_start).date()),
        features=json.dumps(features), means=json.dumps(scaler.mean_.tolist()),
        scales=json.dumps(scaler.scale_.tolist()), coefficients=json.dumps(model.coef_.tolist()),
        intercept=float(model.intercept_))
    return predictions, record


def metrics(actual, predicted):
    y, pred = np.asarray(actual, float), np.asarray(predicted, float)
    good = np.isfinite(y) & (y >= 0) & np.isfinite(pred)
    y, pred = y[good], pred[good]
    positive = y > 0
    error = pred-y
    return dict(n=len(y), positive_targets=int(positive.sum()), zero_targets=int((y==0).sum()),
        rmspe=float(np.sqrt(np.mean((error[positive]/y[positive])**2))) if positive.any() else None,
        mae=float(np.mean(np.abs(error))) if len(y) else None,
        rmse=float(np.sqrt(np.mean(error**2))) if len(y) else None,
        bias=float(np.mean(error)) if len(y) else None)


def grouped_frames(frames):
    return {policy:dict(tuple(frame.groupby('stock',sort=True))) for policy,frame in frames.items()}


def cohort_counts(groups, before, design):
    names = sorted(groups[POLICIES[0]])
    rows = []
    for stock in names:
        record = dict(stock=stock)
        for policy in POLICIES:
            record[policy+'_training_rows'] = len(training_rows(groups[policy][stock],before,design))
        record['eligible'] = all(record[p+'_training_rows'] >= design['minimum_training_origins'] for p in POLICIES)
        rows.append(record)
    return pd.DataFrame(rows)


def tune(groups, design):
    rows, fits, support = [], [], []
    features = {'M1':design['own_features'], 'M2':design['own_features']+design['market_features']}
    for fold,(start,end) in enumerate(design['tuning_folds']):
        cohort = cohort_counts(groups,start,design)
        cohort['fold_start'] = start
        support.append(cohort)
        eligible_names = cohort.loc[cohort.eligible,'stock']
        for policy in POLICIES:
            for stock in eligible_names:
                frame = groups[policy][stock]
                train = training_rows(frame,start,design)
                audit=training_audit(frame,start,design)
                valid = frame[(frame.date >= start) & (frame.date <= end) &
                    (frame.target_end < pd.Timestamp(design['tuning_target_end_before'])) &
                    frame.actual.notna() & finite_features(frame,features['M2'])].copy()
                if not len(valid):
                    continue
                for alpha in design['ridge_alphas']:
                    block = valid[['date','stock','actual','target_end']].copy()
                    block['policy'],block['alpha'],block['fold'] = policy,alpha,fold
                    for model in ['M1','M2']:
                        fit_id=f'tune/{fold}/{policy}/{stock}/{model}/{alpha}'
                        predictions, record = fit_predict(train,valid,features[model],alpha,start,fit_id)
                        record.update(stage='tuning',policy=policy,stock=stock,model=model,**audit)
                        fits.append(record);block[model]=predictions
                    rows.append(block)
        print(f'Completed tuning fold {start} through {end}',flush=True)
    if not rows:
        raise ValueError('No supported tuning predictions; do not relax guards to force results')
    predictions = pd.concat(rows,ignore_index=True)
    expected = len(POLICIES)*len(design['ridge_alphas'])
    counts = predictions.groupby(['date','stock']).size()
    keys = counts[counts == expected].index
    common = predictions.set_index(['date','stock']).index.isin(keys)
    common &= predictions.actual.to_numpy() > 0
    scored = predictions.loc[common]
    results = []
    for model in ['M1','M2']:
        for alpha in design['ridge_alphas']:
            block = scored[scored.alpha == alpha]
            record = dict(model=model,alpha=alpha,**metrics(block.actual,block[model]))
            for policy in POLICIES:
                part=block[block.policy==policy]
                record[policy+'_rmspe']=metrics(part.actual,part[model])['rmspe']
            results.append(record)
    scores = pd.DataFrame(results)
    if scores.rmspe.isna().any():
        raise ValueError('Undefined tuning metric; do not select an unsupported model')
    selected = {model:float(scores[scores.model==model].sort_values(['rmspe','alpha'],ascending=[True,False]).iloc[0].alpha) for model in ['M1','M2']}
    target_sample = scored.drop_duplicates(['date','stock']).actual
    cuts = {str(q):float(target_sample.quantile(q)) for q in [.1,.25,.5,.75,.9]}
    return selected,scores,predictions,pd.DataFrame(fits),pd.concat(support,ignore_index=True),cuts


def evaluate(frames, groups, design, selected):
    cohort = cohort_counts(groups,design['evaluation_folds'][0][0],design)
    names = set(cohort.loc[cohort.eligible,'stock'])
    own = design['own_features']; all_features=own+design['market_features']
    fits,outputs = [],[]
    for policy in POLICIES:
        frame = frames[policy]
        out = frame[(frame.date >= '2015-01-01') & (frame.date <= '2015-12-31')].copy()
        out['cohort_eligible'] = out.stock.isin(names)
        out['own_features_available'] = finite_features(out,own)
        out['market_features_available'] = finite_features(out,design['market_features'])
        out['M0'] = out.rv20.where(out.target_end.notna())
        out['M1'],out['M2'] = np.nan,np.nan
        out['fit_M1'],out['fit_M2'] = '', ''
        for fold,(start,end) in enumerate(design['evaluation_folds']):
            for stock in sorted(names):
                stock_frame=groups[policy][stock]
                train=training_rows(stock_frame,start,design)
                audit=training_audit(stock_frame,start,design)
                if len(train)<design['minimum_training_origins']:
                    raise ValueError('Frozen eligible cohort lost required historical support')
                for model,columns in [('M1',own),('M2',all_features)]:
                    valid=stock_frame[(stock_frame.date >= start)&(stock_frame.date <= end)&
                        stock_frame.target_end.notna()&finite_features(stock_frame,columns)]
                    fit_id=f'eval/{fold}/{policy}/{stock}/{model}'
                    predictions,record=fit_predict(train,valid,columns,selected[model],start,fit_id)
                    record.update(stage='evaluation',policy=policy,stock=stock,model=model,**audit)
                    fits.append(record)
                    out.loc[valid.index,model]=predictions;out.loc[valid.index,'fit_'+model]=fit_id
            print(f'Completed {policy} evaluation quarter starting {start}',flush=True)
        out['target_available']=out.actual.notna()&(out.actual >= 0)
        out['horizon_within_discovery']=out.target_end.notna()
        out['policy_common']=out.target_available&np.isfinite(out[MODELS]).all(axis=1)
        out['quarter']=out.date.dt.to_period('Q').astype(str)
        outputs.append(out)
    predictions=pd.concat(outputs,ignore_index=True)
    counts=predictions[predictions.policy_common].groupby(['date','stock']).size()
    common_keys=counts[counts==len(POLICIES)].index
    predictions['headline']=predictions.set_index(['date','stock']).index.isin(common_keys)&predictions.policy_common
    # Compare target values only on the actual shared observation set.
    common=predictions[predictions.headline].pivot(index=['date','stock'],columns='policy',values='actual')
    if not np.allclose(common.narrow,common.conservative,rtol=0,atol=1e-14):
        raise ValueError('Common-sample targets differ; investigate before score comparison')
    return predictions,pd.DataFrame(fits),cohort


def run(clean_root, design_path, output):
    root,output,design_path=Path(clean_root),Path(output),Path(design_path)
    if output.exists():
        raise ValueError('Fresh forecasting output directory required')
    design=json.loads(design_path.read_text())
    inputs=verify_inputs(root);code_hash=sha256(__file__)
    panels=read_panels(root,design);frames=build_frames(panels,design);groups=grouped_frames(frames)
    output.mkdir(parents=True)
    selected,scores,tuning,tune_fits,tune_support,cuts=tune(groups,design)
    write_json(output/'selected_settings.json',dict(alphas=selected,target_band_cuts_from_2014=cuts,
        rule='Chosen before evaluating 2015, common 2014 observations, same alpha across policies/stocks'))
    scores.to_json(output/'tuning_scores.json',orient='records',indent=2)
    tuning.to_parquet(output/'tuning_predictions.parquet',index=False)
    predictions,eval_fits,cohort=evaluate(frames,groups,design,selected)
    fits=pd.concat([tune_fits,eval_fits],ignore_index=True)
    predictions.to_parquet(output/'predictions.parquet',index=False)
    fits.to_parquet(output/'fits.parquet',index=False)
    cohort.to_json(output/'cohort.json',orient='records',indent=2)
    tune_support.to_json(output/'tuning_support.json',orient='records',indent=2)
    # Keep return paths only through the discovery boundary for failure inspection.
    for policy in POLICIES:
        panels[policy]['log_return'].to_parquet(output/f'{policy}_discovery_returns.parquet')
    from daily_study.forecast_analysis import analyze
    analyze(predictions,fits,cuts,design,output)
    manifest=dict(stage='D008 approved three-model experiment under D009',
        source_sha256=json.loads((root/'manifest.json').read_text())['source_sha256'],
        input_hashes=inputs,design_sha256=sha256(design_path),code_sha256=code_hash,
        analysis_code_sha256=sha256(Path(__file__).with_name('forecast_analysis.py')),
        python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,
        discovery_start=str(panels['narrow']['log_return'].index.min().date()),
        discovery_end=str(panels['narrow']['log_return'].index.max().date()),
        selected_alphas=selected,evaluation_cohort_stocks=int(cohort.eligible.sum()),
        fitted_models_by_stage=fits.groupby('stage').size().to_dict(),
        evaluation='2015 quarterly expanding refits; internal discovery evaluation, not pristine holdout',
        protected_period_observations_loaded=False,precomputed_target_columns_read=False,
        final_reference_criteria_or_extra_architectures=False,
        retrospective_cleaning_limitation=True,raw_prices_changed=False)
    if verify_inputs(root)!=inputs or sha256(__file__)!=code_hash:
        raise ValueError('Inputs or implementation changed during run')
    write_json(output/'manifest.json',manifest)
    write_json(output/'output_hashes.json',{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()})
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-run',required=True);parser.add_argument('--design',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.clean_run,args.design,args.output),indent=2))
