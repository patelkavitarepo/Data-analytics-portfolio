"""Read-only audit of the Decision Quality Framework; no fitting/network/data retrieval.

Pinned bytes anchor this documentation pass to reviewed head b5ba5679. They are
not an empirical registration or an automatic proof of source rights/unseen data.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
WARNING='SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
PINNED = {'CASE_STUDY.md': '0e9a507c3214c199441d4c2fc2789550f12749908d0a351f5e102761814ffe76',
 'README.md': '5a18567c9150d34543a480e6c2d186602b9c1ebe565bd18c17cc81c130864e3b',
 'RESEARCH_SUMMARY.md': 'cb0994cecfa306f9f80fa1b6ec57df51647cb0c5f4f67e7dfdcf04f4fa71be63',
 'SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md': 'cf2dce367e8168af8fb096ca5056788e5e9f79348e790ae14d0841073d95bd8f',
 'SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md': '254c700887971b21706ce6cfd21dd6b7b1ffbfc3205202d15534f5b6b461d15b',
 'markowitz/synthetic_shrinkage_mechanism.py': '6d29db052344851321eae5fe619c212bcc76fafa2249fc093150f8648a65f849',
 'scripts/check_mechanism_report.py': '0c25bb63169b6e13795e546122000f795f6ef2ba01861d76af686d292123eb1d',
 'synthetic-shrinkage-mechanism-results.json': '0ede16c533c4481a4115949aeb2b2f324959f8ead8c6ea1189ae792484fe03ed',
 'tests/test_shrinkage_mechanism.py': '057a1fd22fe5db153622e79e6881eac6638d4b2314f1f87d0610bdeda02c7373'}
doc=(ROOT/'DECISION_QUALITY_FRAMEWORK.md').read_text()
checks=0


def check(condition,message):
    global checks
    if not condition:raise AssertionError(message)
    checks+=1


def contains(text):check(text in doc,'Framework differs from committed evidence: '+text)


def read(path):return json.loads((ROOT/path).read_text())


def one(rows,**selector):
    found=[r for r in rows if all(r[k]==v for k,v in selector.items())]
    check(len(found)==1,'Exact unique source row: '+str(selector))
    return found[0]


for path,expected in PINNED.items():
    check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,'Pinned historical file changed: '+path)
mechanism=read('synthetic-shrinkage-mechanism-results.json')
for path,expected in mechanism['manifest']['preserved_artifacts'].items():
    check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,'Prior protected file changed: '+path)
s=read('synthetic-shrinkage-results.json');v=read('synthetic-robustness-results.json')
for report in (mechanism,s,v):
    check(report['manifest']['warning']==WARNING,'Sourced artifact evidence label')
    check(all(row['Evidence']==WARNING for rows in report['tables'].values() for row in rows),'Sourced rows remain synthetic')
a=one(mechanism['tables']['paired_covariances'],seed=7102,rho=.35,window=504)
b=one(mechanism['tables']['paired_portfolios'],seed=7102,rho=.35,window=504,strategy='min_vol')
contains('seed **7102**, rho **.35**, **504** rows, min-vol')
contains(f"| Total covariance squared loss | {a['sample_total_squared_error']:.6e} | {a['shrink_total_squared_error']:.6e} |")
contains(f"| True min-vol variance regret | {b['sample_raw_oracle_regret']:.6e} | {b['shrink_raw_oracle_regret']:.6e} |")
contains(f"| Target HHI | {b['sample_HHI']:.6f} | {b['shrink_HHI']:.6f} |")
check(a['delta_total_squared_error']<0 and b['delta_raw_oracle_regret']>0 and b['delta_HHI']<0,'Estimation/decision reversal')
ew={method:one(s['tables']['references'],seed=7001,window=126,strategy='equal_weight',method=method) for method in ('sample','diagonal_25')}
contains('seed **7001**, **126** rows, equal weight')
contains(f"| Estimated volatility | {100*ew['sample']['estimated_volatility']:.4f}% | {100*ew['diagonal_25']['estimated_volatility']:.4f}% |")
contains(f"| Known training-covariance volatility | {100*ew['sample']['known_training_volatility']:.4f}% | {100*ew['diagonal_25']['known_training_volatility']:.4f}% |")
for asset in ('Synthetic A','Synthetic B','Synthetic C','Synthetic D','Synthetic E','Synthetic F'):
    check(ew['sample'][asset]==ew['diagonal_25'][asset],'Equal-weight target control')
paths=[x for x in s['tables']['paired_paths'] if x['seed']==7001 and x['window']==126 and x['strategy']=='equal_weight']
check(len(paths)==4 and all(x['delta_'+key]==0 for x in paths for key in ('volatility','CAGR','max_drawdown','gross_traded_notional')),'Equal-weight forward null control')
p=one(v['tables']['paired_paths'],seed=6006,window=504,strategy='min_vol',cost_bps=0.)
contains('seed **6006**,\n**504** rows, min-vol, **zero cost**')
def percent(x):return f'{100*x:.4f}%'.replace('-','−')
contains(f"| Realized annualized volatility | {percent(p['stationary_baseline_volatility'])} | {percent(p['unseen_positive_jump_volatility'])} |")
contains(f"| Maximum drawdown | {percent(p['stationary_baseline_max_drawdown'])} | {percent(p['unseen_positive_jump_max_drawdown'])} |")
check(p['jump_realized_vol_higher'] and not p['jump_drawdown_more_negative'],'Volatility/drawdown counterexample')
check(mechanism['manifest']['counts']['known_failed_candidate_starts']==1 and mechanism['manifest']['counts']['candidate_failures']==0,'Start/candidate success distinction')
# Structural documentation checks, not enforcement of a future evaluation policy.
header='| Review question | Estimation quality | Decision quality | Forward behavior | Operational trust |'
contains(header)
contains('| Entry for each baseline/challenger comparison | Estimation quality | Decision quality | Forward behavior | Operational trust |')
contains('**loss against true covariance is unobservable**')
contains('**true-covariance oracle regret is unavailable**')
contains('**known true future covariance risk is unavailable**')
contains('THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC')
contains('**No composite score, metric weights, invented success thresholds, confidence\nbounds or automatic winner.**')
contains('**not a reuse pool**')
check(doc.count('**'+WARNING)>=4,'Each numerical counterexample retains evidence label')
registry=read('research/model-evolution/registry-v1.json')
check(not registry['decisions'] and not registry['consumption_events'],'No empirical candidate or consumption recorded')
check(registry['holdouts'][0]['state']=='reserved','Original holdout remains untouched')
links=0
for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc):
    if target.startswith('https://'):continue
    path,_,anchor=target.partition('#')
    file=ROOT/path
    check(file.is_file(),'Broken local link: '+target)
    if anchor:
        headings=[re.sub(r'[^\w -]','',x.lower()).replace(' ','-') for x in re.findall(r'^#+\s+(.+)$',file.read_text(),re.MULTILINE)]
        check(anchor in headings,'Broken anchor: '+target)
    links+=1
print(f'PASS: {checks} framework evidence/label/fingerprint/link assertions; {links} local links. No model execution, network or data retrieval.')
