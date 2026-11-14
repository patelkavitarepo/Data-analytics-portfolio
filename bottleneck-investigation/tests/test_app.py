"""Test-only fixtures patched in process; never shipped as a dashboard data bundle."""

from pathlib import Path
from unittest.mock import patch
from datetime import date
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from src.analytics import aggregate

APP = Path(__file__).resolve().parents[1] / "app.py"
SECTIONS = [
    "Overview",
    "Performance Investigation",
    "Geographic Investigation",
    "Recurring Problems",
    "Evidence & Conclusions",
]


@pytest.mark.parametrize("section", SECTIONS)
def test_pending_sections(section):
    st.cache_data.clear()
    at = AppTest.from_file(str(APP)).run()
    at.sidebar.radio[0].set_value(section).run()
    assert not at.exception
    assert any("EVIDENCE PENDING" in w.value for w in at.warning)


@pytest.mark.parametrize("section", SECTIONS)
def test_charts_test_only_fixture(section, records):
    st.cache_data.clear()
    cube = aggregate(records, "2025-03-02T12:00:00Z")
    with patch(
        "src.bundle.load_bundle", return_value=({"extracted_at": "TEST ONLY"}, cube)
    ):
        at = AppTest.from_file(str(APP)).run()
        at.sidebar.radio[0].set_value(section).run()
        assert not at.exception
        at.sidebar.multiselect[0].set_value(["TEST-CATEGORY"]).run()
        assert not at.exception
    st.cache_data.clear()


def test_zero_filter(records):
    st.cache_data.clear()
    cube = aggregate(records, "2025-03-02T12:00:00Z")
    with patch(
        "src.bundle.load_bundle", return_value=({"extracted_at": "TEST ONLY"}, cube)
    ):
        at = AppTest.from_file(str(APP)).run()
        at.sidebar.date_input[0].set_value((date(2025, 1, 2), date(2025, 1, 3))).run()
        assert not at.exception
        assert any("No requests match" in x.value for x in at.info)
    st.cache_data.clear()


@pytest.mark.parametrize(
    "section",
    [
        "Performance Investigation",
        "Geographic Investigation",
        "Recurring Problems",
        "Evidence & Conclusions",
    ],
)
def test_nonempty_comparisons_and_briefs(section):
    """Hundreds of clearly labeled synthetic test rows exercise nonempty screens."""
    import pandas as pd

    rows = []
    for month in [1, 2, 3]:
        for agency, closed in [("TEST-A", 60), ("TEST-B", 80)]:
            for i in range(100):
                created = pd.Timestamp(f"2025-{month:02}-01T12:00:00Z")
                rows.append(
                    {
                        "request_id": f"TEST-{month}-{agency}-{i}",
                        "created_at": created,
                        "closed_at": (
                            created + pd.Timedelta(days=2) if i < closed else pd.NaT
                        ),
                        "status": "closed" if i < closed else "open",
                        "category": "TEST-CATEGORY",
                        "agency": agency,
                        "neighborhood": "TEST-AREA",
                    }
                )
    cube = aggregate(pd.DataFrame(rows), "2025-12-31T12:00:00Z")
    st.cache_data.clear()
    with patch(
        "src.bundle.load_bundle", return_value=({"extracted_at": "TEST ONLY"}, cube)
    ):
        at = AppTest.from_file(str(APP)).run()
        at.sidebar.radio[0].set_value(section).run()
        assert not at.exception
        if section == "Evidence & Conclusions":
            assert any("TEST-A" in e.label for e in at.expander)
        if section == "Geographic Investigation":
            assert len(at.get("plotly_chart")) == 1
        at.sidebar.multiselect[1].set_value(["TEST-A"]).run()
        assert not at.exception
        if section == "Recurring Problems":
            next(r for r in at.radio if r.label.startswith("Negative gap")).set_value(
                15
            ).run()
            assert not at.exception
    st.cache_data.clear()
