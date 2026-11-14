"""Separate-source, non-predictive stock/day mid-price labeling audit.

Works with verified local quote observations, never FI-2010 normalized rows.
Avoids source/stock/day mixing, invalid-book bridging and invented outcomes.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Quote:
    symbol: str
    trading_date: str
    available_at: datetime
    bid: Decimal
    ask: Decimal
    stale: bool = False
    missing_depth: bool = False


@dataclass(frozen=True)
class Label:
    row_index: int
    symbol: str
    trading_date: str
    classification: int | None  # 1 up, 2 stationary, 3 down
    target_indices: tuple[int, ...]
    excluded: str | None


def _to_decimal(value):
    if isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value))
        return d if d.is_finite() else None
    except (TypeError, ValueError, InvalidOperation):
        return None


def _valid(q):
    bid, ask = _to_decimal(q.bid), _to_decimal(q.ask)
    return (not q.stale and not q.missing_depth and bid is not None
            and ask is not None and bid > 0 and ask > bid)


def labels_from_quotes(quotes, k, threshold="0.002", max_gap_seconds=30):
    """Paper-style average-of-next-k midpoints; never cross stock/day/invalidity."""
    if type(k) is not int or k < 1:
        raise ValueError("k must be positive integer sampled-snapshot count")
    t = _to_decimal(threshold)
    if t is None or t <= 0 or t >= 1:
        raise ValueError("threshold must be 0 < t < 1")
    if max_gap_seconds is not None and (type(max_gap_seconds) not in (int, float) or not 0 < max_gap_seconds < 86400):
        raise ValueError("max_gap_seconds must be positive seconds or None")
    max_gap = timedelta(seconds=max_gap_seconds) if max_gap_seconds is not None else None
    rows = tuple(quotes)
    prior = None
    for i, q in enumerate(rows):
        if not isinstance(q, Quote) or not q.symbol or not isinstance(q.symbol, str):
            raise ValueError(f"row {i}: invalid quote or symbol")
        try:
            session = date.fromisoformat(q.trading_date)
        except (TypeError, ValueError) as ex:
            raise ValueError(f"row {i}: invalid trading day") from ex
        if session.isoformat() != q.trading_date:
            raise ValueError(f"row {i}: trading day must be canonical ISO")
        if not isinstance(q.available_at, datetime) or q.available_at.tzinfo is None or q.available_at.utcoffset() is None:
            raise ValueError(f"row {i}: timezone-aware availability required")
        if q.available_at.date() != session:
            raise ValueError(f"row {i}: availability/trading day differ")
        key = (q.trading_date, q.symbol, q.available_at)
        if prior is not None and key <= prior:
            raise ValueError(f"row {i}: repeated or unsorted stock/day/time")
        prior = key
    out = [None] * len(rows)
    i = 0
    while i < len(rows):
        q = rows[i]
        if not _valid(q):
            out[i] = Label(i, q.symbol, q.trading_date, None, (), "invalid_or_stale_quote")
            i += 1
            continue
        first, day, symbol = i, q.trading_date, q.symbol
        while i < len(rows) and rows[i].trading_date == day and rows[i].symbol == symbol and _valid(rows[i]):
            if max_gap is not None and i > first and (
                rows[i].available_at - rows[i - 1].available_at
            ) > max_gap:
                break
            i += 1
        end = i
        # Compute all midpoints and prefix sums exactly once for this contiguous
        # group. Total runtime is O(number of observations), not O(N^2).
        mids = [
            (_to_decimal(rows[j].bid) + _to_decimal(rows[j].ask)) / 2
            for j in range(first, end)
        ]
        prefix = [Decimal(0)]
        for midpoint in mids:
            prefix.append(prefix[-1] + midpoint)
        for origin in range(first, end):
            if origin + k >= end:
                out[origin] = Label(origin, symbol, day, None, (), "incomplete_future")
                continue
            offset = origin - first
            current = mids[offset]
            future_mean = (prefix[offset + k + 1] - prefix[offset + 1]) / k
            ratio = (future_mean - current) / current
            cls = 1 if ratio >= t else 3 if ratio <= -t else 2
            out[origin] = Label(origin, symbol, day, cls, tuple(range(origin + 1, origin + k + 1)), None)
    return tuple(out)
