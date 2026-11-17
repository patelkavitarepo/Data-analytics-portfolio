"""Independent exploratory synthetic candidate; not an empirical challenger.
SYNTHETIC DATA — NOT EMPIRICAL RESULTS.
"""
VERSION = '006-synthetic-shrinkage-v1'
SEEDS = (7001, 7002, 7003, 7004, 7005)
WINDOWS = (126, 504)
TRAIN_POOL = 504
FUTURE_STEPS = 252
BOOTSTRAP_DRAWS = 15
SHRINKAGE = .25
CAP = .35
ANNUAL_RF = .02
TIE_TOLERANCE = 1e-10

import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import analytics
from . import synthetic as lab
from .synthetic_robustness import concentration

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('sample', 'diagonal_25')
REGIMES = ('stationary', 'unseen_jump')
PREDECLARATION_COMMIT = 'cb6f7ca'
PLAN = dict(version=VERSION, seeds=list(SEEDS), windows=list(WINDOWS), training_pool=TRAIN_POOL,
    future_steps=FUTURE_STEPS, bootstrap_draws=BOOTSTRAP_DRAWS, methods=list(METHODS),
    shrinkage=SHRINKAGE, cap=CAP, annual_rf=ANNUAL_RF, training_correlation=.35,
    future_correlations=dict(stationary=.35, unseen_jump=.85), cost_bps=[0.,10.],
    rebalance_steps=21, tie_tolerance=TIE_TOLERANCE,
    generator='PCG64 SeedSequence(seed).spawn(3): 0=train, 1=future, 2=IID rows; trailing training, paired future innovations')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def training_sample(seed, window):
    if seed not in SEEDS or window not in WINDOWS:
        raise ValueError('Outside predeclared seed/window grid')
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[0])
    z = rng.standard_normal((TRAIN_POOL,7))
    pool = lab._draw(z,.35,np.ones(6),lab.ANNUAL_VOLS)
    return pd.DataFrame(pool[-window:],columns=lab.ASSETS,index=pd.RangeIndex(window,name='synthetic_step'))


def future_paths(seed):
    if seed not in SEEDS:
        raise ValueError('Outside predeclared seeds')
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[1])
    z = rng.standard_normal((FUTURE_STEPS,7))
    return {regime:pd.DataFrame(lab._draw(z,rho,np.ones(6),lab.ANNUAL_VOLS),columns=lab.ASSETS,
        index=pd.RangeIndex(TRAIN_POOL,TRAIN_POOL+FUTURE_STEPS,name='synthetic_step'))
        for regime,rho in PLAN['future_correlations'].items()}


def estimate_covariance(sample_covariance, method):
    s = np.asarray(sample_covariance,float)
    if method not in METHODS or s.shape != (6,6) or not np.isfinite(s).all():
        raise ValueError('Known estimator and finite six-asset covariance required')
    if not np.allclose(s,s.T,rtol=0,atol=1e-10) or np.linalg.eigvalsh(s).min() < -1e-10:
        raise ValueError('Sample covariance must be symmetric PSD')
    return s.copy() if method=='sample' else (1-SHRINKAGE)*s+SHRINKAGE*np.diag(np.diag(s))


def fit(mu, sample_covariance, method):
    """Identical training means and original solver; no true/future inputs."""
    covariance = estimate_covariance(sample_covariance,method)
    mu,covariance = analytics.validate_problem(mu,covariance,CAP)
    weights,diagnostics = {},{}
    for strategy in lab.STRATEGIES:
        solver = None
        violation = np.nan
        try:
            if strategy=='equal_weight':
                w = np.full(6,1/6)
                solver = dict(success=True,attempts=[],method='fixed equal weights')
            else:
                candidate = analytics.optimize(mu,covariance,CAP,strategy,ANNUAL_RF)
                w,solver = np.asarray(candidate.weights,float),candidate.diagnostics
            if w.shape != (6,) or not np.isfinite(w).all():
                raise ValueError('Invalid candidate weights')
            violation = float(max(abs(w.sum()-1),max(0.,-w.min(),w.max()-CAP)))
            stats = analytics.portfolio_stats(w,mu,covariance,ANNUAL_RF)
            if not solver['success'] or violation>1e-7 or not all(np.isfinite(v) for v in stats.values()):
                raise ValueError('Rejected solver/constraint/nonfinite objective candidate')
            weights[strategy] = w.copy()
            diagnostics[strategy] = dict(success=True,checked_violation=violation,solver=solver)
        except (ValueError,np.linalg.LinAlgError) as exc:
            diagnostics[strategy] = dict(success=False,checked_violation=violation,solver=solver,error=str(exc))
    return dict(covariance=covariance,weights=weights,diagnostics=diagnostics)


def diagnostic_fields(diag):
    attempts = (diag.get('solver') or {}).get('attempts',[])
    return dict(success=diag['success'],checked_violation=diag['checked_violation'],error=diag.get('error',''),
        failed_solver_starts=sum(not a['success'] for a in attempts) if diag.get('solver') is not None else None)


def bootstrap_summary(log, fits):
    rows = []
    for method in METHODS:
        for strategy in lab.STRATEGIES:
            group = log.loc[(log.method==method)&(log.strategy==strategy)]
            valid = group.loc[group.success]
            distances = valid.half_L1.dropna()
            row = dict(method=method,strategy=strategy,planned_draws=BOOTSTRAP_DRAWS,recorded_draws=len(group),
                successful_draws=len(valid),failed_draws=len(group)-len(valid),valid_distance_draws=len(distances),
                reference_available=strategy in fits[method]['weights'],mean_half_L1=distances.mean(),
                sd_half_L1=distances.std(ddof=1),p05_half_L1=distances.quantile(.05),
                p50_half_L1=distances.quantile(.5),p95_half_L1=distances.quantile(.95),
                mean_asset_weight_std=valid[list(lab.ASSETS)].std(ddof=1).mean() if len(valid)>1 else np.nan,
                known_failed_solver_starts=group.failed_solver_starts.sum(min_count=1),
                unknown_solver_start_counts=int(group.failed_solver_starts.isna().sum()),
                max_checked_violation=group.checked_violation.max())
            for metric in ('HHI','effective_number','max_weight','cap_count','any_cap_binding'):
                row['bootstrap_mean_'+metric] = valid[metric].mean()
            rows.append(row)
    return pd.DataFrame(rows)


def train_case(seed,window):
    """Finish all fitting/resampling before generating or accepting a future path."""
    training = training_sample(seed,window)
    lab._validate_training(training)
    mu,s = analytics.moments(training)
    fits = {method:fit(mu,s,method) for method in METHODS}
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[2])
    indices = rng.integers(0,window,size=(BOOTSTRAP_DRAWS,window))
    logs,details = [],[]
    for draw,ids in enumerate(indices):
        sample = training.iloc[ids].reset_index(drop=True)
        sample.index.name = 'synthetic_step'
        draw_mu,draw_s = analytics.moments(sample)
        sample_hash = digest(ids.astype('<i8').tobytes())
        for method in METHODS:
            fitted = fit(draw_mu,draw_s,method)
            details.append(dict(draw=draw,method=method,diagnostics=fitted['diagnostics']))
            for strategy in lab.STRATEGIES:
                row = dict(seed=seed,window=window,method=method,strategy=strategy,draw=draw,
                    sample_index_sha256=sample_hash,sample_mean_sha256=digest(np.asarray(draw_mu,dtype='<f8').tobytes()),
                    half_L1=np.nan,**diagnostic_fields(fitted['diagnostics'][strategy]))
                row.update({key:np.nan for key in ('HHI','effective_number','max_weight','cap_count','any_cap_binding',*lab.ASSETS)})
                if row['success']:
                    w = fitted['weights'][strategy]
                    row.update(concentration(w));row.update(dict(zip(lab.ASSETS,w)))
                    if strategy in fits[method]['weights']:
                        row['half_L1'] = .5*float(np.abs(w-fits[method]['weights'][strategy]).sum())
                logs.append(row)
    log = pd.DataFrame(logs)
    summary = bootstrap_summary(log,fits)
    summary.insert(0,'window',window);summary.insert(0,'seed',seed)
    return dict(seed=seed,window=window,mu=np.asarray(mu),sample_covariance=np.asarray(s),fits=fits,
        bootstrap_log=log,bootstrap_summary=summary,bootstrap_details=details,
        training_sha256=lab.training_hash(training),index_stream_sha256=digest(indices.astype('<i8').tobytes()))


def volatility(w,covariance):
    return float(np.sqrt(w@covariance@w))


def evaluate_case(trained,paths):
    """Evaluate frozen targets only; all known covariances remain on this side."""
    if set(paths)!=set(REGIMES):
        raise ValueError('Both paired future regimes required')
    for path in paths.values():
        if tuple(path.columns)!=lab.ASSETS or not path.index.equals(pd.RangeIndex(504,756,name='synthetic_step')) or not np.isfinite(path.to_numpy()).all() or (path<=-1).any(axis=None):
            raise ValueError('Finite disjoint ordinal future required')
    seed,window = trained['seed'],trained['window']
    c_train = lab.covariance(.35,np.ones(6),lab.ANNUAL_VOLS)
    references,covariances,risks,realized = [],[],[],[]
    for method in METHODS:
        fitted = trained['fits'][method];cov = fitted['covariance']
        covariances.append(dict(seed=seed,window=window,method=method,
            relative_training_covariance_error=float(np.linalg.norm(cov-c_train,'fro')/np.linalg.norm(c_train,'fro')),
            relative_jump_misspecification_distance=float(np.linalg.norm(cov-lab.covariance(.85,np.ones(6),lab.ANNUAL_VOLS),'fro')/np.linalg.norm(lab.covariance(.85,np.ones(6),lab.ANNUAL_VOLS),'fro')),
            minimum_eigenvalue=float(np.linalg.eigvalsh(cov).min()),condition_number=float(np.linalg.cond(cov))))
        for strategy in lab.STRATEGIES:
            row = dict(seed=seed,window=window,method=method,strategy=strategy,**diagnostic_fields(fitted['diagnostics'][strategy]))
            row.update({key:np.nan for key in ('HHI','effective_number','max_weight','cap_count','any_cap_binding',
                'estimated_volatility','original_S_volatility','known_training_volatility',*lab.ASSETS)})
            w = fitted['weights'].get(strategy)
            if w is not None:
                row.update(concentration(w));row.update(dict(zip(lab.ASSETS,w)))
                row.update(estimated_volatility=volatility(w,cov),original_S_volatility=volatility(w,trained['sample_covariance']),known_training_volatility=volatility(w,c_train))
            references.append(row)
            for regime in REGIMES:
                true_cov = lab.covariance(PLAN['future_correlations'][regime],np.ones(6),lab.ANNUAL_VOLS)
                known = volatility(w,true_cov) if w is not None else np.nan
                gap = row['estimated_volatility']-known
                risks.append(dict(seed=seed,window=window,method=method,strategy=strategy,regime=regime,available=w is not None,
                    estimated_volatility=row['estimated_volatility'],known_future_volatility=known,
                    signed_estimate_minus_known=gap,absolute_risk_gap=abs(gap)))
                for cost in PLAN['cost_bps']:
                    metrics = {k:np.nan for k in ('volatility','CAGR','max_drawdown','gross_traded_notional')}
                    if w is not None:
                        path = lab.path_returns(paths[regime],w,cost,21)
                        stats = lab.path_metrics(path['return'],ANNUAL_RF)
                        metrics.update({k:stats[k] for k in ('volatility','CAGR','max_drawdown')})
                        metrics['gross_traded_notional'] = float(path.gross_traded_notional.sum())
                    realized.append(dict(seed=seed,window=window,method=method,strategy=strategy,regime=regime,cost_bps=cost,available=w is not None,**metrics))
    return dict(references=pd.DataFrame(references),covariances=pd.DataFrame(covariances),risk=pd.DataFrame(risks),paths=pd.DataFrame(realized))


def pair_methods(frame,keys,metrics):
    a = frame.loc[frame.method=='sample'].set_index(keys)
    b = frame.loc[frame.method=='diagonal_25'].set_index(keys)
    if a.index.has_duplicates or b.index.has_duplicates or not a.index.equals(b.index):
        raise ValueError('One paired record per method/key required')
    out = pd.DataFrame(index=a.index)
    for metric in metrics:
        out['sample_'+metric] = a[metric];out['shrink_'+metric] = b[metric]
        out['delta_'+metric] = b[metric]-a[metric]
    if all(asset in frame for asset in lab.ASSETS):
        distances = np.abs(b[list(lab.ASSETS)]-a[list(lab.ASSETS)])
        out['target_half_L1'] = .5*distances.sum(axis=1,min_count=6)
    return out.reset_index()


def aggregate(frame,groups,metrics):
    rows = []
    for key,group in frame.groupby(groups,sort=True):
        if group.seed.duplicated().any():
            raise ValueError('Do not pool paired methods/regimes/windows as independent seeds')
        for metric,lower_better in metrics.items():
            x = group[metric].dropna()
            improve = (x < -TIE_TOLERANCE) if lower_better else (x > TIE_TOLERANCE)
            worsen = (x > TIE_TOLERANCE) if lower_better else (x < -TIE_TOLERANCE)
            rows.append(dict(zip(groups,key),metric=metric,planned_seeds=5,recorded_seeds=len(group),valid_pairs=len(x),
                median=x.median(),minimum=x.min(),maximum=x.max(),lower_is_favorable=lower_better,
                favorable=int(improve.sum()),unfavorable=int(worsen.sum()),numerical_ties=int((x.abs()<=TIE_TOLERANCE).sum())))
    return pd.DataFrame(rows)


def descriptive(frame,groups,metrics):
    rows = []
    for key,group in frame.groupby(groups,sort=True):
        if group.seed.duplicated().any():
            raise ValueError('Descriptive summaries require one record per seed')
        for metric in metrics:
            x = group[metric].dropna()
            rows.append(dict(zip(groups,key),metric=metric,planned_seeds=5,recorded_seeds=len(group),valid_seeds=len(x),
                median=x.median(),minimum=x.min(),maximum=x.max()))
    return pd.DataFrame(rows)


def run_grid():
    trained = [train_case(seed,window) for seed in SEEDS for window in WINDOWS]
    evaluated = [evaluate_case(t,future_paths(t['seed'])) for t in trained]
    tables = {key:pd.concat([e[key] for e in evaluated],ignore_index=True) for key in ('references','covariances','risk','paths')}
    tables.update(bootstrap_summary=pd.concat([t['bootstrap_summary'] for t in trained],ignore_index=True),
        bootstrap_log=pd.concat([t['bootstrap_log'] for t in trained],ignore_index=True))
    comparisons = dict(covariances=(['seed','window'],['relative_training_covariance_error','relative_jump_misspecification_distance']),
        references=(['seed','window','strategy'],['HHI','effective_number','known_training_volatility','estimated_volatility']),
        risk=(['seed','window','strategy','regime'],['known_future_volatility','signed_estimate_minus_known','absolute_risk_gap']),
        paths=(['seed','window','strategy','regime','cost_bps'],['volatility','CAGR','max_drawdown','gross_traded_notional']),
        bootstrap_summary=(['seed','window','strategy'],['mean_half_L1','p95_half_L1','mean_asset_weight_std','bootstrap_mean_HHI','bootstrap_mean_any_cap_binding']))
    for name,(keys,metrics) in comparisons.items():
        tables['paired_'+name] = pair_methods(tables[name],keys,metrics)
    groups_and_metrics = dict(covariances=(['window'],{'delta_relative_training_covariance_error':True,'delta_relative_jump_misspecification_distance':True}),
        references=(['window','strategy'],{'delta_HHI':True,'delta_known_training_volatility':True}),
        risk=(['window','strategy','regime'],{'delta_known_future_volatility':True,'delta_absolute_risk_gap':True}),
        paths=(['window','strategy','regime','cost_bps'],{'delta_volatility':True,'delta_CAGR':False,'delta_max_drawdown':False}),
        bootstrap_summary=(['window','strategy'],{'delta_mean_half_L1':True,'delta_p95_half_L1':True,'delta_bootstrap_mean_HHI':True}))
    for name,(groups,metrics) in groups_and_metrics.items():
        tables['aggregate_'+name] = aggregate(tables['paired_'+name],groups,metrics)
    for name,(keys,metrics) in comparisons.items():
        tables['methods_'+name] = descriptive(tables[name],[k for k in keys if k!='seed']+['method'],metrics)
    registry = json.loads((ROOT/'research/model-evolution/registry-v1.json').read_text())
    log,refs = tables['bootstrap_log'],tables['references']
    return dict(manifest=dict(warning=lab.WARNING,classification='exploratory synthetic candidate; not an empirical challenger',plan=PLAN,
        predeclaration_commit=PREDECLARATION_COMMIT,predeclaration_sha256=digest((ROOT/'SYNTHETIC_SHRINKAGE_PLAN.md').read_bytes()),
        preserved_artifacts=registry['preserved_artifacts'],preserved_registry_sha256=digest((ROOT/'research/model-evolution/registry-v1.json').read_bytes()),
        preserved_template_sha256=digest((ROOT/'research/model-evolution/decision-template.json').read_bytes()),
        true_annual_means=lab.ANNUAL_MEANS.tolist(),true_annual_vols=lab.ANNUAL_VOLS.tolist(),versions={p:version(p) for p in ('numpy','pandas','scipy')},
        counts=dict(training_cases=len(trained),reference_rows=len(refs),reference_failures=int((~refs.success).sum()),bootstrap_rows=len(log),
            bootstrap_failures=int((~log.success).sum()),reference_known_failed_starts=int(refs.failed_solver_starts.sum()),
            bootstrap_known_failed_starts=int(log.failed_solver_starts.sum()),unknown_reference_start_counts=int(refs.failed_solver_starts.isna().sum()),
            unknown_bootstrap_start_counts=int(log.failed_solver_starts.isna().sum()),maximum_checked_bootstrap_violation=float(log.checked_violation.max())),
        cases=[dict(seed=t['seed'],window=t['window'],source_training_steps=[504-t['window'],503],source_future_steps=[504,755],
            training_sha256=t['training_sha256'],bootstrap_indices_sha256=t['index_stream_sha256'],training_mean=t['mu'].tolist(),
            sample_covariance=t['sample_covariance'].tolist(),estimated_covariances={m:t['fits'][m]['covariance'].tolist() for m in METHODS},
            reference_diagnostics={m:t['fits'][m]['diagnostics'] for m in METHODS},
            future_hashes={name:lab.training_hash(path) for name,path in future_paths(t['seed']).items()}) for t in trained]),
        tables=tables,full_bootstrap_diagnostics=[dict(seed=t['seed'],window=t['window'],details=t['bootstrap_details']) for t in trained])


def export_report(result):
    return lab.json_safe(dict(manifest=result['manifest'],tables={k:lab.labeled(v).to_dict(orient='records') for k,v in result['tables'].items()}))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=lab.WARNING+' | fixed independent shrinkage grid')
    parser.add_argument('--output',type=Path,default=Path('work/synthetic-shrinkage-v1'))
    args = parser.parse_args()
    result = run_grid()
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'SYNTHETIC_shrinkage_report.json').write_text(json.dumps(export_report(result),indent=2,allow_nan=False))
    (args.output/'SYNTHETIC_shrinkage_solver_details.json').write_text(json.dumps(lab.json_safe(dict(warning=lab.WARNING,details=result['full_bootstrap_diagnostics'])),indent=2,allow_nan=False))
    print(lab.WARNING);print(json.dumps(result['manifest']['counts'],indent=2))
    print('All fixed seeds retained. No empirical registry entry, market data or holdout evaluation.')


if __name__=='__main__':
    main()
