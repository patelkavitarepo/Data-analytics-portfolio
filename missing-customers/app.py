"""Streamlit investigation; run from any working directory."""
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from src.analytics import load_csv, stage_counts, journey, funnel

st.set_page_config(page_title='The Missing Customers', page_icon='🔎', layout='wide')
st.title('The Missing Customers')
st.caption('PROJECT 005 · An event-log investigation · UTC')
st.markdown('### Where do customers drop off in an online shopping journey, and what can the recorded events establish?')
st.write('Source: [Retailrocket Ecommerce dataset — original publisher](https://www.kaggle.com/retailrocket/ecommerce-dataset). Uploaded files are user-supplied and their provenance is not independently verified.')
st.sidebar.header('Evidence intake')
upload = st.sidebar.file_uploader('Upload events.csv (maximum 100 MiB)', type=['csv'])
local = Path(__file__).parent / 'data' / 'events.csv'
use_local = st.sidebar.checkbox('Use ignored local data/events.csv', disabled=not local.exists())
provenance = st.sidebar.text_input('Source / download date / transformations', placeholder='Record where this file came from')
st.sidebar.caption('Required: timestamp, visitorid, event, itemid. Optional: transactionid. Timestamps must be integer Unix milliseconds (UTC), 2000–2099.')
source = upload if upload is not None else local if use_local else None
if source is None:
    st.info('Awaiting evidence. Download events.csv from the original publisher after reviewing its terms, then upload it here or place it in missing-customers/data/events.csv. No dataset or sample findings are bundled.')
    st.write('Large file? Use the documented offline CLI to create a bounded UTC date slice. The slice limits the observation window and can censor journeys.')
    st.markdown('**Human investigator interpretation: pending.** No empirical findings have been established.')
    st.stop()
try:
    # Cached by file contents for uploads; local size and mtime invalidate local reads.
    @st.cache_data(max_entries=1, show_spinner='Auditing evidence…')
    def intake(contents):
        import io
        return load_csv(io.BytesIO(contents))
    if upload is not None and upload.size > 100 * 1024 * 1024:
        raise ValueError('CSV exceeds 100 MiB. Use the offline CLI first.')
    if use_local and upload is None and local.stat().st_size > 100 * 1024 * 1024:
        raise ValueError('Local CSV exceeds 100 MiB. Use the offline CLI first.')
    df, audit = intake(upload.getvalue() if upload is not None else local.read_bytes())
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f'Cannot load evidence: {exc}')
    st.stop()
st.warning('Provisional observational analysis. Hashed visitor IDs are browser identifiers, not verified people or customers. No revenue, sessions, channels, devices, geography or causal effects are established.')
tabs = st.tabs(['Case overview', 'Evidence audit', 'Shopping journey', 'Alternative explanations', 'Research notes'])
with tabs[0]:
    st.subheader('Evidence status')
    st.write('User-supplied source notes: ' + (provenance or 'Not supplied — provenance needs review.'))
    st.write(f"Accepted events: {len(df):,} · identified visitors: {df.visitorid.nunique():,}")
    st.write(f'Accepted UTC coverage: {df.time.min()} → {df.time.max()}' if len(df) else 'No valid events remain after validation.')
    st.caption('Coverage describes accepted rows, not a guarantee of complete tracking. Exact duplicate rows are removed; invalid timestamps, missing visitors and unsupported events are excluded. Missing items remain eligible only for visitor-level analysis.')
with tabs[1]:
    st.subheader('Full input audit (before date/event filters)')
    st.dataframe(pd.DataFrame([audit]).T.rename(columns={0: 'value'}).astype(str), use_container_width=True)
    st.download_button('Download quality summary', json.dumps({'source_notes': provenance, **audit}, indent=2), 'quality-summary.json', 'application/json')
    st.caption('Duplicate detection uses all supplied columns. Repeated transaction events with different fields remain events, not distinct confirmed purchases. Millisecond timestamps outside 2000–2099 are rejected as implausible for this source. Input ordering reversals are repaired by sorting, not treated as causal evidence.')
if df.empty:
    st.info('No valid rows to explore. Inspect the audit and provide another file.')
    st.stop()
start, end = df.time.min().date(), df.time.max().date()
dates = st.sidebar.date_input('Observation window (UTC, inclusive)', value=(start, end), min_value=start, max_value=end)
if len(dates) != 2:
    st.info('Select both dates to explore the observation window.')
    st.stop()
window = df.loc[df.time.dt.date.between(*dates)]
with tabs[2]:
    st.subheader('Events and visitors are different units')
    selected = st.multiselect('Event types for descriptive counts only', ['view', 'addtocart', 'transaction'], default=['view', 'addtocart', 'transaction'])
    counts = stage_counts(window.loc[window.event.isin(selected)])
    st.dataframe(counts, hide_index=True, use_container_width=True)
    st.plotly_chart(px.bar(counts.melt(id_vars='event', var_name='unit', value_name='count'), x='event', y='count', color='unit', barmode='group'), use_container_width=True)
    st.caption('Distinct visitors can appear at several stages. These totals are not a sequential conversion funnel. Event-type selection affects only descriptive counts and preview below.')
    st.subheader('Strict timestamp-ordered visitor journey')
    st.write('All event types are used for journeys within the selected date window. Entry denominator: visitors with a recorded view in that window. Each subsequent stage must have a strictly later timestamp; simultaneous stages do not establish order.')
    cohort = journey(window)
    strict = journey(window, item_matched=True)
    st.dataframe(funnel(cohort), hide_index=True, use_container_width=True)
    st.plotly_chart(px.bar(funnel(cohort), x='stage', y='visitors', text='visitors'), use_container_width=True)
    st.markdown('**Same-item check** — one visitor counted once if any item has a complete ordered path.')
    st.dataframe(funnel(strict), hide_index=True, use_container_width=True)
    st.caption('Same-item denominator excludes views with missing item IDs. Visitor-level paths may span different products and returning visits. No session boundary is inferred. Date filtering can remove preceding views or later transactions; absence is not proof of abandonment.')
    st.write('Visitor cohort preview (first 100; identifiers shown as provided)')
    st.dataframe(cohort.head(100), hide_index=True, use_container_width=True)
    st.write('Accepted event preview (first 100 in selected event types)')
    st.dataframe(window.loc[window.event.isin(selected)].head(100), hide_index=True, use_container_width=True)
with tabs[3]:
    st.subheader('What else could explain a missing stage?')
    st.markdown('- **Instrumentation gaps:** absent events may reflect tracking failure or a different purchase route.\n- **Left/right censoring:** the file or selected window may omit preceding views and later transactions.\n- **Re-entry:** a visitor can return across multiple visits; these are not session funnels.\n- **Anonymous identifiers:** cookie resets or shared browsers can split or combine people.\n- **Absent transactions:** no recorded transaction does not prove a lost customer, intent or monetary loss.\n- **Ties and products:** equal timestamps cannot prove stage order; cross-item paths can overstate product continuity.')
with tabs[4]:
    st.subheader('Research notes')
    st.write('Observed: the tables describe accepted records in the selected window, under the disclosed rules. Hypotheses: explanations above require additional evidence and are not established causes.')
    st.markdown('**Human investigator interpretation: pending.** Review provenance, exclusions and observation-window sensitivity before drawing conclusions. Persistent evidence findings remain pending until a real source is audited and documented in research/EVIDENCE.md.')
