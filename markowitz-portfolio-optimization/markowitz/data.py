"""Acquisition and explicit exchange-session quality checks. Never fill prices."""
from datetime import datetime, timedelta
from importlib.metadata import version
import hashlib
import io
from pathlib import Path
import time
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import numpy as np
import pandas as pd

TICKERS = ('SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'TLT', 'GLD', 'VNQ')
START = '2016-01-01'


def completed_session(now=None):
    """Conservative cutoff: exclude NY today even after the close/vendor revisions."""
    now = pd.Timestamp(now if now is not None else datetime.now(ZoneInfo('America/New_York')))
    if now.tzinfo is None:
        raise ValueError('now must be timezone aware')
    yesterday = now.tz_convert('America/New_York').date() - timedelta(days=1)
    cal = xcals.get_calendar('XNYS', start='2015-12-01', end=str(yesterday + timedelta(days=10)))
    return cal.date_to_session(str(yesterday), direction='previous').tz_localize(None)


def sessions(start, end):
    cal = xcals.get_calendar('XNYS', start=str((pd.Timestamp(start) - pd.Timedelta(days=10)).date()), end=str((pd.Timestamp(end) + pd.Timedelta(days=10)).date()))
    return cal.sessions_in_range(start, end).tz_localize(None)


def read_csv(raw):
    """Date + ticker columns; reject ambiguous dates/columns and malformed values."""
    frame = pd.read_csv(io.BytesIO(raw))
    if 'Date' not in frame or frame.columns.duplicated().any():
        raise ValueError('CSV needs a Date column and unique ticker columns')
    if any(str(c).endswith('.1') for c in frame.columns):
        raise ValueError('Duplicate/mangled CSV ticker columns')
    dates = pd.to_datetime(frame.pop('Date'), format='%Y-%m-%d', errors='raise')
    frame.index = pd.DatetimeIndex(dates)
    return frame.apply(pd.to_numeric, errors='raise')


def require_yahoo_collection_permission():
    """No provider express permission is recorded; HTTP access is not a grant."""
    raise RuntimeError('YAHOO RIGHTS BLOCKED: automated collection requires express prior provider permission; none is recorded. Use a separately authorized source. See DATA_RIGHTS.md.')


def download_prices(tickers=TICKERS, now=None):
    require_yahoo_collection_permission()  # Before importing/calling the vendor client.
    import yfinance as yf
    yf.set_tz_cache_location(str(Path(__file__).resolve().parents[1] / 'work' / 'vendor-cache'))
    cutoff = completed_session(now)
    # Fetch independently so a partial universe cannot masquerade as success.
    parts = []
    for ticker in tickers:
        error = None
        for attempt in range(2):
            try:
                history = yf.Ticker(ticker).history(start=START,
                    end=str((cutoff + pd.Timedelta(days=1)).date()),
                    auto_adjust=True, actions=False, raise_errors=True, timeout=20)
                if history.empty or 'Close' not in history:
                    raise ValueError(f'No adjusted prices for {ticker}')
                series = history['Close'].rename(ticker)
                series.index = series.index.tz_localize(None).normalize()
                parts.append(series)
                break
            except Exception as exc:
                error = exc
                if attempt == 0:
                    time.sleep(1)
        else:
            raise RuntimeError(f'Yahoo download failed for {ticker}; retry later or upload CSV. {error}') from error
    prices = pd.concat(parts, axis=1).loc[START:cutoff]
    metadata = {
        'vendor': 'Yahoo Finance via yfinance', 'retrieved_utc': datetime.now(ZoneInfo('UTC')).isoformat(),
        'tickers': list(tickers), 'adjustment': 'yfinance auto_adjust=True Close (splits/dividends)',
        'timezone': 'America/New_York sessions; dates stored without timezone',
        'requested_start': START, 'completed_session_cutoff': str(cutoff.date()),
        'last_observation': str(prices.index.max().date()),
        'versions': {p: version(p) for p in ('yfinance', 'pandas', 'numpy', 'exchange-calendars')},
    }
    return prices, metadata


def audit_prices(prices, required=TICKERS, as_of=None, *, now=None):
    """Return clean common prices, daily returns, and a downloadable audit.

    Missing sessions are never bridged as daily returns. Each retained return
    requires valid prices on two consecutive XNYS sessions.
    """
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        raise ValueError('Nonempty DatetimeIndex prices required')
    if prices.index.tz is not None or prices.index.hasnans:
        raise ValueError('Use timezone-naive session dates, without NaT')
    if prices.index.duplicated().any() or prices.columns.duplicated().any():
        raise ValueError('Duplicate price dates or ticker columns')
    if not prices.index.equals(prices.index.normalize()):
        raise ValueError('Daily session dates must have midnight timestamps')
    missing = set(required) - set(prices.columns)
    if missing:
        raise ValueError(f'Missing required tickers: {sorted(missing)}')
    p = prices.loc[:, list(required)].sort_index().astype(float)
    if np.isinf(p.to_numpy()).any() or (p <= 0).any().any():
        raise ValueError('Prices must be finite and strictly positive (missing values audited separately)')
    latest_complete = completed_session(now)
    eligible = p.loc[START:latest_complete]
    observed = eligible.index[eligible.notna().any(axis=1)]
    if observed.empty:
        raise ValueError('No observed prices on or before the last complete session')
    last_observed = observed.max()
    explicit = as_of is not None
    cutoff = pd.Timestamp(as_of) if explicit else latest_complete
    if (isinstance(as_of, str) and as_of != str(cutoff.date())) or pd.isna(cutoff) or cutoff.tzinfo is not None or cutoff != cutoff.normalize():
        raise ValueError('as_of must be a timezone-naive YYYY-MM-DD session date')
    if cutoff < pd.Timestamp(START) or cutoff > latest_complete:
        raise ValueError('as_of must be within the research interval and no later than the last complete session')
    if cutoff not in sessions(cutoff, cutoff):
        raise ValueError('as_of must be an XNYS trading session')
    if explicit and cutoff > last_observed:
        raise ValueError('as_of cannot exceed the snapshot last observed date')
    # A user cannot move the cutoff just before a suspicious gap in a longer
    # supplied snapshot. Check the excluded tail without calculating its returns.
    tail = eligible.reindex(sessions(cutoff, last_observed)) if cutoff < last_observed else None
    if tail is not None and tail.isna().any(axis=None):
        raise ValueError('as_of would conceal missing sessions in the supplied snapshot tail; resolve source gaps first')
    ignored = int(((p.index < pd.Timestamp(START)) | (p.index > cutoff)).sum())
    p = p.loc[START:cutoff]
    if p.empty:
        raise ValueError('No prices in research interval')
    expected = sessions(START, cutoff)
    unexpected = p.index.difference(expected)
    if len(unexpected):
        raise ValueError(f'Non-XNYS session rows: {list(unexpected.date[:5])}')
    grid = p.reindex(expected)
    valid = grid.notna().all(axis=1)
    daily = grid.pct_change(fill_method=None).loc[valid & valid.shift(1, fill_value=False)]
    if len(daily) < 2:
        raise ValueError('Fewer than two consecutive complete daily returns')
    records = []
    for ticker in required:
        s = grid[ticker]
        absent = s.isna()
        longest = int(absent.groupby((~absent).cumsum()).sum().max())
        records.append({'ticker': ticker, 'valid_prices': int(s.notna().sum()),
            'missing_sessions': int(absent.sum()), 'longest_missing_run': longest,
            'first_date': str(s.first_valid_index().date()) if s.notna().any() else None,
            'last_date': str(s.last_valid_index().date()) if s.notna().any() else None})
    summary = {'as_of': str(cutoff.date()), 'as_of_explicit': explicit,
        'latest_complete_session': str(latest_complete.date()),
        'snapshot_last_observed': str(last_observed.date()),
        'source_is_stale': bool(last_observed < latest_complete),
        'historical_as_of': bool(cutoff < latest_complete),
        'source_sessions_after_as_of': int((eligible.index > cutoff).sum()),
        'expected_sessions': len(expected), 'common_prices': int(valid.sum()),
        'lost_price_rows': int((~valid).sum()), 'valid_daily_returns': len(daily),
        'excluded_return_intervals': len(expected) - 1 - len(daily),
        'ignored_outside_interval': ignored, 'duplicate_rows': 0, 'nonpositive_prices': 0,
        'misaligned_sessions': int((grid.notna().any(axis=1) & ~valid).sum()),
        'missing_entire_sessions': [str(d.date()) for d in expected[grid.isna().all(axis=1)]],
        'missing_by_ticker': {t: [str(d.date()) for d in expected[grid[t].isna()]] for t in required},
        'sha256_canonical_prices': hashlib.sha256(p.to_csv(float_format='%.12g').encode()).hexdigest()}
    return grid.loc[valid], daily, pd.DataFrame(records).set_index('ticker'), summary
