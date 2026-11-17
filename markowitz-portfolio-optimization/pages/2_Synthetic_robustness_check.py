"""Read-only predeclared synthetic study; no optimizer, provider or holdout calls."""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from markowitz.synthetic import WARNING
from markowitz.synthetic_robustness import load_report

st.set_page_config(page_title='Synthetic robustness check | Project 006', page_icon='⚗', layout='wide')
st.title('Focused synthetic robustness check')
st.error(WARNING)
st.write('Predeclared paired experiment: unseen positive correlation jump, five seeds and two nested training windows. This page displays the fixed report; it does not refit, search seeds, retrieve data or reveal an empirical holdout.')
st.info('Original lab results and 006-v1 ETF settings remain unchanged. Data permissions remain unresolved. These are constructed conditional diagnostics, not forecasts, confidence intervals or market evidence.')
try:
    report = load_report()
except (OSError, ValueError, KeyError) as exc:
    st.warning(f'{WARNING} · Report unavailable or invalid: {exc}. Reproduce with python -m markowitz.synthetic_robustness. No empirical fallback.')
    st.stop()
manifest = report['manifest']
tables = {key: pd.DataFrame(rows) for key, rows in report['tables'].items()}
st.caption('Fixed seeds 6006–6010 · trailing windows 126/504 ending at step 503 · future steps 504–755 · 10 training-only IID draws/case · cap 35% · assumed RF 2% · cost-free and 10 bps · 21-step target resets.')
st.caption('Paired future innovations are identical across scenarios and windows. Training correlation is +0.35; stationary future +0.35; unseen-jump future +0.85. Weights and bootstrap are fitted once per training case and reused unchanged for both future conditions.')


def table(title, frame):
    st.markdown(f'**{WARNING} · {title}**')
    st.dataframe(frame.round(6), use_container_width=True)


def chart(title, fig):
    st.caption(f'{WARNING} · {title}')
    fig.update_layout(title={'text': f'{WARNING}<br>{title}', 'font': {'size': 11}}, font={'size': 11}, margin={'t': 85})
    st.plotly_chart(fig, use_container_width=True)


def subset(key, metrics):
    frame = tables[key]
    return frame.loc[frame['metric'].isin(metrics)]


table('Across-seed known covariance risk: median / min / max, with valid seed counts', subset('aggregate_risk', ['paired_target_L1', 'known_volatility_ratio']))
st.caption('Analytically known covariance risk uses the stipulated generator, not future sample estimates. Ratio = jump volatility / baseline volatility on the same fitted target. Lower inflation ratios do not imply lower absolute risk or a preferred strategy.')
valid_risk = tables['paired_risk'].query('available == True')
chart('Known future volatility inflation on unchanged targets', px.scatter(valid_risk, x='seed', y='known_volatility_ratio', color='strategy', facet_row='window', labels={'known_volatility_ratio': 'Jump / baseline volatility'}))
table('Every seed: paired target equality and known future risk', tables['paired_risk'].drop(columns=['fit_id', 'bootstrap_reuse_id']))

table('Concentration and bootstrap variability together', subset('aggregate_targets', ['HHI', 'effective_number', 'cap_count', 'bootstrap_mean_half_L1_reallocation', 'bootstrap_cap_binding_incidence', 'bootstrap_mean_cap_count']))
st.caption('HHI = sum(weight²); effective number = 1/HHI. Cap count uses |target weight − .35| ≤ 1e-7. Bootstrap cap incidence is the fraction of successful draws with at least one binding target, not an empirical probability or an interim exposure constraint.')
per_seed = tables['targets'].drop(columns=['fit_id', 'bootstrap_reuse_id', 'training_sha256'])
table('Every seed/window: fitted concentration, instability and cap incidence', per_seed)
chart('Training-only dispersion beside cap-binding incidence', px.scatter(tables['targets'].query('fit_success == True'),
    x='bootstrap_mean_half_L1_reallocation', y='HHI', color='strategy', facet_row='window',
    hover_data=['seed', 'bootstrap_cap_binding_incidence', 'cap_count'], labels={'bootstrap_mean_half_L1_reallocation': 'Mean half-L1 target distance'}))

table('Paired training-window sensitivity: all seeds', tables['window_changes'])
table('Across-seed window sensitivity: median / min / max', tables['aggregate_window_changes'])
st.caption('Short window is the latest 126 of the same 504-step training pool, not the old lab’s first 126 draws. Later innovations and source step ranges are fixed. Ten draws here do not replace the original seed-6006/20-draw result. Half-L1 is target reallocation, not path turnover. Longer windows need not improve every metric.')

table('Finite-path direction counts (five paired seeds, not independent futures)', tables['realized_direction_counts'])
table('Cost-matched later path comparison: every seed/window/strategy', tables['paired_paths'].drop(columns=['fit_id', 'bootstrap_reuse_id']))
with st.expander('Across-seed realized path medians and ranges'):
    table('Realized synthetic path summaries by cost', tables['aggregate_paths'])
st.caption('Realized volatility/drawdown/Sharpe/CAGR are noisy finite-path outcomes, separate from modeled covariance risk. Negative drawdown differences mean worse drawdown. Same cost rates and inception purchase treatment apply to all targets; traded amounts may differ with path drift. No winner is selected.')
with st.expander('Failures, caps and reproducibility'):
    table('All training-only bootstrap records, including failures', tables['bootstrap_log'])
    st.caption(WARNING)
    st.json(manifest, expanded=False)
st.download_button(f'{WARNING} · Download fixed investigation report', json.dumps(report, indent=2, allow_nan=False), 'SYNTHETIC_robustness_report.json', 'application/json')
for key in ('targets', 'paired_risk', 'paired_paths', 'window_changes', 'bootstrap_log'):
    st.download_button(f'{WARNING} · Download {key}', tables[key].to_csv(index=False), f'SYNTHETIC_robustness_{key}.csv', 'text/csv')
st.warning(f'{WARNING} · Gaussian/IID only; five fixed seeds and ten draws do not establish real-world confidence. Serial dependence and moving-block bootstrap remain a later investigation. Original market-data gates and holdout remain untouched.')
