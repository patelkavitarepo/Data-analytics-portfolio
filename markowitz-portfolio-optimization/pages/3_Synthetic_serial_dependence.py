"""Read-only independent synthetic serial-dependence investigation; no refits."""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from markowitz.synthetic import WARNING
from markowitz.synthetic_serial import load_report

st.set_page_config(page_title='Synthetic serial dependence | Project 006', page_icon='⚗', layout='wide')
st.title('Synthetic serial-dependence investigation')
st.error(WARNING)
st.write('Does IID row bootstrap mischaracterize allocation instability under constructed temporal dependence? This independent page displays a fixed predeclared report, without rerunning optimization or retrieving data.')
st.info('Previous synthetic experiments and the original ETF study remain unchanged. Market-data permissions remain unresolved; no empirical holdout has been evaluated.')
try:
    report = load_report()
except (OSError, ValueError, KeyError) as exc:
    st.warning(f'{WARNING} · Report unavailable or invalid: {exc}. Reproduce with python -m markowitz.synthetic_serial. No empirical fallback.')
    st.stop()
tables = {k: pd.DataFrame(v) for k, v in report['tables'].items()}
st.caption('Seeds 6006–6010 · 504 training steps · phi 0 / .5 · 15 draws/method · circular five-row blocks, last block truncated · six abstract assets · 35% cap · assumed annual RF 2%. No future sample is generated.')
st.caption('Stationary Gaussian AR initialization preserves theoretical one-step marginal means/covariance across phi. Sample moments need not match. Methods resample complete contemporaneous vectors from the same training sample; shared random starts are not identical bootstrap samples. Circular 503→0 joins are artificial.')


def table(title, frame):
    st.markdown(f'**{WARNING} · {title}**')
    st.dataframe(frame.round(6), use_container_width=True)


table('Across-seed paired differences: MBB minus IID, median / min / max', tables['aggregate_differences'])
st.caption('Half-L1 is target reassignment, not trading turnover. Predeclared materiality flag: absolute difference in mean half-L1 ≥ .02 (two percentage points). This descriptive threshold is not a statistical test. Five-seed ranges are not confidence intervals; every seed is retained.')
paired = tables['paired_differences']
fig = px.scatter(paired, x='seed', y='delta_mean_half_L1', color='strategy', facet_row='phi', labels={'delta_mean_half_L1': 'MBB minus IID mean half-L1'})
fig.add_hline(y=0, line_dash='dot')
fig.add_hline(y=.02, line_dash='dash')
fig.add_hline(y=-.02, line_dash='dash')
fig.update_layout(title={'text': f'{WARNING}<br>Paired method differences by seed and AR coefficient', 'font': {'size': 11}}, margin={'t': 85})
st.caption(f'{WARNING} · Paired method differences; dashed materiality thresholds')
st.plotly_chart(fig, use_container_width=True)
table('Every seed: paired method differences and materiality flags', paired)
table('Every seed/method: instability, concentration, caps and denominators', tables['summary'])
st.caption('Quantiles/SD summarize successful bootstrap draws conditional on one training sample. They are not confidence bounds. Missing reference or failed fits produce unavailable distances, not zeros. Equal-weight distance is zero by construction; it does not measure uncertainty in equal-weight risk.')
with st.expander('Across-seed method summaries'):
    table('Method medians and descriptive ranges', tables['aggregate_methods'])
with st.expander('Draw-level checks, failures and resampling audit trail'):
    table('Every draw and strategy, including failures', tables['bootstrap_log'])
    st.caption(f'{WARNING} · Full ordered source indices, hashes and block starts are in the JSON/CSV exports.')
    st.json(report['manifest'], expanded=False)
st.download_button(f'{WARNING} · Download fixed serial investigation', json.dumps(report, indent=2, allow_nan=False), 'SYNTHETIC_serial_report.json', 'application/json')
for key in tables:
    st.download_button(f'{WARNING} · Download {key}', tables[key].to_csv(index=False), f'SYNTHETIC_serial_{key}.csv', 'text/csv')
st.warning(f'{WARNING} · Only five seeds, 15 draws and one five-row block length. Block joins truncate dependence; caps and local optima can mask or amplify variability. Annualized sample covariance remains the fixed objective, not long-horizon AR risk. No coverage study, method winner or market conclusion.')
