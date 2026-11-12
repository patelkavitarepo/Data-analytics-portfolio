"""Independent synthetic mechanism study; true covariance is scoring-only.
SYNTHETIC DATA — NOT EMPIRICAL RESULTS.
"""
VERSION = '006-synthetic-shrinkage-mechanism-v1'
SEEDS = (7101,7102,7103,7104,7105)
RHOS = (0.,.35)
WINDOWS = (63,504)
TRAIN_POOL = 504
SHRINKAGE = .25
CAP = .35
ANNUAL_RF = .02
TIE_TOLERANCE = 1e-12
ORACLE_TOLERANCE = 1e-9

import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import analytics
from . import synthetic as lab
from . import synthetic_shrinkage as prototype
from .synthetic_robustness import concentration

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('sample','diagonal_25')
ORACLE_LABEL = 'THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC'
PREDECLARATION_COMMIT = '90c137c'
PLAN = dict(version=VERSION,seeds=list(SEEDS),rhos=list(RHOS),windows=list(WINDOWS),training_pool=TRAIN_POOL,
    methods=list(METHODS),shrinkage=SHRINKAGE,cap=CAP,annual_rf=ANNUAL_RF,tie_tolerance=TIE_TOLERANCE,
    oracle_tolerance=ORACLE_TOLERANCE,generator='PCG64 SeedSequence(seed).spawn(3)[0], 504x7 paired normals; streams 1/2 unused',
    scope='estimation only; no resampling, futures, paths or costs')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def training_sample(seed,rho,window):
    if seed not in SEEDS or rho not in RHOS or window not in WINDOWS:
        raise ValueError('Outside predeclared seed/rho/window grid')
    rng=np.random.default_rng(np.random.SeedSequence(seed).spawn(3)[0])
    z=rng.standard_normal((TRAIN_POOL,7))
    pool=lab._draw(z,rho,np.ones(6),lab.ANNUAL_VOLS)
    return pd.DataFrame(pool[-window:],columns=lab.ASSETS,index=pd.RangeIndex(window,name='synthetic_step'))


def fit_training(training):
    """Candidate-only interface: no rho, true covariance, oracle or future accepted."""
    if tuple(training.columns)!=lab.ASSETS or len(training) not in WINDOWS or not training.index.equals(pd.RangeIndex(len(training),name='synthetic_step')):
        raise ValueError('Only predeclared ordinal 63/504-row training permitted')
    if not np.isfinite(training.to_numpy()).all() or (training<=-1).any(axis=None):
        raise ValueError('Finite simple training returns > -1 required')
    mu,s=analytics.moments(training)
    fits={}
    for method in METHODS:
        covariance=prototype.estimate_covariance(s,method)
        try:
            fits[method]=prototype.fit(mu,s,method)
        except (ValueError,np.linalg.LinAlgError) as exc:
            fits[method]=dict(covariance=covariance,weights={},diagnostics={strategy:dict(success=False,
                checked_violation=np.nan,solver=None,error=str(exc)) for strategy in lab.STRATEGIES})
    return dict(training_sha256=lab.training_hash(training),mean=np.asarray(mu),sample_covariance=np.asarray(s),fits=fits)


def error_components(estimated,true):
    estimated,true=np.asarray(estimated,float),np.asarray(true,float)
    analytics.validate_problem(np.zeros(6),estimated,CAP)
    analytics.validate_problem(np.zeros(6),true,CAP)
    error=estimated-true
    diagonal=float(np.square(np.diag(error)).sum())
    offdiag=float(np.square(error[~np.eye(6,dtype=bool)]).sum())
    total=float(np.square(error).sum())
    return dict(total_squared_error=total,diagonal_squared_error=diagonal,offdiagonal_squared_error=offdiag,
        relative_squared_error=total/float(np.square(true).sum()),minimum_eigenvalue=float(np.linalg.eigvalsh(estimated).min()),
        condition_number=float(np.linalg.cond(estimated)))


def mechanism_terms(sample,true):
    s,c=np.asarray(sample,float),np.asarray(true,float)
    mask=~np.eye(6,dtype=bool);e=(s-c)[mask];truth=c[mask]
    terms=dict(sample_error_term=float(-.4375*(e@e)),target_term=float(.0625*(truth@truth)),
        interaction_term=float(-.375*(e@truth)))
    terms['decomposition_sum']=sum(terms.values())
    return terms


def solve_oracle(true):
    """Scoring baseline only: original checked convex min-vol solve on known C."""
    solver=None;residual=np.nan
    try:
        candidate=analytics.optimize(np.zeros(6),true,CAP,'min_vol',ANNUAL_RF)
        w=np.asarray(candidate.weights,float);solver=candidate.diagnostics
        if w.shape!=(6,) or not np.isfinite(w).all():raise ValueError('Invalid oracle weights')
        residual=float(max(abs(w.sum()-1),max(0.,-w.min(),w.max()-CAP)))
        variance=float(w@true@w)
        if not solver['success'] or residual>1e-7 or not np.isfinite(variance):raise ValueError('Rejected oracle solver/constraints')
        return dict(weights=w,variance=variance,diagnostics=dict(success=True,checked_violation=residual,solver=solver))
    except (ValueError,np.linalg.LinAlgError) as exc:
        return dict(weights=None,variance=np.nan,diagnostics=dict(success=False,checked_violation=residual,solver=solver,error=str(exc)))


def score_case(trained,true,oracle):
    """Pure scoring: known truth/oracle cannot feed back into fitted portfolios."""
    covariance_rows,portfolio_rows=[],[]
    for method in METHODS:
        fit=trained['fits'][method];cov=fit['covariance']
        covariance_rows.append(dict(method=method,**error_components(cov,true)))
        for strategy in lab.STRATEGIES:
            diag=fit['diagnostics'][strategy]
            row=dict(method=method,strategy=strategy,**prototype.diagnostic_fields(diag),
                **{key:np.nan for key in ('HHI','effective_number','max_weight','cap_count','any_cap_binding',
                   'estimated_variance','true_variance','oracle_variance','raw_oracle_regret','relative_oracle_regret',*lab.ASSETS)},
                oracle_regret_applicable=strategy=='min_vol',oracle_regret_valid=None)
            w=fit['weights'].get(strategy)
            if w is not None:
                row.update(concentration(w));row.update(dict(zip(lab.ASSETS,w)))
                row.update(estimated_variance=float(w@cov@w),true_variance=float(w@true@w))
                if strategy=='min_vol' and oracle['diagnostics']['success']:
                    gap=row['true_variance']-oracle['variance']
                    row.update(oracle_variance=oracle['variance'],raw_oracle_regret=gap,
                        relative_oracle_regret=gap/oracle['variance'],oracle_regret_valid=bool(gap>=-ORACLE_TOLERANCE))
            portfolio_rows.append(row)
    return dict(covariances=pd.DataFrame(covariance_rows),portfolios=pd.DataFrame(portfolio_rows),
        decomposition=mechanism_terms(trained['sample_covariance'],true))


def summarize(frame,groups,metrics):
    rows=[]
    for key,group in frame.groupby(groups,sort=True):
        if group.seed.duplicated().any():raise ValueError('One record per seed; do not pool paired cases')
        for metric in metrics:
            x=group[metric].dropna()
            rows.append(dict(zip(groups,key),metric=metric,planned_seeds=5,recorded_seeds=len(group),valid_seeds=len(x),
                median=x.median(),minimum=x.min(),maximum=x.max()))
    return pd.DataFrame(rows)


def contrast_summary(frame,groups,metrics):
    result=summarize(frame,groups,metrics)
    for i,row in result.iterrows():
        group=frame
        for key in groups:group=group.loc[group[key]==row[key]]
        x=group[row.metric].dropna()
        result.loc[i,'lower']=int((x < -TIE_TOLERANCE).sum())
        result.loc[i,'higher']=int((x > TIE_TOLERANCE).sum())
        result.loc[i,'numerical_ties']=int((x.abs()<=TIE_TOLERANCE).sum())
    return result


def preserved_fingerprints():
    registry_path=ROOT/'research/model-evolution/registry-v1.json'
    files=json.loads(registry_path.read_text())['preserved_artifacts'].copy()
    for path in ('MODEL_EVOLUTION_PLAN.md','research/model-evolution/registry-v1.json',
        'research/model-evolution/decision-template.json','markowitz/synthetic_shrinkage.py',
        'SYNTHETIC_SHRINKAGE_PLAN.md','SYNTHETIC_SHRINKAGE_FINDINGS.md','synthetic-shrinkage-results.json',
        'scripts/check_shrinkage_report.py'):
        files[path]=digest((ROOT/path).read_bytes())
    for path,expected in files.items():
        if digest((ROOT/path).read_bytes())!=expected:raise ValueError('Historical artifact changed: '+path)
    return files


def run_grid():
    fingerprints=preserved_fingerprints()
    # Complete ALL candidate fitting before creating true scoring/oracle objects.
    trained=[dict(seed=seed,rho=rho,window=window,**fit_training(training_sample(seed,rho,window)))
        for seed in SEEDS for rho in RHOS for window in WINDOWS]
    truths={rho:lab.covariance(rho,np.ones(6),lab.ANNUAL_VOLS) for rho in RHOS}
    oracles={rho:solve_oracle(truths[rho]) for rho in RHOS}
    scored=[score_case(case,truths[case['rho']],oracles[case['rho']]) for case in trained]
    tables={}
    for key in ('covariances','portfolios'):
        frames=[]
        for case,score in zip(trained,scored):
            frame=score[key].copy()
            for field in ('seed','rho','window'):frame.insert(0,field,case[field])
            frames.append(frame)
        tables[key]=pd.concat(frames,ignore_index=True)
    covariance_metrics=['total_squared_error','diagonal_squared_error','offdiagonal_squared_error','relative_squared_error','condition_number']
    portfolio_metrics=['HHI','true_variance','raw_oracle_regret']
    tables['paired_covariances']=prototype.pair_methods(tables['covariances'],['seed','rho','window'],covariance_metrics)
    tables['paired_portfolios']=prototype.pair_methods(tables['portfolios'],['seed','rho','window','strategy'],portfolio_metrics)
    decompositions=[]
    for case,score in zip(trained,scored):
        decompositions.append(dict(seed=case['seed'],rho=case['rho'],window=case['window'],**score['decomposition']))
    tables['decomposition']=pd.DataFrame(decompositions)
    tables['oracles']=pd.DataFrame([dict(rho=rho,comparator=ORACLE_LABEL,variance=o['variance'],
        **prototype.diagnostic_fields(o['diagnostics']),**{a:(o['weights'][i] if o['weights'] is not None else np.nan) for i,a in enumerate(lab.ASSETS)}) for rho,o in oracles.items()])
    tables['covariance_summaries']=summarize(tables['covariances'],['rho','window','method'],covariance_metrics)
    tables['covariance_contrasts']=contrast_summary(tables['paired_covariances'],['rho','window'],['delta_'+m for m in covariance_metrics])
    tables['portfolio_summaries']=summarize(tables['portfolios'],['rho','window','method','strategy'],['HHI','true_variance'])
    tables['portfolio_contrasts']=contrast_summary(tables['paired_portfolios'],['rho','window','strategy'],['delta_HHI','delta_true_variance'])
    minvol=tables['portfolios'].query("strategy=='min_vol'")
    valid_minvol=minvol.copy()
    for field in ('raw_oracle_regret','relative_oracle_regret'):
        valid_minvol[field]=valid_minvol[field].where(valid_minvol.oracle_regret_valid.eq(True))
    paired_minvol=prototype.pair_methods(valid_minvol,['seed','rho','window','strategy'],['raw_oracle_regret'])
    tables['regret_summaries']=summarize(valid_minvol,['rho','window','method'],['raw_oracle_regret','relative_oracle_regret'])
    tables['regret_contrasts']=contrast_summary(paired_minvol,['rho','window'],['delta_raw_oracle_regret'])
    rows=tables['portfolios'];oracle_rows=tables['oracles']
    counts=dict(training_cases=len(trained),covariance_rows=len(tables['covariances']),candidate_rows=len(rows),candidate_failures=int((~rows.success).sum()),
        oracle_solves=len(oracles),oracle_failures=int((~oracle_rows.success).sum()),
        known_failed_candidate_starts=int(rows.failed_solver_starts.sum()),unknown_candidate_start_counts=int(rows.failed_solver_starts.isna().sum()),
        known_failed_oracle_starts=int(oracle_rows.failed_solver_starts.sum()),unknown_oracle_start_counts=int(oracle_rows.failed_solver_starts.isna().sum()),
        invalid_oracle_regret_rows=int((minvol.oracle_regret_valid==False).sum()),
        valid_oracle_regret_rows=int(minvol.oracle_regret_valid.eq(True).sum()),missing_oracle_regret_rows=int(minvol.oracle_regret_valid.isna().sum()),
        max_checked_candidate_violation=float(rows.checked_violation.max()),max_checked_oracle_violation=float(oracle_rows.checked_violation.max()))
    return dict(manifest=dict(warning=lab.WARNING,classification='exploratory synthetic mechanism study; not independent confirmation or empirical candidate',
        plan=PLAN,predeclaration_commit=PREDECLARATION_COMMIT,predeclaration_sha256=digest((ROOT/'SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md').read_bytes()),
        preserved_artifacts=fingerprints,counts=counts,oracle_label=ORACLE_LABEL,
        true_annual_means=lab.ANNUAL_MEANS.tolist(),true_annual_vols=lab.ANNUAL_VOLS.tolist(),
        true_covariances={rho:cov.tolist() for rho,cov in truths.items()},oracle_full_diagnostics={rho:o['diagnostics'] for rho,o in oracles.items()},
        versions={p:version(p) for p in ('numpy','pandas','scipy')},
        cases=[dict(seed=t['seed'],rho=t['rho'],window=t['window'],source_steps=[504-t['window'],503],training_sha256=t['training_sha256'],
            sample_mean=t['mean'].tolist(),sample_covariance=t['sample_covariance'].tolist(),
            estimated_covariances={m:t['fits'][m]['covariance'].tolist() for m in METHODS},
            full_candidate_diagnostics={m:t['fits'][m]['diagnostics'] for m in METHODS}) for t in trained]),tables=tables)


def export_report(result):
    return lab.json_safe(dict(manifest=result['manifest'],tables={k:lab.labeled(v).to_dict(orient='records') for k,v in result['tables'].items()}))


def main():
    import argparse
    parser=argparse.ArgumentParser(description=lab.WARNING+' | fixed shrinkage mechanism study; no future/paths/resampling')
    parser.add_argument('--output',type=Path,default=Path('work/synthetic-shrinkage-mechanism-v1'))
    args=parser.parse_args();result=run_grid();args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'SYNTHETIC_mechanism_report.json').write_text(json.dumps(export_report(result),indent=2,allow_nan=False))
    print(lab.WARNING);print(ORACLE_LABEL);print(json.dumps(result['manifest']['counts'],indent=2))
    print('All cases retained. No empirical registry, market data, future paths or holdout evaluation.')


if __name__=='__main__':
    main()
