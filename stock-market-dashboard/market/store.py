"""Validated OHLCV storage. Queries use bound parameters."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import pandas as pd

COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']


def validate(frame):
    if not set(COLUMNS).issubset(frame.columns):
        raise ValueError('Expected date, open, high, low, close, volume, symbol columns')
    data = frame[COLUMNS].copy()
    if data.empty:
        raise ValueError('No market observations supplied')
    if data.isna().any().any():
        raise ValueError('Missing market values')
    data['date'] = pd.to_datetime(data['date'], format='ISO8601', errors='raise').dt.strftime('%Y-%m-%d')
    data['symbol'] = data['symbol'].astype(str).str.strip().str.upper()
    nums = COLUMNS[1:6]
    data[nums] = data[nums].apply(pd.to_numeric, errors='raise')
    if data.isna().any().any() or not np.isfinite(data[nums]).all().all():
        raise ValueError('Missing or non-finite market values')
    if (data[nums[:4]] <= 0).any().any() or (data.volume < 0).any():
        raise ValueError('Prices must be positive and volume nonnegative')
    if ((data.high < data[['open', 'close', 'low']].max(axis=1)) |
            (data.low > data[['open', 'close', 'high']].min(axis=1))).any():
        raise ValueError('Inconsistent OHLC prices')
    if not data.symbol.str.fullmatch(r'[A-Z][A-Z0-9.\-]{0,14}').all():
        raise ValueError('Invalid symbol')
    if data.duplicated(['date', 'symbol']).any():
        raise ValueError('Duplicate symbol/date observations')
    return data.sort_values(['symbol', 'date'])


@contextmanager
def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript('''
    CREATE TABLE IF NOT EXISTS prices (
      date TEXT NOT NULL, open REAL NOT NULL, high REAL NOT NULL,
      low REAL NOT NULL, close REAL NOT NULL, volume REAL NOT NULL,
      symbol TEXT NOT NULL, PRIMARY KEY(symbol,date));
    CREATE VIEW IF NOT EXISTS daily_returns AS
      SELECT *, close / LAG(close) OVER (PARTITION BY symbol ORDER BY date) - 1 AS daily_return
      FROM prices;
    ''')
    try:
        with con:
            yield con
    finally:
        con.close()


def ingest(path, frame):
    data = validate(frame)
    with connect(path) as con:
        con.executemany('INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?,?)',
                        data.itertuples(index=False, name=None))
    return len(data)


def query(path, symbols, start, end):
    if not symbols:
        return pd.DataFrame(columns=COLUMNS + ['daily_return'])
    marks = ','.join('?' for _ in symbols)
    with connect(path) as con:
        return pd.read_sql_query(
            f'SELECT * FROM daily_returns WHERE symbol IN ({marks}) AND date BETWEEN ? AND ? ORDER BY date,symbol',
            con, params=[*symbols, str(start), str(end)], parse_dates=['date'])
