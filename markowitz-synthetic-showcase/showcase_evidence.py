"""Read-only exhibit: stdlib JSON selection/formatting, no model or provider imports."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WARNING='SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
ORACLE='THEORETICAL ORACLE — NON-INVESTABLE DIAGNOSTIC'
REPOSITORY='https://github.com/patelkavitarepo/Data-analytics-portfolio/blob/main/markowitz-synthetic-showcase/'
SPECS = {'lab': {'file': 'synthetic-default-summary.json',
         'findings': 'SYNTHETIC_LAB.md',
         'title': 'Scenario lab',
         'sha256': '86f55b9554ec17e0a8f95e65066d2a2c13e7d347249d5b428b7d0786c7f976eb'},
 'robustness': {'file': 'synthetic-robustness-results.json',
                'findings': 'SYNTHETIC_ROBUSTNESS_FINDINGS.md',
                'title': 'Unseen correlation jump',
                'sha256': '298614f65707c2496df539f612ac6a8b6af57cc5fab295dac7c1599b86c9b70a'},
 'serial': {'file': 'synthetic-serial-results.json',
            'findings': 'SYNTHETIC_SERIAL_FINDINGS.md',
            'title': 'Serial dependence',
            'sha256': '5c9a8ae56f5d14ebaa81da074f948bcb708a747615f69eb1a861cda92c597779'},
 'shrinkage': {'file': 'synthetic-shrinkage-results.json',
               'findings': 'SYNTHETIC_SHRINKAGE_FINDINGS.md',
               'title': 'Fixed covariance shrinkage',
               'sha256': '6a27520431f351c258395384cb0eeb78fdbde655d96a576e33db3505945f763d'},
 'mechanism': {'file': 'synthetic-shrinkage-mechanism-results.json',
               'findings': 'SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md',
               'title': 'Shrinkage mechanism',
               'sha256': '0ede16c533c4481a4115949aeb2b2f324959f8ead8c6ea1189ae792484fe03ed'}}


def _invalid_constant(value):
    raise ValueError('Nonfinite JSON constant: '+value)


def _labels(value):
    count=0
    if isinstance(value,dict):
        if 'Evidence' in value:
            if value['Evidence']!=WARNING:raise ValueError('Mislabeled evidence row')
            count+=1
        for child in value.values():count+=_labels(child)
    elif isinstance(value,list):
        for child in value:count+=_labels(child)
    return count


def load_reports(root=ROOT, *, with_bytes=False):
    """Only fixed committed JSON files. Missing/altered evidence has no fallback."""
    reports={};raw_reports={}
    for study,spec in SPECS.items():
        try:
            raw=(root/spec['file']).read_bytes()
            report=json.loads(raw,parse_constant=_invalid_constant)
            if not isinstance(report,dict):raise ValueError('Expected report object')
            if study=='lab':
                if not isinstance(report.get('scenarios'),dict):raise ValueError('Expected scenario records')
                warning=report.get('warning')
            else:
                if not isinstance(report.get('manifest'),dict) or not isinstance(report.get('tables'),dict):raise ValueError('Expected manifest and tables')
                if not all(isinstance(rows,list) and all(isinstance(row,dict) and row.get('Evidence')==WARNING for row in rows) for rows in report['tables'].values()):raise ValueError('Every table row must be labeled synthetic')
                warning=report['manifest'].get('warning')
            if warning!=WARNING or _labels(report)==0:raise ValueError('Missing synthetic evidence labels')
            if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('Artifact differs from reviewed committed bytes')
            reports[study]=report;raw_reports[study]=raw
        except (OSError,ValueError,TypeError,RecursionError) as exc:
            raise ValueError(f"{spec['file']}: {exc}") from exc
    return (reports,raw_reports) if with_bytes else reports


def one(rows,**where):
    matches=[r for r in rows if all(r.get(k)==v for k,v in where.items())]
    if len(matches)!=1:raise ValueError('Expected one source row: '+str(where))
    return matches[0]


def number(value,kind='percent',digits=4):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('Display requires an observed finite number, never a default')
    if kind=='percent':result=f'{100*value:.{digits}f}%'
    elif kind=='pp':result=f'{100*value:+.{digits}f} pp'
    elif kind=='squared':result=f'{value:.6e}'
    else:result=f'{value:.{digits}f}'
    return result.replace('-','−')


def cell(label,value):
    return dict(label=label,value=value)


def block(title,unit,rows,note):
    return dict(title=title,unit=unit,rows=rows,note=note)


def shared_context(reports):
    cfg=reports['lab']['scenarios']['baseline']['config']
    for study in ('robustness','serial','shrinkage','mechanism'):
        plan=reports[study]['manifest']['plan']
        if plan['cap']!=cfg['cap'] or plan['annual_rf']!=cfg['annual_rf']:
            raise ValueError('Studies no longer share the displayed cap/risk-free assumptions')
    assets=len(reports['mechanism']['manifest']['true_annual_means'])
    return f"{assets} abstract assets · long-only, fully invested · target cap {number(cfg['cap'],digits=0)} · assumed effective annual RF {number(cfg['annual_rf'],digits=0)}"


def build_panels(reports):
    """Preselected cases only; no fitting, simulation or new research summaries."""
    panels={}
    lab=reports['lab'];base=lab['scenarios']['baseline'];bias=lab['scenarios']['mean_estimation_error'];cfg=base['config']
    distances={s:one(base['bootstrap_summary'],index=s)['mean_half_L1_reallocation'] for s in ('min_vol','max_sharpe','equal_weight')}
    a=one(base['estimated'],index='min_vol');b=one(bias['estimated'],index='min_vol')
    panels['lab']=dict(
        title='Estimated opportunity can hide fragile weights',
        context=f"Seed {cfg['seed']} · {cfg['train_steps']} training / {cfg['future_steps']} later steps · {cfg['bootstrap_draws']} IID draws · cap {number(cfg['cap'],digits=0)} · assumed annual RF {number(cfg['annual_rf'],digits=0)}",
        finding='The local max-Sharpe target is more sensitive to resampling than minimum variance in this one constructed baseline. This is not a general estimator ranking.',
        blocks=[block('Training-only allocation sensitivity','Mean half-L1 target reassignment',[
            cell('Minimum variance',number(distances['min_vol'],digits=2)),cell('LOCAL max Sharpe',number(distances['max_sharpe'],digits=2)),cell('Equal weight (fixed control)',number(distances['equal_weight'],digits=2))],
            'Half-L1 is target capital reassigned after resampling, not actual turnover or an uncertainty interval.'),
            block('Counterexample: an estimate changes, the portfolio does not','Training estimated Sharpe (unitless)',[
                cell('Baseline estimated means',number(a['estimated_sharpe'],'unitless',3)),cell('Biased estimated means',number(b['estimated_sharpe'],'unitless',3))],
                'Minimum-variance weights and later outcomes remain unchanged. Raising displayed ex-ante Sharpe is not a portfolio improvement.')],
        limits='One seed and a short IID bootstrap do not establish market performance, confidence bounds or universal sensitivity. Gaussian inputs and illustrative costs omit real execution.',
        sources=['scenarios.baseline.bootstrap_summary: min_vol / max_sharpe / equal_weight','scenarios.baseline.estimated and mean_estimation_error.estimated: min_vol'],
        chart=[dict(Allocation=name,Reassignment=100*distances[key]) for name,key in [('Minimum variance','min_vol'),('LOCAL max Sharpe','max_sharpe'),('Equal weight','equal_weight')]])
    r=reports['robustness'];p=r['manifest']['plan'];t=r['tables']
    ratio=one(t['aggregate_risk'],window=504,strategy='min_vol',metric='known_volatility_ratio')
    path=one(t['paired_paths'],seed=6006,window=504,strategy='min_vol',cost_bps=0.)
    panels['robustness']=dict(title='Unchanged weights can face different risk',
        context=f"Seeds {p['seeds'][0]}–{p['seeds'][-1]} · trailing windows {' / '.join(map(str,p['windows']))} · {p['future_steps']} later steps · {p['bootstrap_draws']} IID draws/case · training rho {p['training_correlation']} → unseen future {p['jump_future_correlation']}",
        finding='Targets and resampling diagnostics are fixed before the unseen correlation jump. Constructed covariance risk rises, but no single finite path must deteriorate in every metric.',
        blocks=[block('Long-window minimum variance: known model-risk inflation','Jump / stationary fixed-target volatility ratio',[
            cell(f"Median across {ratio['valid_seed_count']} valid seeds, 504-row window",number(ratio['median'],'ratio')),
            cell('Descriptive seed range',number(ratio['minimum'],'ratio')+' to '+number(ratio['maximum'],'ratio'))],
            'This uses stipulated generator covariance, not an observable market truth or a forecast. The targets are unchanged across paired futures.'),
            block(f"Counterexample: seed {path['seed']}, {path['window']} rows, zero cost",'Realized finite-path risk; same cost and reset conventions',[
                cell('Annualized volatility: stationary → jump',number(path['stationary_baseline_volatility'])+' → '+number(path['unseen_positive_jump_volatility'])),
                cell('Maximum drawdown: stationary → jump',number(path['stationary_baseline_max_drawdown'])+' → '+number(path['unseen_positive_jump_max_drawdown']))],
                'Volatility rises while this drawdown becomes slightly less negative. Fixed-target model risk and drifting path outcomes are different quantities.')],
        limits='Five seeds and nested windows are not independent market evidence. More positive correlation need not make every finite drawdown worse. Bootstrap cap binding can mask variability.',
        sources=['tables.aggregate_risk: window=504, strategy=min_vol, metric=known_volatility_ratio','tables.paired_paths: seed=6006, window=504, strategy=min_vol, cost_bps=0'])
    r=reports['serial'];p=r['manifest']['plan'];t=r['tables']
    comparisons=[one(t['aggregate_differences'],phi=phi,strategy='max_sharpe',metric='delta_mean_half_L1') for phi in p['phis']]
    panels['serial']=dict(title='Preserving time order does not force a larger uncertainty diagnostic',
        context=f"Seeds {p['seeds'][0]}–{p['seeds'][-1]} · {p['training_steps']} training rows · {p['draws']} draws/method · circular blocks of {p['block_length']} · AR(1) phi {' / '.join(map(str,p['phis']))}",
        finding='Moving blocks and IID resampling produce mixed allocation-sensitivity differences. Even the independent-return control has method differences; systematic IID underestimation is not established.',
        blocks=[block('LOCAL max Sharpe: moving-block minus IID','Mean half-L1 difference, percentage points',[
            cell(f"phi={x['phi']}: median ({x['valid_seeds']} valid seeds)",number(x['median'],'pp')+'; range '+number(x['minimum'],'pp')+' to '+number(x['maximum'],'pp')) for x in comparisons],
            'Positive means more target reassignment under moving blocks; negative means less. These ranges are across five fixed seeds, not confidence intervals.')],
        limits='Only one positive persistence and one block length. Short runs, artificial circular joins, caps and local optima can alter the contrast. A method contrast does not identify a causal effect of dependence.',
        sources=['tables.aggregate_differences: phi=0/.5, strategy=max_sharpe, metric=delta_mean_half_L1'])
    r=reports['shrinkage'];p=r['manifest']['plan'];t=r['tables']
    errors=[one(t['aggregate_covariances'],window=w,metric='delta_relative_training_covariance_error') for w in p['windows']]
    ew={method:one(t['references'],seed=7001,window=126,strategy='equal_weight',method=method) for method in p['methods']}
    panels['shrinkage']=dict(title='Better conditioning does not guarantee better risk estimates',
        context=f"Seeds {p['seeds'][0]}–{p['seeds'][-1]} · windows {' / '.join(map(str,p['windows']))} · {p['bootstrap_draws']} paired IID draws/case · shrinkage {number(p['shrinkage'],digits=0)} · training rho {p['training_correlation']}",
        finding='The fixed diagonal target worsens covariance error under genuine positive correlation in this grid. Concentration often falls, yet allocation stability is mixed and risk can worsen.',
        blocks=[block('Training covariance error: shrinkage versus sample','Relative Frobenius error; per-window direction counts',[
            cell(f"{x['window']} rows",f"Worse in {x['unfavorable']}/{x['valid_pairs']} paired seeds; median error difference {number(x['median'],'ratio',6)}") for x in errors],
            'The two nested windows are reported separately, not pooled as independent seeds. This estimator uses a fixed illustrative coefficient, not an optimized intensity.'),
            block('Counterexample: unchanged equal-weight portfolio','Seed 7001 · 126 rows · annualized volatility',[
                cell('Sample-covariance estimated volatility',number(ew['sample']['estimated_volatility'])),
                cell('Shrinkage estimated volatility',number(ew['diagonal_25']['estimated_volatility'])),
                cell('Known training risk, either view',number(ew['sample']['known_training_volatility']))],
                'Weights, constructed risk and later paths are identical across methods. A lower reported estimate alone is not improvement.')],
        limits='The target removes genuine positive correlations. This does not establish that all shrinkage is ineffective. Earlier path outcomes and bootstrap diagnostics are separate from covariance loss.',
        sources=['tables.aggregate_covariances: window=126/504, metric=delta_relative_training_covariance_error','tables.references: seed=7001, window=126, strategy=equal_weight, method=sample/diagonal_25'])
    r=reports['mechanism'];p=r['manifest']['plan'];t=r['tables'];rows=[]
    for rho in p['rhos']:
        for window in p['windows']:
            c=one(t['covariance_contrasts'],rho=rho,window=window,metric='delta_total_squared_error')
            g=one(t['regret_contrasts'],rho=rho,window=window,metric='delta_raw_oracle_regret')
            rows.append(cell(f"rho={rho}, {window} rows",f"Matrix loss: lower {int(c['lower'])}/{c['valid_seeds']}, higher {int(c['higher'])}/{c['valid_seeds']}; min-vol regret: lower {int(g['lower'])}/{g['valid_seeds']}, higher {int(g['higher'])}/{g['valid_seeds']}"))
    c=one(t['paired_covariances'],seed=7102,rho=.35,window=504)
    g=one(t['paired_portfolios'],seed=7102,rho=.35,window=504,strategy='min_vol')
    panels['mechanism']=dict(title='Matrix accuracy and allocation quality can disagree',
        context=f"Seeds {p['seeds'][0]}–{p['seeds'][-1]} · rho {' / '.join(map(str,p['rhos']))} · trailing windows {' / '.join(map(str,p['windows']))} · no resampling or future paths · fixed shrinkage {number(p['shrinkage'],digits=0)}",
        finding='At zero true correlation the diagonal target matches the structure. With positive correlation it introduces target bias. The matrix-loss identity does not guarantee better constrained portfolio decisions.',
        blocks=[block('The two correlation conditions','Observed directions within each five-seed/window group',rows,
            f"{ORACLE}. Regret is true min-vol variance minus the constrained oracle variance, not return or Sharpe regret. True covariance is available only inside this constructed model."),
            block('Counterexample: seed 7102 · rho=.35 · 504 rows','Two separate loss units; sample → shrinkage',[
                cell('Matrix squared loss (squared annual covariance units)',number(c['sample_total_squared_error'],'squared')+' → '+number(c['shrink_total_squared_error'],'squared')),
                cell('Min-vol true-variance regret (annual variance units)',number(g['sample_raw_oracle_regret'],'squared')+' → '+number(g['shrink_raw_oracle_regret'],'squared')),
                cell('Target concentration HHI (unitless)',number(g['sample_HHI'],'unitless',6)+' → '+number(g['shrink_HHI'],'unitless',6))],
                'Matrix loss improves while portfolio regret worsens. HHI and condition number are diagnostics, not proof of a better decision.')],
        limits=f"{ORACLE}. Known truth is scoring-only, never a fitted input. Five seeds are deliberately diagnostic follow-up, not independent confirmation. No real market true-covariance loss or oracle regret is available.",
        sources=['tables.covariance_contrasts / regret_contrasts: each rho/window; five paired seeds separately','tables.paired_covariances / paired_portfolios: seed=7102, rho=.35, window=504, strategy=min_vol'])
    return panels
