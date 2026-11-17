import numpy as np
import pandas as pd
import pytest
from markowitz.data import audit_prices, completed_session, read_csv, sessions, download_prices


def sample():
    idx = sessions('2016-01-01', '2016-01-12')
    return pd.DataFrame({'A': np.arange(len(idx)) + 100., 'SPY': np.arange(len(idx)) + 200.}, index=idx)


def test_simple_returns_calendar_and_no_holiday_missing():
    p = sample()
    clean, r, audit, summary = audit_prices(p, ['A', 'SPY'], p.index[-1])
    np.testing.assert_allclose(r['A'], p['A'].to_numpy()[1:] / p['A'].to_numpy()[:-1] - 1)
    assert summary['lost_price_rows'] == 0
    assert pd.Timestamp('2016-01-01') not in clean.index
    assert audit['missing_sessions'].sum() == 0


def test_missing_and_misaligned_sessions_never_bridge_gap():
    p = sample()
    missing_day, next_day = p.index[2:4]
    p.loc[missing_day, 'A'] = np.nan
    _, r, audit, summary = audit_prices(p, ['A', 'SPY'], p.index[-1])
    assert missing_day not in r.index and next_day not in r.index
    assert audit.loc['A', 'missing_sessions'] == 1
    assert summary['misaligned_sessions'] == 1
    p = sample().drop(missing_day)
    _, r, _, summary = audit_prices(p, ['A', 'SPY'], p.index[-1])
    assert summary['missing_entire_sessions'] == [str(missing_day.date())]
    assert next_day not in r.index


@pytest.mark.parametrize('bad', [0, -1, np.inf, -np.inf])
def test_nonpositive_and_nonfinite(bad):
    p = sample()
    p.iloc[2, 0] = bad
    with pytest.raises(ValueError, match='strictly positive'):
        audit_prices(p, ['A', 'SPY'], p.index[-1])


def test_duplicate_and_missing_ticker():
    p = sample()
    with pytest.raises(ValueError, match='Duplicate'):
        audit_prices(pd.concat([p, p.iloc[:1]]), ['A', 'SPY'], p.index[-1])
    with pytest.raises(ValueError, match='Missing required'):
        audit_prices(p, ['QQQ'], p.index[-1])
    p.columns = ['SPY', 'SPY']
    with pytest.raises(ValueError, match='Duplicate'):
        audit_prices(p, ['SPY'], p.index[-1])


def test_unexpected_sessions_and_timestamp():
    p = sample()
    p.loc[pd.Timestamp('2016-01-09')] = [100, 200]
    with pytest.raises(ValueError, match='Non-XNYS'):
        audit_prices(p, ['A', 'SPY'], '2016-01-12')
    p = sample()
    p.index += pd.Timedelta(hours=1)
    with pytest.raises(ValueError, match='midnight'):
        audit_prices(p, ['A', 'SPY'], '2016-01-12')


def test_stale_and_long_gaps_audited():
    p = sample().iloc[:3]
    _, _, audit, summary = audit_prices(p, ['A', 'SPY'], now='2016-02-02T10:00:00-05:00')
    assert audit.loc['A', 'longest_missing_run'] > 5
    assert summary['lost_price_rows'] > 5


def test_complete_day_cutoff_weekend_holiday_and_timezones():
    assert completed_session('2026-11-09T20:00:00-05:00') == pd.Timestamp('2026-11-06')
    assert completed_session('2026-07-06T10:00:00-04:00') == pd.Timestamp('2026-07-02')
    assert completed_session('2026-11-11T00:30:00+00:00') == pd.Timestamp('2026-11-09')
    with pytest.raises(ValueError):
        completed_session('2026-11-10')


def test_csv_validation():
    p = read_csv(b'Date,A,SPY\n2016-01-04,100,200\n2016-01-05,101,202\n')
    assert p.loc['2016-01-04', 'A'] == 100
    for content in (b'Date,A,A\n2016-01-04,1,2\n', b'Date,A\nnope,1\n', b'Date,A\n2016-01-04,text\n', b'A\n1\n'):
        with pytest.raises(ValueError):
            read_csv(content)


def test_failed_download_is_not_partial_or_synthetic(monkeypatch):
    # Exercise the legacy client with synthetic responses only, not real permission.
    monkeypatch.setattr('markowitz.data.require_yahoo_collection_permission', lambda: None)
    import yfinance
    class Broken:
        def __init__(self, ticker):
            pass
        def history(self, **kwargs):
            raise RuntimeError('rate limited')
    monkeypatch.setattr(yfinance, 'Ticker', Broken)
    monkeypatch.setattr('markowitz.data.time.sleep', lambda _: None)
    with pytest.raises(RuntimeError, match='rate limited'):
        download_prices(['SPY'], now='2026-11-11T10:00:00-05:00')


def test_downloader_adjustment_end_exclusive_and_provenance(monkeypatch):
    monkeypatch.setattr('markowitz.data.require_yahoo_collection_permission', lambda: None)
    import yfinance
    calls = []
    class Fake:
        def __init__(self, ticker):
            self.ticker = ticker
        def history(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame({'Close': [100., 101.]}, index=pd.date_range('2026-11-09', periods=2, tz='America/New_York'))
    monkeypatch.setattr(yfinance, 'Ticker', Fake)
    p, m = download_prices(['SPY'], now='2026-11-11T10:00:00-05:00')
    assert calls[0]['auto_adjust'] is True
    assert calls[0]['end'] == '2026-11-11'
    assert p.index.tz is None and m['last_observation'] == '2026-11-10'
    assert m['retrieved_utc'] and m['versions']['yfinance']


def test_explicit_archived_as_of_completeness_and_stale_disclosure():
    p = sample()
    _, r, audit, summary = audit_prices(p, ['A', 'SPY'], as_of='2016-01-12', now='2026-11-11T12:00:00-05:00')
    assert summary['as_of'] == '2016-01-12' and summary['as_of_explicit']
    assert summary['historical_as_of'] and summary['source_is_stale']
    assert summary['lost_price_rows'] == 0
    assert len(r) == len(p) - 1
    assert summary['snapshot_last_observed'] == '2016-01-12'
    assert summary['latest_complete_session'] == '2026-11-10'
    # Default audit does not silently shorten the interval to the observed date.
    _, _, _, current = audit_prices(p, ['A', 'SPY'], now='2026-11-11T12:00:00-05:00')
    assert current['as_of'] == '2026-11-10' and current['lost_price_rows'] > 0


@pytest.mark.parametrize('as_of', ['2026-11-12', '2016-01-13', '2016-01-09', '2015-12-31', '2016-01-12T01:00:00', '2016-01-12T00:00:00Z'])
def test_as_of_bounds_and_session(as_of):
    with pytest.raises(ValueError, match='as_of'):
        audit_prices(sample(), ['A', 'SPY'], as_of=as_of, now='2026-11-11T12:00:00-05:00')


def test_cutoff_cannot_hide_interior_or_excluded_tail_gaps():
    p = sample().drop(sample().index[3])
    # A gap inside the chosen period is audited and blocks downstream analysis.
    _, _, _, summary = audit_prices(p, ['A', 'SPY'], as_of='2016-01-12')
    assert summary['lost_price_rows'] == 1
    # Moving the cutoff before the missing session in a supplied longer source is rejected.
    with pytest.raises(ValueError, match='conceal missing'):
        audit_prices(p, ['A', 'SPY'], as_of='2016-01-06')


def test_cutoff_can_restrict_complete_snapshot_without_changing_splits():
    _, r, _, summary = audit_prices(sample(), ['A', 'SPY'], as_of='2016-01-08')
    assert r.index.max() == pd.Timestamp('2016-01-08')
    assert summary['source_sessions_after_as_of'] == 2
    assert summary['lost_price_rows'] == 0


def test_yahoo_collection_blocked_before_any_vendor_request(monkeypatch):
    import yfinance
    def forbidden(*args, **kwargs):
        pytest.fail('Unpermitted Yahoo client must not be called')
    monkeypatch.setattr(yfinance, 'Ticker', forbidden)
    with pytest.raises(RuntimeError, match='YAHOO RIGHTS BLOCKED'):
        download_prices()
