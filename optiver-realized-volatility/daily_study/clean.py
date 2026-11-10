"""Versioned provisional masking and selection audit. No repairs or model training."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
import exchange_calendars as xc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from daily_study.quality import EXPECTED_SHA, OHLC, sha256, read_raw, row_flags, bool_panel, evidence_panel, repeated_groups
from daily_study.targets import session_returns, forward_rv, backward_rv

VERSION='D003-v1'
REASONS={1:'no recorded observation',2:'contradictory OHLC record',4:'repeated OHLC suspicion',
         8:'invalid numeric field',16:'verified economic-action boundary',32:'outside active span'}


def policy_layers(raw,sessions,evidence):
    flags=row_flags(raw);columns=pd.Index(sorted(raw.Name.unique()),name='Name')
    panels={c:raw.pivot(index='date',columns='Name',values=c).reindex(index=sessions,columns=columns) for c in OHLC+['volume']}
    present=raw.assign(present=True).pivot(index='date',columns='Name',values='present').reindex(index=sessions,columns=columns).astype('boolean').fillna(False).astype(bool)
    masks={n:bool_panel(flags,n,sessions,columns) for n in ['ohlc_contradiction','invalid_numeric','repeated_ohlc','missing_ohlc']}
    bad=masks['ohlc_contradiction']|masks['invalid_numeric'];repeat=masks['repeated_ohlc']
    action=evidence_panel(evidence,sessions,columns,{'verified_action_boundary'})
    protected=evidence_panel(evidence,sessions,columns,{'documented_market_move'})
    outside=pd.DataFrame(False,index=sessions,columns=columns)
    for stock,g in raw.groupby('Name'):outside.loc[(sessions<g.date.min())|(sessions>g.date.max()),stock]=True
    missing=(~present).astype('uint16')+outside.astype('uint16')*32
    common=missing+masks['ohlc_contradiction'].astype('uint16')*2+masks['invalid_numeric'].astype('uint16')*8
    layers={}
    for name in ['raw_reference','error_only_reference','narrow','conservative']:
        extra=name=='conservative';guard=name in ['narrow','conservative']
        price_mask=bad|(repeat if extra else False)
        codes=common+repeat.astype('uint16')*4 if extra else common.copy()
        if name=='raw_reference':price_mask=bad&False;codes=missing.copy()
        close=panels['close'].mask(price_mask)
        returns=session_returns(close,action if guard else None)
        return_codes=codes|codes.shift(1,fill_value=1).astype('uint16')
        if guard:return_codes=return_codes|action.astype('uint16')*16
        target=forward_rv(returns)
        target_codes=return_codes.shift(-1,fill_value=1).astype('uint16')
        for k in range(2,6):target_codes=target_codes|return_codes.shift(-k,fill_value=1).astype('uint16')
        volume=panels['volume'].mask(repeat if extra else repeat&False)
        range_ok=present&~masks['missing_ohlc']&~bad&(~repeat if extra else True)
        if guard:
            pd.testing.assert_series_equal(returns.where(protected).stack(),session_returns(panels['close']).where(protected).stack())
        layers[name]=dict(close=close,returns=returns,target=target,price_mask=price_mask,volume=volume,
                          price_reasons=codes,return_reasons=return_codes,target_reasons=target_codes,range_ok=range_ok)
    return panels,present,flags,action,protected,layers


def ledger_rows(raw,sessions,flags,evidence):
    rows=[];lookup={}
    groups,_=repeated_groups(raw)
    for i,g in enumerate(groups):
        ds=sorted(g['dates'])
        for day in ds:lookup[(g['stock'],day)]=(f'REPEAT-{i:04d}',max(day,min(d for d in ds if d!=day)),ds)
    definitions={
      'missing_ohlc':('missing_field','Incomplete range inputs; close retained unless separately flagged','narrow,conservative',False,False),
      'ohlc_contradiction':('confirmed_record_inconsistency_field_unresolved','At least one price field inconsistent; specific wrong field/replacement unknown','narrow,conservative',True,False),
      'invalid_numeric':('confirmed_invalid_numeric','Nonfinite/nonpositive price or negative volume','narrow,conservative',True,False),
      'zero_volume':('unresolved_quality_flag','Recorded zero volume is preserved; not proof of an invalid close','none_review_only',False,False),
      'repeated_ohlc':('suspicious_repeated_record','Both dated copies provisionally masked for price and volume analysis; genuine date unknown','conservative',True,False)}
    for row in flags.itertuples(index=False):
        stock,day=row.Name,str(row.date.date())
        for rule,(category,note,policies,price,boundary) in definitions.items():
            if not getattr(row,rule):continue
            item=dict(cause_id=f'{stock}/{day}/{rule}',stock=stock,date=day,rule=rule,category=category,note=note,
                      masked_in=policies,masks_price=price,masks_return=boundary,point_in_time_delivery_verified=False,sources=[],
                      timing='same_session_fields_if_delivered; actual vendor delivery time unknown')
            if rule=='repeated_ohlc':
                gid,detect,ds=lookup[(stock,day)]
                item.update(repetition_group=gid,comparison_dates=ds,timing='historical_comparison_may_require_future_observation',
                            earliest_detection_session_if_delivered=detect,requires_future_session_at_observation=detect>day)
            rows.append(item)
    events=set()
    for e in evidence['events']:
        events.add((e['stock'],e['date']));boundary=e['category']=='verified_action_boundary'
        rows.append(dict(cause_id=e['id'],stock=e['stock'],date=e['date'],rule='documented_event',category=e['category'],note=e['note'],
                         masked_in='narrow,conservative' if boundary else 'none_review_only',masks_price=False,masks_return=boundary,
                         point_in_time_delivery_verified=False,timing='retrospective_source_verification; historical publication availability unverified',sources=e['sources']))
    for stock,g in raw.groupby('Name'):
        span=sessions[(sessions>=g.date.min())&(sessions<=g.date.max())]
        for stamp in span.difference(pd.DatetimeIndex(g.date)):
            day=str(stamp.date())
            rows.append(dict(cause_id=f'{stock}/{day}/missing_session',stock=stock,date=day,rule='missing_session',category='missing_observation_not_invented',
                             note='No source row inside active span; never bridge the session',masked_in='all_missing_input',masks_price=True,masks_return=False,
                             point_in_time_delivery_verified=False,timing='same_session_absence_if_feed_complete; delivery unknown',sources=[]))
    close=raw.pivot(index='date',columns='Name',values='close').reindex(sessions)
    for stamp,stock in (np.expm1(session_returns(close)).abs()>.2).stack()[lambda s:s].index:
        day=str(stamp.date())
        if (stock,day) not in events:
            rows.append(dict(cause_id=f'{stock}/{day}/extreme_review',stock=stock,date=day,rule='magnitude_screen_review_only',category='unresolved_extreme_move',
                             note='No exclusion on magnitude alone; independent structural rules may apply',masked_in='none_review_only',masks_price=False,masks_return=False,
                             point_in_time_delivery_verified=False,timing='same_session_return_if_delivered; delivery unknown',sources=[]))
    if len(rows)!=len({r['cause_id'] for r in rows}):raise AssertionError('Duplicate ledger IDs')
    return rows


def contexts(raw_returns,eligible_returns):
    """Fixed audit bands, not learned forecasting regimes. No future targets used."""
    out=pd.DataFrame(index=raw_returns.index)
    for prefix,r in [('raw',raw_returns),('quality_eligible',eligible_returns)]:
        median=r.median(axis=1);variation=r.abs().median(axis=1)
        out[prefix+'_median_return']=median;out[prefix+'_median_abs_return']=variation
        out[prefix+'_peer_count']=r.notna().sum(axis=1)
        out[prefix+'_direction']=np.select([median<-.01,median>.01,median.notna()],['median_decline_gt_1pct','median_rise_gt_1pct','within_plus_minus_1pct'],default='unavailable')
        out[prefix+'_variation']=pd.cut(variation,[-np.inf,.005,.01,.02,np.inf],labels=['at_most_0.5pct','0.5_to_1pct','1_to_2pct','above_2pct']).astype('object').fillna('unavailable')
    return out


def write_frame(path,frame):
    frame=frame.copy()
    for c in frame:
        if pd.api.types.is_datetime64_any_dtype(frame[c]):frame[c]=frame[c].dt.strftime('%Y-%m-%d')
    path.write_text(frame.to_json(orient='records',indent=2)+'\n')


def target_cause_links(lost,sessions,ledger,policy):
    price_lookup=defaultdict(list);boundary_lookup=defaultdict(list)
    effective_policy='narrow' if policy=='error_only_reference' else policy
    for row in ledger:
        if effective_policy not in row['masked_in'].split(',') and row['masked_in']!='all_missing_input':continue
        key=(row['stock'],row['date'])
        if row['masks_price']:price_lookup[key].append(row['cause_id'])
        if row['masks_return'] and policy!='error_only_reference':boundary_lookup[key].append(row['cause_id'])
    links=[]
    for origin,stock in lost.stack()[lambda s:s].index:
        i=sessions.get_loc(origin);ids=[]
        for j,day in enumerate(sessions[i:i+6]):
            key=(stock,str(day.date()));ids+=price_lookup.get(key,[])
            if j>0:ids+=boundary_lookup.get(key,[])
        if not ids:raise AssertionError('Unexplained target exclusion')
        links.append(dict(stock=stock,origin=str(origin.date()),target_end=str(sessions[i+5].date()),cause_ids=sorted(set(ids))))
    return links


def build(csv,evidence_path,output,enforce_hash=True):
    output=Path(output)
    if output.exists():raise ValueError('Fresh output directory required; clean versions are immutable')
    before=sha256(csv)
    if enforce_hash and before!=EXPECTED_SHA:raise ValueError('Source snapshot mismatch')
    raw=read_raw(csv);evidence=json.loads(Path(evidence_path).read_text())
    cal=xc.get_calendar('XNYS',start=raw.date.min()-pd.Timedelta(days=7),end=raw.date.max()+pd.Timedelta(days=7))
    sessions=cal.sessions_in_range(raw.date.min(),raw.date.max()).tz_localize(None)
    if len(pd.DatetimeIndex(raw.date.unique()).difference(sessions)):raise ValueError('Non-session observations')
    panels,present,flags,action,protected,layers=policy_layers(raw,sessions,evidence)
    ledger=ledger_rows(raw,sessions,flags,evidence)
    context=contexts(layers['raw_reference']['returns'],layers['conservative']['returns'])
    base=layers['raw_reference']['target'].notna();base_returns=layers['raw_reference']['returns'];denom=int(base.to_numpy().sum())
    review=np.expm1(base_returns).abs()>.2;unresolved=review&~action&~protected
    unresolved_target=unresolved&False
    for k in range(1,6):unresolved_target=unresolved_target|unresolved.shift(-k,fill_value=False)
    output.mkdir(parents=True)
    (output/'ledger.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in ledger))
    aligned=pd.concat(panels,axis=1).stack(level=1,future_stack=True).rename_axis(['date','stock']).reset_index()
    aligned['source_present']=present.stack(future_stack=True).to_numpy();aligned.to_parquet(output/'aligned_raw.parquet',index=False)
    summaries=[];stock_tables=[];date_tables=[];condition_tables=[];activity_tables=[]
    activities={}
    for proxy,volume in [('raw',panels['volume']),('quality_eligible',layers['conservative']['volume'])]:
        rel=volume/volume.shift(1).rolling(20,min_periods=20).median().replace(0,np.nan)
        activities[proxy]=pd.DataFrame(np.select([rel>2,rel<=2],['over_2x_prior_20_session_median','at_most_2x'],default='unavailable'),index=sessions,columns=volume.columns)
    for name,layer in layers.items():
        available=layer['target'].notna();lost=base&~available
        summary=dict(policy=name,price_rows_masked=int((layer['price_mask']&present).to_numpy().sum()),
                     source_rows_retained=int((present&layer['close'].notna()).to_numpy().sum()),
                     explicit_action_boundaries=int(action.to_numpy().sum()) if name in ['narrow','conservative'] else 0,
                     newly_unavailable_returns=int((base_returns.notna()&layer['returns'].isna()).to_numpy().sum()),
                     available_targets=int(available.to_numpy().sum()),targets_lost_vs_raw=int(lost.to_numpy().sum()),
                     loss_pct_vs_raw=float(100*lost.to_numpy().sum()/denom) if denom else None,
                     targets_lost_vs_narrow=int((layers['narrow']['target'].notna()&~available).to_numpy().sum()),
                     optional_20_return_history_and_target=int((available&backward_rv(layer['returns']).notna()).to_numpy().sum()),
                     targets_retained_touching_unresolved_gt20pct_moves=int((available&unresolved_target).to_numpy().sum()),
                     protected_returns_retained=int((protected&layer['returns'].notna()).to_numpy().sum()))
        summaries.append(summary)
        stocks=pd.DataFrame({'raw_targets':base.sum(),'available_targets':available.sum(),'lost_targets':lost.sum(),
                             'price_rows_masked':(layer['price_mask']&present).sum(),'source_rows':present.sum()})
        stocks['loss_pct']=100*stocks.lost_targets/stocks.raw_targets.replace(0,np.nan);stocks['policy']=name
        stock_tables.append(stocks.rename_axis('stock').reset_index())
        dates=pd.DataFrame({'raw_targets':base.sum(axis=1),'available_targets':available.sum(axis=1),'lost_targets':lost.sum(axis=1),
                            'price_rows_masked':(layer['price_mask']&present).sum(axis=1),'source_rows':present.sum(axis=1)})
        dates['loss_pct']=100*dates.lost_targets/dates.raw_targets.replace(0,np.nan);dates['policy']=name;dates=dates.join(context)
        date_tables.append(dates.rename_axis('date').reset_index())
        for prefix in ['raw','quality_eligible']:
            for condition in ['direction','variation']:
                ct=dates.groupby(prefix+'_'+condition,observed=True).agg(dates=('raw_targets','size'),raw_targets=('raw_targets','sum'),
                      available_targets=('available_targets','sum'),lost_targets=('lost_targets','sum'))
                ct['loss_pct']=100*ct.lost_targets/ct.raw_targets.replace(0,np.nan)
                ct['policy']=name;ct['proxy']=prefix;ct['condition']=condition;condition_tables.append(ct.rename_axis('band').reset_index())
        for proxy,activity in activities.items():
            for band in ['over_2x_prior_20_session_median','at_most_2x','unavailable']:
                member=activity.eq(band)&base;n=int(member.to_numpy().sum());k=int((member&lost).to_numpy().sum())
                activity_tables.append(dict(policy=name,proxy=proxy,band=band,raw_targets=n,lost_targets=k,loss_pct=100*k/n if n else None))
        view=pd.concat({'analysis_close':layer['close'],'analysis_volume':layer['volume'],'log_return':layer['returns'],
             'provisional_target_5':layer['target'],'price_reason_codes':layer['price_reasons'],'return_reason_codes':layer['return_reasons'],
             'target_reason_codes':layer['target_reasons'],'range_features_eligible':layer['range_ok']},axis=1).stack(level=1,future_stack=True).rename_axis(['date','stock']).reset_index()
        view['target_end']=view.date.map(pd.Series(sessions,index=sessions).shift(-5))
        view.to_parquet(output/f'{name}.parquet',index=False)
        links=target_cause_links(lost,sessions,ledger,name)
        (output/f'{name}_target_exclusions.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in links))
    if sha256(csv)!=before:raise AssertionError('Raw source changed')
    stocks=pd.concat(stock_tables,ignore_index=True);dates=pd.concat(date_tables,ignore_index=True);conditions=pd.concat(condition_tables,ignore_index=True)
    write_frame(output/'by_stock.json',stocks);write_frame(output/'by_date.json',dates);write_frame(output/'by_condition.json',conditions)
    (output/'by_activity.json').write_text(json.dumps(activity_tables,indent=2)+'\n')
    cs=stocks[stocks.policy=='conservative'].sort_values('loss_pct',ascending=False);dt=dates[dates.policy=='conservative'].sort_values('lost_targets',ascending=False)
    repeats=[r for r in ledger if r['rule']=='repeated_ohlc'];loss=int(cs.lost_targets.sum())
    manifest=dict(version=VERSION,decision='D003',models_trained=False,prices_replaced=0,source_sha256=before,source_sha256_after=sha256(csv),
         evidence_sha256=sha256(evidence_path),code_sha256=sha256(__file__),target_code_sha256=sha256(Path(__file__).with_name('targets.py')),
         python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,calendar_version=xc.__version__,rows_in_raw=len(raw),
         aligned_positions=int(present.size),recorded_source_rows=int(present.to_numpy().sum()),reason_codes=REASONS,policy_summaries=summaries,
         ledger_entries=len(ledger),repeated_rows=len(repeats),repeated_rows_requiring_future_session_at_observation=sum(r['requires_future_session_at_observation'] for r in repeats),
         top20_origin_dates_share_of_conservative_target_loss=float(dt.head(20).lost_targets.sum()/loss) if loss else 0,
         top_stock_loss_rates=json.loads(cs.head(15).to_json(orient='records')),
         notes=['Narrow/conservative share economic-action guards; actions are not errors.',
                'No magnitude exclusions or zero-volume price exclusions. All originals preserved.',
                'Fixed condition bands are descriptive audit bins, not forecasting regime choices.',
                'Masks are retrospective; actual source delivery timestamps unavailable.',
                'Outside recorded active span is not exclusion of an existing source row.'])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,5));top=cs.head(12).iloc[::-1]
    axes[0].barh(top.stock,top.loss_pct);axes[0].set_xlabel('Five-session targets unavailable vs raw (%)');axes[0].set_title('Most affected stocks: conservative policy')
    for policy in ['narrow','conservative']:
        g=dates[dates.policy==policy];axes[1].plot(g.date,g.loss_pct,label=policy,linewidth=.8)
    axes[1].set_title('Concentration by forecast-origin date');axes[1].set_ylabel('Raw targets lost (%)');axes[1].legend();fig.tight_layout();fig.savefig(output/'selection-bias.svg');plt.close(fig)
    for p in output.glob('*.svg'):p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
    (output/'artifact_hashes.json').write_text(json.dumps({p.name:sha256(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    return manifest


def verify_run(output,source=None):
    """Reject incomplete or modified clean artifacts; optionally recheck raw source."""
    root=Path(output)
    hashes=json.loads((root/'artifact_hashes.json').read_text())
    for name,digest in hashes.items():
        if Path(name).name!=name or sha256(root/name)!=digest:
            raise ValueError(f'Artifact integrity mismatch: {name}')
    manifest=json.loads((root/'manifest.json').read_text())
    if source is not None and sha256(source)!=manifest['source_sha256']:
        raise ValueError('Raw source no longer matches this run')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--csv',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.csv,a.evidence,a.output),indent=2))


if __name__=='__main__':main()
