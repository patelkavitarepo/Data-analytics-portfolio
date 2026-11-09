"""Synthetic fixtures below are mathematical test cases, never market data."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from market.analytics import analyze
from market.store import ingest, query, validate

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def sample():
    return pd.DataFrame({'date': pd.date_range('2020-01-01', periods=4),
                         'open': [100,110,88,121], 'high': [100,110,88,121],
                         'low': [100,110,88,121], 'close': [100,110,88,121],
                         'volume': [1,2,3,4], 'symbol': ['TEST']*4})


def test_known_returns_and_risk(sample):
    result = analyze(sample, 2)
    assert result['summary'].loc['TEST', 'Price return'] == pytest.approx(.21)
    assert result['summary'].loc['TEST', 'Max drawdown'] == pytest.approx(-.2)
    expected = pd.Series([.1, -.2, .375]).std() * np.sqrt(252)
    assert result['summary'].loc['TEST', 'Annualized volatility'] == pytest.approx(expected)
    assert result['summary'].loc['TEST', 'Annualized return'] == pytest.approx(1.21 ** (365.25 / 3) - 1)
    assert result['growth'].iloc[0, 0] == 1
    assert result['rolling_volatility'].iloc[0].isna().all()


def test_sql_roundtrip_upsert_and_window(tmp_path, sample):
    db = tmp_path / 'test.sqlite'
    ingest(db, sample)
    ingest(db, sample)
    rows = query(db, ['TEST'], '2020-01-02', '2020-01-04')
    assert len(rows) == 3
    assert rows.daily_return.iloc[0] == pytest.approx(.1)
    assert query(db, ["TEST' OR 1=1 --"], '2000', '2030').empty
    assert query(db, [], '2000', '2030').empty


@pytest.mark.parametrize('kind', ['missing', 'negative', 'ohlc', 'duplicate', 'infinite', 'date', 'symbol'])
def test_reject_invalid_input(sample, kind):
    if kind == 'missing': sample.loc[0, 'close'] = np.nan
    if kind == 'negative': sample.loc[0, 'volume'] = -1
    if kind == 'ohlc': sample.loc[0, 'high'] = 1
    if kind == 'duplicate': sample = pd.concat([sample, sample.iloc[:1]])
    if kind == 'infinite': sample['close'] = sample['close'].astype(float); sample.loc[0, 'close'] = np.inf
    if kind == 'date': sample['date'] = 'not-a-date'
    if kind == 'symbol': sample.loc[0, 'symbol'] = None
    with pytest.raises(ValueError): validate(sample)


def test_shared_dates_and_small_window(sample):
    other = sample.iloc[1:].assign(symbol='OTHER')
    result = analyze(pd.concat([sample, other]))
    assert len(result['prices']) == 3
    with pytest.raises(ValueError): analyze(sample.iloc[:2])


def test_bundled_real_data():
    data = validate(pd.read_csv(ROOT / 'data/history.csv'))
    assert set(data.symbol) == {'AAPL','AMZN','GOOG','MSFT'}
    assert len(data) > 4000


def test_dashboard_controls():
    from streamlit.testing.v1 import AppTest
    # App uses its project-local DB, containing only the bundled real snapshot.
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 4
    app.multiselect[0].set_value(['AAPL']).run()
    assert not app.exception
    assert app.selectbox[0].value == 'AAPL'
    app.select_slider[0].set_value(63).run()
    assert not app.exception
    app.date_input[0].set_value((pd.Timestamp('2017-01-01').date(), pd.Timestamp('2017-12-31').date())).run()
    assert not app.exception
    assert len(app.metric) == 4
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert 'Select at least one' in app.info[0].value


def test_snapshot_checksum():
    import hashlib
    import json
    meta = json.loads((ROOT / 'data/provenance.json').read_text())
    assert hashlib.sha256((ROOT / 'data/history.csv').read_bytes()).hexdigest() == meta['subset_sha256']


def test_invalid_import_is_atomic(tmp_path, sample):
    db = tmp_path / 'atomic.sqlite'
    ingest(db, sample)
    sample.loc[0, 'close'] = -1
    with pytest.raises(ValueError): ingest(db, sample)
    assert len(query(db, ['TEST'], '2020-01-01', '2020-01-04')) == 4
