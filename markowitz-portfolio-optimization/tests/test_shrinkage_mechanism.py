"""Synthetic-only mechanism checks; no provider input or research CLI execution."""
import hashlib
import inspect
import json
import pickle
import socket

import numpy as np
import pandas as pd
import pytest

from markowitz import analytics
from markowitz import synthetic as lab
from markowitz import synthetic_shrinkage_mechanism as study


def fake_fit(mu, sample, method):
    covariance=study.prototype.estimate_covariance(sample,method)
    return dict(covariance=covariance,weights={k:np.full(6,1/6) for k in lab.STRATEGIES},
        diagnostics={k:dict(success=True,checked_violation=0.,solver=dict(success=True,attempts=[])) for k in lab.STRATEGIES})


def test_fixed_grid_nested_windows_and_paired_innovations():
    assert study.SEEDS==(7101,7102,7103,7104,7105)
    assert study.RHOS==(0.,.35) and study.WINDOWS==(63,504) and study.SHRINKAGE==.25
    z=np.random.default_rng(np.random.SeedSequence(7101).spawn(3)[0]).standard_normal((504,7))
    for rho in study.RHOS:
        short=study.training_sample(7101,rho,63)
        long=study.training_sample(7101,rho,504)
        np.testing.assert_array_equal(short,long.iloc[-63:])
        np.testing.assert_array_equal(long,lab._draw(z,rho,np.ones(6),lab.ANNUAL_VOLS))
        pd.testing.assert_frame_equal(short,study.training_sample(7101,rho,63))
        assert short.index.equals(pd.RangeIndex(63,name='synthetic_step'))
    expected=lab.ANNUAL_MEANS/252+z[:,1:]*lab.ANNUAL_VOLS/np.sqrt(252)
    np.testing.assert_array_equal(study.training_sample(7101,0.,504),expected)
    zero=lab.covariance(0.)
    np.testing.assert_array_equal(zero,np.diag(lab.ANNUAL_VOLS**2))
    assert np.linalg.eigvalsh(zero).min()>0
    with pytest.raises(ValueError):study.training_sample(7100,0.,63)
    with pytest.raises(ValueError):study.training_sample(7101,.5,63)
    with pytest.raises(ValueError):study.training_sample(7101,0.,126)


def test_new_short_window_does_not_relax_original_training_validator(monkeypatch):
    sample=study.training_sample(7101,0.,63)
    with pytest.raises(ValueError):lab._validate_training(sample)
    monkeypatch.setattr(study.prototype,'fit',fake_fit)
    study.fit_training(sample)
    for invalid in (sample.set_axis(pd.RangeIndex(1,64,name='synthetic_step')), sample.set_axis(pd.date_range('2000-01-01',periods=63)), pd.concat([sample,sample.iloc[:1]],ignore_index=True)):
        with pytest.raises(ValueError):study.fit_training(invalid)
    bad=sample.copy();bad.iloc[0,0]=-1.
    with pytest.raises(ValueError):study.fit_training(bad)


def test_diagonal_offdiagonal_total_and_mechanism_decomposition():
    for rho in study.RHOS:
        true=lab.covariance(rho)
        sample=lab.covariance(.2)+np.diag(np.arange(1,7)*.0001)
        shrink=study.prototype.estimate_covariance(sample,'diagonal_25')
        a=study.error_components(sample,true);b=study.error_components(shrink,true)
        for estimate,row in ((sample,a),(shrink,b)):
            assert row['total_squared_error']==pytest.approx(row['diagonal_squared_error']+row['offdiagonal_squared_error'],abs=1e-17)
            assert row['total_squared_error']==pytest.approx(np.linalg.norm(estimate-true,'fro')**2,abs=1e-17)
            assert row['relative_squared_error']==pytest.approx(row['total_squared_error']/np.square(true).sum())
        assert b['diagonal_squared_error']==a['diagonal_squared_error']
        observed=b['offdiagonal_squared_error']-a['offdiagonal_squared_error']
        terms=study.mechanism_terms(sample,true)
        assert terms['decomposition_sum']==pytest.approx(observed,abs=1e-17)
        mask=~np.eye(6,dtype=bool)
        identity=-.4375*np.square(sample[mask]).sum()+.5*(sample[mask]*true[mask]).sum()
        assert observed==pytest.approx(identity,abs=1e-17)
        if rho==0.:
            assert b['offdiagonal_squared_error']==pytest.approx(.5625*a['offdiagonal_squared_error'],abs=1e-17)
            assert b['total_squared_error']<=a['total_squared_error']
            assert terms['target_term']==terms['interaction_term']==0.
    with pytest.raises(ValueError):study.error_components(-np.eye(6),np.eye(6))


def test_training_means_pairing_and_oracle_truth_isolation(monkeypatch):
    sample=study.training_sample(7101,.35,63)
    captured=[]
    def forbidden(*args,**kwargs):raise AssertionError('No oracle/truth/future/network in fitting')
    def capture(mu,cov,method):
        captured.append((method,np.asarray(mu).copy(),np.asarray(cov).copy()))
        return fake_fit(mu,cov,method)
    with monkeypatch.context() as m:
        m.setattr(study,'solve_oracle',forbidden)
        m.setattr(lab,'covariance',forbidden)
        m.setattr(lab,'construct',forbidden)
        m.setattr(study.prototype,'fit',capture)
        m.setattr(socket,'create_connection',forbidden)
        trained=study.fit_training(sample)
    assert list(inspect.signature(study.fit_training).parameters)==['training']
    assert len(captured)==2 and [x[0] for x in captured]==list(study.METHODS)
    np.testing.assert_array_equal(captured[0][1],captured[1][1])
    np.testing.assert_array_equal(captured[0][2],captured[1][2])
    before=pickle.dumps(trained)
    true=lab.covariance(.35)
    oracle=dict(variance=.001,diagnostics=dict(success=True))
    monkeypatch.setattr(study.prototype,'fit',forbidden)
    a=study.score_case(trained,true,oracle)
    b=study.score_case(trained,lab.covariance(0.),dict(oracle,variance=.002))
    assert pickle.dumps(trained)==before
    assert not a['covariances'].equals(b['covariances'])
    assert not a['portfolios'].true_variance.equals(b['portfolios'].true_variance)
    for asset in lab.ASSETS:
        pd.testing.assert_series_equal(a['portfolios'][asset],b['portfolios'][asset])


def test_raw_oracle_regret_tolerance_and_failed_oracle_missingness(monkeypatch):
    monkeypatch.setattr(study.prototype,'fit',fake_fit)
    trained=study.fit_training(study.training_sample(7101,.35,63))
    true=lab.covariance(.35);w=np.full(6,1/6);variance=float(w@true@w)
    within=study.score_case(trained,true,dict(variance=variance+.5*study.ORACLE_TOLERANCE,diagnostics=dict(success=True)))['portfolios']
    minvol=within.query("strategy=='min_vol'")
    assert minvol.oracle_regret_valid.eq(True).all() and (minvol.raw_oracle_regret<0).all()
    assert minvol.raw_oracle_regret.min()==pytest.approx(-.5*study.ORACLE_TOLERANCE,abs=1e-17)
    beyond=study.score_case(trained,true,dict(variance=variance+2*study.ORACLE_TOLERANCE,diagnostics=dict(success=True)))['portfolios']
    assert beyond.query("strategy=='min_vol'").oracle_regret_valid.eq(False).all()
    assert (beyond.query("strategy=='min_vol'").raw_oracle_regret<0).all()
    failed=study.score_case(trained,true,dict(variance=np.nan,diagnostics=dict(success=False)))['portfolios']
    assert failed.raw_oracle_regret.isna().all() and failed.oracle_regret_valid.isna().all()
    other=within.query("strategy!='min_vol'")
    assert not other.oracle_regret_applicable.any() and other.raw_oracle_regret.isna().all()
    assert json.loads(json.dumps(lab.json_safe(dict(gap=np.nan)),allow_nan=False))==dict(gap=None)


@pytest.mark.parametrize('mode',['cap','nan','false_success','raise'])
def test_rejected_oracle_candidates_and_failure_diagnostics(monkeypatch,mode):
    def rejected(*args,**kwargs):
        if mode=='raise':raise ValueError('injected oracle failure')
        w=np.array([.4,.12,.12,.12,.12,.12]) if mode=='cap' else np.full(6,1/6)
        if mode=='nan':w[0]=np.nan
        return analytics.Candidate(w,dict(success=mode!='false_success',attempts=[dict(success=False)]))
    monkeypatch.setattr(analytics,'optimize',rejected)
    oracle=study.solve_oracle(lab.covariance(0.))
    assert oracle['weights'] is None and not oracle['diagnostics']['success'] and np.isnan(oracle['variance'])
    assert oracle['diagnostics']['error']
    if mode=='raise':assert study.prototype.diagnostic_fields(oracle['diagnostics'])['failed_solver_starts'] is None


@pytest.mark.parametrize('mode',['cap','nan','false_success','raise'])
def test_rejected_fitted_candidates_do_not_become_zero_risk(monkeypatch,mode):
    def rejected(*args,**kwargs):
        if mode=='raise':raise ValueError('injected candidate failure')
        w=np.array([.4,.12,.12,.12,.12,.12]) if mode=='cap' else np.full(6,1/6)
        if mode=='nan':w[0]=np.nan
        return analytics.Candidate(w,dict(success=mode!='false_success',attempts=[dict(success=False)]))
    monkeypatch.setattr(analytics,'optimize',rejected)
    trained=study.fit_training(study.training_sample(7101,0.,63))
    for fit in trained['fits'].values():
        assert list(fit['weights'])==['equal_weight']
    score=study.score_case(trained,lab.covariance(0.),dict(variance=.001,diagnostics=dict(success=True)))
    rejected_rows=score['portfolios'].query("strategy!='equal_weight'")
    assert not rejected_rows.success.any() and rejected_rows.true_variance.isna().all()
    assert rejected_rows.raw_oracle_regret.isna().all()


def test_descriptive_denominators_and_duplicate_seed_pooling():
    f=pd.DataFrame(dict(seed=[7101,7102,7103],rho=[0.]*3,delta=[-1.,2.,np.nan]))
    row=study.contrast_summary(f,['rho'],['delta']).iloc[0]
    assert row.planned_seeds==5 and row.recorded_seeds==3 and row.valid_seeds==2
    assert row.lower==1 and row.higher==1 and row.numerical_ties==0 and row['median']==.5
    with pytest.raises(ValueError):study.summarize(pd.concat([f,f]),['rho'],['delta'])


def test_committed_report_oracle_regret_labels_and_preserved_history(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Audit reads committed evidence only')
    monkeypatch.setattr(study,'fit_training',forbidden);monkeypatch.setattr(study,'solve_oracle',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)
    report=json.loads((study.ROOT/'synthetic-shrinkage-mechanism-results.json').read_text())
    assert report['manifest']['plan']==study.PLAN
    assert report['manifest']['predeclaration_commit']==study.PREDECLARATION_COMMIT
    assert report['manifest']['predeclaration_sha256']==study.digest((study.ROOT/'SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md').read_bytes())
    t=report['tables'];assert len(report['manifest']['cases'])==20 and len(t['portfolios'])==120 and len(t['covariances'])==40
    assert len(t['oracles'])==2 and {r['comparator'] for r in t['oracles']}=={study.ORACLE_LABEL}
    assert all(row['Evidence']==lab.WARNING for rows in t.values() for row in rows)
    for path,expected in report['manifest']['preserved_artifacts'].items():
        assert hashlib.sha256((study.ROOT/path).read_bytes()).hexdigest()==expected
    registry=json.loads((study.ROOT/'research/model-evolution/registry-v1.json').read_text())
    assert registry['decisions']==[] and registry['consumption_events']==[]
    truths={float(k):np.array(v) for k,v in report['manifest']['true_covariances'].items()}
    oracles={r['rho']:r for r in t['oracles']}
    for rho,oracle in oracles.items():
        assert oracle['success']
        w=np.array([oracle[a] for a in lab.ASSETS])
        assert w.sum()==pytest.approx(1.,abs=1e-7) and w.min()>=-1e-7 and w.max()<=.35+1e-7
        assert oracle['variance']==pytest.approx(w@truths[rho]@w,abs=1e-15)
    for row in t['portfolios']:
        if not row['success']:continue
        w=np.array([row[a] for a in lab.ASSETS]);true=truths[row['rho']]
        assert row['true_variance']==pytest.approx(w@true@w,abs=1e-15)
        if row['strategy']=='min_vol':
            gap=row['true_variance']-oracles[row['rho']]['variance']
            assert row['raw_oracle_regret']==pytest.approx(gap,abs=1e-15)
            assert gap>=-study.ORACLE_TOLERANCE and row['oracle_regret_valid']
        else:assert row['raw_oracle_regret'] is None and not row['oracle_regret_applicable']
    for row in t['paired_covariances']:
        assert row['delta_diagonal_squared_error']==0
        assert row['delta_total_squared_error']==pytest.approx(row['delta_offdiagonal_squared_error'],abs=1e-15)
        if row['rho']==0.:
            assert row['shrink_offdiagonal_squared_error']==pytest.approx(.5625*row['sample_offdiagonal_squared_error'],abs=1e-15)


def test_zero_rho_oracle_matches_independent_capped_inverse_variance_solution():
    # Analytic verification of the already predeclared oracle, not an extra strategy.
    report=json.loads((study.ROOT/'synthetic-shrinkage-mechanism-results.json').read_text())
    oracle=next(r for r in report['tables']['oracles'] if r['rho']==0.)
    variances=lab.ANNUAL_VOLS**2
    expected=np.zeros(6);free=np.arange(6);remaining=1.
    while len(free):
        allocation=remaining*(1/variances[free])/(1/variances[free]).sum()
        hit=allocation>study.CAP
        if not hit.any():
            expected[free]=allocation
            break
        expected[free[hit]]=study.CAP
        remaining-=study.CAP*int(hit.sum())
        free=free[~hit]
    actual=np.array([oracle[a] for a in lab.ASSETS])
    np.testing.assert_allclose(actual,expected,atol=2e-5,rtol=0)
    assert oracle['variance']==pytest.approx(float((expected**2*variances).sum()),abs=1e-10)


def test_markdown_numerical_audit_is_offline():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,str(study.ROOT/'scripts/check_mechanism_report.py')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'no model execution or data access' in result.stdout
