"""D004 descriptive discovery: no future outcomes, prediction models or peer forecasts."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from daily_study.clean import verify_run
from daily_study.quality import sha256


class LeaveOutMedian:
    """Exact row medians after deleting zero, one or two named columns."""
    def __init__(self,values):
        a=np.asarray(values,dtype=float);self.valid=np.isfinite(a);self.count=self.valid.sum(axis=1)
        self.sorted=np.sort(np.where(self.valid,a,np.inf),axis=1)
        order=np.argsort(np.where(self.valid,a,np.inf),axis=1,kind='stable')
        ranks=np.empty_like(order);np.put_along_axis(ranks,order,np.broadcast_to(np.arange(a.shape[1]),a.shape),axis=1)
        self.ranks=np.where(self.valid,ranks,-1)
    def median(self,exclude=()):
        if len(set(exclude))!=len(exclude) or len(exclude)>2:raise ValueError('Distinct zero/one/two exclusions required')
        removed=[];n=self.count.copy()
        for j in exclude:
            r=self.ranks[:,j];n-=r>=0;removed.append(np.where(r>=0,r,self.sorted.shape[1]+1))
        if removed:removed=np.sort(np.array(removed),axis=0)
        result=[]
        for k in [(np.maximum(n,1)-1)//2,np.maximum(n,1)//2]:
            idx=k.copy()
            for r in removed:idx+=(r<=idx)
            idx=np.minimum(idx,self.sorted.shape[1]-1)
            result.append(self.sorted[np.arange(len(n)),idx])
        with np.errstate(invalid='ignore'):value=(result[0]+result[1])/2
        return np.where(n>0,value,np.nan),n


class Context:
    def __init__(self,returns,design):
        self.simple=np.expm1(returns);self.valid=np.isfinite(self.simple)
        self.order=LeaveOutMedian(self.simple);self.design=design
    def states(self,exclude=(),rule=None):
        rule=rule or self.design['primary_decline']
        median,n=self.order.median(exclude)
        low=(self.simple<=rule['donor_simple_return_at_most']+1e-12)&self.valid
        negative=low.sum(axis=1)
        for j in exclude:negative-=low[:,j]
        valid=n>=self.design['minimum_context_donors']
        stress=valid&(negative>=rule['minimum_fraction']*n-1e-12)
        ordinary=valid&~stress&(np.abs(median)<=self.design['ordinary']['absolute_leave_out_donor_median_simple_return_at_most']+1e-12)
        return ordinary,stress,n,median


def reaction(returns,design):
    """Own scale uses only the preceding 60 sessions; no current/future return."""
    scale=returns.abs().shift(1).rolling(design['scale_window_sessions'],min_periods=design['scale_minimum_observed_returns']).median()
    scale=scale.where(scale>0)
    z=np.log((returns.abs()+.000001)/scale)
    signed=returns/scale
    return z,signed,scale


def corr(x,y,mask):
    good=mask&np.isfinite(x)&np.isfinite(y);a=x[good];b=y[good]
    if len(a)<3:return np.nan,len(a)
    a=a-a.mean();b=b-b.mean();den=float(np.sqrt(np.dot(a,a)*np.dot(b,b)))
    return (float(np.dot(a,b)/den) if den>1e-14 else np.nan),len(a)


def episode_ids(indices,gap):
    indices=np.asarray(indices,dtype=int)
    return np.cumsum(np.r_[0,np.diff(indices)>gap]) if len(indices) else np.array([],dtype=int)


def pair_metrics(i,j,z,signed,market_reactions,context,design,rule=None):
    ordinary,stress,donors,_=context.states((i,j),rule)
    factor,n=market_reactions.median((i,j));valid=n>=design['minimum_context_donors']
    x=z[:,i]-factor;y=z[:,j]-factor
    ordinary=ordinary&valid;stress=stress&valid
    oc,no=corr(x,y,ordinary);sc,ns=corr(x,y,stress)
    raw,_=corr(z[:,i],z[:,j],stress)
    signed_corr,_=corr(signed[:,i],signed[:,j],ordinary)
    good=stress&np.isfinite(x)&np.isfinite(y)
    episode_count=len(np.unique(episode_ids(np.flatnonzero(good),design['episode_gap_sessions'])))
    return dict(ordinary_adjusted_corr=oc,decline_adjusted_corr=sc,decline_raw_corr=raw,
                ordinary_signed_corr=signed_corr,correlation_change=sc-oc,
                ordinary_n=no,decline_n=ns,decline_episodes=episode_count),dict(x=x,y=y,ordinary=ordinary,stress=stress)


def passes(row,design):
    s=design['candidate_screen']
    return bool(row['ordinary_n']>=design['minimum_pair_ordinary_observations'] and row['decline_n']>=design['minimum_pair_decline_observations'] and row['decline_episodes']>=design['minimum_pair_decline_episodes']
                and abs(row['ordinary_signed_corr'])<=s['absolute_ordinary_signed_correlation_at_most']
                and abs(row['ordinary_adjusted_corr'])<=s['absolute_ordinary_adjusted_reaction_correlation_at_most']
                and row['decline_adjusted_corr']>=s['decline_adjusted_reaction_correlation_at_least']
                and row['correlation_change']>=s['decline_minus_ordinary_adjusted_correlation_at_least'])


def bootstrap_episode(x,y,stress,design,seed):
    good=stress&np.isfinite(x)&np.isfinite(y);indices=np.flatnonzero(good)
    labels=episode_ids(indices,design['episode_gap_sessions']);groups=[indices[labels==g] for g in np.unique(labels)]
    point,_=corr(x,y,good)
    leave=[]
    for group in groups:
        mask=good.copy();mask[group]=False;value,_=corr(x,y,mask)
        if np.isfinite(value):leave.append(value)
    boot=[];rng=np.random.default_rng(seed)
    if len(groups)>=2:
        for _ in range(1000):
            sampled=np.concatenate([groups[k] for k in rng.integers(0,len(groups),size=len(groups))])
            value,_=corr(x[sampled],y[sampled],np.ones(len(sampled),dtype=bool))
            if np.isfinite(value):boot.append(value)
    rank,_=corr(pd.Series(x[good]).rank().to_numpy(),pd.Series(y[good]).rank().to_numpy(),np.ones(good.sum(),dtype=bool))
    return dict(pearson=point,spearman=rank,observations=len(indices),episodes=len(groups),
                episode_bootstrap_95pct=np.quantile(boot,[.025,.975]).tolist() if boot else None,
                leave_one_episode_out_range=[min(leave),max(leave)] if leave else None,
                caution='Descriptive post-selection intervals; not multiple-testing-adjusted or predictive confirmation')


def load_returns(clean_root,design):
    # Read no target columns and filter before any relationship computation.
    frames={}
    for name in ['narrow','conservative']:
        frame=pd.read_parquet(Path(clean_root)/f'{name}.parquet',columns=['date','stock','log_return'],
                              filters=[('date','<=',pd.Timestamp(design['discovery_end'])),('date','>=',pd.Timestamp(design['discovery_start']))])
        frames[name]=frame.pivot(index='date',columns='stock',values='log_return').sort_index()
    if not frames['narrow'].index.equals(frames['conservative'].index):raise ValueError('Policy calendar mismatch')
    return frames


def safe_json(value):
    if isinstance(value,dict):return {str(k):safe_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [safe_json(v) for v in value]
    if isinstance(value,np.ndarray):return safe_json(value.tolist())
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,(np.bool_,)):return bool(value)
    return value


def write_json(path,value):path.write_text(json.dumps(safe_json(value),indent=2,allow_nan=False)+'\n')


def run(clean_root,design_path,output):
    output=Path(output)
    if output.exists():raise ValueError('Fresh descriptive output directory required')
    source=verify_run(clean_root);design=json.loads(Path(design_path).read_text());frames=load_returns(clean_root,design)
    output.mkdir(parents=True)
    dates=frames['conservative'].index;stocks=frames['conservative'].columns.tolist();arrays={};profiles=[]
    reactions={}
    for policy,frame in frames.items():
        z,signed,scale=reaction(frame,design);arrays[policy]=(z.to_numpy(),signed.to_numpy());reactions[policy]=z
    context=Context(frames['conservative'].to_numpy(),design)
    market_reactions=LeaveOutMedian(reactions['conservative'].to_numpy())
    global_ordinary,global_stress,donors,market_return=context.states()
    timeline=pd.DataFrame({'date':dates,'ordinary':global_ordinary,'decline':global_stress,'donors':donors,'donor_median_simple_return':market_return})
    timeline.to_json(output/'context_timeline.json',orient='records',date_format='iso',indent=2)
    for policy,(z,signed) in arrays.items():
        for i,stock in enumerate(stocks):
            ordinary,stress,_,_=context.states((i,));factor,n=market_reactions.median((i,));residual=z[:,i]-factor
            valid=np.isfinite(residual)&(n>=design['minimum_context_donors'])
            a=ordinary&valid;b=stress&valid
            no,ns=int(a.sum()),int(b.sum())
            adequate=no>=design['minimum_profile_ordinary_observations'] and ns>=design['minimum_profile_decline_observations']
            def median(values,mask):return float(np.median(values[mask])) if mask.any() else np.nan
            record=dict(stock=stock,policy=policy,ordinary_n=no,decline_n=ns,support_adequate=adequate,
                        ordinary_recorded_returns=int((ordinary&np.isfinite(frames[policy].to_numpy()[:,i])).sum()),
                        decline_recorded_returns=int((stress&np.isfinite(frames[policy].to_numpy()[:,i])).sum()),
                        ordinary_response_ratio=np.exp(median(z[:,i],a)),decline_response_ratio=np.exp(median(z[:,i],b)),
                        raw_amplification=np.exp(median(z[:,i],b)-median(z[:,i],a)),
                        market_adjusted_amplification=np.exp(median(residual,b)-median(residual,a)))
            profiles.append(record)
    profile=pd.DataFrame(profiles);profile.to_json(output/'stock_profiles.json',orient='records',indent=2)
    rows=[];total=len(stocks)*(len(stocks)-1)//2
    for i in range(len(stocks)):
        for j in range(i+1,len(stocks)):
            for policy,(z,signed) in arrays.items():
                metrics,_=pair_metrics(i,j,z,signed,market_reactions,context,design)
                metrics.update(stock_a=stocks[i],stock_b=stocks[j],policy=policy)
                metrics['screen_pass']=passes(metrics,design);rows.append(metrics)
        if i and i%100==0:print(f'Completed pair discovery for first {i} stocks',flush=True)
    pairs=pd.DataFrame(rows);pairs.to_parquet(output/'all_pairs_discovery.parquet',index=False)
    a=pairs[pairs.policy=='narrow'].set_index(['stock_a','stock_b']);b=pairs[pairs.policy=='conservative'].set_index(['stock_a','stock_b'])
    agreed=a.screen_pass&b.screen_pass
    ranked=pd.DataFrame({'minimum_policy_change':np.minimum(a.correlation_change,b.correlation_change)})[agreed].sort_values('minimum_policy_change',ascending=False)
    selected=list(ranked.head(design['candidate_screen']['maximum_examples']).index)
    controls=[tuple(x) for x in design['fixed_controls'] if all(s in stocks for s in x)]
    examples=[];example_series=[]
    for number,(sa,sb) in enumerate(dict.fromkeys(selected+controls)):
        i,j=stocks.index(sa),stocks.index(sb);record=dict(stock_a=sa,stock_b=sb,selection='discovery_screen' if (sa,sb) in selected else 'predeclared_control',policies={},sensitivities={})
        details={}
        for policy,(z,signed) in arrays.items():
            metrics,detail=pair_metrics(i,j,z,signed,market_reactions,context,design);details[policy]=detail
            record['policies'][policy]=dict(metrics=metrics,uncertainty=bootstrap_episode(detail['x'],detail['y'],detail['stress'],design,design['seed']+number))
            good=detail['stress']&np.isfinite(detail['x'])&np.isfinite(detail['y'])
            for t in np.flatnonzero(good):example_series.append(dict(stock_a=sa,stock_b=sb,policy=policy,date=str(dates[t].date()),a_adjusted_response=float(detail['x'][t]),b_adjusted_response=float(detail['y'][t])))
            for rule in design['sensitivity_rules']:
                met,_=pair_metrics(i,j,z,signed,market_reactions,context,design,rule)
                record['sensitivities'][policy+'/'+rule['name']]=met
        # Common-date comparison separates extra observations from baseline-scale effects.
        common={}
        for state in ['ordinary','stress']:
            valid=details['narrow'][state]&details['conservative'][state]
            for detail in details.values():valid&=np.isfinite(detail['x'])&np.isfinite(detail['y'])
            common[state]={policy:dict(zip(['correlation','n'],corr(d['x'],d['y'],valid))) for policy,d in details.items()}
        record['same_date_comparison']=common;examples.append(record)
    write_json(output/'examples.json',examples);write_json(output/'example_observations.json',example_series)
    write_json(output/'candidate_screen.json',[dict(stock_a=x[0],stock_b=x[1],minimum_policy_change=row.minimum_policy_change) for x,row in ranked.iterrows()])
    sensitivity=[]
    for rule in design['sensitivity_rules']:
        ordinary,stress,n,_=context.states(rule=rule)
        sensitivity.append(dict(rule=rule['name'],ordinary_dates=int(ordinary.sum()),decline_dates=int(stress.sum()),donor_eligible_dates=int((n>=design['minimum_context_donors']).sum())))
    summary=dict(stage='descriptive_discovery_evidence_for_lead_interpretation',prediction_models_trained=False,future_target_columns_read=False,
                 discovery_start=str(dates.min().date()),discovery_end=str(dates.max().date()),discovery_dates=len(dates),stocks_in_aligned_grid=len(stocks),stocks_with_observed_discovery_returns=int(frames['conservative'].notna().any().sum()),
                 global_context_decline_dates=int(global_stress.sum()),global_context_ordinary_dates=int(global_ordinary.sum()),
                 global_context_other_or_unavailable_dates=int((~global_stress&~global_ordinary).sum()),
                 global_decline_episodes=len(np.unique(episode_ids(np.flatnonzero(global_stress),design['episode_gap_sessions']))),
                 pair_universe=total,both_policy_screen_passes=len(ranked),selected_examples=selected,primary_context_sensitivities=sensitivity,
                 design_sha256=sha256(design_path),clean_manifest_sha256=sha256(Path(clean_root)/'manifest.json'),code_sha256=sha256(__file__),
                 later_relationship_results_examined=False,profile_support_counts={},pair_support_counts={},correlation_distributions={})
    for policy in arrays:
        p=profile[profile.policy==policy];q=pairs[pairs.policy==policy]
        supported=(q.ordinary_n>=design['minimum_pair_ordinary_observations'])&(q.decline_n>=design['minimum_pair_decline_observations'])&(q.decline_episodes>=design['minimum_pair_decline_episodes'])
        summary['profile_support_counts'][policy]=int(p.support_adequate.sum());summary['pair_support_counts'][policy]=int(supported.sum())
        summary['correlation_distributions'][policy]={c:q.loc[supported,c].quantile([.1,.5,.9,.99]).to_dict() for c in ['ordinary_adjusted_corr','decline_raw_corr','decline_adjusted_corr','correlation_change']}
    write_json(output/'summary.json',summary)
    # Plots are evidence displays, deliberately not titled as a conclusion.
    fig,axes=plt.subplots(2,1,figsize=(12,6),sharex=False)
    axes[0].plot(dates,market_return*100,linewidth=.7,color='#506780');axes[0].scatter(dates[global_stress],market_return[global_stress]*100,s=12,color='#bf4c45',label='Breadth-defined decline dates');axes[0].set_ylabel('Donor median return (%)');axes[0].legend()
    for policy in arrays:
        p=profile[(profile.policy==policy)&profile.support_adequate]
        axes[1].hist(p.raw_amplification,bins=35,alpha=.5,label=policy)
    axes[1].set_xlabel('Stock median response under decline / ordinary (own-scale normalized)');axes[1].set_ylabel('Stocks');axes[1].legend();fig.suptitle('Discovery evidence: dates and stock response distributions');fig.tight_layout();fig.savefig(output/'dates-and-responses.svg');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    pp=profile.pivot(index='stock',columns='policy',values='market_adjusted_amplification')
    axes[0].scatter(pp.narrow,pp.conservative,s=10,alpha=.6);axes[0].axline((1,1),slope=1,color='gray',linestyle='--');axes[0].set_xlabel('Narrow: market-adjusted amplification');axes[0].set_ylabel('Conservative: market-adjusted amplification')
    q=pairs[pairs.policy=='conservative'];support=(q.ordinary_n>=100)&(q.decline_n>=20)&(q.decline_episodes>=6)
    axes[1].hist(q.loc[support,'decline_raw_corr'],bins=50,alpha=.5,label='Before market de-medianing');axes[1].hist(q.loc[support,'decline_adjusted_corr'],bins=50,alpha=.5,label='After de-medianing');axes[1].set_xlabel('Pair response correlation on decline dates');axes[1].set_ylabel('Supported pairs');axes[1].legend();fig.suptitle('Policy sensitivity and common-reaction control');fig.tight_layout();fig.savefig(output/'controls-and-policy.svg');plt.close(fig)
    fig,axes=plt.subplots(1,max(1,len(examples)),figsize=(max(6,4*len(examples)),4),squeeze=False)
    for ax,e in zip(axes.flat,examples):
        pts=[r for r in example_series if r['stock_a']==e['stock_a'] and r['stock_b']==e['stock_b'] and r['policy']=='conservative']
        ax.scatter([r['a_adjusted_response'] for r in pts],[r['b_adjusted_response'] for r in pts],s=18,alpha=.7);ax.set_title(e['stock_a']+' / '+e['stock_b']);ax.set_xlabel('First stock: adjusted log response');ax.set_ylabel('Second stock: adjusted log response')
    fig.suptitle('Example decline observations: descriptive discovery only');fig.tight_layout();fig.savefig(output/'pair-examples.svg');plt.close(fig)
    for path in output.glob('*.svg'):path.write_text('\n'.join(s.rstrip() for s in path.read_text().splitlines())+'\n')
    write_json(output/'artifact_hashes.json',{p.name:sha256(p) for p in output.iterdir() if p.is_file()})
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-run',type=Path,required=True);p.add_argument('--design',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(safe_json(run(a.clean_run,a.design,a.output)),indent=2))


if __name__=='__main__':main()
