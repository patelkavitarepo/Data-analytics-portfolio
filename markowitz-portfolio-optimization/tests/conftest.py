import numpy as np
import pandas as pd
import pytest
from markowitz.data import TICKERS, sessions


@pytest.fixture
def historical_returns():
    """SYNTHETIC; deterministic mathematical fixture, never research evidence."""
    idx = sessions('2016-01-01', '2026-11-10')
    rng = np.random.default_rng(6006)
    values = rng.normal(.0002, .01, (len(idx), len(TICKERS)))
    values += rng.normal(0, .003, (len(idx), 1))
    return pd.DataFrame(values, index=idx, columns=TICKERS)
