"""Run with streamlit run markowitz-portfolio-optimization/app.py."""
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from markowitz.analytics import frontier, moments, optimize, portfolio_stats
from markowitz.data import TICKERS, audit_prices, completed_session, download_prices, read_csv
from markowitz.research import PROTOCOL, evaluate, wealth_and_drawdown
from markowitz.verification import verify_source, source_review_template

st.set_page_config(page_title='The Efficient Frontier | Project 006', page_icon='◉', layout='wide')
st.title('The Efficient Frontier')
st.caption('PROJECT 006 · MARKOWITZ PORTFOLIO OPTIMIZATION · EDUCATIONAL RESEARCH')
st.page_link('pages/1_Synthetic_scenario_lab.py', label='Synthetic scenario lab — constructed data only', icon='⚗')
st.markdown('Can constrained optimization improve **out-of-sample risk-adjusted performance** over equal weights? The evidence must answer; optimization alone does not.')
st.info('No investment recommendation. Real adjusted ETF prices only. No sample performance is substituted when data are unavailable.')


@st.cache_data(ttl=21600, show_spinner='Retrieving adjusted daily prices…')
def live_data(cutoff_key):
    return download_prices()


with st.sidebar:
    st.header('Research controls')
    mode = st.radio('Data source', ['Live Yahoo Finance', 'Upload adjusted-price CSV'])
    assets = st.multiselect('Diversified portfolio assets', TICKERS, default=list(TICKERS))
    cap = st.slider('Maximum target weight per ETF', .15, 1., .35, .05)
    rf = st.number_input('Assumed constant effective annual risk-free rate (%)', min_value=0., max_value=20., value=2., step=.25) / 100
    cost = st.number_input('Sensitivity cost (bps per gross traded notional)', min_value=0., max_value=100., value=10., step=1.)
    st.caption('Risk-free rate is a user assumption, not a historical Treasury series. Defaults fixed before observing results. Changes are exploratory and consume the holdout.')

st.header('1 · Case overview & provenance')
st.write('SPY / QQQ / IWM overlap in US equities; EFA and EEM add international equities; TLT, GLD and VNQ represent long Treasury bonds, gold and US real estate. All predate 2016, but availability must still be checked. This selected surviving universe cannot establish freedom from selection or survivorship bias.')
st.caption('Protocol 006-v1: train 2016–2022 → validation 2023–2024. Refit both prespecified objectives on 2016–2024 → holdout 2025 onward. No strategy winner or hyperparameter is selected automatically.')
prices = metadata = None
as_of = None
if mode == 'Live Yahoo Finance':
    st.warning('YAHOO RIGHTS BLOCKED: no express prior collection permission is recorded. Successful past downloads did not establish permission. Use only separately authorized CSV inputs; see DATA_RIGHTS.md.')
    if st.button('Load / refresh live data', disabled=True):
        live_data.clear()
        try:
            st.session_state['live_dataset'] = live_data(str(completed_session().date()))
        except Exception as exc:
            st.session_state.pop('live_dataset', None)
            st.error(f'LIVE DATA UNAVAILABLE: {exc}')
    if 'live_dataset' in st.session_state:
        st.session_state.pop('live_dataset', None)
else:
    upload = st.file_uploader('CSV: Date (YYYY-MM-DD), SPY, QQQ, IWM, EFA, EEM, TLT, GLD, VNQ', type=['csv'])
    source = st.text_input('CSV source / adjustment method / retrieval date')
    as_of = st.text_input('Historical as_of cutoff (YYYY-MM-DD; explicit archived snapshot date)', value='')
    st.caption('Every session from 2016 through as_of is audited. Cutoff cannot exceed observed prices or the latest complete session. Missing intervals cannot be hidden by moving the cutoff.')
    confirmed = st.checkbox('I confirm these are real historical split/dividend-adjusted prices and I am authorized to analyze them here.')
    st.caption('Analysis permission does not establish permission to redistribute, publish or bundle these prices. A checkbox records an assertion and grants no provider rights. Raw prices are never offered for download.')
    if upload and confirmed and source.strip() and as_of.strip():
        try:
            raw = upload.getvalue()
            prices = read_csv(raw)
            metadata = {'vendor': 'User-supplied CSV — provenance asserted by uploader', 'source': source,
                'loaded_utc': datetime.now(timezone.utc).isoformat(), 'file_sha256': hashlib.sha256(raw).hexdigest(),
                'timezone': 'Date-only XNYS sessions', 'adjustment': 'Uploader attests split/dividend adjustment'}
        except Exception as exc:
            st.error(f'INVALID CSV: {exc}')
if prices is None:
    st.warning('NO HISTORICAL DATA LOADED. Yahoo collection is blocked; upload an entitled historical CSV for audit. Performance remains gated by provider-rights and independent review.')
    st.stop()

st.json(metadata, expanded=False)
if len(assets) < 2 or len(assets) * cap < 1 - 1e-10:
    st.error('Infeasible selection: require at least two assets and number of assets × cap ≥ 1.')
    st.stop()
required = list(TICKERS)  # Verify the full prespecified source, even when exploring a subset.
try:
    clean, returns, audit, summary = audit_prices(prices, required, as_of=as_of)
except Exception as exc:
    st.error(f'DATA VALIDATION FAILED: {exc}')
    st.stop()
st.write(f'Observed common prices: **{clean.index.min().date()} → {clean.index.max().date()}** · latest eligible completed session: **{completed_session().date()}**')
st.write(f"Research as_of: **{summary['as_of']}** · snapshot last observation: **{summary['snapshot_last_observed']}**")
if summary['source_is_stale'] or summary['historical_as_of']:
    st.warning('HISTORICAL SNAPSHOT: not current market data. Results, if verified, end at the explicitly recorded as_of; calendar period boundaries remain fixed.')
st.caption('Conservative end rule excludes the current New York date, including after close. XNYS calendar. 252 sessions/year. No forward/back filling. Prices align on common valid sessions; returns spanning a missing exchange session are excluded.')

st.header('2 · Evidence audit')
st.dataframe(audit, use_container_width=True)
st.json(summary, expanded=False)
st.download_button('Download quality audit CSV', audit.to_csv(), 'quality_audit.csv', 'text/csv')
st.download_button('Download provenance & complete audit', json.dumps({'provenance': metadata, 'audit': summary, 'protocol': PROTOCOL}, indent=2), 'provenance_audit.json', 'application/json')
if summary['lost_price_rows']:
    st.error('INCOMPLETE HISTORY: performance evaluation blocked. Review missing sessions and calendar mismatches above; supply complete real data. No missing interval is silently omitted from a backtest.')
    st.stop()
st.download_button('Download unverified source-review template (no prices)', json.dumps(source_review_template(summary), indent=2), 'source_review_template.json', 'application/json')
review_upload = st.file_uploader('Source verification JSON (all eight ETFs; independent adjustment/spot checks and analysis rights)', type=['json'])
if review_upload:
    try:
        st.session_state['source_review'] = json.loads(review_upload.getvalue())
    except (ValueError, UnicodeDecodeError) as exc:
        st.error(f'INVALID SOURCE REVIEW: {exc}')
        st.stop()
try:
    source_verification = verify_source(prices, summary, st.session_state.get('source_review'))
except (ValueError, TypeError, KeyError) as exc:
    st.warning(f'SOURCE UNVERIFIED: {exc}. No performance analysis computed. See README source-review format.')
    st.stop()
st.json(source_verification, expanded=False)
with st.sidebar:
    holdout_count = len(returns.loc['2025-01-01':])
    reveal = st.checkbox('Reveal final holdout (2025 onward)', value=False, disabled=holdout_count < 60)
    if holdout_count < 60:
        st.caption('Holdout reveal unavailable: at least 60 audited holdout sessions required.')
    if reveal:
        st.warning('Once inspected, this holdout is no longer untouched. Do not tune settings to its results.')
try:
    train = returns.loc['2016':'2022', assets]
    mu, cov = moments(train)
    stats = pd.DataFrame({'training_arithmetic_mean_annualized': mu, 'training_volatility_annualized': np.sqrt(np.diag(cov))})
    st.caption('Asset statistics and heatmaps below use training data only (2016–2022).')
    st.dataframe(stats.style.format('{:.2%}'), use_container_width=True)
    st.plotly_chart(px.imshow(train.corr(), zmin=-1, zmax=1, color_continuous_scale='RdBu_r', title='Training correlations'), use_container_width=True)
    st.plotly_chart(px.imshow(cov, title='Training annualized sample covariance (decimal return²)'), use_container_width=True)
    st.header('3 · Efficient frontier — IN SAMPLE, 2016–2022')
    curve, failures = frontier(mu, cov, cap)
    fig = go.Figure(go.Scatter(x=curve['volatility'], y=curve['expected_return'], mode='lines', name='Feasible efficient frontier'))
    lab_weights = {}
    for name in ('min_vol', 'max_sharpe', 'equal_weight'):
        w = np.full(len(assets), 1 / len(assets)) if name == 'equal_weight' else optimize(mu, cov, cap, name, rf).weights
        lab_weights[name] = w
        s = portfolio_stats(w, mu, cov, rf)
        fig.add_scatter(x=[s['volatility']], y=[s['expected_return']], mode='markers', name=name)
    fig.update_layout(xaxis_title='Annualized volatility', yaxis_title='Expected arithmetic annual return', xaxis_tickformat='.0%', yaxis_tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Sample estimates are not forecasts. Minimum variance is a convex problem; SLSQP is checked numerically. Max Sharpe is a deterministic multi-start local solver candidate, without a global-optimality claim. Failed frontier points are excluded.')
    if failures:
        st.warning(f'{len(failures)} frontier targets failed; omitted.')
        st.json(failures)

    st.header('4 · Out-of-sample portfolio comparison')
    st.caption('Monthly reset to fixed targets on the first session, using prior-close holdings; weights drift between resets. Every strategy starts afresh at each evaluation boundary. SPY uses the identical return dates and cost rate, including initial purchase. Costs = bps × sum(abs(trades))/NAV. Notional includes both buys and sells; inception = 1. No taxes, financing or market impact.')
    # Do not compute final holdout until explicitly revealed.
    evaluation_returns = returns if reveal else returns.loc[:'2024-12-31']
    if not reveal:
        # Evaluate validation without touching holdout observations or fitting holdout weights.
        from markowitz.research import evaluate_validation
        free = evaluate_validation(evaluation_returns, assets, cap, rf, 0.)
        costly = evaluate_validation(evaluation_returns, assets, cap, rf, cost)
    else:
        free = evaluate(evaluation_returns, assets, cap, rf, 0.)
        costly = evaluate(evaluation_returns, assets, cap, rf, cost)
    for period in free:
        st.subheader(period.title())
        result = free[period]
        st.caption(f"Fit {result['fit_start']}–{result['fit_end']}; evaluate {result['test_start']}–{result['test_end']}. Target cap does not constrain interim drift; SPY is an uncapped external benchmark.")
        st.dataframe(result['weights'].style.format('{:.1%}'), use_container_width=True)
        for label, bundle in [('Cost-free', free[period]), (f'{cost:g} bps sensitivity', costly[period])]:
            st.markdown(f'**{label}**')
            st.dataframe(bundle['metrics'], use_container_width=True)
            st.download_button(f'Download {period} {label} metrics', bundle['metrics'].to_csv(), f'{period}_{label}_metrics.csv', 'text/csv')
            wealth, dd = wealth_and_drawdown(bundle['returns'])
            anchor = pd.DataFrame(1., index=[bundle['returns'].index[0] - pd.Timedelta(days=1)], columns=wealth.columns)
            st.plotly_chart(px.line(pd.concat([anchor, wealth]), title=f'{period.title()} · {label} · wealth from 1'), use_container_width=True)
            st.plotly_chart(px.line(pd.concat([anchor * 0, dd]), title=f'{period.title()} · {label} · drawdown'), use_container_width=True)
        with st.expander(f'{period.title()} solver diagnostics & reproducibility'):
            st.json(result['diagnostics'])
            manifest = dict(protocol=PROTOCOL, selected_assets=assets, cap=cap, assumed_rf=rf, cost_bps=cost,
                provenance=metadata, as_of=summary['as_of'], source_verification=source_verification, audit=summary, fit_start=result['fit_start'], fit_end=result['fit_end'],
                test_start=result['test_start'], test_end=result['test_end'], diagnostics=result['diagnostics'])
            st.download_button(f'Download {period} run manifest', json.dumps(manifest, indent=2), f'{period}_manifest.json', 'application/json')
            st.download_button(f'Download {period} weights', result['weights'].to_csv(), f'{period}_weights.csv', 'text/csv')
            st.download_button(f'Download {period} net returns', costly[period]['returns'].to_csv(), f'{period}_net_returns.csv', 'text/csv')
except (ValueError, KeyError) as exc:
    st.error(f'ANALYSIS BLOCKED: {exc}')

st.header('5 · Sensitivity, limitations & owner interpretation')
st.write('Compare the fixed 35% cap with alternatives only as exploratory sensitivity; record each setting before revealing its holdout. Expected returns are noisy; sample covariance can be ill-conditioned. Shrinkage and walk-forward studies are deferred. The fixed ETF universe, retrospective adjusted prices, constant risk-free assumption, one holdout, execution approximation and vendor revisions limit inference.')
st.write('Owner review: Does any validation advantage persist into holdout and after equal transaction costs? Is lower volatility purchased with concentration or lower return? Is the difference economically meaningful? No automated investment conclusion is drawn.')
