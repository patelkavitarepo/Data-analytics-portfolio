"""Optional real-artifact integration checks; no production data-directory changes."""

import os
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from src.bundle import load_bundle
from src.analytics import metrics, persistent

FOLDER = os.getenv("CASE002_EVIDENCE_DIR")
pytestmark = pytest.mark.skipif(
    not FOLDER, reason="Authentic review artifact not configured"
)


@pytest.fixture(scope="module")
def authentic():
    meta, cube = load_bundle(Path(FOLDER))
    assert cube is not None and meta["synthetic"] is False
    assert (
        meta["unique_request_ids"]
        == meta["rows"]
        == meta["downloaded_rows"]
        == meta["source_count_before"]
        == meta["source_count_after"]
    )
    assert meta["sql_python_parity_pages"] == meta["pages"]
    assert pd.to_datetime(cube.created_date).dt.year.eq(2025).all()
    assert cube.closed_valid.le(cube.requests).all()
    return meta, cube


def test_authentic_aggregate_consistency(authentic):
    meta, cube = authentic
    m = metrics(cube)
    assert m["requests"] == meta["rows"]
    assert m["closed30"] <= m["eligible30"] <= m["requests"]
    assert m["closed7"] <= m["eligible7"] <= m["requests"]
    assert meta["quality"]["duplicate_ids"] == meta["quality"]["missing_ids"] == 0
    # Full 2025 follow-up is mature at this release's extraction date.
    if pd.Timestamp(meta["as_of"]) >= pd.Timestamp("2026-02-01T08:00:00Z"):
        assert m["eligible30"] == m["requests"]
    a = persistent(cube, 10)
    b = persistent(cube, 15)
    assert set(map(tuple, b.loc[b.candidate, ["agency", "category"]].values)) <= set(
        map(tuple, a.loc[a.candidate, ["agency", "category"]].values)
    )


@pytest.mark.parametrize(
    "section",
    [
        "Overview",
        "Performance Investigation",
        "Geographic Investigation",
        "Recurring Problems",
        "Evidence & Conclusions",
    ],
)
def test_authentic_sections(authentic, section):
    st.cache_data.clear()
    with patch("src.bundle.load_bundle", return_value=authentic):
        app = Path(__file__).resolve().parents[1] / "app.py"
        at = AppTest.from_file(str(app), default_timeout=180).run()
        at.sidebar.radio[0].set_value(section).run()
        assert not at.exception
        at.sidebar.multiselect[0].set_value([authentic[1].category.iloc[0]]).run()
        assert not at.exception
        at.sidebar.multiselect[1].set_value([authentic[1].agency.iloc[0]]).run()
        assert not at.exception
    st.cache_data.clear()
