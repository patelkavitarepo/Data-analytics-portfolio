"""Deterministic synthetic-only validation; no provider inputs or ETF changes."""
import copy
import hashlib
import json
import pickle
import socket

import numpy as np
import pandas as pd
import pytest

from markowitz import analytics
from markowitz import synthetic as lab
from markowitz import synthetic_shrinkage as study


def test_exact_predeclared_grid_nested_training_and_paired_innovations():
    assert study.SEEDS==(7001,7002,7003,7004,7005) and study.WINDOWS==(126,504)
    assert study.SHRINKAGE==.25 and study.BOOTSTRAP_DRAWS==15
    short=study.training_sample(7001,126);long=study.training_sample(7001,504)
    np.testing.assert_array_equal(short,long.iloc[-126:])
    pd.testing.assert_frame_equal(short,study.training_sample(7001,126))
    paths=study.future_paths(7001)
    pd.testing.assert_frame_equal(paths['stationary'],study.future_paths(7001)['stationary'])
    z=np.random.default_rng(np.random.SeedSequence(7001).spawn(3)[1]).standard_normal((252,7))
    for regime,rho in study.PLAN['future_correlations'].items():
        np.testing.assert_array_equal(paths[regime],lab._draw(z,rho,np.ones(6),lab.ANNUAL_VOLS))
        assert paths[regime].index.equals(pd.RangeIndex(504,756,name='synthetic_step'))
        assert np.linalg.eigvalsh(lab.covariance(rho)).min()>0
    with pytest.raises(ValueError):study.training_sample(7006,126)
    with pytest.raises(ValueError):study.training_sample(7001,252)


def test_shrinkage_math_diagonal_offdiagonal_psd_and_no_mutation():
    _,s=analytics.moments(study.training_sample(7001,126));original=s.copy()
    chosen=study.estimate_covariance(s,'diagonal_25')
    np.testing.assert_array_equal(np.diag(chosen),np.diag(s))
    np.testing.assert_allclose(chosen,.75*s+.25*np.diag(np.diag(s)),rtol=0,atol=0)
    mask=~np.eye(6,dtype=bool)
    np.testing.assert_array_equal(chosen[mask],.75*s.to_numpy()[mask])
    assert np.linalg.eigvalsh(chosen).min()>0
    pd.testing.assert_frame_equal(s,original)
    np.testing.assert_array_equal(study.estimate_covariance(s,'sample'),s)


@pytest.mark.parametrize('invalid',[np.zeros((5,5)),np.full((6,6),np.nan),-np.eye(6),np.triu(np.ones((6,6)))])
def test_invalid_covariance_rejected(invalid):
    with pytest.raises(ValueError):study.estimate_covariance(invalid,'diagonal_25')


def test_sample_prototype_matches_original_solver_and_equal_weight_control():
    data=study.training_sample(7001,126)
    mu,s=analytics.moments(data)
    _,_,original,_=lab.fit(data,np.zeros(6),.35,.02)
    a=study.fit(mu,s,'sample');b=study.fit(mu,s,'diagonal_25')
    for strategy in lab.STRATEGIES:
        np.testing.assert_array_equal(a['weights'][strategy],original[strategy])
    np.testing.assert_array_equal(a['weights']['equal_weight'],b['weights']['equal_weight'])
    w=a['weights']['equal_weight']
    assert study.volatility(w,b['covariance'])<study.volatility(w,a['covariance'])
    with pytest.raises(ValueError):study.fit(mu,np.zeros((6,6)),'sample')


def fake_fit(mu,s,method):
    cov=study.estimate_covariance(s,method)
    weights={k:np.full(6,1/6) for k in lab.STRATEGIES}
    diag={k:dict(success=True,checked_violation=0.,solver=dict(success=True,attempts=[])) for k in lab.STRATEGIES}
    return dict(covariance=cov,weights=weights,diagnostics=diag)


def test_training_isolation_row_and_mean_pairing_future_mutation(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('No future/network access or refitting')
    captured=[]
    def capture(mu,s,method):
        captured.append((method,np.asarray(mu).copy(),np.asarray(s).copy()))
        return fake_fit(mu,s,method)
    with monkeypatch.context() as m:
        m.setattr(socket,'create_connection',forbidden)
        m.setattr(study,'future_paths',forbidden)
        m.setattr(lab,'covariance',forbidden)
        m.setattr(study,'fit',capture)
        trained=study.train_case(7001,126)
    assert len(captured)==32
    for i in range(0,len(captured),2):
        assert [captured[i][0],captured[i+1][0]]==list(study.METHODS)
        np.testing.assert_array_equal(captured[i][1],captured[i+1][1])
        np.testing.assert_array_equal(captured[i][2],captured[i+1][2])
    # Complete-vector IID indices exactly match the predeclared stream.
    data=study.training_sample(7001,126)
    rng=np.random.default_rng(np.random.SeedSequence(7001).spawn(3)[2])
    ids=rng.integers(0,126,size=(15,126))
    for draw in range(15):
        sample=data.iloc[ids[draw]].reset_index(drop=True)
        mu,s=analytics.moments(sample)
        np.testing.assert_array_equal(captured[2+2*draw][1],mu)
        np.testing.assert_array_equal(captured[2+2*draw][2],s)
        group=trained['bootstrap_log'].query('draw==@draw')
        assert group.sample_index_sha256.nunique()==1 and group.sample_mean_sha256.nunique()==1
        assert group.sample_index_sha256.iloc[0]==study.digest(ids[draw].astype('<i8').tobytes())
    before=pickle.dumps(trained)
    paths=study.future_paths(7001)
    monkeypatch.setattr(study,'fit',forbidden)
    a=study.evaluate_case(trained,paths)
    changed={k:v+.0001 for k,v in paths.items()}
    b=study.evaluate_case(trained,changed)
    assert pickle.dumps(trained)==before
    for key in ('references','covariances','risk'):pd.testing.assert_frame_equal(a[key],b[key])
    assert not a['paths'].equals(b['paths'])
    changed['stationary'].index=pd.RangeIndex(252,name='synthetic_step')
    with pytest.raises(ValueError):study.evaluate_case(trained,changed)


@pytest.mark.parametrize('mode',['cap','nan','false_success'])
def test_candidate_false_success_and_cap_failures_retained(monkeypatch,mode):
    mu,s=analytics.moments(study.training_sample(7001,126))
    def invalid(*args,**kwargs):
        w=np.array([.4,.12,.12,.12,.12,.12]) if mode=='cap' else np.full(6,1/6)
        if mode=='nan':w[0]=np.nan
        return analytics.Candidate(w,dict(success=mode!='false_success',attempts=[dict(success=False)]))
    monkeypatch.setattr(analytics,'optimize',invalid)
    result=study.fit(mu,s,'diagonal_25')
    assert list(result['weights'])==['equal_weight']
    assert not result['diagnostics']['min_vol']['success']
    assert study.diagnostic_fields(result['diagnostics']['min_vol'])['failed_solver_starts']==1


def test_bootstrap_failures_missing_reference_and_unknown_starts(monkeypatch):
    count=0
    def fail(mu,s,method):
        nonlocal count
        result=fake_fit(mu,s,method);count+=1
        if count<=2: # Both original max-Sharpe references missing.
            strategy='max_sharpe'
        elif count==3: # One failed sample-covariance min-vol bootstrap candidate.
            strategy='min_vol'
        else:return result
        result['weights'].pop(strategy)
        result['diagnostics'][strategy]=dict(success=False,checked_violation=np.nan,solver=None,error='injected failure')
        return result
    monkeypatch.setattr(study,'fit',fail)
    result=study.train_case(7001,126)
    summary=result['bootstrap_summary'].set_index(['method','strategy'])
    assert summary.loc[('sample','min_vol'),'successful_draws']==14
    assert summary.loc[('sample','min_vol'),'failed_draws']==1
    assert summary.loc[('sample','min_vol'),'unknown_solver_start_counts']==1
    assert summary.loc[('sample','max_sharpe'),'successful_draws']==15
    assert summary.loc[('sample','max_sharpe'),'valid_distance_draws']==0
    assert pd.isna(summary.loc[('sample','max_sharpe'),'mean_half_L1'])
    row=result['bootstrap_log'].query("method=='sample' and strategy=='min_vol' and draw==0").iloc[0]
    assert pd.isna(row.HHI) and pd.isna(row.half_L1)
    evaluated=study.evaluate_case(result,study.future_paths(7001))
    failed=evaluated['references'].query("strategy=='max_sharpe'")
    assert failed.estimated_volatility.isna().all()
    paired=study.pair_methods(failed,['seed','window','strategy'],['HHI'])
    assert paired.target_half_L1.isna().all()
    safe=lab.json_safe(dict(distance=np.nan,starts=None))
    assert json.loads(json.dumps(safe,allow_nan=False))==dict(distance=None,starts=None)


def test_pairing_aggregation_directions_and_no_duplicate_pooling():
    frame=pd.DataFrame(dict(seed=[7001,7002,7003],window=[126]*3,delta=[-.1,.2,np.nan]))
    row=study.aggregate(frame,['window'],{'delta':True}).iloc[0]
    assert row.valid_pairs==2 and row.planned_seeds==5 and row.favorable==1 and row.unfavorable==1
    assert row['median']==pytest.approx(.05)
    with pytest.raises(ValueError):study.aggregate(pd.concat([frame,frame]),['window'],{'delta':True})
    with pytest.raises(ValueError):study.pair_methods(pd.DataFrame(dict(seed=[7001]*4,method=['sample','sample','diagonal_25','diagonal_25'],x=[0]*4)),['seed'],['x'])


def test_committed_evidence_risk_costs_labels_fingerprints_and_registry(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Committed audit must not fit or contact providers')
    monkeypatch.setattr(study,'fit',forbidden);monkeypatch.setattr(socket,'create_connection',forbidden)
    report=json.loads((study.ROOT/'synthetic-shrinkage-results.json').read_text())
    assert report['manifest']['plan']==study.PLAN
    assert all(row['Evidence']==lab.WARNING for rows in report['tables'].values() for row in rows)
    assert len(report['tables']['references'])==60 and len(report['tables']['bootstrap_log'])==900
    assert len(report['manifest']['cases'])==10
    registry=study.ROOT/'research/model-evolution/registry-v1.json'
    assert study.digest(registry.read_bytes())==report['manifest']['preserved_registry_sha256']
    assert json.loads(registry.read_text())['decisions']==[] and json.loads(registry.read_text())['consumption_events']==[]
    for path,value in report['manifest']['preserved_artifacts'].items():
        assert study.digest((study.ROOT/path).read_bytes())==value
    for row in report['tables']['paired_paths']:
        if row['strategy']=='equal_weight':
            assert all(row['delta_'+key]==0 for key in ('volatility','CAGR','max_drawdown','gross_traded_notional'))
    for case in report['manifest']['cases']:
        s=np.array(case['sample_covariance'])
        for method in study.METHODS:
            np.testing.assert_allclose(case['estimated_covariances'][method],study.estimate_covariance(s,method),rtol=0,atol=0)
        matching=[c for c in report['manifest']['cases'] if c['seed']==case['seed']]
        assert matching[0]['future_hashes']==matching[1]['future_hashes']
    # Independently replay cost accounting on one committed fitted target, both methods.
    for method in study.METHODS:
        row=next(r for r in report['tables']['references'] if r['seed']==7001 and r['window']==126 and r['strategy']=='min_vol' and r['method']==method)
        w=np.array([row[k] for k in lab.ASSETS])
        for regime,path in study.future_paths(7001).items():
            c=lab.covariance(study.PLAN['future_correlations'][regime])
            risk=next(r for r in report['tables']['risk'] if r['seed']==7001 and r['window']==126 and r['strategy']=='min_vol' and r['method']==method and r['regime']==regime)
            assert risk['known_future_volatility']==pytest.approx(np.sqrt(w@c@w),abs=1e-14)
            for cost in (0.,10.):
                direct=lab.path_returns(path,w,cost_bps=cost,rebalance_every=21)
                stats=lab.path_metrics(direct['return'],.02)
                actual=next(r for r in report['tables']['paths'] if r['seed']==7001 and r['window']==126 and r['strategy']=='min_vol' and r['method']==method and r['regime']==regime and r['cost_bps']==cost)
                for key in ('CAGR','volatility','max_drawdown'):assert actual[key]==pytest.approx(stats[key],abs=1e-14)
                assert direct.gross_traded_notional.iloc[0]==1


def test_markdown_evidence_audit_offline():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,str(study.ROOT/'scripts/check_shrinkage_report.py')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'no fitting or data access' in result.stdout
