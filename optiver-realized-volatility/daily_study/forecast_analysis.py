"""Report all approved forecasts, including small-target failures; never trim scores."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from daily_study.forecast import MODELS, POLICIES, metrics
from daily_study.declines import write_json


def outcome_band(values, cuts):
    thresholds=[cuts[str(q)] for q in [.1,.25,.5,.75,.9]]
    labels=['positive ≤2014 q10','2014 q10–q25','2014 q25–q50','2014 q50–q75','2014 q75–q90','above 2014 q90']
    result=np.array(['unknown']*len(values),dtype=object)
    y=np.asarray(values,float);positive=np.isfinite(y)&(y>0)
    result[np.isfinite(y)&(y==0)]='zero'
    result[positive]=np.array(labels,dtype=object)[np.searchsorted(thresholds,y[positive],side='left')]
    return result


def score_rows(frame, label, extra=None):
    records=[]
    for model in MODELS:
        records.append(dict(scope=label,model=model,**(extra or {}),**metrics(frame.actual,frame[model])))
    return records


def loss_concentration(frame):
    """Cumulative small-outcome contributions. No observations are removed."""
    data=frame[frame.actual>0].sort_values(['actual','date','stock'])
    records=[]
    for fraction in [.01,.05,.10]:
        count=max(1,int(np.ceil(len(data)*fraction))) if len(data) else 0
        subset=data.iloc[:count]
        for model in MODELS:
            e=data[model]-data.actual;se=(e/data.actual)**2;ae=e.abs();mse=e**2
            part=subset[model]-subset.actual
            records.append(dict(smallest_fraction=fraction,observations=count,total_positive_observations=len(data),model=model,
                sum_squared_percentage_error_share=float(((part/subset.actual)**2).sum()/se.sum()) if se.sum()>0 else None,
                absolute_error_share=float(part.abs().sum()/ae.sum()) if ae.sum()>0 else None,
                squared_absolute_error_share=float((part**2).sum()/mse.sum()) if mse.sum()>0 else None,
                largest_actual_in_subset=float(subset.actual.max()) if len(subset) else None,
                removed_from_headline=False))
    return records


def paired_block_uncertainty(frame, design):
    """Fixed-forecast paired intervals, jointly resampling all stocks by date."""
    results=[]
    positions=np.sort(frame.session_pos.unique())
    start,end=int(positions.min()),int(positions.max())
    for length in [20,60]:
        calendar=np.arange(start,end+1)
        block_count=int((calendar[-1]-calendar[0])//length+1)
        weights=np.random.default_rng(design['seed']+length).multinomial(block_count,np.full(block_count,1/block_count),size=1000)
        for policy in POLICIES:
            data=frame[(frame.policy==policy)&frame.headline].copy()
            data['block']=(data.session_pos-start)//length
            data['n']=1;data['np']=(data.actual>0).astype(int)
            for model in MODELS:
                error=data[model]-data.actual
                data[model+'_ae']=error.abs();data[model+'_se']=error**2
                data[model+'_spe']=np.where(data.actual>0,(error/data.actual.where(data.actual>0))**2,0)
            columns=['n','np']+[m+s for m in MODELS for s in ['_ae','_se','_spe']]
            aggregate=data.groupby('block')[columns].sum().reindex(range(block_count),fill_value=0)
            draws=weights@aggregate.to_numpy()
            ns,positives=draws[:,0],draws[:,1]
            for metric,suffix,denominator,root in [('mae','_ae',ns,False),('rmse','_se',ns,True),('rmspe','_spe',positives,True)]:
                losses={}
                with np.errstate(divide='ignore',invalid='ignore'):
                    for model in MODELS:
                        values=draws[:,columns.index(model+suffix)]/denominator
                        losses[model]=np.sqrt(values) if root else values
                point={m:metrics(data.actual,data[m])[metric] for m in MODELS}
                for a,b in [('M1','M0'),('M2','M0'),('M2','M1')]:
                    delta=losses[a]-losses[b];finite=np.isfinite(delta)
                    results.append(dict(policy=policy,block_sessions=length,calendar_blocks=block_count,model=a,comparison=b,metric=metric,
                        point_difference=point[a]-point[b],
                        descriptive_95pct_low=float(np.quantile(delta[finite],.025)) if finite.any() else None,
                        descriptive_95pct_high=float(np.quantile(delta[finite],.975)) if finite.any() else None,
                        undefined_resamples=int((~finite).sum()),resamples=len(delta),
                        interpretation='Positive difference means higher error. Conditional on fixed forecasts; no refitting, calibrated significance or independence guarantee.'))
    return results


def failure_cases(frame, count=5):
    records=[]
    for policy in POLICIES:
        data=frame[(frame.policy==policy)&frame.headline]
        for model in MODELS:
            block=data.copy();block['prediction']=block[model]
            block['absolute_error']=(block.prediction-block.actual).abs()
            block['relative_error']=(block.prediction-block.actual).abs()/block.actual.where(block.actual>0)
            for criterion,loss in [('absolute','absolute_error'),('relative','relative_error')]:
                chosen=block[block[loss].notna()].sort_values([loss,'date','stock'],ascending=[False,True,True]).head(count)
                for rank,(_,row) in enumerate(chosen.iterrows(),1):
                    records.append(dict(policy=policy,model=model,criterion=criterion,case_number=rank,
                        stock=row.stock,date=str(row.date.date()),target_end=str(row.target_end.date()),
                        actual=float(row.actual),prediction=float(row.prediction),absolute_error=float(row.absolute_error),
                        relative_error=float(row.relative_error) if pd.notna(row.relative_error) else None,
                        rv20=float(row.rv20),market_return=float(row.market_return),
                        market_down_breadth=float(row.market_down_breadth),origin_market_decline=bool(row.origin_market_decline),
                        forecast_direction='overprediction' if row.prediction>row.actual else 'underprediction',
                        current_price_reason=int(row.price_reason),current_return_reason=int(row.return_reason),
                        fit_id=str(row.get('fit_'+model,'')) if model!='M0' else 'parameter-free',
                        interpretation='Large observed forecast error retained. Economic cause unresolved; inspect return path/QC evidence before attribution.'))
    return records


def failure_paths(cases, output):
    paths=[]
    for policy in POLICIES:
        returns=pd.read_parquet(Path(output)/f'{policy}_discovery_returns.parquet')
        for case in cases:
            if case['policy']!=policy:
                continue
            path=returns.loc[(returns.index>pd.Timestamp(case['date']))&(returns.index<=pd.Timestamp(case['target_end'])),case['stock']]
            if len(path)!=5 or path.isna().any():
                raise ValueError('A reported error case must have five genuine observed target returns')
            reconstructed=float(np.sqrt(path.pow(2).sum()))
            if not np.isclose(reconstructed,case['actual'],rtol=0,atol=1e-13):
                raise ValueError('Failure target does not reconstruct from observed discovery returns')
            paths.append(dict(policy=policy,model=case['model'],criterion=case['criterion'],stock=case['stock'],origin=case['date'],
                target_reconstructed=reconstructed,
                next_five_returns=[dict(date=str(day.date()),log_return=float(value)) for day,value in path.items()]))
    return paths


def analyze(predictions, fits, cuts, design, output):
    output=Path(output)
    if predictions.date.max()>pd.Timestamp('2015-12-31'):
        raise ValueError('Reserved evaluation period must not enter analysis')
    predictions=predictions.copy()
    predictions['outcome_band']=outcome_band(predictions.actual,cuts)
    scores=[];coverage=[];subgroups=[];stock_scores=[];offsets=[];concentration=[]
    for policy in POLICIES:
        data=predictions[predictions.policy==policy]
        common=data[data.headline]
        scores+=score_rows(common,'headline',dict(policy=policy))
        scores+=score_rows(data[data.policy_common],'policy_common',dict(policy=policy))
        baseline=data[data.target_available&data.M0.notna()]
        scores.append(dict(scope='baseline_available',policy=policy,model='M0',**metrics(baseline.actual,baseline.M0)))
        coverage.append(dict(policy=policy,origin_stock_grid=len(data),cohort_stocks=int(data[data.cohort_eligible].stock.nunique()),
            target_available=int(data.target_available.sum()),zero_targets=int((data.actual==0).sum()),
            outside_discovery_horizon=int((~data.horizon_within_discovery).sum()),
            own_features_unavailable=int((~data.own_features_available).sum()),
            market_features_unavailable=int((~data.market_features_available).sum()),
            outside_frozen_cohort=int((~data.cohort_eligible).sum()),
            all_model_policy_common=int(data.policy_common.sum()),headline_common_both_policies=int(data.headline.sum()),
            forecasts={model:int(data[model].notna().sum()) for model in MODELS},
            note='Reason counts overlap; row-level eligibility is retained in predictions.parquet. Zero targets stay in absolute metrics.'))
        for field in ['quarter','origin_market_decline','outcome_band']:
            for value,block in common.groupby(field,dropna=False):
                subgroups+=score_rows(block,'headline_subgroup',dict(policy=policy,dimension=field,value=str(value)))
        for stock,block in common.groupby('stock'):
            stock_scores+=score_rows(block,'headline_stock',dict(policy=policy,stock=stock))
        for offset in range(5):
            block=common[common.session_pos%5==offset]
            offsets+=score_rows(block,'nonoverlap',dict(policy=policy,offset=offset))
        concentration += [dict(policy=policy,**record) for record in loss_concentration(common)]
    scoreframe=pd.DataFrame(scores)
    for i,row in scoreframe.iterrows():
        baseline=scoreframe[(scoreframe.scope==row.scope)&(scoreframe.policy==row.policy)&(scoreframe.model=='M0')]
        for metric in ['rmspe','mae','rmse']:
            denominator=baseline.iloc[0][metric] if len(baseline) else np.nan
            scoreframe.loc[i,metric+'_improvement_vs_M0']=1-row[metric]/denominator if denominator and np.isfinite(denominator) else np.nan
    stockframe=pd.DataFrame(stock_scores)
    balanced=[]
    for (policy,model),block in stockframe.groupby(['policy','model']):
        balanced.append(dict(policy=policy,model=model,stocks=len(block),mean_stock_rmspe=float(block.rmspe.mean()),
                             median_stock_rmspe=float(block.rmspe.median()),mean_stock_mae=float(block.mae.mean())))
    cases=failure_cases(predictions)
    paths=failure_paths(cases,output)
    scoreframe.to_json(output/'scores.json',orient='records',indent=2)
    pd.DataFrame(subgroups).to_json(output/'subgroups.json',orient='records',indent=2)
    stockframe.to_parquet(output/'stock_scores.parquet',index=False)
    write_json(output/'coverage.json',coverage);write_json(output/'stock_balanced.json',balanced)
    write_json(output/'nonoverlap.json',offsets);write_json(output/'loss_concentration.json',concentration)
    write_json(output/'uncertainty.json',paired_block_uncertainty(predictions,design))
    write_json(output/'failure_cases.json',cases);write_json(output/'failure_paths.json',paths)
    write_json(output/'metric_integrity.json',dict(headline_positive_targets_trimmed=0,
        epsilon_added_to_denominator=False,training_response='log positive target; no post-hoc calibration',
        outcome_bands='2014 tuning quantiles; retrospective 2015 outcome diagnostics, never model inputs',
        per_observation_order='For the same positive actual, absolute and percentage errors order models identically; aggregate disagreement is weighting and/or squaring.',
        baseline_metric_coverage='Wider baseline sample shown separately; headline identical for all three models and both masks'))
    plot_results(scoreframe,pd.DataFrame(subgroups),pd.DataFrame(concentration),predictions,output)


def plot_results(scores, subgroups, concentration, predictions, output):
    labels={'M0':'Historical volatility','M1':'Stock-specific Ridge','M2':'Stock + market Ridge'}
    colors=['#57758a','#277e79','#c87543']
    fig,axes=plt.subplots(1,3,figsize=(13,4.5))
    for ax,metric,title in zip(axes,['rmspe','mae','rmse'],['RMSPE (%)','MAE (volatility percentage points)','RMSE (volatility percentage points)']):
        for i,policy in enumerate(POLICIES):
            rows=scores[(scores.scope=='headline')&(scores.policy==policy)].set_index('model')
            ax.bar(np.arange(3)+(i-.5)*.34,[rows.loc[m,metric]*100 for m in MODELS],width=.34,label=policy,alpha=1 if i else .6,color=colors)
        ax.set_xticks(range(3),['Historical\nvolatility','Stock-specific\nRidge','Stock + market\nRidge'])
        ax.set_ylabel(title);ax.set_ylim(bottom=0)
    axes[0].legend(fontsize=8)
    fig.suptitle('Actual 2015 internal evaluation — identical observations across models and policies')
    fig.tight_layout();fig.savefig(output/'model-comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    for model,color in zip(MODELS,colors):
        part=concentration[(concentration.policy=='conservative')&(concentration.model==model)].sort_values('smallest_fraction')
        axes[0].plot(part.smallest_fraction*100,part.sum_squared_percentage_error_share*100,marker='o',color=color,label=labels[model])
        axes[1].plot(part.smallest_fraction*100,part.absolute_error_share*100,marker='o',color=color,label=labels[model])
    for ax in axes:
        ax.set_xlabel('Smallest actual-volatility observations (%)');ax.set_ylim(bottom=0);ax.legend(fontsize=8)
    axes[0].set_ylabel('Share of total squared percentage error (%)');axes[1].set_ylabel('Share of total absolute error (%)')
    fig.suptitle('Small-target loss concentration — conservative policy; no observations removed')
    fig.tight_layout();fig.savefig(output/'small-targets.png',dpi=160);plt.close(fig)
    quarters=subgroups[(subgroups.dimension=='quarter')&(subgroups.policy=='conservative')]
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    for model,color in zip(MODELS,colors):
        part=quarters[quarters.model==model].sort_values('value')
        for ax,metric in zip(axes,['rmspe','mae']):
            ax.plot(part.value,part[metric]*100,color=color,marker='o',label=labels[model])
    axes[0].set_ylabel('RMSPE (%)');axes[1].set_ylabel('MAE (volatility percentage points)')
    axes[0].legend(fontsize=8)
    fig.suptitle('Quarter stability — conservative policy, same common evaluation observations')
    fig.tight_layout();fig.savefig(output/'quarters.png',dpi=160);plt.close(fig)
