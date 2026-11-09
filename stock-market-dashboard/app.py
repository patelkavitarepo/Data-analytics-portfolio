"""Interactive stock market analytics dashboard."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from market.store import ingest, query, connect
from market.analytics import analyze

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data/market.sqlite'
st.set_page_config(page_title='Stock Market Analytics', page_icon='📈', layout='wide')
st.markdown('''<style>.block-container{padding-top:4rem}h1{letter-spacing:-.04em}
[data-testid="stMetric"]{background:#152237;color:#e8eef6;padding:18px;border-radius:12px}
</style>''', unsafe_allow_html=True)
st.caption('MARKET LAB / DATA ANALYTICS PORTFOLIO')
st.title('Stock Market Analytics Dashboard')
st.write('Explore performance. Understand risk. Compare the evidence.')
try:
    if not DB.exists():
        ingest(DB, pd.read_csv(ROOT / 'data/history.csv'))
    with connect(DB) as con:
        catalog = pd.read_sql_query('SELECT symbol, MIN(date) first, MAX(date) last, COUNT(*) rows FROM prices GROUP BY symbol', con)
    if catalog.empty:
        st.error('Database is empty. Run python -m market.ingest to load data.')
        st.stop()
except Exception as exc:
    st.error(f'Unable to load market database: {exc}')
    st.stop()

with st.sidebar:
    st.header('Research controls')
    symbols = st.multiselect('Stocks', catalog.symbol.tolist(), default=catalog.symbol.tolist())
    lo = pd.to_datetime(catalog['first'].min()).date()
    hi = pd.to_datetime(catalog['last'].max()).date()
    dates = st.date_input('Analysis period', value=(max(lo, hi.replace(year=hi.year-2)), hi), min_value=lo, max_value=hi)
    window = st.select_slider('Volatility window (sessions)', [10, 21, 63], value=21)
    st.divider()
    st.caption('Bundled source: Plotly historical S&P 500 dataset (2013–2018). Not live quotes. USD. Custom SQLite imports may extend this snapshot; see README for provenance and limitations.')
    st.caption(f'Available: {lo} → {hi}')
if not symbols:
    st.info('Select at least one stock to begin.')
    st.stop()
if len(dates) != 2 or dates[0] >= dates[1]:
    st.info('Select a start and end date with start before end.')
    st.stop()
rows = query(DB, symbols, *dates)
try:
    result = analyze(rows, window)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()
s = result['summary']
focus = st.selectbox('Featured stock', symbols)
cols = st.columns(4)
for col, label in zip(cols, ['Price return', 'Annualized return', 'Annualized volatility', 'Max drawdown']):
    col.metric(label, f'{s.loc[focus, label]:.2%}')
st.caption(f"Shared observations: {len(result['prices']):,} · {result['prices'].index.min().date()} → {result['prices'].index.max().date()} · No missing-price forward filling")

def line(frame, title, percent=False):
    fig = px.line(frame, title=title, color_discrete_sequence=['#24b6a6', '#619bff', '#f6bc60', '#e98bab'])
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text='', hovermode='x unified', height=410, yaxis_title='')
    if percent:
        fig.update_yaxes(tickformat='.0%')
    st.plotly_chart(fig, width='stretch')

performance, risk, prices_tab, data_tab = st.tabs(['Performance', 'Risk & relationships', 'Price explorer', 'Data & methodology'])
with performance:
    line(result['growth'] * 100, 'Growth of $100 · shared starting date')
    st.dataframe(s.style.format({c: '{:.2%}' for c in s.columns if c != 'Observations'}), width='stretch')
with risk:
    line(result['drawdown'], 'Decline from the running peak', True)
    line(result['rolling_volatility'], f'{window}-session annualized volatility', True)
    st.plotly_chart(px.imshow(result['correlation'], zmin=-1, zmax=1, color_continuous_scale='RdBu', text_auto='.2f', title='Daily return correlation'), width='stretch')
with prices_tab:
    price_rows = rows[rows.symbol == focus]
    fig = go.Figure(go.Candlestick(x=price_rows.date, open=price_rows.open, high=price_rows.high, low=price_rows.low, close=price_rows.close, name=focus))
    fig.update_layout(title=f'{focus} · OHLC prices (USD)', template='plotly_dark', height=500)
    st.plotly_chart(fig, width='stretch')
    st.plotly_chart(px.bar(price_rows, x='date', y='volume', title=f'{focus} · daily share volume'), width='stretch')
with data_tab:
    st.write('Returns use closing prices. Annualized volatility uses sample daily standard deviation × √252. Annualized return uses elapsed calendar years. Drawdown measures loss from the highest close since the selected start date.')
    st.warning('Historical snapshot only. Adjustment status is unverified; these are price-based results, not dividend-reinvested total returns. A selected window resets the drawdown peak. Past performance does not predict future returns.')
    st.dataframe(rows, width='stretch', hide_index=True)
    st.download_button('Download filtered observations (CSV)', rows.to_csv(index=False), 'market-observations.csv', 'text/csv')
    st.caption('SQL daily_return uses the preceding stored trading observation, including one before the selected start date. Charts and summary recalculate returns within the selected shared-date window.')
