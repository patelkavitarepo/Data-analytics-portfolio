"""Offline documentation checks against frozen JSON evidence; no model execution.

Run from any directory. Uses only the standard library and committed files.
Recomputes descriptive summaries from existing records, never fits or simulates.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
from statistics import median
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
WARNING = 'SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
case = (ROOT/'CASE_STUDY.md').read_text()
checks = 0


def check(condition, message):
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1


def contains(text):
    check(text in case, f'Case study differs from evidence: {text}')


def one(rows, **criteria):
    matches = [r for r in rows if all(r[k] == v for k, v in criteria.items())]
    check(len(matches) == 1, f'Expected unique evidence row: {criteria}')
    return matches[0]


def read(name):
    return json.loads((ROOT/name).read_text())


def number(value, places, signed=False):
    return (f'{value:+.{places}f}' if signed else f'{value:.{places}f}').replace('-', '−')


def literal_assignment(path, name):
    for node in ast.parse((ROOT/path).read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'Missing {name} in {path}')


v1 = read('synthetic-default-summary.json')
v2 = read('synthetic-robustness-results.json')
v3 = read('synthetic-serial-results.json')
s = v1['scenarios']; base = s['baseline']; p2 = v2['manifest']['plan']; p3 = v3['manifest']['plan']
check(v1['warning'] == v2['manifest']['warning'] == v3['manifest']['warning'] == WARNING, 'Evidence labels')
check(len(s) == 5 and all(x['config'] == base['config'] for x in s.values()), 'v1 scenario/config counts')
check(base['config'] == dict(seed=6006, train_steps=504, future_steps=252, bootstrap_draws=20, cap=.35, annual_rf=.02), 'v1 design')
contains('seed **6006**, **504 training / 252 later steps**, and\n**20 IID bootstrap draws**')
check(p2['seeds'] == p3['seeds'] == list(range(6006, 6011)), 'Paired seed grids')
check(p2['windows'] == [126,504] and p2['bootstrap_draws'] == 10 and p2['future_steps'] == 252, 'v2 windows/draws')
contains('Seeds **6006–6010**, nested trailing windows **126/504**, and **10 IID draws**')
check(p2['training_correlation'] == p2['stationary_future_correlation'] == .35 and p2['jump_future_correlation'] == .85, 'v2 correlations')
contains('**+0.35**. Paired later paths retain +0.35 or jump unseen to **+0.85**')
check(p3['training_steps'] == 504 and p3['draws'] == 15 and p3['block_length'] == 5 and p3['phis'] == [0.,.5], 'v3 design')
contains('Seeds **6006–6010**, **504 training steps**, **15 draws per method**, and circular\nblocks of length **5**')
contains('**phi=0/.5**')
check(p2['cap'] == p3['cap'] == base['config']['cap'] == .35 and p2['annual_rf'] == p3['annual_rf'] == .02, 'Fixed assumptions')
contains('**35% per-asset cap**'); contains('**2% assumed effective annual risk-free rate**')
check(literal_assignment('markowitz/analytics.py', 'DAYS') == 252, 'Annualization convention')
contains('**252 steps/year**')
check(p2['cost_bps'] == [0.,10.] and p2['rebalancing_steps'] == 21, 'v2 path settings')
check({row['cost_bps'] for row in base['realized']} == {0.,10.}, 'v1 path costs')
node = next(n for n in ast.parse((ROOT/'markowitz/synthetic.py').read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'path_returns')
check(ast.literal_eval(node.args.defaults[-1]) == 21, 'v1 reset interval')
contains('**21 steps**'); contains('**0/10 bps**')
protocol = literal_assignment('markowitz/research.py', 'PROTOCOL')
check(protocol['train'] == ['2016-01-01','2022-12-31'] and protocol['validation'] == ['2023-01-01','2024-12-31'] and protocol['holdout_start'] == '2025-01-01', 'Frozen empirical dates')
contains('**2016–2022**, validates on **2023–2024**, and reserves **2025 onward**')

bmin = one(base['bootstrap_summary'], index='min_vol')['mean_half_L1_reallocation']
bmax = one(base['bootstrap_summary'], index='max_sharpe')['mean_half_L1_reallocation']
contains(f'| Baseline mean bootstrap half-L1 | Minimum variance **{100*bmin:.2f}%**; local max Sharpe **{100*bmax:.2f}%** |')
est0 = one(base['estimated'], index='min_vol'); bias = s['mean_estimation_error']
est1 = one(bias['estimated'], index='min_vol')
check(bias['target_weight_L1_change_from_baseline']['min_vol'] == 0, 'Mean-bias min-vol target equality')
check([r for r in base['realized'] if r['strategy']=='min_vol'] == [r for r in bias['realized'] if r['strategy']=='min_vol'], 'Mean-bias min-vol path equality')
contains(f"| Mean bias, minimum-variance estimated Sharpe | **{est0['estimated_sharpe']:.3f} → {est1['estimated_sharpe']:.3f}**")
spike = one(s['correlation_spike']['estimated'], index='min_vol')
contains(f"| Known high-correlation regime, min-vol estimated volatility / HHI | **{100*est0['estimated_volatility']:.2f}% → {100*spike['estimated_volatility']:.2f}%** / **{est0['target_HHI']:.4f} → {spike['target_HHI']:.4f}**")
ew0 = one(base['estimated'], index='equal_weight'); ew1 = one(s['correlation_sign_flip']['estimated'], index='equal_weight')
contains(f"| Unseen sign flip, equal-weight stipulated future volatility | **{100*ew0['constructed_future_volatility']:.2f}% → {100*ew1['constructed_future_volatility']:.2f}%**")

risk = v2['tables']['paired_risk']; targets = v2['tables']['targets']
check(len(risk) == 30 and all(r['paired_target_L1']==0 for r in risk), 'Unchanged paired targets')
contains('All **30** target distances exactly **0**')
inflation = median(r['known_volatility_ratio'] for r in risk if r['strategy']=='min_vol' and r['window']==504)
contains(f'Median **+{100*(inflation-1):.2f}%**, relative to stationary future')
for strategy, label, direction in [('min_vol','Min-vol','lower'), ('max_sharpe','Local max-Sharpe','higher')]:
    a = {w:{r['seed']:r['bootstrap_mean_half_L1_reallocation'] for r in targets if r['strategy']==strategy and r['window']==w} for w in (126,504)}
    count = sum((a[504][seed] < a[126][seed]) if direction=='lower' else (a[504][seed] > a[126][seed]) for seed in p2['seeds'])
    contains(f'| {label} bootstrap mean half-L1, short → long | Median **{100*median(a[126].values()):.2f}% → {100*median(a[504].values()):.2f}%**; {direction} in **{count}/5** seeds |')
check(median(r['HHI'] for r in targets if r['strategy']=='min_vol' and r['window']==504) > median(r['HHI'] for r in targets if r['strategy']=='min_vol' and r['window']==126), 'v2 concentration counterexample')
check(all(r['bootstrap_cap_binding_incidence']==1 for r in targets if r['strategy']!='equal_weight'), 'v2 cap incidence')
paths = v2['tables']['paired_paths']
dd = one(paths, seed=6006, window=504, strategy='min_vol', cost_bps=0.)
contains(f"| Seed 6006, long-window min-vol, cost-free drawdown | **{number(100*dd['stationary_baseline_max_drawdown'],4)}% → {number(100*dd['unseen_positive_jump_max_drawdown'],4)}%**")
check(all(r['known_volatility_ratio']>1 for r in risk), 'v2 modeled volatility increase')
check(dd['jump_realized_vol_higher'] and not dd['jump_drawdown_more_negative'], 'v2 realized counterexample')
check(not one(paths, seed=6006, window=504, strategy='min_vol', cost_bps=10.)['jump_drawdown_more_negative'], 'v2 cost-matched exception')

paired = v3['tables']['paired_differences']; threshold = p3['materiality_half_L1']
check(threshold == .02, 'Predeclared materiality')
contains('**2 pp**')
for phi, phi_label in [(0.,'0'),(.5,'.5')]:
    for strategy,label in [('min_vol','Minimum variance'),('max_sharpe','Local max Sharpe')]:
        rows = [r for r in paired if r['phi']==phi and r['strategy']==strategy]
        check(len(rows)==5 and {r['seed'] for r in rows}==set(p3['seeds']), 'Complete paired group')
        values = [100*r['delta_mean_half_L1'] for r in rows]
        flags = sum(abs(r['delta_mean_half_L1']) >= threshold for r in rows)
        contains(f'| phi={phi_label} | {label} | {number(median(values),4,phi!=0)} | {number(min(values),4)} to {number(max(values),4,True)} | {flags}/5 |')
        check(all(r['material_difference'] == (abs(r['delta_mean_half_L1'])>=threshold) for r in rows), 'Flags agree with threshold')
tail = median(r['delta_p95_half_L1'] for r in paired if r['phi']==.5 and r['strategy']=='max_sharpe')
contains(f'**{number(100*tail,4)} pp**, despite its positive mean-distance contrast')
log = v3['tables']['bootstrap_log']
for strategy,label in [('min_vol','minimum-variance'),('max_sharpe','max-Sharpe')]:
    rows = [r for r in log if r['strategy']==strategy]
    check(all(r['success'] for r in rows), 'Valid v3 candidates')
    count = sum(r['any_cap_binding'] for r in rows)
    contains(f'**{count}/{len(rows)}** {label}')
check(all(r['half_L1']==0 for r in log if r['strategy']=='equal_weight'), 'Equal-weight null finding')

# Verify prior code, evidence and gates against v3's committed fingerprints.
for path, expected in v3['manifest']['preserved_sha256'].items():
    check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, f'Frozen evidence changed: {path}')

# Check relative links and heading anchors without contacting any service.
links = 0
for filename in ('CASE_STUDY.md','README.md'):
    content = (ROOT/filename).read_text()
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
        if target.startswith(('https://','http://','mailto:')):
            continue
        path, _, fragment = unquote(target).partition('#')
        destination = ROOT/path if path else ROOT/filename
        check(destination.is_file(), f'Broken local link in {filename}: {target}')
        if fragment:
            anchors = []
            for heading in re.findall(r'^#+\s+(.+)$', destination.read_text(), re.MULTILINE):
                anchors.append(re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-'))
            check(fragment in anchors, f'Broken anchor in {filename}: {target}')
        links += 1
check(case.count('**'+WARNING) >= 4, 'Persistent stage/table labels')
print(f'PASS: {checks} evidence/design/link assertions; {links} local links/anchors. No fitting, simulation, network or provider access.')
