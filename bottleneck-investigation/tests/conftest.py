"""SYNTHETIC TEST FIXTURES ONLY; never public-service evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest


@pytest.fixture
def records():
    s = pd.Timestamp("2025-01-01T12:00:00", tz="UTC")
    return pd.DataFrame(
        {
            "request_id": ["TEST-" + str(i) for i in range(5)],
            "created_at": [s, s, s, s + pd.Timedelta(days=59), s],
            "closed_at": [
                s + pd.Timedelta(days=7),
                pd.NaT,
                s + pd.Timedelta(days=31),
                s + pd.Timedelta(days=60),
                s - pd.Timedelta(days=1),
            ],
            "status": ["closed", "open", "closed", "closed", "closed"],
            "category": ["TEST-CATEGORY"] * 5,
            "agency": ["TEST-AGENCY"] * 5,
            "neighborhood": ["TEST-AREA"] * 5,
        }
    )
