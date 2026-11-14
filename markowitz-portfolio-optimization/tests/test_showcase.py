"""Read-only showcase tests: frozen artifacts, presentation and offline boundaries."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

import showcase_evidence as evidence

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/'synthetic_showcase.py'
spec=importlib.util.spec_from_file_location('showcase_audit',ROOT/'scripts/check_showcase.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture
def reports():
    return evidence.load_reports()


@pytest.fixture
def copied_reports(tmp_path):
    for item in evidence.SPECS.values():
        shutil.copyfile(ROOT/item['file'],tmp_path/item['file'])
    return tmp_path


def exact(rows,**where):
    matches=[row for row in rows if all(row.get(k)==value for k,value in where.items())]
    assert len(matches)==1
    return matches[0]


def all_values(panel):
    return [row['value'] for block in panel['blocks'] for row in block['rows']]


def test_all_five_reports_are_pinned_labeled_and_downloaded_unchanged():
    reports,raw=evidence.load_reports(with_bytes=True)
    assert tuple(reports)==('lab','robustness','serial','shrinkage','mechanism')
    assert tuple(raw)==tuple(reports)
    for key,item in evidence.SPECS.items():
        assert isinstance(raw[key],bytes)
        assert raw[key]==(ROOT/item['file']).read_bytes()
        assert hashlib.sha256(raw[key]).hexdigest()==item['sha256']
        if key=='lab':assert reports[key]['warning']==evidence.WARNING
        else:
            assert reports[key]['manifest']['warning']==evidence.WARNING
            assert all(row['Evidence']==evidence.WARNING for rows in reports[key]['tables'].values() for row in rows)


@pytest.mark.parametrize('study',['lab','mechanism'])
@pytest.mark.parametrize('defect',['missing','corrupt','mislabeled','missing_warning','altered','nonfinite','wrong_shape'])
def test_missing_corrupt_mislabeled_or_altered_reports_fail_visibly(copied_reports,study,defect):
    path=copied_reports/evidence.SPECS[study]['file']
    if defect=='missing':path.unlink()
    elif defect=='corrupt':path.write_text('{broken JSON')
    elif defect=='wrong_shape':path.write_text('[]')
    elif defect=='nonfinite':path.write_text('{"value": NaN}')
    else:
        value=json.loads(path.read_text())
        if study=='lab':
            if defect=='mislabeled':value['scenarios']['baseline']['bootstrap_summary'][0]['Evidence']='EMPIRICAL'
            elif defect=='missing_warning':value.pop('warning')
            else:value['scenarios']['baseline']['bootstrap_summary'][0]['mean_half_L1_reallocation']+=.01
        else:
            if defect=='mislabeled':value['tables']['covariances'][0]['Evidence']='EMPIRICAL'
            elif defect=='missing_warning':value['manifest'].pop('warning')
            else:value['tables']['covariances'][0]['total_squared_error']+=.01
        path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match=evidence.SPECS[study]['file']):
        evidence.load_reports(copied_reports)


def test_selectors_and_finite_number_rules_never_invent_defaults():
    with pytest.raises(ValueError,match='one source row'):evidence.one([],seed=1)
    with pytest.raises(ValueError,match='one source row'):evidence.one([{'seed':1},{'seed':1}],seed=1)
    for invalid in (None,True,float('nan'),float('inf'),'0.1'):
        with pytest.raises(ValueError,match='observed finite'):evidence.number(invalid)
    assert evidence.number(-.1)=='−10.0000%'
    assert evidence.number(.02,'pp')=='+2.0000 pp'


def test_panel_findings_match_exact_source_rows_and_units(reports):
    panels=evidence.build_panels(reports)
    assert list(panels)==list(evidence.SPECS)
    # Each study retains distinct context/units and original source selectors.
    for panel in panels.values():
        assert all(panel[field] for field in ('title','context','finding','blocks','limits','sources'))
        for block in panel['blocks']:
            assert block['unit'] and block['note'] and block['rows']
    base=reports['lab']['scenarios']['baseline']
    source={s:exact(base['bootstrap_summary'],index=s)['mean_half_L1_reallocation'] for s in ('min_vol','max_sharpe','equal_weight')}
    assert all_values(panels['lab'])[:3]==[f'{source[s]*100:.2f}%' for s in ('min_vol','max_sharpe','equal_weight')]
    assert [row['Reassignment'] for row in panels['lab']['chart']]==[source[s]*100 for s in ('min_vol','max_sharpe','equal_weight')]
    assert '20 IID draws' in panels['lab']['context'] and '6006' in panels['lab']['context']
    biased=exact(reports['lab']['scenarios']['mean_estimation_error']['estimated'],index='min_vol')
    original=exact(base['estimated'],index='min_vol')
    assert all_values(panels['lab'])[3:]==[f"{original['estimated_sharpe']:.3f}",f"{biased['estimated_sharpe']:.3f}"]
    ratio=exact(reports['robustness']['tables']['aggregate_risk'],window=504,strategy='min_vol',metric='known_volatility_ratio')
    assert all_values(panels['robustness'])[0]==f"{ratio['median']:.4f}"
    path=exact(reports['robustness']['tables']['paired_paths'],seed=6006,window=504,strategy='min_vol',cost_bps=0.)
    assert all_values(panels['robustness'])[2]==f"{path['stationary_baseline_volatility']*100:.4f}% → {path['unseen_positive_jump_volatility']*100:.4f}%"
    expected=f"{path['stationary_baseline_max_drawdown']*100:.4f}% → {path['unseen_positive_jump_max_drawdown']*100:.4f}%".replace('-','−')
    assert all_values(panels['robustness'])[3]==expected
    for index,phi in enumerate((0.,.5)):
        item=exact(reports['serial']['tables']['aggregate_differences'],phi=phi,strategy='max_sharpe',metric='delta_mean_half_L1')
        assert all_values(panels['serial'])[index]==f"{100*item['median']:+.4f} pp; range {100*item['minimum']:+.4f} pp to {100*item['maximum']:+.4f} pp".replace('-','−')
    assert '15 draws/method' in panels['serial']['context'] and 'blocks of 5' in panels['serial']['context']
    for i,window in enumerate((126,504)):
        item=exact(reports['shrinkage']['tables']['aggregate_covariances'],window=window,metric='delta_relative_training_covariance_error')
        assert all_values(panels['shrinkage'])[i]==f"Worse in {item['unfavorable']}/{item['valid_pairs']} paired seeds; median error difference {item['median']:.6f}"
    ew={m:exact(reports['shrinkage']['tables']['references'],seed=7001,window=126,strategy='equal_weight',method=m) for m in ('sample','diagonal_25')}
    assert all_values(panels['shrinkage'])[2:]==[f"{ew['sample']['estimated_volatility']*100:.4f}%",f"{ew['diagonal_25']['estimated_volatility']*100:.4f}%",f"{ew['sample']['known_training_volatility']*100:.4f}%"]
    counter=exact(reports['mechanism']['tables']['paired_covariances'],seed=7102,rho=.35,window=504)
    regret=exact(reports['mechanism']['tables']['paired_portfolios'],seed=7102,rho=.35,window=504,strategy='min_vol')
    mechanism_values={row['label']:row['value'] for row in panels['mechanism']['blocks'][1]['rows']}
    assert mechanism_values['Matrix squared loss (squared annual covariance units)']==f"{counter['sample_total_squared_error']:.6e} → {counter['shrink_total_squared_error']:.6e}".replace('-','−')
    assert mechanism_values['Min-vol true-variance regret (annual variance units)']==f"{regret['sample_raw_oracle_regret']:.6e} → {regret['shrink_raw_oracle_regret']:.6e}".replace('-','−')
    assert mechanism_values['Target concentration HHI (unitless)']==f"{regret['sample_HHI']:.6f} → {regret['shrink_HHI']:.6f}"
    assert evidence.ORACLE in panels['mechanism']['limits']
    assert 'no resampling or future paths' in panels['mechanism']['context']
    assert 'annual variance units' in panels['mechanism']['blocks'][1]['rows'][1]['label']


def test_missing_selected_value_is_not_silently_replaced(reports):
    bad=copy.deepcopy(reports)
    row=exact(bad['lab']['scenarios']['baseline']['bootstrap_summary'],index='max_sharpe')
    row['mean_half_L1_reallocation']=None
    with pytest.raises(ValueError,match='observed finite'):evidence.build_panels(bad)


def test_all_six_views_are_readonly_offline_labeled_and_download_original_bytes(monkeypatch):
    import streamlit as st
    def forbidden(*args,**kwargs):raise AssertionError('No network or model execution is permitted')
    monkeypatch.setattr(socket,'create_connection',forbidden)
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    downloads=[]
    original_download=st.download_button
    def capture(label,data,*args,**kwargs):
        downloads.append((label,data))
        return original_download(label,data,*args,**kwargs)
    monkeypatch.setattr(st,'download_button',capture)
    at=AppTest.from_file(str(ENTRY),default_timeout=40).run()
    assert not at.exception
    choices=['Start here',*[item['title'] for item in evidence.SPECS.values()]]
    assert at.radio[0].options==choices
    for choice in choices:
        if choice!='Start here':at.radio[0].set_value(choice).run()
        assert not at.exception
        assert any(evidence.WARNING in item.value for item in at.error)
        assert any('eight-ETF historical question is unanswered' in item.value and '2025+' in item.value for item in at.info)
        assert not at.number_input and not at.slider and not at.text_input and not at.checkbox
        assert {button.label for button in at.button} <= {'Open '+item['title'] for item in evidence.SPECS.values()}
        assert not at.get('file_uploader') and not at.get('form') and not at.get('page_link')
        for chart in at.get('plotly_chart'):
            spec=json.loads(chart.proto.spec)
            assert evidence.WARNING in spec['layout']['title']['text']
            assert 'reassignment' in spec['layout']['xaxis']['title']['text'].lower()
            x=spec['data'][0]['x']
            if isinstance(x,dict):x=np.frombuffer(base64.b64decode(x['bdata']),dtype=x['dtype']).tolist()
            reports=evidence.load_reports()
            expected=[100*exact(reports['lab']['scenarios']['baseline']['bootstrap_summary'],index=s)['mean_half_L1_reallocation'] for s in ('min_vol','max_sharpe','equal_weight')]
            assert list(x)==expected
    assert len(downloads)==5
    for (label,data),(key,item) in zip(downloads,evidence.SPECS.items()):
        assert evidence.WARNING in label
        assert data==(ROOT/item['file']).read_bytes()


@pytest.mark.parametrize('message',['Committed report missing','Committed report corrupt'])
def test_invalid_evidence_page_fails_visibly_without_fallback(monkeypatch,message):
    def missing(*args,**kwargs):raise ValueError(message)
    def forbidden(*args,**kwargs):raise AssertionError('No panel defaults after load failure')
    monkeypatch.setattr(evidence,'load_reports',missing)
    monkeypatch.setattr(evidence,'build_panels',forbidden)
    at=AppTest.from_file(str(ENTRY),default_timeout=30).run()
    assert not at.exception
    assert any('Evidence unavailable or invalid' in item.value and message in item.value for item in at.error)
    assert not at.radio and not at.get('plotly_chart') and not at.get('download_button')
    assert any('No placeholder figures' in item.value for item in at.markdown)


def test_source_audit_allows_only_two_bounded_readonly_files():
    assert audit.audit_sources()==2
    result=subprocess.run([sys.executable,str(ROOT/'scripts/check_showcase.py')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert '5 pinned/labeled JSON reports' in result.stdout and '5 panels' in result.stdout
    assert 'No model execution or network access' in result.stdout


@pytest.mark.parametrize('unsafe',[
    '\nimport requests\n',
    '\nfrom markowitz.analytics import optimize\n',
    '\nfit()\n',
    '\nPath("x").write_text("bad")\n',
    '\nst.file_uploader("prices")\n',
    '\nst.switch_page("app.py")\n',
    '\nst.Page("app.py")\n',
])
def test_source_audit_rejects_model_network_writes_and_other_navigation(tmp_path,unsafe):
    for name in audit.ALLOWED_IMPORTS:shutil.copyfile(ROOT/name,tmp_path/name)
    path=tmp_path/'synthetic_showcase.py'
    path.write_text(path.read_text()+unsafe)
    with pytest.raises(ValueError):audit.audit_sources(tmp_path)


def test_overview_ctas_change_only_the_navigation():
    at=AppTest.from_file(str(ENTRY),default_timeout=40).run()
    assert not at.exception
    assert {b.label for b in at.button}=={'Open '+item['title'] for item in evidence.SPECS.values()}
    for item in evidence.SPECS.values():
        at.radio[0].set_value('Start here').run()
        button=next(b for b in at.button if b.label=='Open '+item['title'])
        button.click().run()
        assert not at.exception and at.radio[0].value==item['title']
        assert not at.number_input and not at.slider and not at.get('file_uploader')


def test_shared_constraint_caption_is_sourced_and_consistent():
    from showcase_evidence import load_reports,shared_context
    reports=load_reports()
    caption=shared_context(reports)
    cfg=reports['lab']['scenarios']['baseline']['config']
    assert f"target cap {cfg['cap']*100:.0f}%" in caption
    assert f"annual RF {cfg['annual_rf']*100:.0f}%" in caption
    assert str(len(reports['mechanism']['manifest']['true_annual_means']))+' abstract assets' in caption
    reports['serial']['manifest']['plan']['cap']=.4
    with pytest.raises(ValueError,match='no longer share'):shared_context(reports)
