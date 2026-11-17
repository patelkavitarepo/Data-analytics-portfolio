"""Audit frozen synthetic mechanism figures, identities and links; never fit models."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'synthetic-shrinkage-mechanism-results.json').read_text())
t=r['tables'];doc=(ROOT/'SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md').read_text()
checks=0


def check(value,message):
    global checks
    if not value:raise AssertionError(message)
    checks+=1


def contains(text):check(text in doc,'Figure differs from frozen evidence: '+text)


for path,value in r['manifest']['preserved_artifacts'].items():
    check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value,'Historical file: '+path)
check(r['manifest']['predeclaration_sha256']==hashlib.sha256((ROOT/'SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md').read_bytes()).hexdigest(),'Predeclaration unchanged')
check(all(row['Evidence']=='SYNTHETIC DATA — NOT EMPIRICAL RESULTS' for rows in t.values() for row in rows),'Export labels')
check(all(row['comparator']=='THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC' for row in t['oracles']),'Oracle labels')
for v in t['paired_covariances']:
    contains(f"| {v['seed']} | {v['rho']:g} | {v['window']} | {v['sample_total_squared_error']:.6e} | {v['shrink_total_squared_error']:.6e} | {v['sample_diagonal_squared_error']:.6e} | {v['sample_offdiagonal_squared_error']:.6e} | {v['shrink_offdiagonal_squared_error']:.6e} |")
    check(abs(v['delta_diagonal_squared_error'])<=1e-12,'Diagonal loss unchanged')
    for method in ('sample','shrink'):
        check(abs(v[method+'_total_squared_error']-v[method+'_diagonal_squared_error']-v[method+'_offdiagonal_squared_error'])<=1e-12,'Loss components sum')
    terms=next(x for x in t['decomposition'] if all(x[k]==v[k] for k in ('seed','rho','window')))
    check(abs(terms['decomposition_sum']-v['delta_offdiagonal_squared_error'])<=1e-12,'Mechanism decomposition identity')
    if v['rho']==0.:
        check(abs(v['shrink_offdiagonal_squared_error']-.5625*v['sample_offdiagonal_squared_error'])<=1e-12,'Zero-correlation identity')
for name,metric in [('covariance_contrasts','delta_total_squared_error'),('regret_contrasts','delta_raw_oracle_regret')]:
    for v in t[name]:
        if v['metric']!=metric:continue
        contains(f"| {v['rho']:g} | {v['window']} | {v['median']:+.6e} | {v['minimum']:+.6e} to {v['maximum']:+.6e} | {int(v['lower'])} / {int(v['higher'])} / {int(v['numerical_ties'])} |")
        check(v['valid_seeds']==v['recorded_seeds']==v['planned_seeds']==5,'Five paired seeds per group')
for v in t['paired_portfolios']:
    if v['strategy']!='min_vol':continue
    rows=[x for x in t['portfolios'] if all(x[k]==v[k] for k in ('seed','rho','window','strategy'))]
    caps={x['method']:x['cap_count'] for x in rows}
    contains(f"| {v['seed']} | {v['rho']:g} | {v['window']} | {v['sample_raw_oracle_regret']:.6e} | {v['shrink_raw_oracle_regret']:.6e} | {v['delta_raw_oracle_regret']:+.6e} | {v['delta_HHI']:+.6f} | {caps['sample']} / {caps['diagonal_25']} |")
for v in t['oracles']:contains(f"| {v['rho']:g} | {v['variance']:.12e} | checked valid |")
positive=[v for v in t['paired_covariances'] if v['rho']==.35]
check(sum(v['delta_total_squared_error']< -1e-12 for v in positive)==1,'Positive-rho matrix counterexample retained')
for rho,lower in ((0.,True),(.35,False)):
    gaps=[v for v in t['paired_portfolios'] if v['rho']==rho and v['strategy']=='min_vol']
    check(len(gaps)==10 and all((v['delta_raw_oracle_regret']< -1e-12) if lower else (v['delta_raw_oracle_regret']>1e-12) for v in gaps),'Observed regret direction counts')
min0=[v for v in t['paired_portfolios'] if v['rho']==0. and v['strategy']=='min_vol']
check(sum(v['delta_HHI']>1e-12 for v in min0)==7,'HHI counterexample count')
min35=[v for v in t['paired_portfolios'] if v['rho']==.35 and v['strategy']=='min_vol']
check(all(v['delta_HHI']< -1e-12 for v in min35),'Positive-rho concentration count')
for v in t['paired_portfolios']:
    if v['strategy']=='equal_weight':check(v['target_half_L1']==v['delta_true_variance']==0,'Equal-weight null control')
counts=r['manifest']['counts']
check(counts['candidate_rows']==120 and counts['oracle_solves']==2 and counts['valid_oracle_regret_rows']==40,'Case counts')
check(counts['candidate_failures']==counts['oracle_failures']==counts['invalid_oracle_regret_rows']==counts['missing_oracle_regret_rows']==0,'No suppressed failures/invalid gaps')
check(counts['known_failed_candidate_starts']==1,'Reported failed start')
contains(f"**{counts['max_checked_candidate_violation']:.2e}**")
for filename in ('SYNTHETIC_SHRINKAGE_MECHANISM_PLAN.md','SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',(ROOT/filename).read_text()):
        if not target.startswith('https://'):check((ROOT/target.split('#')[0]).is_file(),'Broken local link '+target)
print(f'PASS: {checks} mechanism evidence/identity/fingerprint/link assertions; no model execution or data access.')
