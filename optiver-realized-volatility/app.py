"""Private research review UI: no fallback observations or invented findings."""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Optiver · Research 002', layout='wide')
st.title('Project 002 · Conditional vulnerabilities')
st.caption('Human-led quantitative research · AI-assisted implementation')
st.info('Research hypothesis: stocks may share vulnerabilities in specific conditions even when their overall behavior differs. This is untested.')
run_name = st.sidebar.text_input('Private research run folder', value='discovery-001')
if not run_name or Path(run_name).name != run_name or run_name in {'.', '..'}:
    st.error('Enter a single folder name inside artifacts/.')
    st.stop()
run = ROOT / 'artifacts' / run_name
if not (run / 'audit.json').is_file() or not (run / 'features.parquet').is_file():
    st.warning('No empirical findings are available. Official data access and an approved discovery manifest are required. No synthetic data is shown.')
    st.write('Read research/PROTOCOL.md and research/DECISIONS.md before running the exploration command in README.md.')
    st.stop()
audit = json.loads((run / 'audit.json').read_text())
if audit.get('status') != 'target-free-feature-exploration' or audit.get('labels_read') is not False:
    st.error('This UI requires a target-free feature exploration run.')
    st.stop()
data = pd.read_parquet(run / 'features.parquet')
if 'target' in data:
    st.error('Target data is not permitted in this initial review UI.')
    st.stop()
st.caption(f"Discovery decision: {audit['decision_id']} · {audit['stock_window_rows']:,} stock/window observations. Source provenance is in the private audit record.")
symbols = st.multiselect('Anonymous stocks', sorted(data.stock_id.unique()), default=sorted(data.stock_id.unique()))
view = data[data.stock_id.isin(symbols)]
if view.empty:
    st.info('Select at least one stock.')
    st.stop()
metric = st.selectbox('Observed indicator', ['mid_rv', 'wap_rv', 'spread_time_mean', 'depth_time_mean', 'abs_imbalance_mean', 'book_updates', 'trade_volume', 'order_count'])
st.plotly_chart(px.box(view, x=view.stock_id.astype(str), y=metric, title='Stock-specific distributions · approved discovery windows'), width='stretch')
st.plotly_chart(px.scatter(view, x='spread_time_mean', y='mid_rv', color=view.stock_id.astype(str), title='Liquidity and observed RV · not future forecast performance'), width='stretch')
st.warning('These are descriptive associations from observed windows. No conditional peers, predictive gains, or causal effects have been established.')
st.write('Lead researcher: What do you notice, and what alternative explanation could produce the same pattern? Record your interpretation before requesting the next analysis.')
