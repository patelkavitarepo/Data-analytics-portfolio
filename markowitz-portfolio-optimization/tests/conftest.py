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


@pytest.fixture
def source_review():
    """Build a SYNTHETIC consistency-review fixture, never a genuine source review."""
    def build(prices, summary):
        date = prices.loc[:min(summary['as_of'], '2024-12-31')].index[-1]
        return {'reviewer': 'SYNTHETIC TEST ONLY', 'retrieved_utc': pd.Timestamp.now(tz='UTC').isoformat(),
            'source_url': 'https://example.invalid/SYNTHETIC',
            'adjustment_convention': 'split_and_dividend_adjusted_close',
            'adjustment_evidence': 'SYNTHETIC fixture, no vendor adjustment assertion',
            'analysis_use_authorized': True, 'analysis_permission_evidence': 'SYNTHETIC fixture created in tests',
            'as_of': summary['as_of'], 'snapshot_sha256': summary['sha256_canonical_prices'],
            'spot_checks': {ticker: {'date': str(date.date()), 'reference_url': 'https://www.nasdaq.com/SYNTHETIC-TEST-ONLY',
                'reference_price': float(prices.loc[date, ticker]),
                'adjustment_basis': 'split_and_dividend_adjusted_close'} for ticker in TICKERS}}
    return build
