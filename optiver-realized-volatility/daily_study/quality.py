"""Reproducible raw-data audit and cleaning-policy sensitivity; never repairs data."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
import exchange_calendars as xc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from daily_study.targets import session_returns, forward_rv, backward_rv

EXPECTED_SHA = '6aea253cd19de60b568143991aaf1fa482456565c389205658d236e595e716cf'
OHLC = ['open','high','low','close']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_raw(path):
    raw = pd.read_csv(path)
    if set(raw.columns) != {'date','Name','volume',*OHLC}:
        raise ValueError('Unexpected CSV schema')
    raw['date'] = pd.to_datetime(raw.date, format='%Y-%m-%d', errors='raise')
    for col in OHLC + ['volume']:
        raw[col] = pd.to_numeric(raw[col], errors='raise')
    if raw.Name.isna().any() or raw.date.isna().any():
        raise ValueError('Missing stock/date identifiers')
    if raw.duplicated(['Name','date']).any():
        raise ValueError('Duplicate stock/date identifiers need an explicit resolution')
    return raw.sort_values(['Name','date']).reset_index(drop=True)


def row_flags(raw):
    flags = raw[['Name','date']].copy()
    flags['missing_ohlc'] = raw[OHLC].isna().any(axis=1)
    flags['invalid_numeric'] = ((~np.isfinite(raw[OHLC+['volume']]) & raw[OHLC+['volume']].notna()).any(axis=1)
                                | (raw[OHLC] <= 0).any(axis=1) | (raw.volume < 0))
    flags['ohlc_contradiction'] = raw[OHLC].notna().all(axis=1) & (
        (raw.high < raw[['open','low','close']].max(axis=1)) |
        (raw.low > raw[['open','high','close']].min(axis=1)))
    flags['zero_volume'] = raw.volume.eq(0)
    complete = raw[OHLC].notna().all(axis=1)
    # Mark BOTH copies. Date order does not identify which observation is genuine.
    flags['repeated_ohlc'] = complete & raw.duplicated(['Name',*OHLC], keep=False)
    flags['repeated_ohlcv'] = complete & raw.duplicated(['Name',*OHLC,'volume'], keep=False)
    return flags


def make_panels(raw, sessions):
    return {col: raw.pivot(index='date',columns='Name',values=col).reindex(sessions)
            for col in ['close','volume']}


def bool_panel(flags, name, sessions, columns):
    return flags.pivot(index='date',columns='Name',values=name).reindex(index=sessions,columns=columns).astype('boolean').fillna(False).astype(bool)


def evidence_panel(evidence, sessions, columns, categories):
    mask = pd.DataFrame(False,index=sessions,columns=columns)
    for event in evidence['events']:
        if event['category'] in categories:
            day, stock = pd.Timestamp(event['date']), event['stock']
            if day not in mask.index or stock not in mask.columns:
                raise ValueError(f'Evidence key outside panel: {event}')
            mask.loc[day,stock] = True
    return mask


def repeated_groups(raw):
    counts = Counter()
    records=[]
    subset=raw[raw[OHLC].notna().all(axis=1)&raw.duplicated(['Name',*OHLC],keep=False)]
    for _,group in subset.groupby(['Name',*OHLC]):
        dates=tuple(group.date.dt.strftime('%Y-%m-%d'))
        counts[dates]+=1
        records.append({'stock':group.Name.iloc[0],'dates':list(dates),
                        'same_volume':bool(group.volume.nunique()==1),'rows':len(group)})
    return records,[{'dates':list(k),'stocks':v} for k,v in counts.most_common()]


def investigate(path, evidence_path, output, enforce_hash=True):
    output=Path(output)
    if output.exists():
        raise ValueError('Refusing to overwrite an audit; use a fresh output directory')
    raw_hash=sha256(path)
    if enforce_hash and raw_hash!=EXPECTED_SHA:
        raise ValueError('Source hash changed: inspect the new snapshot before comparing counts')
    evidence=json.loads(Path(evidence_path).read_text())
    raw=read_raw(path);flags=row_flags(raw)
    calendar=xc.get_calendar('XNYS',start=raw.date.min()-pd.Timedelta(days=7),end=raw.date.max()+pd.Timedelta(days=7))
    sessions=calendar.sessions_in_range(raw.date.min(),raw.date.max()).tz_localize(None)
    observed=pd.DatetimeIndex(sorted(raw.date.unique()))
    if len(observed.difference(sessions)):
        raise ValueError('Non-exchange dates require investigation before target construction')
    panels=make_panels(raw,sessions);close=panels['close'];columns=close.columns
    baseline=session_returns(close)
    bad=bool_panel(flags,'ohlc_contradiction',sessions,columns)|bool_panel(flags,'invalid_numeric',sessions,columns)
    repeated=bool_panel(flags,'repeated_ohlc',sessions,columns)
    zero=bool_panel(flags,'zero_volume',sessions,columns)
    action=evidence_panel(evidence,sessions,columns,{'verified_action_boundary'})
    possible=evidence_panel(evidence,sessions,columns,{'action_date_incomplete'})
    legitimate=evidence_panel(evidence,sessions,columns,{'documented_market_move'})
    extreme=baseline.abs().notna() & (np.expm1(baseline).abs()>.2)
    # Scenarios preview consequences. No cleaned prices, training table, or model is written.
    scenarios=[('raw_calendar_only',pd.DataFrame(False,index=sessions,columns=columns),None),
               ('S1_contradictory_prices',bad,None),
               ('S2_plus_repeated_OHLC',bad|repeated,None),
               ('S3_plus_verified_action_boundaries',bad|repeated,action),
               ('S4_plus_documented_action_date_pending',bad|repeated,action|possible),
               ('sensitivity_zero_volume',bad|repeated|zero,action|possible),
               ('sensitivity_unresolved_extremes',bad|repeated,action|possible|(extreme&~legitimate))]
    base_target=forward_rv(baseline)
    base_count=int(base_target.notna().to_numpy().sum())
    effects=[]
    for name,price_mask,return_mask in scenarios:
        returns=session_returns(close.mask(price_mask),return_mask)
        target=forward_rv(returns)
        loss=base_target.notna() & target.isna()
        effects.append({'scenario':name,'masked_existing_price_rows':int((price_mask&close.notna()).to_numpy().sum()),
                        'explicit_return_boundaries':int(return_mask.to_numpy().sum()) if return_mask is not None else 0,
                        'valid_five_session_targets':int(target.notna().to_numpy().sum()),
                        'targets_unavailable_vs_raw':int(loss.to_numpy().sum()),
                        'percent_target_loss_vs_raw':100*int(loss.to_numpy().sum())/base_count,
                        'origins_with_20_return_history_and_target':int((target.notna()&backward_rv(returns).notna()).to_numpy().sum())})
    details=[]
    for stock,group in raw.groupby('Name'):
        span=sessions[(sessions>=group.date.min())&(sessions<=group.date.max())]
        missing=span.difference(pd.DatetimeIndex(group.date))
        details.append({'stock':stock,'first':str(group.date.min().date()),'last':str(group.date.max().date()),
                        'observations':len(group),'interior_missing_dates':missing.strftime('%Y-%m-%d').tolist()})
    ledger=[]
    event_map={(e['stock'],e['date']):e for e in evidence['events']}
    base_bad=bad|bad.shift(1,fill_value=False)
    copied=repeated|repeated.shift(1,fill_value=False)
    for date,stock in extreme.stack()[lambda s:s].index:
        key=(stock,str(date.date()));event=event_map.get(key)
        status=event['category'] if event else ('unresolved_price_contradiction' if base_bad.loc[date,stock]
                                               else 'unresolved_repeated_price' if copied.loc[date,stock]
                                               else 'unresolved_extreme_move')
        prior=sessions[sessions.get_loc(date)-1]
        ledger.append({'stock':stock,'date':str(date.date()),'previous_close':float(close.loc[prior,stock]),
                       'close':float(close.loc[date,stock]),'simple_return':float(np.expm1(baseline.loc[date,stock])),
                       'status':status,'evidence_id':event['id'] if event else None,
                       'source_urls':event['sources'] if event else [],
                       'note':event['note'] if event else 'Unresolved: magnitude alone is not an error diagnosis'})
    groups,pairs=repeated_groups(raw)
    # Split-ratio screens are only flags, not split detections or proposed adjustments.
    factors=np.array([.1,.2,.25,1/3,.5,2/3,.75,.8,1.25,4/3,1.5,2,3,4,5,10])
    ratio=close/close.shift(1);distance=pd.DataFrame(np.inf,index=sessions,columns=columns)
    nearest=pd.DataFrame(np.nan,index=sessions,columns=columns)
    for factor in factors:
        delta=(ratio/factor-1).abs();better=delta<distance
        nearest=nearest.mask(better,factor);distance=distance.mask(better,delta)
    split_like=(distance<=.01)&(np.expm1(baseline).abs()>=.15)
    candidates=[{'stock':s,'date':str(t.date()),'price_ratio':float(ratio.loc[t,s]),
                 'nearest_simple_factor':float(nearest.loc[t,s]),'diagnosis':'unresolved_screen_not_verified_split'}
                for t,s in split_like.stack()[lambda x:x].index]
    stats={'status':'investigation_only_cleaning_not_approved','models_trained':False,'prices_corrected':0,
           'source_sha256':raw_hash,'evidence_sha256':sha256(evidence_path),'rows':len(raw),'stocks':len(columns),
           'sessions':len(sessions),'first_date':str(sessions[0].date()),'last_date':str(sessions[-1].date()),
           'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__,
           'audit_code_sha256':sha256(__file__),'target_code_sha256':sha256(Path(__file__).with_name('targets.py')),
           'calendar_package':xc.__version__,'calendar':'XNYS','python':platform.python_version(),
           'missing_whole_panel_sessions':sessions.difference(observed).strftime('%Y-%m-%d').tolist(),
           'missing_values':raw.isna().sum().to_dict(),'flags':{c:int(flags[c].sum()) for c in flags.columns if c not in ['Name','date']},
           'interior_missing_stock_sessions':sum(len(r['interior_missing_dates']) for r in details),
           'repeated_OHLC_groups':len(groups),'repeated_OHLC_stocks':int(flags.loc[flags.repeated_ohlc,'Name'].nunique()),
           'repeated_OHLCV_stocks':int(flags.loc[flags.repeated_ohlcv,'Name'].nunique()),
           'large_adjacent_session_moves':len(ledger),'large_move_status_counts':dict(Counter(r['status'] for r in ledger)),
           'split_ratio_screen_count':len(candidates),'rule_effects':effects,
           'coverage_min_rows':min(r['observations'] for r in details),
           'coverage_full_session_stocks':sum(r['observations']==len(sessions) for r in details),
           'zero_targets_raw':int(base_target.eq(0).to_numpy().sum()),
           'raw_target_count':base_count,'unsafe_compressed_row_targets_in_excess':None}
    # Compare unsafe row-compressed computation to exact-session labels: count eligible
    # origins whose future would have bridged an absent exchange observation.
    compressed_count=0
    for _,group in raw.groupby('Name'):
        compressed_count+=max(0,len(group)-5)
    stats['unsafe_compressed_row_targets_in_excess']=compressed_count-base_count
    output.mkdir(parents=True)
    (output/'summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    for name,value in [('large_moves',ledger),('coverage',details),('repeated_records',groups),('repeated_date_pairs',pairs),('split_ratio_candidates',candidates)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2)+'\n')
    flags.loc[flags.drop(columns=['Name','date']).any(axis=1)].to_json(output/'row_flags.json',orient='records',date_format='iso',indent=2)
    # Supporting figures show recorded observations and counts only, never inferred fixes.
    plt.rcParams.update({'font.size':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,(stock,start,end) in zip(axes.flat,[('LNT','2016-05-12','2016-05-25'),('VRTX','2013-04-12','2013-04-26'),('DISCA','2014-07-31','2014-08-14'),('MPC','2017-09-11','2017-09-20')]):
        view=raw[(raw.Name==stock)&raw.date.between(start,end)]
        ax.plot(view.date,view.close,marker='o');ax.set_title(f'{stock}: recorded closes (no correction)');ax.tick_params(axis='x',rotation=35);ax.set_ylabel('Recorded price')
    fig.suptitle('Different large moves require different explanations');fig.tight_layout();fig.savefig(output/'case-studies.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5));top=pairs[:8]
    ax.barh([' / '.join(r['dates']) for r in top][::-1],[r['stocks'] for r in top][::-1]);ax.set_xlabel('Stocks with exactly repeated OHLC on these dates');ax.set_title('Shared repeated-record dates can create artificial stock relationships');fig.tight_layout();fig.savefig(output/'repeated-records.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4));ax.barh([r['scenario'] for r in effects][::-1],[r['targets_unavailable_vs_raw'] for r in effects][::-1]);ax.set_xlabel('Five-session targets unavailable versus raw calendar-aligned data');ax.set_title('Policy sensitivity only: no prices changed or models trained');fig.tight_layout();fig.savefig(output/'rule-effects.svg');plt.close(fig)
    return stats


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(investigate(args.csv,args.evidence,args.output),indent=2))


if __name__=='__main__': main()
