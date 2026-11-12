"""Read committed synthetic evidence only; verify report figures, labels and links."""
import hashlib
import json
from pathlib import Path
import re
from statistics import median

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'synthetic-shrinkage-results.json').read_text())
t=r['tables'];doc=(ROOT/'SYNTHETIC_SHRINKAGE_FINDINGS.md').read_text()
WARNING='SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
checks=0


def check(value,message):
    global checks
    if not value:raise AssertionError(message)
    checks+=1


def contains(text):check(text in doc,'Report differs from evidence: '+text)


def one(name,**where):
    rows=[v for v in t[name] if all(v[k]==x for k,x in where.items())]
    check(len(rows)==1,'Unique evidence row required: '+str(where))
    return rows[0]


check(r['manifest']['plan']['seeds']==list(range(7001,7006)),'All fixed seeds')
check(r['manifest']['plan']['shrinkage']==.25,'Fixed illustrative shrinkage')
check(r['manifest']['predeclaration_sha256']==hashlib.sha256((ROOT/'SYNTHETIC_SHRINKAGE_PLAN.md').read_bytes()).hexdigest(),'Plan unchanged')
check(all(v['Evidence']==WARNING for rows in t.values() for v in rows),'All exported rows labeled')
for name,value in r['manifest']['preserved_artifacts'].items():
    check(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,'Frozen artifact: '+name)
for path,key in [('research/model-evolution/registry-v1.json','preserved_registry_sha256'),('research/model-evolution/decision-template.json','preserved_template_sha256')]:
    check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==r['manifest'][key],'Empirical registry/template unchanged')
check(all(v['delta_relative_training_covariance_error']>0 for v in t['paired_covariances']),'Training covariance error worse in all ten')
check(len(t['paired_covariances'])==10,'All training cases')
for v in t['paired_covariances']:
    contains(f"| {v['seed']} | {v['window']} | {v['sample_relative_training_covariance_error']:.6f} | {v['shrink_relative_training_covariance_error']:.6f} | {v['delta_relative_training_covariance_error']:+.6f} |")
for v in t['paired_bootstrap_summary']:
    if v['strategy']=='equal_weight':continue
    contains(f"| {v['seed']} | {v['window']} | {v['strategy']} | {100*v['sample_mean_half_L1']:.4f} | {100*v['shrink_mean_half_L1']:.4f} | {100*v['delta_mean_half_L1']:+.4f} |")
for w in (126,504):
    for strategy in ('min_vol','max_sharpe','equal_weight'):
        a=[v for v in t['bootstrap_summary'] if v['window']==w and v['strategy']==strategy]
        x=one('aggregate_bootstrap_summary',window=w,strategy=strategy,metric='delta_mean_half_L1')
        m={method:100*median(v['mean_half_L1'] for v in a if v['method']==method) for method in ('sample','diagonal_25')}
        contains(f"| {w} | {strategy} | {m['sample']:.4f} | {m['diagonal_25']:.4f} | {100*x['median']:+.4f} [{100*x['minimum']:+.4f}, {100*x['maximum']:+.4f}] | {x['favorable']} / {x['unfavorable']} / {x['numerical_ties']} |")
    for strategy in ('min_vol','max_sharpe'):
        counts=[]
        for regime in ('stationary','unseen_jump'):
            values=[]
            for metric in ('volatility','CAGR','max_drawdown'):
                a=one('aggregate_paths',window=w,strategy=strategy,regime=regime,cost_bps=0.,metric='delta_'+metric)
                b=one('aggregate_paths',window=w,strategy=strategy,regime=regime,cost_bps=10.,metric='delta_'+metric)
                check(a['favorable']==b['favorable'] and a['unfavorable']==b['unfavorable'] and a['numerical_ties']==b['numerical_ties'],'Both cost direction counts')
                values.append(str(a['favorable']))
            counts.append(' / '.join(values))
        contains(f'| {w} | {strategy} | {counts[0]} | {counts[1]} |')
refs={m:one('references',seed=7001,window=126,strategy='equal_weight',method=m) for m in ('sample','diagonal_25')}
contains(f"| Estimated volatility | {100*refs['sample']['estimated_volatility']:.4f}% | {100*refs['diagonal_25']['estimated_volatility']:.4f}% |")
for method in ('sample','diagonal_25'):
    check(refs[method]['original_S_volatility']==refs['sample']['original_S_volatility'],'EW cross-estimator S risk control')
for v in t['paired_paths']:
    if v['strategy']=='equal_weight':check(all(v['delta_'+k]==0 for k in ('CAGR','volatility','max_drawdown','gross_traded_notional')),'EW exact paths')
for label,key in [('Known stationary covariance volatility','known_training_volatility'),('Original-S cross-evaluated volatility','original_S_volatility')]:
    contains(f"| {label} | {100*refs['sample'][key]:.4f}% | {100*refs['diagonal_25'][key]:.4f}% |")
x=one('paired_risk',seed=7003,window=126,strategy='max_sharpe',regime='stationary')
contains(f"**{100*x['sample_absolute_risk_gap']:.4f} pp to\n{100*x['shrink_absolute_risk_gap']:.4f} pp**")
x=one('paired_references',seed=7005,window=126,strategy='max_sharpe')
contains(f"**{100*x['sample_estimated_volatility']:.4f}% → {100*x['shrink_estimated_volatility']:.4f}%**")
x=one('paired_paths',seed=7002,window=126,strategy='max_sharpe',regime='stationary',cost_bps=10.)
for key in ('CAGR','volatility','max_drawdown'):
    expected=f"{100*x['sample_'+key]:.4f}% → {100*x['shrink_'+key]:.4f}%".replace('-','−')
    check(expected in doc.replace('\n',' '),'Favorable path example '+expected)
counts=r['manifest']['counts']
check(counts['reference_rows']==60 and counts['bootstrap_rows']==900 and counts['bootstrap_known_failed_starts']==22,'Reported counts')
check(counts['reference_failures']==counts['bootstrap_failures']==counts['unknown_bootstrap_start_counts']==counts['unknown_reference_start_counts']==0,'No hidden failures or missing starts')
contains(f"**{counts['maximum_checked_bootstrap_violation']:.2e}**")
for filename in ('SYNTHETIC_SHRINKAGE_FINDINGS.md','SYNTHETIC_SHRINKAGE_PLAN.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',(ROOT/filename).read_text()):
        if not target.startswith('https://'):check((ROOT/target.split('#')[0]).is_file(),'Local link '+target)
print(f'PASS: {checks} shrinkage evidence/label/fingerprint/link assertions; no fitting or data access.')
