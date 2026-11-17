"""Standalone read-only exhibit. Explicit navigation excludes the existing apps."""
import plotly.express as px
import streamlit as st

from showcase_evidence import ORACLE, REPOSITORY, SPECS, WARNING, build_panels, load_reports, shared_context

st.set_page_config(page_title='Project 006 | Synthetic research exhibit',page_icon='⚗',layout='centered',initial_sidebar_state='auto')

DOCS={
    'Project case study':'CASE_STUDY.md',
    'Decision Quality Framework':'DECISION_QUALITY_FRAMEWORK.md',
    'Source-rights gate':'DATA_RIGHTS.md',
    'Independent adjustment verification':'ADJUSTMENT_REVIEW.md',
}


def render_block(item):
    with st.container(border=True):
        st.subheader(item['title'])
        st.caption(WARNING+' · '+item['unit'])
        for row in item['rows']:
            st.markdown('**'+row['label']+'**')
            st.write(row['value'])
        st.caption(item['note'])


def documentation_links(study=None):
    with st.expander('Read the original evidence and research gates'):
        st.caption('Everything essential is summarized here offline. These optional links open the repository when you have a connection; the files also live beside this app.')
        for label,path in DOCS.items():st.markdown(f'[{label} — {path}]({REPOSITORY+path})')
        studies=[study] if study else list(SPECS)
        for key in studies:
            spec=SPECS[key]
            st.markdown(f"[{spec['title']} — {spec['findings']}]({REPOSITORY+spec['findings']})")


def select_study(title):
    st.session_state['showcase_section']=title


def render_showcase():
    st.title('What makes a portfolio decision trustworthy?')
    st.caption('Project 006 · Offline synthetic research exhibit · Read-only committed evidence')
    st.error(WARNING)
    st.info('The eight-ETF historical question is unanswered. Source rights and independent adjusted-price verification remain unresolved. The 2025+ real holdout is untouched.')
    try:
        reports,raw_reports=load_reports(with_bytes=True)
        panels=build_panels(reports)
        assumptions=shared_context(reports)
    except (ValueError,KeyError,TypeError) as exc:
        st.error(f'{WARNING} · Evidence unavailable or invalid: {exc}')
        st.write('No placeholder figures, fitting, downloads from providers or empirical fallback. Restore the exact committed report before reviewing results.')
        documentation_links()
        st.stop()
    st.caption(assumptions)
    choices=['Start here',*[spec['title'] for spec in SPECS.values()]]
    st.sidebar.header('Explore the evidence')
    selected=st.sidebar.radio('Investigation',choices,key='showcase_section',label_visibility='visible')
    st.sidebar.caption('Navigation changes the presentation only. No parameters, uploads or experiment runs.')
    st.sidebar.caption(WARNING)
    if selected=='Start here':
        st.header('One question, two distinct research tracks')
        st.write('Can constrained Markowitz portfolios improve out-of-sample risk-adjusted performance over equal weights? The historical ETF application has not answered that question. These completed studies instead examine assumptions in six abstract, constructed assets.')
        st.subheader('Five investigations, including negative findings')
        for key,panel in panels.items():
            with st.container(border=True):
                st.markdown('**'+SPECS[key]['title']+'**')
                st.write(panel['title'])
                st.caption('Each finding keeps its own seeds, windows, units and counterexample.')
                st.button('Open '+SPECS[key]['title'],on_click=select_study,args=(SPECS[key]['title'],),key='open_'+key,use_container_width=True)
        st.subheader('What passed / what remains blocked')
        st.success('Available for review: five committed synthetic reports, reproducible code and test records. This page selects existing evidence; it does not refit or simulate.')
        st.warning('Still blocked: real ETF performance evaluation and empirical model promotion. No approved data source, independent price-adjustment evidence or fresh confirmation authorization is established.')
        st.write('Estimation accuracy, chosen weights, forward behavior and operational reliability are separate claims. There is no composite score, portfolio leaderboard or investment recommendation here.')
        st.caption('Half-L1 measures target reassignment, not trading turnover. HHI measures concentration, not confidence. Sharpe estimates are not promises. Known covariance and oracle risk are privileges of synthetic models, not observable market truth.')
        st.caption(ORACLE+' · used for scoring only in the mechanism study.')
        documentation_links()
    else:
        key=next(key for key,spec in SPECS.items() if spec['title']==selected)
        panel=panels[key]
        st.header(selected)
        st.subheader(panel['title'])
        st.caption(WARNING+' · '+panel['context'])
        st.write(panel['finding'])
        for item in panel['blocks']:render_block(item)
        if key=='lab':
            fig=px.bar(panel['chart'],x='Reassignment',y='Allocation',orientation='h',labels={'Reassignment':'Mean half-L1 target reassignment (%)'})
            fig.update_layout(title={'text':WARNING+'<br>One-seed baseline resampling sensitivity','font':{'size':11}},height=310,margin={'l':0,'r':10,'t':70,'b':15},showlegend=False)
            st.caption(WARNING+' · Chart repeats the values printed above; same sample and units. It is not a strategy ranking.')
            st.plotly_chart(fig,use_container_width=True)
        st.warning('Limits · '+panel['limits'])
        with st.expander('Exact source selectors and unchanged report'):
            st.caption(WARNING+' · No new observations or summaries are generated.')
            for selector in panel['sources']:st.code(selector,language=None,wrap_lines=True)
            st.caption('Artifact: '+SPECS[key]['file']+' · SHA-256: '+SPECS[key]['sha256'])
            st.download_button(WARNING+' · Download original '+SPECS[key]['title'],raw_reports[key],file_name='SYNTHETIC_'+key+'_committed_report.json',mime='application/json',on_click='ignore')
        documentation_links(key)
    st.divider()
    st.caption(WARNING+' · Synthetic results do not validate ETFs or license data. Publication, merge and deployment remain subject to separate owner approval.')


# A single callable page suppresses Streamlit's implicit sibling pages/ discovery.
# Existing experiment pages and the empirical app are never part of this navigation.
st.navigation([st.Page(render_showcase,title='Synthetic research exhibit',default=True)],position='hidden').run()
