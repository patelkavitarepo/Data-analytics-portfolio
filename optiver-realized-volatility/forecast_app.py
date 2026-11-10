"""Daily volatility research review: fixed real forecasts, no runtime training."""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from daily_study.forecast import MODELS, metrics
from daily_study.forecast_analysis import outcome_band, loss_concentration
from daily_study.forecast_snapshot import load_snapshot, return_path

ROOT=Path(__file__).resolve().parent
RESULTS=Path(os.environ.get('FORECAST_RESULTS_DIR',str(ROOT/'research/forecast-D008/results')))
LABELS={'M0':'Historical volatility','M1':'Stock-specific Ridge','M2':'Stock + market Ridge'}
COLORS={'Actual':'#647d91','M0':'#778899','M1':'#23857f','M2':'#c16a3c'}
GITHUB='https://github.com/patelkavitarepo/Data-analytics-portfolio'

st.set_page_config(page_title='Daily Volatility · Research 002',page_icon='📈',layout='wide',initial_sidebar_state='auto')
st.markdown('''<style>
.block-container { max-width: 1440px; padding-top: 4.5rem; padding-bottom: 3rem; }
div[data-testid="stMetric"] { background:rgba(113,128,150,.07); border:1px solid rgba(113,128,150,.25); border-radius:12px; padding:16px 18px; }
div[data-testid="stMetricLabel"] { font-size:.85rem; }
div[data-testid="stMetricValue"] { font-size:1.8rem; }
.eyebrow { font-size:.75rem; letter-spacing:.14em; color:#23857f; font-weight:700; }
h1 { letter-spacing:-.035em; } h2,h3 { letter-spacing:-.02em; }
div[data-testid="stTabs"] button { font-weight:600; }
@media(max-width:700px) { .block-container { padding:4.5rem 1rem 1rem; } h1 { font-size:1.9rem!important; } }
</style>''',unsafe_allow_html=True)
st.markdown('<div class="eyebrow">HUMAN-LED QUANTITATIVE RESEARCH · PROJECT 002</div>',unsafe_allow_html=True)
st.title('Daily stock volatility')
st.write('Five-session prediction and model failure analysis')
st.caption('2015 internal evaluation · D001–D006 frozen · 2016–2018 reserved · AI-assisted implementation')


@st.cache_data(show_spinner='Verifying the research snapshot…')
def cached_snapshot(path,version):
    return load_snapshot(path)


try:
    snapshot=cached_snapshot(str(RESULTS),(RESULTS/'manifest.json').stat().st_mtime_ns)
except (FileNotFoundError,ValueError,KeyError) as error:
    st.error('The verified research-results bundle is unavailable. No substitute or synthetic data is shown.')
    st.caption(str(error));st.stop()

data=snapshot['predictions'];fixed_scores=pd.DataFrame(snapshot['scores'])
cohort=pd.DataFrame(snapshot['cohort']);eligible_names=sorted(cohort.loc[cohort.eligible,'stock'])
headline_dates=data.loc[data.headline,'date']
minimum,maximum=headline_dates.min().date(),headline_dates.max().date()

st.sidebar.header('Explore the evidence')
policy=st.sidebar.radio('Cleaning policy',['conservative','narrow'],format_func=str.title)
scope=st.sidebar.radio('Stock scope',['All eligible stocks','Selected stocks'])
defaults=['AAPL'] if 'AAPL' in eligible_names else eligible_names[:1]
chosen=st.sidebar.multiselect('Selected stocks',eligible_names,default=defaults,disabled=scope=='All eligible stocks')
date_range=st.sidebar.date_input('Forecast origin dates',(minimum,maximum),min_value=minimum,max_value=maximum)
selected_models=st.sidebar.multiselect('Models on forecast chart',MODELS,default=MODELS,format_func=lambda m:LABELS[m])
st.sidebar.caption('Filters change the displayed sample. They never retrain models, change cleaning or remove observations from the fixed study scorecard.')
st.sidebar.markdown(f'[Research decisions]({GITHUB}/blob/feat/002-optiver-research/optiver-realized-volatility/research/DECISIONS.md)')

if len(date_range)!=2:
    st.info('Choose both forecast-date endpoints.');st.stop()
names=eligible_names if scope=='All eligible stocks' else chosen
if not names:
    st.info('Select at least one stock to explore the forecasts.');st.stop()
selected=data[(data.policy==policy)&data.stock.isin(names)&(data.date>=pd.Timestamp(date_range[0]))&(data.date<=pd.Timestamp(date_range[1]))]
view=selected[selected.headline].copy()
if view.empty:
    st.info('No common completed forecasts match these filters. Expand the date range or stock selection.');st.stop()
score=pd.DataFrame([dict(model=m,**metrics(view.actual,view[m])) for m in MODELS]).set_index('model')
st.caption(f'{len(view):,} common stock-date observations · {view.stock.nunique():,} stocks · {policy} cleaning · all three models evaluated on identical rows')
card_metric=st.radio('Metric shown in model cards',['RMSPE','MAE','RMSE'],horizontal=True)
metric_key=card_metric.lower()
cards=st.columns(3)
for column,model in zip(cards,MODELS):
    value=score.loc[model,metric_key]
    base=score.loc['M0',metric_key]
    change=(value/base-1)*100 if base else np.nan
    formatted=f'{value*100:.2f}'+('%' if metric_key=='rmspe' else ' pp')
    column.metric(LABELS[model],formatted,delta=None if model=='M0' else f'{change:+.1f}% error vs baseline',delta_color='inverse')
    if model!='M0':column.caption(f"Ridge strength {snapshot['selected_settings']['alphas'][model]:g} · selected using 2014 only")


def score_table(frame):
    table=frame.copy()
    table['Model']=[LABELS.get(m,m) for m in table.index]
    for key,label in [('rmspe','RMSPE (%)'),('mae','MAE (volatility pp)'),('rmse','RMSE (volatility pp)'),('bias','Bias (volatility pp)')]:
        table[label]=table[key]*100
    table['Observations']=table.n.astype(int)
    return table[['Model','RMSPE (%)','MAE (volatility pp)','RMSE (volatility pp)','Bias (volatility pp)','Observations']].reset_index(drop=True)


def chart_style(fig,height=370):
    fig.update_layout(height=height,margin=dict(l=12,r=16,t=48,b=20),
        font=dict(family='Arial, sans-serif'),legend=dict(orientation='h',y=-.18))
    return fig


performance,disagreements,failures,methods=st.tabs(['Forecasts & performance','Metric disagreements','Failure lab','Coverage & methodology'])
with performance:
    st.subheader('Measured performance')
    st.dataframe(score_table(score),hide_index=True,width='stretch')
    st.caption('MAE/RMSE use unannualized five-session volatility units. One pp is 0.01 volatility. RMSPE uses positive actuals only; zero targets remain in absolute metrics.')
    focus_names=sorted(view.stock.unique());focus_index=focus_names.index('AAPL') if 'AAPL' in focus_names else 0
    focus=st.selectbox('Stock to inspect',focus_names,index=focus_index)
    series=view[view.stock==focus].sort_values('date')
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=series.date,y=series.actual,name='Actual',line=dict(color=COLORS['Actual'],width=2.3),customdata=series.target_end.dt.strftime('%Y-%m-%d'),hovertemplate='%{x|%Y-%m-%d}<br>Actual: %{y:.2%}<br>Target ends: %{customdata}<extra></extra>'))
    for model in selected_models:
        fig.add_trace(go.Scatter(x=series.date,y=series[model],name=LABELS[model],line=dict(color=COLORS[model],width=1.5)))
    fig.update_layout(title=f'{focus} · forecast at the close, outcome over the next five sessions',yaxis_tickformat='.1%',hovermode='x unified')
    st.plotly_chart(chart_style(fig,420),width='stretch')
    st.caption('Adjacent targets overlap. The plotted line is daily close-to-close variation, not intraday realized volatility or a trading return.')
    quarters=[]
    for quarter,block in view.groupby('quarter'):
        for model in MODELS:quarters.append(dict(Quarter=quarter,Model=LABELS[model],**metrics(block.actual,block[model])))
    left,right=st.columns(2)
    for col,key,title in [(left,'rmspe','Quarterly RMSPE (%)'),(right,'mae','Quarterly MAE (volatility pp)')]:
        table=pd.DataFrame(quarters);table['Value']=table[key]*100
        fig=px.bar(table,x='Quarter',y='Value',color='Model',barmode='group',title=title,color_discrete_sequence=[COLORS[m] for m in MODELS])
        col.plotly_chart(chart_style(fig),width='stretch')
    exports=view[['date','target_end','stock','policy','actual']+MODELS+['headline','fit_M1','fit_M2']]
    st.download_button('Download displayed predictions (CSV)',exports.to_csv(index=False).encode(),file_name='2015-volatility-forecasts.csv',mime='text/csv')

with disagreements:
    st.subheader('Why the metrics can disagree')
    st.latex(r'\mathrm{RMSPE}^{2}=\frac{1}{N}\sum_i\frac{(\hat{y}_i-y_i)^2}{y_i^2}')
    st.write('The same absolute miss contributes 100 times more squared percentage error when actual volatility is ten times smaller. MAE weights absolute misses directly; RMSE squares them. A model can improve absolute error while doing worse on quiet observations.')
    st.info('For a single positive actual outcome, absolute and percentage errors order models identically. Disagreement appears when errors are aggregated with different weights or powers.')
    st.dataframe(score_table(score),hide_index=True,width='stretch')
    st.caption(f"Zero actual targets in this view: {int((view.actual==0).sum()):,}. They are undefined for RMSPE, retained for MAE/RMSE. No epsilon or small-positive-target trimming is used.")
    cuts=snapshot['selected_settings']['target_band_cuts_from_2014'];bands=outcome_band(view.actual,cuts)
    diagnostic=view.assign(outcome_band=bands);rows=[]
    for band,block in diagnostic.groupby('outcome_band',sort=False):
        for model in MODELS:
            error=block[model]-block.actual
            rows.append(dict(Band=band,Model=LABELS[model],**metrics(block.actual,block[model]),
                squared_percentage_error=float(((error/block.actual.where(block.actual>0))**2).sum()),absolute_error=float(error.abs().sum())))
    bands_frame=pd.DataFrame(rows)
    for key,new in [('squared_percentage_error','Squared percentage loss share (%)'),('absolute_error','Absolute loss share (%)')]:
        denominator=bands_frame.groupby('Model')[key].transform('sum')
        bands_frame[new]=100*bands_frame[key]/denominator.where(denominator>0)
    left,right=st.columns(2)
    for col,key in [(left,'Squared percentage loss share (%)'),(right,'Absolute loss share (%)')]:
        fig=px.bar(bands_frame,x='Band',y=key,color='Model',barmode='group',color_discrete_sequence=[COLORS[m] for m in MODELS])
        col.plotly_chart(chart_style(fig,440),width='stretch')
    st.caption('Bands use fixed quantiles of completed 2014 tuning targets. Grouping 2015 by its actual future outcome is retrospective failure analysis, never a forecast input.')
    concentration=pd.DataFrame(loss_concentration(view))
    concentration['Model']=concentration.model.map(LABELS)
    concentration['Smallest actuals (%)']=concentration.smallest_fraction*100
    concentration['Squared percentage loss share (%)']=concentration.sum_squared_percentage_error_share*100
    concentration['Absolute loss share (%)']=concentration.absolute_error_share*100
    st.dataframe(concentration[['Model','Smallest actuals (%)','observations','Squared percentage loss share (%)','Absolute loss share (%)']],hide_index=True,width='stretch')
    st.caption('These contribution calculations keep every eligible observation in the headline score. They do not report a replacement score after deleting difficult cases.')

with failures:
    st.subheader('Inspect the largest misses')
    left,right=st.columns(2)
    model=left.selectbox('Forecast model',MODELS,format_func=lambda m:LABELS[m],index=2)
    criterion=right.radio('Error used to find cases',['Absolute error','Percentage error'],horizontal=True)
    cases=view.copy();cases['prediction']=cases[model]
    cases['absolute_error']=(cases.prediction-cases.actual).abs()
    cases['percentage_error']=cases.absolute_error/cases.actual.where(cases.actual>0)
    key='absolute_error' if criterion=='Absolute error' else 'percentage_error'
    cases=cases[cases[key].notna()].sort_values([key,'date','stock'],ascending=[False,True,True]).head(25)
    if cases.empty:
        st.info('No cases with a defined error match these filters.')
    else:
        table=cases[['stock','date','target_end','actual','prediction','absolute_error','percentage_error','origin_market_decline']].copy()
        for key in ['actual','prediction','absolute_error','percentage_error']:table[key]*=100
        table=table.rename(columns={'actual':'Actual volatility (%)','prediction':'Forecast volatility (%)','absolute_error':'Absolute error (pp)','percentage_error':'Absolute percentage error (%)'})
        st.dataframe(table,hide_index=True,width='stretch')
        case_keys=list(cases.index)
        selected_case=st.selectbox('Case to examine',case_keys,format_func=lambda k:f"{cases.loc[k,'stock']} · {cases.loc[k,'date']:%Y-%m-%d}")
        row=cases.loc[selected_case]
        path=return_path(RESULTS,policy,row.stock,row.date,row.target_end)
        reconstructed=float(np.sqrt(path.pow(2).sum()))
        if not np.isclose(reconstructed,row.actual,rtol=0,atol=1e-13):
            st.error('The outcome does not match its observed return path.');st.stop()
        fig=go.Figure(go.Bar(x=path.index,y=path.to_numpy()*100,marker_color=['#b75445' if value<0 else '#23857f' for value in path]))
        fig.update_layout(title=f'{row.stock} · the five observed target returns',yaxis_title='Daily log return (%)')
        st.plotly_chart(chart_style(fig,310),width='stretch')
        st.write(f"The forecast was **{'above' if row.prediction>row.actual else 'below'}** realized five-session variation. The prior 20-session baseline was **{row.rv20:.2%}**; actual variation was **{row.actual:.2%}**.")
        st.caption('This path explains the measured miss, not its economic cause. News/event attribution is unresolved unless separately evidenced. These future returns were not model features; repeated overlapping windows are not independent failures.')
        with st.expander('Inputs and fit available at the forecast origin'):
            fields=json.loads(snapshot['fits'].loc[snapshot['fits'].fit_id==row.get('fit_'+model,''),'features'].iloc[0]) if model!='M0' else ['rv20']
            st.dataframe(pd.DataFrame({'Input':fields,'Observed value':[row[f] for f in fields]}),hide_index=True,width='stretch')
            if model!='M0':
                fit=snapshot['fits'][snapshot['fits'].fit_id==row['fit_'+model]].iloc[0]
                st.write(f"Fit used {fit.train_rows:,} matured observations. Latest training target ended {fit.train_target_end_max}; this evaluation quarter started {fit.validation_start}.")
            st.caption('The source and quality masks are retrospective snapshots. Correct feature timing does not establish original feed availability or real-time validity of every quality decision.')

with methods:
    st.subheader('Coverage and a reproducible comparison')
    st.dataframe(pd.DataFrame(snapshot['coverage']).drop(columns=['forecasts','note']),hide_index=True,width='stretch')
    st.caption('Full-experiment counts. Reasons overlap. A missing input, immature target or insufficient stock history is disclosed, never replaced with an invented value. The last five discovery origins cannot be scored without reserved-period returns.')
    with st.expander('Fixed full-study scorecard — unaffected by filters',expanded=True):
        full=fixed_scores[(fixed_scores.scope=='headline')&(fixed_scores.policy==policy)].set_index('model')
        st.dataframe(score_table(full),hide_index=True,width='stretch')
    st.markdown('''**Target:** square root of the sum of the next five squared log returns, with five consecutive valid returns. No annualization, centering or imputation.

**Validation:** 2014 Q3/Q4 chronological tuning; quarterly 2015 refits using only matured past labels. Training transformations use training data only. Tuning targets finish before 2015 evaluation begins.

**Three models:** historical volatility; per-stock log-volatility Ridge; the same Ridge family with broad-market information excluding the focal stock. No peer selection or additional architectures.

**Interpretation:** 2015 was already examined descriptively and is internal discovery evaluation. Retrospective masks, adjustment ambiguity and survivorship remain limitations. The advanced vulnerability hypothesis is a future extension.''')
    st.subheader('Paired uncertainty checks')
    intervals=pd.DataFrame(snapshot['uncertainty'])
    st.dataframe(intervals[(intervals.policy==policy)&(intervals.metric=='rmspe')][['block_sessions','calendar_blocks','model','comparison','point_difference','descriptive_95pct_low','descriptive_95pct_high']],hide_index=True,width='stretch')
    st.caption('Full-study fixed-forecast calendar-block resampling, all stocks jointly. Positive differences mean higher error. Few blocks, shared market episodes and nonstationarity limit interpretation; this is not a significance or causal guarantee.')
    ledger=data[data.policy==policy][['date','stock','policy','target_available','horizon_within_discovery','cohort_eligible','own_features_available','market_features_available','policy_common','headline','price_reason','return_reason','label_reason_bits']].copy()
    ledger['pre2015_complete_training_rows']=ledger.stock.map(cohort.set_index('stock')[policy+'_training_rows'])
    st.download_button('Download full 2015 eligibility ledger (CSV)',ledger.to_csv(index=False).encode(),file_name='full-2015-forecast-coverage.csv',mime='text/csv')
    st.caption('This full-policy ledger includes all 505 aligned names, dates outside the fitting cohort and the final five unscored origins, independently of view filters. Label reason bits combine the next five return reasons: 1 missing record, 2 contradictory OHLC, 4 repeated-record suspicion, 8 invalid numeric, 16 action boundary, 32 outside active span, 64 horizon outside discovery. They are outcome diagnostics, not model features.')
    with st.expander('Provenance and authorship'):
        st.json(snapshot['manifest'])
        st.write('The lead supplied the research hypothesis, interpretations, scope changes and approvals. Code, implementation and recommendations are AI assistance; they are not presented as manually written by the lead.')
        st.markdown(f'[Frozen exploratory foundation]({GITHUB}/tree/research-d001-d006-freeze) · [Approved experiment plan]({GITHUB}/blob/feat/002-optiver-research/optiver-realized-volatility/research/forecast-D008/PLAN.md) · [Cleaning evidence ledger]({GITHUB}/blob/research-d001-d006-freeze/optiver-realized-volatility/research/cleaning-D003/README.md)')
