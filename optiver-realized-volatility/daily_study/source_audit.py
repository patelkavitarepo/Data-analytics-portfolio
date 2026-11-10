"""D007 source sampling helpers: date-guarded quality checks, no relationships.

This module never stitches histories, corrects prices, fits models or computes
cross-stock association. Future source rows are skipped before numeric parsing.
"""
import csv
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CUTOFF = '2015-12-31'


def read_csv_discovery(path, stock=None, wide_columns=None):
    rows = []
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        if not columns or not any(c.lower() == 'date' for c in columns):
            raise ValueError('Expected CSV with date header, not HTML or a pointer')
        date_col = next(c for c in columns if c.lower() == 'date')
        for row in reader:
            date = row[date_col][:10]
            # ISO dates required; fail rather than silently interpret other formats.
            if len(date) != 10 or date[4] != '-' or date[7] != '-':
                raise ValueError('Expected ISO date')
            if date > CUTOFF:
                continue
            if wide_columns:
                for name in wide_columns:
                    rows.append(dict(date=date, stock=name, close=row[name]))
            else:
                out = {k.lower():v for k,v in row.items() if k is not None and k != date_col}
                out['date'] = date
                out['stock'] = stock or out.pop('name', out.pop('ticker', None))
                if out['stock'] is None:
                    raise ValueError('Stock identity required')
                rows.append(out)
    frame = pd.DataFrame(rows)
    if not len(frame):
        return frame, columns
    frame['date'] = pd.to_datetime(frame['date'], errors='raise')
    for col in ['open','high','low','close','volume','openint']:
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors='raise')
    return frame.sort_values(['stock','date']).reset_index(drop=True), columns


def read_lean_discovery(path, stock):
    rows = []
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith('.csv')]
        if len(members) != 1:
            raise ValueError('Expected one daily CSV')
        with archive.open(members[0]) as binary:
            for row in csv.reader(io.TextIOWrapper(binary, encoding='utf-8')):
                date = row[0][:8]
                if date > '20151231':
                    continue
                if len(row) != 6:
                    raise ValueError('Unexpected daily trade-bar format')
                values = [float(v)/10000 for v in row[1:5]]
                rows.append(dict(date=pd.to_datetime(date, format='%Y%m%d'), stock=stock,
                                 **dict(zip(['open','high','low','close'],values)), volume=float(row[5])))
    return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)


def audit_prices(frame):
    if frame.empty:
        return dict(rows=0)
    if frame.date.max() > pd.Timestamp(CUTOFF):
        raise ValueError('Protected later observations in audit input')
    frame = frame.sort_values(['stock','date'])
    returns = frame.groupby('stock').close.pct_change(fill_method=None)
    summary = dict(rows=len(frame), stocks=frame.stock.nunique(), first=str(frame.date.min().date()),
                   last=str(frame.date.max().date()),
                   missing_by_column={c:int(frame[c].isna().sum()) for c in frame.columns},
                   duplicate_stock_dates=int(frame.duplicated(['stock','date']).sum()),
                   nonpositive_close=int((frame.close <= 0).sum()),
                   zero_recorded_close_change=int((returns == 0).sum()),
                   gt20pct_absolute_simple_moves_for_review=int((returns.abs() > .2).sum()),
                   gt20pct_note='Review trigger inherited from D003, not an error classification or reliability gate; no exclusions')
    if set(['open','high','low']).issubset(frame):
        ohlc = frame[['open','high','low','close']]
        complete = ohlc.notna().all(axis=1)
        contradiction = (frame.high < ohlc[['open','low','close']].max(axis=1)) | (frame.low > ohlc[['open','high','close']].min(axis=1))
        summary.update(complete_ohlc_rows=int(complete.sum()),
                       internally_inconsistent_ohlc=int((complete & contradiction).sum()),
                       nonpositive_ohlc_rows=int((ohlc <= 0).any(axis=1).sum()))
    if 'volume' in frame:
        summary['zero_volume_rows'] = int((frame.volume == 0).sum())
    return summary


def same_stock_comparison(left, right, stock, start='2013-02-08'):
    """Vendor consistency, NOT a relationship between different stocks.

    Calculate each source's return before aligning; require the same preceding
    trading date to avoid comparing a multi-day change to a one-day change.
    """
    def prepare(frame):
        data = frame[frame.stock == stock].sort_values('date').copy()
        if data.date.max() > pd.Timestamp(CUTOFF):
            raise ValueError('Protected observations in vendor comparison')
        if data.duplicated('date').any():
            raise ValueError('Duplicate source dates require adjudication')
        data['return'] = np.log(data.close.where(data.close > 0)).diff()
        data['previous_date'] = data.date.shift(1)
        return data[['date','previous_date','return']]
    paired = prepare(left).merge(prepare(right), on='date', suffixes=('_left','_right'))
    paired = paired[(paired.date >= pd.Timestamp(start)) & (paired.previous_date_left == paired.previous_date_right)]
    delta = (paired.return_left-paired.return_right).dropna().abs()*10000
    return dict(stock=stock, matched_return_intervals=len(delta),
                absolute_log_return_difference_basis_points={str(q):float(delta.quantile(q)) for q in [.5,.9,.95,.99,1]},
                note='Same-stock cross-vendor comparison only. Dividend conventions/rounding may explain differences; not automatic data errors.')


def period_coverage(frame, periods):
    if len(frame) and frame.date.max() > pd.Timestamp(CUTOFF):
        raise ValueError('Protected observations in period coverage')
    output=[]
    for name,start,end in periods:
        subset=frame[(frame.date >= start)&(frame.date <= end)]
        output.append(dict(period=name,start=start,end=end,rows=len(subset),
                           sample_stocks_observed=int(subset.stock.nunique()),
                           distinct_sample_dates=int(subset.date.nunique()),
                           scope='Availability only, not a stress-state definition or independent episode count'))
    return output
