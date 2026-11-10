"""Explicit post-hoc measurement diagnostics for already-selected D004 examples.

No rescreening, new pair selection, future periods, quote correction or training.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from daily_study.declines import load_returns,reaction,Context,LeaveOutMedian,pair_metrics,write_json,corr
from daily_study.quality import sha256


def response_variants(frame,design):
    _,signed,scale=reaction(frame,design)
    variants={f'log_floor_{floor:g}':np.log((frame.abs()+floor)/scale) for floor in [1e-8,1e-6,1e-4]}
    variants['linear_abs_return_ratio']=frame.abs()/scale
    return variants,signed


def run(clean_root,design_path,experiment,output):
    output=Path(output)
    if output.exists():raise ValueError('New diagnostic output required')
    design=json.loads(Path(design_path).read_text());examples=json.loads((Path(experiment)/'examples.json').read_text())
    frames=load_returns(clean_root,design);stocks=frames['conservative'].columns.tolist();dates=frames['conservative'].index
    context=Context(frames['conservative'].to_numpy(),design);variants={};signed={}
    for policy,frame in frames.items():variants[policy],signed[policy]=response_variants(frame,design)
    diagnostics=[];influential=[];full_period=[];levels=[]
    market_primary=LeaveOutMedian(variants['conservative']['log_floor_1e-06'].to_numpy())
    for policy,frame in frames.items():
        values=frame.to_numpy();zs=variants[policy]['log_floor_1e-06'].to_numpy()
        for i,stock in enumerate(stocks):
            ordinary,stress,_,_=context.states((i,));factor,n=market_primary.median((i,))
            valid=np.isfinite(zs[:,i])&np.isfinite(factor)&(n>=design['minimum_context_donors'])
            masks={'ordinary':ordinary&valid,'decline':stress&valid}
            row=dict(stock=stock,policy=policy)
            for state,mask in masks.items():
                row[state+'_n']=int(mask.sum());row[state+'_median_abs_log_return_pct']=float(np.median(np.abs(values[mask,i]))*100) if mask.any() else np.nan
            levels.append(row)
    for e in examples:
        i,j=stocks.index(e['stock_a']),stocks.index(e['stock_b'])
        for policy,frame in frames.items():
            unconditioned,n=corr(frame.to_numpy()[:,i],frame.to_numpy()[:,j],np.ones(len(dates),dtype=bool))
            full_period.append(dict(stock_a=stocks[i],stock_b=stocks[j],policy=policy,full_discovery_signed_log_return_correlation=unconditioned,n=n,note='Includes decline days; not an ordinary-only estimate'))
        for variant in variants['conservative']:
            market=LeaveOutMedian(variants['conservative'][variant].to_numpy())
            for policy in frames:
                metrics,detail=pair_metrics(i,j,variants[policy][variant].to_numpy(),signed[policy].to_numpy(),market,context,design)
                diagnostics.append(dict(stock_a=stocks[i],stock_b=stocks[j],policy=policy,variant=variant,metrics=metrics))
                if variant=='log_floor_1e-06' and policy=='conservative':
                    good=detail['stress']&np.isfinite(detail['x'])&np.isfinite(detail['y'])
                    indices=np.flatnonzero(good);x=detail['x'][good];y=detail['y'][good]
                    if len(indices):
                        contribution=(x-x.mean())*(y-y.mean());position=int(indices[np.argmax(np.abs(contribution))])
                        influential.append(dict(stock_a=stocks[i],stock_b=stocks[j],date=str(dates[position].date()),
                             a_log_return=float(frames[policy].iloc[position,i]),b_log_return=float(frames[policy].iloc[position,j]),
                             a_adjusted_log_response=float(detail['x'][position]),b_adjusted_log_response=float(detail['y'][position]),
                             note='Largest absolute Pearson covariance contribution, not an error diagnosis; observation retained'))
    # Post-hoc masking sensitivity, not a newly selected hypothesis candidate.
    pairs=pd.read_parquet(Path(experiment)/'all_pairs_discovery.parquet')
    a=pairs[pairs.policy=='narrow'].set_index(['stock_a','stock_b'])
    b=pairs[pairs.policy=='conservative'].set_index(['stock_a','stock_b'])
    supported=(a.ordinary_n>=design['minimum_pair_ordinary_observations'])&(a.decline_n>=design['minimum_pair_decline_observations'])&(a.decline_episodes>=design['minimum_pair_decline_episodes'])&(b.ordinary_n>=design['minimum_pair_ordinary_observations'])&(b.decline_n>=design['minimum_pair_decline_observations'])&(b.decline_episodes>=design['minimum_pair_decline_episodes'])
    delta=(a.decline_adjusted_corr-b.decline_adjusted_corr).abs()[supported]
    masking_example=None
    if len(delta):
        sa,sb=delta.idxmax();i,j=stocks.index(sa),stocks.index(sb)
        market=LeaveOutMedian(variants['conservative']['log_floor_1e-06'].to_numpy())
        details={};metrics={}
        for policy in frames:
            met,detail=pair_metrics(i,j,variants[policy]['log_floor_1e-06'].to_numpy(),signed[policy].to_numpy(),market,context,design)
            metrics[policy]=met;details[policy]=detail
        common=details['narrow']['stress']&details['conservative']['stress']
        for detail in details.values():common&=np.isfinite(detail['x'])&np.isfinite(detail['y'])
        matched={}
        for policy,detail in details.items():
            value,n=corr(detail['x'],detail['y'],common);matched[policy]=dict(correlation=value,n=n)
        narrow_good=details['narrow']['stress']&np.isfinite(details['narrow']['x'])&np.isfinite(details['narrow']['y'])
        conservative_good=details['conservative']['stress']&np.isfinite(details['conservative']['x'])&np.isfinite(details['conservative']['y'])
        masking_example=dict(stock_a=sa,stock_b=sb,selection='post_hoc_maximum_masking_difference_not_hypothesis_candidate',
                             metrics=metrics,matched_date_results=matched,
                             dates_only_in_narrow=dates[narrow_good&~conservative_good].strftime('%Y-%m-%d').tolist())
    policy_comparison=dict(pairs_supported_both=int(supported.sum()),absolute_decline_correlation_difference_quantiles=delta.quantile([.5,.95,1]).to_dict(),masking_example=masking_example)
    output.mkdir(parents=True)
    write_json(output/'stock_variation_levels.json',levels)
    write_json(output/'full_period_signed_correlations.json',full_period)
    write_json(output/'masking_comparison.json',policy_comparison)
    write_json(output/'floor_and_transform_checks.json',diagnostics);write_json(output/'influential_observations.json',influential)
    # Matching source observations provide concrete evidence without asserting a correction.
    source=pd.read_parquet(Path(clean_root)/'aligned_raw.parquet',columns=['date','stock','open','high','low','close','volume'],filters=[('date','<=',pd.Timestamp(design['discovery_end']))])
    quotes=[]
    for item in influential:
        for stock in [item['stock_a'],item['stock_b']]:
            g=source[source.stock==stock].sort_values('date');stamp=pd.Timestamp(item['date']);n=int(np.flatnonzero(g.date.to_numpy()==stamp.to_datetime64())[0])
            for _,row in g.iloc[max(0,n-1):n+1].iterrows():
                quotes.append(dict(example=item['stock_a']+'/'+item['stock_b'],stock=stock,date=str(row.date.date()),
                                   open=row.open,high=row.high,low=row.low,close=row.close,volume=row.volume))
    write_json(output/'recorded_quote_excerpts.json',quotes)
    points=json.loads((Path(experiment)/'example_observations.json').read_text())
    fig,axes=plt.subplots(2,3,figsize=(13,8),squeeze=False)
    for ax,e in zip(axes.flat,examples):
        pts=[r for r in points if r['stock_a']==e['stock_a'] and r['stock_b']==e['stock_b'] and r['policy']=='conservative']
        ax.scatter([p['a_adjusted_response'] for p in pts],[p['b_adjusted_response'] for p in pts],s=18,alpha=.7)
        mark=next((x for x in influential if x['stock_a']==e['stock_a'] and x['stock_b']==e['stock_b']),None)
        if mark:
            center=np.mean([p['a_adjusted_response'] for p in pts]) if pts else 0
            right=mark['a_adjusted_log_response']>center
            ax.annotate(mark['date'],(mark['a_adjusted_log_response'],mark['b_adjusted_log_response']),fontsize=8,xytext=(-4 if right else 4,7),ha='right' if right else 'left',textcoords='offset points')
        ax.set_title(e['stock_a']+' / '+e['stock_b']);ax.set_xlabel('First stock: adjusted log response');ax.set_ylabel('Second stock: adjusted log response')
    fig.suptitle('Discovery examples with largest covariance-contribution dates labeled');fig.tight_layout();fig.savefig(output/'annotated-examples.svg');fig.savefig(output/'annotated-examples.png',dpi=130);plt.close(fig)
    for p in output.glob('*.svg'):p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
    write_json(output/'diagnostic_manifest.json',dict(kind='post_hoc_measurement_diagnostic_not_predeclared_screen',
           primary_examples_sha256=sha256(Path(experiment)/'examples.json'),code_sha256=sha256(__file__),primary_results_changed=False,
           new_hypothesis_candidates_selected=False,post_hoc_masking_example_selected=True,later_periods_examined=False,notes=['Initiated after primary example checks showed Pearson/rank/episode differences.',
           'All variants displayed; no best floor chosen and no primary result replaced.',
           'Zero recorded returns are retained; a zero is not a demonstrated data error.',
           'Full-period signed correlations and raw variation levels describe baseline differences; they do not change the screen.']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-run',type=Path,required=True);p.add_argument('--design',type=Path,required=True);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.clean_run,a.design,a.experiment,a.output)
