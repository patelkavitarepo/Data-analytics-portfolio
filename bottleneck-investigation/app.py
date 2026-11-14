"""Portfolio dashboard. Launch from any directory with streamlit run path/to/app.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import streamlit as st
from src.analytics import metrics, summary, adjusted, persistent
from src.bundle import load_bundle

ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="The Bottleneck Investigation", page_icon="🔎", layout="wide"
)
st.markdown(
    """<style>.block-container{padding-top:2.3rem;max-width:1450px}h1{letter-spacing:-1.3px}
[data-testid="stMetric"]{background:#fff;border:1px solid #dce5ed;border-radius:12px;padding:18px}
[data-testid="stSidebar"]{border-right:1px solid #dce5ed}
@media(max-width:640px){h1{font-size:2rem!important;overflow-wrap:anywhere}h3{font-size:1.25rem!important}.block-container{padding-left:1rem;padding-right:1rem}p{overflow-wrap:anywhere}}</style>""",
    unsafe_allow_html=True,
)
st.caption("CASE 002  /  OPERATIONS INTELLIGENCE  /  SAN FRANCISCO 311")
st.title("The Bottleneck Investigation")
st.markdown("### An Operations & Performance Analytics Case Study")
st.write(
    "Why do some public-service requests take significantly longer to close than others?"
)
st.caption(
    "Administrative closure is a recorded workflow event. It does not establish that a problem was resolved."
)


@st.cache_data(show_spinner=False)
def cached_bundle(metadata_bytes, cube_stamp):
    return load_bundle(ROOT / "data")


try:
    path = ROOT / "data" / "cube.parquet"
    meta, cube = cached_bundle(
        (ROOT / "data" / "provenance.json").read_bytes(),
        path.stat().st_mtime_ns if path.exists() else 0,
    )
except Exception as exc:
    st.error(f"Evidence unavailable: bundle verification failed. {exc}")
    st.stop()

sections = [
    "Overview",
    "Performance Investigation",
    "Geographic Investigation",
    "Recurring Problems",
    "Evidence & Conclusions",
]
section = st.sidebar.radio("Investigation workspace", sections)
st.sidebar.caption("2025 creation cohort • 7- and 30-day follow-up")

if cube is None:
    st.warning(
        "EVIDENCE PENDING — No verified public extract is bundled. No operational findings are available."
    )
    st.info(meta.get("reason", "Source verification is pending."))
    if section == "Overview":
        cols = st.columns(4)
        for c, label in zip(
            cols,
            [
                "Requests",
                "Closed within 7 days",
                "Closed within 30 days",
                "Median closure time",
            ],
        ):
            c.metric(
                label, "—", help="Unavailable until verified authentic data is loaded."
            )
        st.subheader("Follow the evidence, from volume to persistent delay")
        st.write(
            "Begin with cohort coverage, compare equivalent categories, then investigate differences that recur across months. Empty evidence is never replaced with demonstration findings."
        )
    elif section == "Performance Investigation":
        st.subheader("Compare equivalent work")
        st.write(
            "Agency comparisons require the same category and month, at least 30 eligible requests in both the agency and its other-agency peer group. Categories handled by only one agency cannot support this comparison."
        )
    elif section == "Geographic Investigation":
        st.subheader("Place differences in context")
        st.write(
            "Neighborhood comparisons and category heatmaps will appear after extraction. Missing neighborhoods remain visible as Unknown; no unverified geographic boundaries or coordinates are plotted."
        )
    elif section == "Recurring Problems":
        st.subheader("A signal must persist")
        st.write(
            "Screen: ≥3 comparable months; ≥90 comparable requests; a ≥10 percentage-point deficit in at least half of months, with at least two qualifying months. Repeat at 15 points. This is an investigation screen, not a causal finding."
        )
    else:
        st.subheader("Evidence ledger")
        st.json(meta)
        st.markdown((ROOT / "DATA_DICTIONARY.md").read_text())
    st.sidebar.info("No credentials are required to view this application.")
    st.stop()

st.sidebar.success("Verified public extract")
st.sidebar.caption(f"Extracted: {meta['extracted_at']}")
dates = pd.to_datetime(cube.created_date)
date_range = st.sidebar.date_input(
    "Creation date",
    (dates.min().date(), dates.max().date()),
    min_value=dates.min().date(),
    max_value=dates.max().date(),
)
categories = st.sidebar.multiselect(
    "Request category",
    sorted(cube.category.unique()),
    help="Empty selection includes all categories.",
)
agencies = st.sidebar.multiselect(
    "Responsible agency",
    sorted(cube.agency.unique()),
    help="Empty selection includes all agencies. Peer comparisons use all agencies in the selected date/category cohort.",
)
mask = pd.Series(True, index=cube.index)
if len(date_range) == 2:
    mask &= dates.between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
else:
    st.info("Choose both endpoints of the creation-date range.")
    st.stop()
if categories:
    mask &= cube.category.isin(categories)
reference = cube[mask].copy()
d = reference[reference.agency.isin(agencies)] if agencies else reference
st.caption(
    "Filters apply to creation dates. Closure horizons use the fixed extraction timestamp, not today. Peer baselines retain all agencies in the selected date/category cohort."
)
if d.empty:
    st.info("No requests match these filters. Widen the selection.")
    st.stop()


def table(frame):
    st.dataframe(frame, hide_index=True, width="stretch")


def chart(frame, x, y, color=None, kind="bar"):
    if frame.empty:
        st.info("Insufficient comparable observations for this view.")
        return
    fig = (px.line if kind == "line" else px.bar)(
        frame,
        x=x,
        y=y,
        color=color,
        template="plotly_white",
        color_discrete_sequence=["#007F82", "#E5A145", "#526C9C"],
    )
    fig.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig, width="stretch")


if section == "Overview":
    m = metrics(d)
    a, b, c, e = st.columns(4)
    a.metric("Requests", f"{m['requests']:,.0f}")
    b.metric(
        "Closed within 7 days",
        f"{m['rate7']:.1%}" if pd.notna(m["rate7"]) else "—",
        help=f"Eligible denominator: {m['eligible7']:,.0f}; unresolved retained",
    )
    c.metric(
        "Closed within 30 days",
        f"{m['rate30']:.1%}" if pd.notna(m["rate30"]) else "—",
        help=f"Eligible denominator: {m['eligible30']:,.0f}; unresolved retained",
    )
    e.metric(
        "Median closure, days ≈",
        f"{m['median_days']:.0f}" if pd.notna(m["median_days"]) else "—",
        help="Closed valid cases only; day-bin estimate, less than one day rounding error. Unresolved excluded from time quantiles only.",
    )
    monthly = summary(d.assign(month=d.created_date.str[:7]), ["month"])
    l, r = st.columns(2)
    with l:
        st.subheader("Request volume")
        chart(monthly, "month", "requests", kind="line")
    with r:
        st.subheader("Eligible-cohort closure rates")
        rates = monthly.melt(
            id_vars="month",
            value_vars=["rate7", "rate30"],
            var_name="horizon",
            value_name="closure_rate",
        )
        chart(rates, "month", "closure_rate", "horizon", "line")
    st.subheader("Administrative closure-time distribution")
    hist = (
        d[d.duration_day.ge(0)].groupby("duration_day").closed_valid.sum().reset_index()
    )
    chart(hist, "duration_day", "closed_valid")
    st.caption(
        f"Closed-case P90 ≈ {m['p90_days']:.0f} days. Quantiles are lower bounds from floored day bins (error <1 day); unresolved durations are censored and not included."
    )
    table(monthly)
elif section == "Performance Investigation":
    st.subheader("Agency context — descriptive, not a league table")
    table(summary(d, ["agency"]))
    st.subheader("Category-adjusted monthly comparisons")
    cells = adjusted(reference)
    if agencies:
        cells = cells[cells.agency.isin(agencies)]
    st.write(
        "Gap in percentage points = agency 30-day closure rate − other agencies in the same category/month. Each side needs ≥30 eligible requests. No overlap means no defensible adjusted comparison."
    )
    table(cells)
    st.subheader("Slow categories with ≥90 valid closures")
    cats = summary(d, ["category"])
    table(cats[cats.closed_valid.ge(90)].sort_values("p90_days", ascending=False))
elif section == "Geographic Investigation":
    st.subheader("Neighborhood differences")
    unknown = d.loc[d.neighborhood.eq("Unknown"), "requests"].sum() / d.requests.sum()
    st.warning(
        f"Unknown neighborhood: {unknown:.1%} of selected requests. Coverage and category mix can influence comparisons. No population/exposure adjustment is available."
    )
    table(summary(d, ["neighborhood"]))
    geo = summary(d, ["neighborhood", "category"])
    geo = geo[geo.eligible30.ge(30)]
    if not geo.empty:
        grid = geo.pivot(index="neighborhood", columns="category", values="rate30")
        st.plotly_chart(
            px.imshow(
                grid,
                color_continuous_scale="Teal",
                zmin=0,
                zmax=1,
                aspect="auto",
                labels={"color": "30-day rate"},
            ),
            width="stretch",
        )
    st.caption(
        "Cells require ≥30 eligible requests. Geographic variation is not evidence of unequal service without further controls."
    )
elif section == "Recurring Problems":
    st.subheader("Persistent within-category delay screens")
    threshold = st.radio(
        "Negative gap threshold, percentage points", [10, 15], horizontal=True
    )
    st.write(
        "≥3 comparable months, ≥90 eligible requests, deficit in ≥half of comparable months and at least two months. Peers exclude the focal agency; cells need ≥30 requests per side."
    )
    signals = persistent(reference, threshold)
    if agencies:
        signals = signals[signals.agency.isin(agencies)]
    table(signals)
    st.caption(
        "candidate=True identifies an investigative signal, not a proven operational failure."
    )
    st.subheader("Monthly within-category gaps")
    cells = adjusted(reference)
    if agencies:
        cells = cells[cells.agency.isin(agencies)]
    table(cells)
    st.subheader("Recurring reporting intensity")
    recurrence = summary(
        d.assign(month=d.created_date.str[:7]), ["month", "neighborhood", "category"]
    )
    table(recurrence.sort_values("requests", ascending=False))
    st.caption(
        "Repeated category/neighborhood reports do not establish repeated failures at the same physical location."
    )
else:
    st.subheader("Provenance & quality")
    st.json(meta)
    st.subheader("Investigation briefs")
    candidates = persistent(reference)
    candidates = candidates[candidates.candidate]
    if agencies:
        candidates = candidates[candidates.agency.isin(agencies)]
    if candidates.empty:
        st.info(
            "No agency/category pairs meet this screen in the current comparable cohort. Lack of a signal does not establish absence of a bottleneck."
        )
    for _, row in candidates.iterrows():
        with st.expander(f"{row.agency} · {row.category}"):
            st.write(
                f"Observed: {row.qualifying_months}/{row.months} comparable months with ≥10-point deficits; {row.comparable_requests:,} eligible requests; weighted gap {row.gap_pp:.1f} pp against other agencies within category/month."
            )
            st.write(
                "Possible explanations: subcategory complexity, routing rules, administrative closure practices, or service constraints. These are hypotheses. Validate subcategory mix, status histories, work orders and field outcomes; review the 15-point sensitivity result before prioritizing a process audit. Staffing and dispatch failures are not inferred."
            )
    st.markdown((ROOT / "DATA_DICTIONARY.md").read_text())
    st.download_button(
        "Download filtered aggregate evidence",
        d.to_csv(index=False),
        "bottleneck-filtered-aggregates.csv",
        "text/csv",
    )
