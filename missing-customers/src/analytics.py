"""Retailrocket intake and visitor-level observational analysis. All times are UTC."""
from pathlib import Path
import pandas as pd

EVENTS = ['view', 'addtocart', 'transaction']
REQUIRED = {'timestamp', 'visitorid', 'event', 'itemid'}
MAX_BYTES = 100 * 1024 * 1024


def load_csv(source):
    """Read bounded CSV as strings so identifiers never lose leading zeros."""
    size = Path(source).stat().st_size if isinstance(source, (str, Path)) else source.size if hasattr(source, 'size') else None
    if size is not None and size > MAX_BYTES:
        raise ValueError('CSV exceeds 100 MiB. Use the offline date-slice CLI first.')
    try:
        frame = pd.read_csv(source, dtype='string')
    except pd.errors.EmptyDataError as exc:
        raise ValueError('CSV is empty; include the required header.') from exc
    return prepare(frame)


def prepare(raw):
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(sorted(missing)))
    df = raw.copy()
    for col in df.columns:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    numeric = pd.to_numeric(df.timestamp, errors='coerce')
    # Retailrocket specifies integer Unix milliseconds, never seconds or inferred units.
    valid_ms = numeric.notna() & numeric.mod(1).eq(0) & numeric.ge(946684800000) & numeric.lt(4102444800000)
    df['time'] = pd.to_datetime(numeric.where(valid_ms).astype('float64'), unit='ms', utc=True, errors='coerce')
    duplicate = df.duplicated(subset=list(raw.columns))
    valid = df.time.notna() & df.visitorid.notna() & df.event.isin(EVENTS)
    reversed_rows = df.loc[valid].groupby('visitorid', sort=False).time.diff().lt(pd.Timedelta(0))
    reversed_visitors = df.loc[reversed_rows.index[reversed_rows], 'visitorid'].nunique()
    audit = {
        'input_rows': len(df), 'distinct_identified_visitors': int(df.visitorid.nunique()),
        'missing_visitor_ids': int(df.visitorid.isna().sum()),
        'missing_item_ids': int(df.itemid.isna().sum()),
        'invalid_timestamps': int(df.time.isna().sum()),
        'unknown_or_missing_events': int((~df.event.isin(EVENTS)).sum()),
        'exact_duplicate_rows': int(duplicate.sum()),
        'visitors_with_input_order_reversals': int(reversed_visitors),
        'excluded_invalid_rows': int((~valid).sum()),
        'duplicate_valid_rows_removed': int((valid & duplicate).sum()),
        'fields_available': ', '.join(raw.columns),
        'null_counts_by_field': {col: int(df[col].isna().sum()) for col in raw.columns},
        'input_event_type_counts': {str(k): int(v) for k, v in df.event.fillna('(missing)').value_counts().items()},
    }
    clean = df.loc[valid & ~duplicate].sort_values('time', kind='stable').reset_index(drop=True)
    audit['analysis_rows'] = len(clean)
    return clean, audit


def stage_counts(df):
    return pd.DataFrame({'event': EVENTS, 'events': [int(df.event.eq(e).sum()) for e in EVENTS],
                         'visitors': [int(df.loc[df.event.eq(e), 'visitorid'].nunique()) for e in EVENTS]})


def journey(df, item_matched=False):
    """Earliest strict progression, ties excluded; one row per view entrant visitor.

    Item-matched paths require the same item across all three stages. A visitor
    counts once even when several items qualify. No session or identity inference.
    """
    keys = ['visitorid', 'itemid'] if item_matched else ['visitorid']
    data = df.dropna(subset=keys)
    views = data.loc[data.event.eq('view')].groupby(keys).time.min().rename('view_time').reset_index()
    carts = data.loc[data.event.eq('addtocart'), keys + ['time']].merge(views, on=keys)
    carts = carts.loc[carts.time.gt(carts.view_time)].groupby(keys).time.min().rename('cart_time').reset_index()
    transactions = data.loc[data.event.eq('transaction'), keys + ['time']].merge(carts, on=keys)
    transactions = transactions.loc[transactions.time.gt(transactions.cart_time)].groupby(keys).time.min().rename('transaction_time').reset_index()
    paths = views.merge(carts, on=keys, how='left').merge(transactions, on=keys, how='left')
    if item_matched:
        return paths.groupby('visitorid')[['view_time', 'cart_time', 'transaction_time']].min().reset_index()
    return paths


def funnel(cohort):
    counts = [len(cohort), int(cohort.cart_time.notna().sum()), int(cohort.transaction_time.notna().sum())]
    return pd.DataFrame({'stage': ['Viewed', 'Then added to cart', 'Then transacted'], 'visitors': counts,
                         'percent_of_view_entrants': [100 * n / counts[0] if counts[0] else 0.0 for n in counts]})
