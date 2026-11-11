"""Independent, offline page; no empirical-panel imports or provider calls."""
import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from markowitz.synthetic import (ANNUAL_MEANS, ASSETS, SCENARIOS, WARNING, LabConfig,
                                 construct, json_safe, labeled, run)

st.set_page_config(page_title='Synthetic scenario lab | Project 006', page_icon='⚗', layout='wide')
st.title('Synthetic scenario lab')
st.error(WARNING)
st.write('Constructed optimizer stress laboratory. No market inputs, ETF proxies, historical analogues or investable forecasts. Nothing here authorizes real-data use or changes protocol 006-v1.')
st.info('ETF and French-library permissions remain unresolved. The original ETF study and real holdout remain blocked and untouched. Synthetic later steps are not the historical holdout.')


@st.cache_data(max_entries=8, show_spinner=False)
def cached_run(name, config):
    return run(name, config)


def table(title, frame):
    st.markdown(f'**{WARNING} · {title}**')
    st.dataframe(labeled(frame.round(6)), use_container_width=True)


def chart(title, fig):
    st.caption(f'{WARNING} · {title}')
    fig.update_layout(title={'text': f'{WARNING}<br>{title}', 'font': {'size': 11}}, margin={'t': 75},
                      legend_title_text='Synthetic allocation', font={'size': 11})
    st.plotly_chart(fig, use_container_width=True)


with st.form('synthetic_controls'):
    name = st.selectbox('Constructed scenario', list(SCENARIOS), format_func=lambda key: key.replace('_', ' ').title())
    seed = st.number_input('Synthetic seed (no market calibration)', min_value=0, max_value=2**32-1, value=6006, step=1)
    training = st.selectbox('Synthetic training observations', [126, 504, 1008], index=1)
    draws = st.slider('Training-only IID bootstrap draws (bounded)', 2, 30, 20)
    cap = st.slider('Lab-only cap (does not alter ETF default)', .20, 1., .35, .05)
    submitted = st.form_submit_button('Run synthetic experiment')
if submitted:
    config = LabConfig(seed=int(seed), train_steps=int(training), bootstrap_draws=int(draws), cap=float(cap))
    with st.spinner('Running bounded, training-only synthetic solves…'):
        st.session_state['synthetic_result'] = (name, config, cached_run(name, config))
if 'synthetic_result' not in st.session_state:
    st.warning('No experiment run yet. Choose constructed assumptions and run; no live data is needed.')
    st.stop()

name, config, result = st.session_state['synthetic_result']
st.subheader(f'{WARNING} · {name.replace("_", " ").title()}')
st.caption('Outputs remain for the last submitted settings; submit again to apply changed controls.')
st.write(SCENARIOS[name])
st.write(f'Seed {config.seed} · training steps 0–{config.train_steps-1} · later steps {config.train_steps}–{config.train_steps+config.future_steps-1} · cap {config.cap:.0%} · assumed effective annual risk-free {config.annual_rf:.0%}.')
st.caption('Six abstract assets A–F, with arbitrary specified means/volatilities. Independent Gaussian factor/idiosyncratic innovations; common random numbers pair the scenarios. No clipping of invalid returns. No fat tails, serial dependence, liquidity or realistic market calibration is modeled.')

scenario = construct(name, config)
with st.expander('Constructed inputs and correlation matrices'):
    table('Assumed generator inputs (not estimates)', pd.DataFrame({
        'true_annual_arithmetic_mean': ANNUAL_MEANS, 'estimator_mean_bias_annual': scenario.mean_bias,
        'true_training_volatility': np.sqrt(np.diag(scenario.train_covariance)),
        'true_later_volatility': np.sqrt(np.diag(scenario.future_covariance))}, index=ASSETS))
    for phase, cov in [('Training', scenario.train_covariance), ('Later path', scenario.future_covariance)]:
        vol = np.sqrt(np.diag(cov))
        correlation = pd.DataFrame(cov / np.outer(vol, vol), index=ASSETS, columns=ASSETS)
        chart(f'Assumed {phase.lower()} correlations', px.imshow(correlation, zmin=-1, zmax=1, color_continuous_scale='RdBu_r'))

table('Fitted target weights; valid candidates only', result['weights'])
table('Target changes from paired baseline (percentage-point units when multiplied by 100)', result['changes_from_baseline'])
chart('Target weights', px.bar(result['weights'].rename_axis('asset').reset_index(), x='asset',
                              y=list(result['weights'].columns), barmode='group', labels={'value': 'Target weight'}))
st.caption('Min-vol solves checked convex minimum variance; max Sharpe is a deterministic multi-start local candidate. Equal weights use the same assumptions. No winner is selected. Target caps can be exceeded by drifting holdings between resets.')

table('Training-only estimated annual moments and target concentration', result['estimated'].drop(columns=['constructed_future_volatility']))
table('Known constructed later volatility of frozen weights (not estimated from the later sample)', result['estimated'][['constructed_future_volatility']])
st.caption('Estimated Sharpe uses annualized arithmetic mean excess return and sample covariance. Generator volatility is a known scenario assumption, not an empirical estimate or forecast. HHI is sum of squared target weights.')

table('Realized synthetic later-path metrics; same costs for all allocations', result['realized'])
st.caption('Separate from training estimates: CAGR is geometric, volatility uses sample daily SD, Sharpe uses daily excess returns. 252 assumed steps/year. Targets reset every 21 steps before returns, drift between resets; initial purchase is charged. Costs are 0 or 10 bps × gross traded notional, using a proportional-cost approximation. This is not an ETF backtest or actual execution model.')
for cost in (0., 10.):
    paths = pd.DataFrame({strategy: series for (strategy, c), series in result['paths'].items() if c == cost})
    if paths.empty:
        continue
    wealth = (1 + paths).cumprod()
    anchor = pd.DataFrame(1., index=[config.train_steps - 1], columns=wealth.columns)
    chart(f'Later synthetic wealth · {cost:g} bps', px.line(pd.concat([anchor, wealth]), labels={'index': 'Synthetic step', 'value': 'Wealth from 1'}))
    dd = wealth / wealth.cummax().clip(lower=1) - 1
    chart(f'Later synthetic drawdown · {cost:g} bps', px.line(pd.concat([anchor * 0, dd]), labels={'index': 'Synthetic step', 'value': 'Drawdown'}))

st.subheader(f'{WARNING} · Training-only weight instability')
table('Bootstrap summary', result['bootstrap']['summary'])
st.caption('IID resampling preserves each contemporaneous asset row but destroys time ordering; it does not model regime shifts or serial dependence and is not a confidence interval. Mean L1 is sum(abs(draw weights − original fitted weights)); half-L1 is a notional target reallocation, not realized path turnover. Dispersion is mean per-asset sample SD across successful draws. Failed draws are counted and excluded, never imputed as zero weights.')
samples = []
for strategy, frame in result['bootstrap']['samples'].items():
    if not frame.empty:
        samples.append(frame.assign(strategy=strategy).melt(id_vars='strategy', var_name='asset', value_name='weight'))
if samples:
    chart('Successful bootstrap weight distributions', px.box(pd.concat(samples), x='asset', y='weight', color='strategy'))
failed = [key for key, diag in result['manifest']['diagnostics'].items() if not diag['success']]
if failed:
    st.warning(f'{WARNING} · Failed fitted candidates omitted: {failed}. See diagnostics.')
with st.expander('Reproducibility, failures and solver diagnostics'):
    table('Every bootstrap draw and strategy, including failures', result['bootstrap']['log'])
    st.caption(WARNING)
    st.json(json_safe(result['manifest']), expanded=False)
st.download_button(f'{WARNING} · Download run manifest', json.dumps(json_safe(result['manifest']), indent=2, allow_nan=False), 'SYNTHETIC_manifest.json', 'application/json')
for key in ('weights', 'changes_from_baseline', 'estimated', 'realized'):
    st.download_button(f'{WARNING} · Download {key}', labeled(result[key]).to_csv(), f'SYNTHETIC_{key}.csv', 'text/csv')
st.download_button(f'{WARNING} · Download bootstrap diagnostics', labeled(result['bootstrap']['log']).to_csv(), 'SYNTHETIC_bootstrap_log.csv', 'text/csv')
st.warning(f'{WARNING} · This run supports questions about optimizer fragility under constructed assumptions only. It cannot establish market superiority, investment suitability or permission to use provider data. Keep empirical model choices frozen.')
