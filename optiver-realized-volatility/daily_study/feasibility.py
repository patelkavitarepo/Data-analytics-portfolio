"""D006 discovery support audit. No pair CVRs, rankings or predictive models.

All simulations are explicitly synthetic. Counts are evidence feasibility, not
independent sample sizes or final eligibility/reliability decisions.
"""
import argparse
import json
import math
import platform
from pathlib import Path
from statistics import NormalDist

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from daily_study.declines import Context, episode_ids, write_json
from daily_study.quality import sha256


def describe(values):
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    return dict(total=values.size, undefined=int(values.size-finite.size),
                quantiles=dict(zip(['min', 'p10', 'p25', 'median', 'p75', 'p90', 'max'],
                    np.quantile(finite, [0, .1, .25, .5, .75, .9, 1]).tolist())) if finite.size else {})


def verify_inputs(root):
    root = Path(root)
    expected = json.loads((root/'artifact_hashes.json').read_text())
    observed = {}
    for name in ['manifest.json', 'narrow.parquet', 'conservative.parquet', 'aligned_raw.parquet']:
        observed[name] = sha256(root/name)
        if observed[name] != expected.get(name):
            raise ValueError(f'Existing cleaning artifact hash mismatch: {name}')
    return observed


def load_inputs(root, design):
    """Column projection and date predicate precede all feature calculations."""
    filters = [('date', '>=', pd.Timestamp(design['discovery_start'])),
               ('date', '<=', pd.Timestamp(design['discovery_end']))]
    root = Path(root)
    panels = {}
    for policy in ['narrow', 'conservative']:
        table = pd.read_parquet(root/f'{policy}.parquet', filters=filters,
            columns=['date', 'stock', 'log_return', 'range_features_eligible',
                     'price_reason_codes', 'return_reason_codes'])
        panels[policy] = {col: table.pivot(index='date', columns='stock', values=col).sort_index()
                          for col in table.columns if col not in ['date', 'stock']}
    raw = pd.read_parquet(root/'aligned_raw.parquet', filters=filters,
                         columns=['date', 'stock', 'high', 'low', 'source_present'])
    raw = {col: raw.pivot(index='date', columns='stock', values=col).sort_index()
           for col in ['high', 'low', 'source_present']}
    reference = panels['conservative']['log_return']
    for fields in [*panels.values(), raw]:
        for frame in fields.values():
            if not frame.index.equals(reference.index) or not frame.columns.equals(reference.columns):
                raise ValueError('Input alignment mismatch')
    if reference.index.max() > pd.Timestamp('2015-12-31'):
        raise ValueError('Discovery boundary cannot extend into reserved relationship period')
    return panels, raw


def measurements(fields, raw):
    r = fields['log_return']
    valid_range = fields['range_features_eligible'].astype(bool) & (raw['low'] > 0) & (raw['high'] >= raw['low'])
    intraday = np.log(raw['high']/raw['low']).where(valid_range)
    return dict(absolute_return=r.abs(), downside_magnitude=(-r).clip(lower=0),
                intraday_range=intraday,
                backward_five_rv=np.sqrt(r.pow(2).rolling(5, min_periods=5).sum()))


def stress_states(frame, window, q, coverage):
    minimum = math.ceil(window*coverage)
    historical = frame.shift(1).rolling(window, min_periods=minimum)
    threshold = historical.quantile(q, interpolation='linear')
    count = frame.shift(1).rolling(window, min_periods=1).count()
    # A zero tail threshold is counted, not interpreted as meaningful scale evidence.
    eligible = frame.notna() & threshold.notna() & (threshold > 0)
    stressed = eligible & frame.gt(threshold)
    return dict(valid=eligible.to_numpy(), stress=stressed.to_numpy(),
                current=frame.notna().to_numpy(), threshold=threshold.to_numpy(),
                historical_count=count.to_numpy(),
                zero_threshold=(frame.notna() & threshold.eq(0)).to_numpy(),
                ties=(eligible & frame.eq(threshold)).to_numpy())


def potential_context(context, columns):
    """Exact leave-both-out decline context; no focal outcomes define donors.

    Vectorized exact median deletion on only dates that could pass after removing
    at most two names. Returns anonymous pair-index arrays, never candidate scores.
    """
    n = context.valid.sum(axis=1)
    low = context.valid & (context.simple <= context.design['primary_decline']['donor_simple_return_at_most']+1e-12)
    negatives = low.sum(axis=1)
    fraction = context.design['primary_decline']['minimum_fraction']
    minimum = context.design['minimum_context_donors']
    possible = (n >= minimum) & (negatives >= fraction*(n-2)-1e-12)
    dates = np.flatnonzero(possible)
    local_i, local_j = np.triu_indices(len(columns), 1)
    i, j = columns[local_i], columns[local_j]
    valid = context.valid[dates]
    pair_n = n[dates, None]-valid[:, i]-valid[:, j]
    pair_negative = negatives[dates, None]-low[dates][:, i]-low[dates][:, j]
    decline = (pair_n >= minimum) & (pair_negative >= fraction*pair_n-1e-12)
    ranks = context.order.ranks[dates]
    ri, rj = ranks[:, i], ranks[:, j]
    sentinel = context.simple.shape[1]+1
    removed = np.sort(np.stack([np.where(ri >= 0, ri, sentinel),
                                np.where(rj >= 0, rj, sentinel)]), axis=0)
    middle = []
    for k in [(pair_n-1)//2, pair_n//2]:
        index = np.maximum(k, 0).copy()
        for rank in removed:
            index += rank <= index
        index = np.minimum(index, context.simple.shape[1]-1)
        middle.append(context.order.sorted[dates[:, None], index])
    with np.errstate(invalid='ignore'):
        medians = (middle[0]+middle[1])/2
    return dict(dates=dates, i=i, j=j, decline=decline, median=medians,
                local_i=local_i, local_j=local_j)


def wilson_width(trials, probability=.5, level=.95):
    """IID benchmark only, not a valid dependent-financial-data interval."""
    n = np.asarray(trials, dtype=float)
    z = NormalDist().inv_cdf((1+level)/2)
    with np.errstate(divide='ignore', invalid='ignore'):
        width = 2*z*np.sqrt(probability*(1-probability)/n+z*z/(4*n*n))/(1+z*z/n)
    return np.where(n > 0, width, np.nan)


def episode_support(valid, stressed, context_mask, dates, gap):
    positions = np.flatnonzero(context_mask)
    labels = episode_ids(positions, gap)
    # Use market-defined episodes before removing unknown stock observations.
    totals = np.array([(valid[positions[labels == g]]).sum(axis=0) for g in np.unique(labels)])
    events = np.array([(stressed[positions[labels == g]]).sum(axis=0) for g in np.unique(labels)])
    if not len(totals):
        totals = np.zeros((0, valid.shape[1]), dtype=int)
        events = totals.copy()
    count = events.sum(axis=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        concentration = (events**2).sum(axis=0)/(count**2)
        largest = events.max(axis=0)/count if len(events) else np.full(valid.shape[1], np.nan)
    return dict(totals=totals, events=events, calendar_blocks=len(totals),
                observed_blocks=(totals > 0).sum(axis=0),
                event_blocks=(events > 0).sum(axis=0),
                concentration_equivalent_blocks=np.where(count > 0, 1/concentration, np.nan),
                largest_event_block_share=largest)


def marginal_bootstrap(totals, events, seed, repetitions=1000):
    """Fixed-state stress-frequency feasibility, NOT conditional pair uncertainty."""
    k = len(totals)
    width = np.full(totals.shape[1], np.nan)
    undefined = np.ones(totals.shape[1])
    if k < 2:
        return width, undefined
    weights = np.random.default_rng(seed).multinomial(k, np.full(k, 1/k), size=repetitions)
    n, successes = weights@totals, weights@events
    with np.errstate(divide='ignore', invalid='ignore'):
        p = successes/n
    undefined = (~np.isfinite(p)).mean(axis=0)
    usable = np.isfinite(p).any(axis=0)
    if usable.any():
        bounds = np.nanquantile(p[:, usable], [.025, .975], axis=0)
        width[usable] = bounds[1]-bounds[0]
    return width, undefined


def pair_count_summary(states, pair, severity_cut, gap):
    d, i, j = pair['dates'], pair['i'], pair['j']
    valid = states['valid'][d]
    stress = states['stress'][d]
    paired = valid[:, i] & valid[:, j] & pair['decline']
    a = paired & stress[:, i]
    c = paired & stress[:, j]
    both = a & c
    n, na, nc, n11 = (x.sum(axis=0) for x in [paired, a, c, both])
    # Reference blocks are defined by union-of-possible decline dates, not events.
    labels = episode_ids(d, gap)
    co_blocks = np.zeros(len(i), dtype=int)
    max_block = np.zeros(len(i), dtype=int)
    for block in np.unique(labels):
        counts = both[labels == block].sum(axis=0)
        co_blocks += counts > 0
        max_block = np.maximum(max_block, counts)
    with np.errstate(divide='ignore', invalid='ignore'):
        share = np.where(n11 > 0, max_block/n11, np.nan)
    # Counterfactual mixture lift using ONLY within-stratum marginal counts.
    # This is not observed CVR: no n11 appears in this calculation.
    severe = pair['median'] <= severity_cut
    expected_joint = np.zeros(len(i), dtype=float)
    represented = np.ones(len(i), dtype=bool)
    for mask in [severe, ~severe]:
        ns = (paired & mask).sum(axis=0)
        nas = (a & mask).sum(axis=0)
        ncs = (c & mask).sum(axis=0)
        represented &= ns > 0
        with np.errstate(divide='ignore', invalid='ignore'):
            expected_joint += np.where(ns > 0, nas*ncs/ns, 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        null_lift = np.where(represented & (na > 0) & (nc > 0), n*expected_joint/(na*nc), np.nan)
    directional_trials = np.r_[na, nc]
    return dict(pairs=len(i), paired_decline_dates=describe(n),
                no_paired_observations=int((n == 0).sum()),
                directional_reference_stress_trials=describe(directional_trials),
                zero_reference_stress_directions=int((directional_trials == 0).sum()),
                joint_stress_dates=describe(n11), zero_joint_stress_pairs=int((n11 == 0).sum()),
                co_stress_reference_blocks=describe(co_blocks),
                pairs_with_one_or_zero_co_stress_blocks=int((co_blocks <= 1).sum()),
                largest_block_fraction_of_co_stress=describe(share),
                iid_worst_case_conditional_probability_interval_width=describe(wilson_width(directional_trials)),
                severity_mixture_null_lift=describe(null_lift),
                severity_null_lift_scope='Counterfactual expected lift from paired marginal severity rates only; not observed pair CVR or causal explanation')


def synthetic_precision(lengths, seed, repetitions=10000):
    rng = np.random.default_rng(seed)
    n = int(sum(lengths))
    result = []
    scenarios = [('iid_p10', .1, False), ('iid_p30', .3, False),
                 ('iid_p50', .5, False), ('episode_constant_p30', .3, True),
                 ('severity_mixture_p10_p80', None, False)]
    for name, p, clustered in scenarios:
        units = len(lengths) if clustered else n
        probabilities = np.full(units, p) if p is not None else np.r_[np.full(n//2, .1), np.full(n-n//2, .8)]
        a = rng.random((repetitions, units)) < probabilities
        c = rng.random((repetitions, units)) < probabilities
        weights = np.asarray(lengths) if clustered else np.ones(n, dtype=int)
        na, nc, joint = a@weights, c@weights, (a & c)@weights
        with np.errstate(divide='ignore', invalid='ignore'):
            cvr = np.where((na > 0) & (nc > 0), n*joint/(na*nc), np.nan)
        expected_joint = np.dot(weights, probabilities**2)/n
        mean_rate = np.dot(weights, probabilities)/n
        result.append(dict(scenario=name, label='SYNTHETIC, NOT MARKET RELATIONSHIPS',
                           experiments=repetitions, dates=n, independent_units=units,
                           population_pooled_lift=expected_joint/mean_rate**2,
                           cvr=describe(cvr), undefined_fraction=float((~np.isfinite(cvr)).mean()),
                           zero_joint_fraction=float((joint == 0).mean()),
                           estimated_cvr_above_two_fraction=float((cvr > 2).mean())))
    return result


def run(root, design_path, output):
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError('Fresh feasibility output directory required')
    design_path = Path(design_path)
    design = json.loads(design_path.read_text())
    if design['discovery_end'] != '2015-12-31':
        raise ValueError('Reserved later relationship period must remain excluded')
    input_hashes = verify_inputs(root)
    implementation_hash = sha256(__file__)
    context_path = (design_path.parent/design['context_design']).resolve()
    context_design = json.loads(context_path.read_text())
    panels, raw = load_inputs(root, design)
    returns = panels['conservative']['log_return']
    dates, names = returns.index, returns.columns
    columns = np.flatnonzero(returns.notna().any().to_numpy())
    context = Context(returns.to_numpy(), context_design)
    ordinary, decline, donors, market_return = context.states()
    severity_cut = float(np.median(market_return[decline]))
    pair = potential_context(context, columns)
    focal_calendars = {int(col):context.states((int(col),))[1] for col in columns}
    output.mkdir(parents=True)
    timeline = pd.DataFrame(dict(date=dates, decline=decline, ordinary=ordinary,
                                donors=donors, donor_median=market_return,
                                more_severe=decline & (market_return <= severity_cut)))
    timeline.to_json(output/'context.json', orient='records', date_format='iso', indent=2)
    arrays, summaries, profiles, availability, cache = {}, [], [], [], {}
    common_calendar = np.arange(len(dates)) >= max(design['history_sessions'])+4
    for policy, fields in panels.items():
        arrays[policy] = measurements(fields, raw)
        for measure in design['measurements']:
            for h in design['history_sessions']:
                for q in design['quantiles']:
                    for coverage in design['history_coverage_fractions']:
                        key = f'{measure}/H{h}/q{q}/coverage{coverage}'
                        states = stress_states(arrays[policy][measure], h, q, coverage)
                        cache[policy, key] = states['valid'], states['stress']
                        subset = {k: v[:, columns] for k, v in states.items()}
                        # Calendar for pooled distributions only; stock profiles below use focal exclusion.
                        support = episode_support(subset['valid'], subset['stress'], decline, dates,
                                                  design['episode_primary_gap'])
                        widths, undefined = marginal_bootstrap(support['totals'], support['events'], design['seed'])
                        n = (decline[:, None] & subset['valid']).sum(axis=0)
                        k = (decline[:, None] & subset['stress']).sum(axis=0)
                        with np.errstate(divide='ignore', invalid='ignore'):
                            rate = k/n
                        severity = {}
                        for label, mask in [('less_severe', decline & (market_return > severity_cut)),
                                            ('more_severe', decline & (market_return <= severity_cut))]:
                            ns = (subset['valid'] & mask[:, None]).sum(axis=0)
                            ks = (subset['stress'] & mask[:, None]).sum(axis=0)
                            with np.errstate(divide='ignore', invalid='ignore'):
                                severity[label] = dict(available=describe(ns), stress_frequency=describe(ks/ns))
                        summary = dict(policy=policy, definition=key, measurement=measure, history=h,
                            quantile=q, coverage=coverage, stock_universe=len(columns),
                            decline_available_stock_dates=int(n.sum()), decline_stress_stock_dates=int(k.sum()),
                            common_calendar_decline_available_stock_dates=int((subset['valid'] & decline[:, None] & common_calendar[:, None]).sum()),
                            available_decline_dates_per_stock=describe(n), stress_decline_dates_per_stock=describe(k),
                            stress_frequency=describe(rate), stress_supporting_blocks=describe(support['event_blocks']),
                            concentration_equivalent_blocks=describe(support['concentration_equivalent_blocks']),
                            largest_event_block_share=describe(support['largest_event_block_share']),
                            marginal_fixed_state_bootstrap_width=describe(widths),
                            marginal_bootstrap_undefined_fraction=describe(undefined),
                            stocks_with_no_decline_stress=int((k == 0).sum()),
                            zero_event_stocks_with_misleading_zero_bootstrap_width=int(((k == 0) & (widths == 0)).sum()),
                            severity_strata=severity,
                            pair_support=pair_count_summary(states, pair, severity_cut, design['episode_primary_gap']))
                        summaries.append(summary)
                        for year in sorted(set(dates.year)):
                            for label, mask in [('decline', decline), ('ordinary', ordinary), ('all', np.ones(len(dates), bool))]:
                                mask = mask & (dates.year == year)
                                availability.append(dict(policy=policy, definition=key, year=int(year), context=label,
                                    reference_dates=int(mask.sum()),
                                    source_stock_dates=int(raw['source_present'].to_numpy()[mask][:, columns].sum()),
                                    finite_measure_stock_dates=int(subset['current'][mask].sum()),
                                    eligible_stock_dates=int(subset['valid'][mask].sum()),
                                    stress_stock_dates=int(subset['stress'][mask].sum()),
                                    zero_threshold_stock_dates=int(subset['zero_threshold'][mask].sum()),
                                    threshold_ties=int(subset['ties'][mask].sum())))
                        for position, col in enumerate(columns):
                            focal_decline = focal_calendars[int(col)]
                            valid = states['valid'][:, [col]]
                            stressed = states['stress'][:, [col]]
                            record = dict(policy=policy, definition=key, stock=str(names[col]),
                                decline_dates=int((valid[:, 0] & focal_decline).sum()),
                                stress_dates=int((stressed[:, 0] & focal_decline).sum()))
                            for gap in design['episode_gap_sessions']:
                                blocks = episode_support(valid, stressed, focal_decline, dates, gap)
                                record[f'calendar_blocks_gap{gap}'] = blocks['calendar_blocks']
                                record[f'stress_blocks_gap{gap}'] = int(blocks['event_blocks'][0])
                                record[f'concentration_equivalent_gap{gap}'] = float(blocks['concentration_equivalent_blocks'][0])
                            profiles.append(record)
                        print(f'Completed {policy} {key}', flush=True)
    comparisons = []
    for policy, other in [('narrow', 'conservative')]:
        for key in sorted({k for p, k in cache if p == policy}):
            v, s = cache[policy, key]
            ov, os = cache[other, key]
            common = v & ov & decline[:, None]
            comparisons.append(dict(definition=key, scope='global decline calendar; 495 discovery-observed names',
                narrow_only_eligible=int((v & ~ov & decline[:, None])[:, columns].sum()),
                conservative_only_eligible=int((ov & ~v & decline[:, None])[:, columns].sum()),
                common_eligible=int(common[:, columns].sum()),
                common_date_state_flips=int((common & (s != os))[:, columns].sum()),
                narrow_stress_on_common=int((common & s)[:, columns].sum()),
                conservative_stress_on_common=int((common & os)[:, columns].sum())))
    definition_comparisons = []
    for policy in panels:
        for measure in design['measurements']:
            for q in design['quantiles']:
                for coverage in design['history_coverage_fractions']:
                    a, b = (f'{measure}/H{h}/q{q}/coverage{coverage}' for h in design['history_sessions'])
                    av, ast = cache[policy, a]; bv, bst = cache[policy, b]
                    common = av & bv & decline[:, None]
                    union_stress = common & (ast | bst)
                    definition_comparisons.append(dict(policy=policy, measurement=measure, quantile=q, coverage=coverage,
                        common_eligible=int(common[:, columns].sum()),
                        stress_in_either=int(union_stress[:, columns].sum()),
                        disagreeing_states=int((common & (ast != bst))[:, columns].sum())))
    global_positions = np.flatnonzero(decline)
    labels = episode_ids(global_positions, design['episode_primary_gap'])
    lengths = [int((labels == g).sum()) for g in np.unique(labels)]
    simulations = synthetic_precision(lengths, design['seed'])
    pd.DataFrame(profiles).sort_values(['policy', 'definition', 'stock']).to_json(output/'stock_support.jsonl', orient='records', lines=True)
    write_json(output/'definitions.json', summaries)
    write_json(output/'coverage.json', availability)
    write_json(output/'mask_comparison.json', comparisons)
    write_json(output/'history_comparison.json', definition_comparisons)
    write_json(output/'synthetic_precision.json', simulations)
    write_json(output/'iid_precision_benchmarks.json', [dict(trials=n, full_width=float(wilson_width(n))) for n in [5, 10, 20, 50, 100, 200, 400]])
    manifest = dict(stage='D006 discovery feasibility only', source_sha256=json.loads((root/'manifest.json').read_text()).get('source_sha256'),
        discovery_start=str(dates.min().date()), discovery_end=str(dates.max().date()), discovery_sessions=len(dates),
        aligned_names=len(names), discovery_observed_names=len(columns), pair_universe=len(pair['i']),
        global_decline_dates=int(decline.sum()), global_ordinary_dates=int(ordinary.sum()),
        possible_pair_decline_dates=len(pair['dates']),
        global_episode_blocks={str(g):len(np.unique(episode_ids(global_positions, g))) for g in design['episode_gap_sessions']},
        episode_lengths_gap5=lengths, severity_discovery_median_donor_return_cut=severity_cut,
        definitions_per_policy=len(summaries)//2, later_relationship_observations_read=False,
        target_columns_read=False, models_trained=False, pair_cvr_computed=False, reference_candidates_ranked=False,
        input_hashes=input_hashes,
        design_sha256=sha256(design_path), context_design_sha256=sha256(context_path), code_sha256=sha256(__file__),
        context_code_sha256=sha256(Path(__file__).with_name('declines.py')),
        python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__,
        bootstrap_scope='marginal frequencies, fixed historical states, global reference blocks; not calibrated pair intervals',
        pair_block_scope='union-of-possible leave-two-out decline calendar; support concentration convention, not independence proof',
        common_calendar_start=str(dates[np.flatnonzero(common_calendar)[0]].date()) if common_calendar.any() else None)
    if verify_inputs(root) != input_hashes or sha256(__file__) != implementation_hash:
        raise ValueError('Inputs or implementation changed during the audit')
    write_json(output/'manifest.json', manifest)
    plot_evidence(summaries, simulations, output)
    write_json(output/'output_hashes.json', {p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()})
    return manifest


def plot_evidence(summaries, simulations, output):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    measures = ['absolute_return', 'downside_magnitude', 'intraday_range', 'backward_five_rv']
    for h, marker in [(60, 'o'), (252, 's')]:
        for q, color in [(.9, '#226d9e'), (.95, '#b25d35')]:
            rows = [next(s for s in summaries if s['policy'] == 'conservative' and s['measurement'] == m and s['history'] == h and s['quantile'] == q and s['coverage'] == 1) for m in measures]
            label = f'{h} sessions, q={q}'
            for ax, metric in zip(axes, ['available_decline_dates_per_stock', 'stress_decline_dates_per_stock']):
                ax.plot(range(4), [s[metric]['quantiles']['median'] for s in rows], marker=marker, color=color,
                        linestyle='-' if h == 60 else '--', label=label)
            axes[2].plot(range(4), [s['pair_support']['directional_reference_stress_trials']['quantiles']['median'] for s in rows], marker=marker, color=color,
                         linestyle='-' if h == 60 else '--', label=label)
    for ax, title in zip(axes, ['Available decline dates per stock', 'Stock-stress dates during declines', 'Reference-stress trials per direction']):
        ax.set_xticks(range(4), ['Absolute\nreturn', 'Downside', 'Intraday\nrange', 'Trailing\n5-session RV'])
        ax.set_title(title+'\nMedian; conservative, complete history', fontsize=10)
        ax.set_ylabel('Observed dates, not independent events')
        ax.set_ylim(bottom=0)
    axes[0].legend(fontsize=8)
    fig.suptitle('Discovery support feasibility — definitions are comparisons, not chosen winners')
    fig.tight_layout(); fig.savefig(output/'support.svg'); fig.savefig(output/'support.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ns = np.arange(1, 401)
    axes[0].plot(ns, wilson_width(ns)*100, color='#226d9e')
    axes[0].set_xlabel('Independent reference-stress observations (hypothetical)')
    axes[0].set_ylabel('Full 95% interval width, percentage points')
    axes[0].set_title('Optimistic IID precision at probability 0.5\nNo baseline, multiplicity or serial-dependence uncertainty')
    rows = simulations[:4]
    axes[1].bar(range(4), [100*s['estimated_cvr_above_two_fraction'] for s in rows], color=['#226d9e']*3+['#b25d35'])
    axes[1].set_xticks(range(4), ['IID\np=.1', 'IID\np=.3', 'IID\np=.5', 'Episode-constant\np=.3'])
    axes[1].set_ylabel('Experiments with estimated CVR > 2 (%)')
    axes[1].set_title('SYNTHETIC independent A/C processes\nCVR > 2 is an illustration, never a reliability gate')
    fig.tight_layout(); fig.savefig(output/'precision.svg'); fig.savefig(output/'precision.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for policy, color in [('narrow', '#226d9e'), ('conservative', '#b25d35')]:
        for coverage, style in [(1., '-'), (.8, '--')]:
            values = [next(s for s in summaries if s['policy'] == policy and s['measurement'] == 'absolute_return' and s['history'] == h and s['quantile'] == .9 and s['coverage'] == coverage) for h in [60, 252]]
            axes[0].plot([60, 252], [s['common_calendar_decline_available_stock_dates'] for s in values],
                         color=color, linestyle=style, marker='o', label=f'{policy}; {coverage:.0%} history')
    axes[0].set_xticks([60, 252]); axes[0].set_xlabel('Historical window, sessions')
    axes[0].set_ylabel('Eligible stock-dates on shared evaluation calendar')
    axes[0].set_title('Coverage after a common warmup\nAbsolute-return q=.90; February 14, 2014 onward')
    axes[0].legend(fontsize=8)
    for label, color in [('less_severe', '#226d9e'), ('more_severe', '#b25d35')]:
        values = [next(s for s in summaries if s['policy'] == 'conservative' and s['measurement'] == m and s['history'] == 60 and s['quantile'] == .9 and s['coverage'] == 1.) for m in measures]
        axes[1].plot(range(4), [s['severity_strata'][label]['stress_frequency']['quantiles']['median']*100 for s in values],
                         marker='o', color=color, label=label.replace('_', ' '))
    axes[1].set_xticks(range(4), ['Absolute\nreturn', 'Downside', 'Intraday\nrange', 'Trailing\n5-session RV'])
    axes[1].set_ylabel('Median stock stress frequency (%)')
    axes[1].set_title('Discovery severity diagnostic, not causal adjustment\nComplete 60-session history, q=.90, conservative')
    axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(output/'coverage-and-severity.svg'); fig.savefig(output/'coverage-and-severity.png', dpi=160); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-run', required=True)
    parser.add_argument('--design', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.clean_run, args.design, args.output), indent=2))
