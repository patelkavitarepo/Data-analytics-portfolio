"""Exchange-session-aware quote-label construction on a separate Shenzhen source.

D008: noncommercial research on Quant-Arena Public L1, NOT FI-2010.
This is a retrospective LABEL construction routine, not a prediction model.

Important:
- Morning [09:30, 11:30] and afternoon [13:00, 15:00] are distinct
  operational session groups for this pinned source. The last 3 minutes
  may reflect a closing call auction; this routine does not claim they are
  continuously tradable or equivalent to the morning.
- Explicit session partition works even if max_gap_seconds=None.
- The old stockday_labels module is unmodified so historical receipts remain
  reproducible.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from .stockday_labels import Label, Quote


MORNING_START = time(9, 30)
MORNING_END = time(11, 30)
AFTERNOON_START = time(13, 0)
AFTERNOON_END = time(15, 0)
EXCHANGE_UTC_OFFSET = timedelta(hours=8)


def exchange_session(timestamp):
    """Exchange-local operational labels; explicit out-of-session rejection."""
    if (not isinstance(timestamp, datetime) or timestamp.tzinfo is None
            or timestamp.utcoffset() != EXCHANGE_UTC_OFFSET):
        raise ValueError("quote timestamp must be timezone-aware UTC+08:00")
    clock = timestamp.timetz().replace(tzinfo=None)
    if MORNING_START <= clock <= MORNING_END:
        return "morning"
    if AFTERNOON_START <= clock <= AFTERNOON_END:
        return "afternoon"
    return None


def _price(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        dec = Decimal(str(value))
        return dec if dec.is_finite() else None
    except (ValueError, TypeError, InvalidOperation):
        return None


def _valid(q):
    bid, ask = _price(q.bid), _price(q.ask)
    return (q.stale is False and q.missing_depth is False
            and bid is not None and ask is not None and bid > 0 and ask > bid)


def session_labels_from_quotes(quotes, k, threshold="0.002", max_gap_seconds=30):
    """Retrospective mean-next-k midpoint label with hard session isolation.

    One Label for every original row, preserving source row index. Invalid or
    outside-session origin has no target; at session end, incomplete targets
    are not invented. Valid contiguous segments use O(N) Decimal prefix sums.
    """
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    t = _price(threshold)
    if t is None or not 0 < t < 1:
        raise ValueError("threshold must be a finite decimal strictly between 0 and 1")
    if (max_gap_seconds is not None and
            (type(max_gap_seconds) not in (int, float)
             or not 0 < max_gap_seconds < 86400)):
        raise ValueError("max_gap_seconds must be positive or None")

    rows = tuple(quotes)
    sessions = []
    previous_key = None
    for i, q in enumerate(rows):
        if not isinstance(q, Quote) or not isinstance(q.symbol, str) or not q.symbol.strip():
            raise ValueError(f"row {i}: missing or malformed stock identity")
        try:
            day = date.fromisoformat(q.trading_date)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"row {i}: invalid trading date") from exc
        if day.isoformat() != q.trading_date:
            raise ValueError(f"row {i}: date not canonical ISO")
        session = exchange_session(q.available_at)
        if q.available_at.date() != day:
            raise ValueError(f"row {i}: source exchange date conflicts with trading date")
        key = (q.trading_date, q.symbol, q.available_at)
        if previous_key is not None and key <= previous_key:
            raise ValueError(f"row {i}: duplicated or unsorted stock/date/timestamp")
        previous_key = key
        sessions.append(session)

    out = [None] * len(rows)
    max_gap = timedelta(seconds=max_gap_seconds) if max_gap_seconds is not None else None
    i = 0
    while i < len(rows):
        q = rows[i]
        if sessions[i] is None:
            out[i] = Label(i, q.symbol, q.trading_date, None, (), "outside_session")
            i += 1
            continue
        if not _valid(q):
            out[i] = Label(i, q.symbol, q.trading_date, None, (), "invalid_or_stale_quote")
            i += 1
            continue
        start, symbol, day, session = i, q.symbol, q.trading_date, sessions[i]
        while (i < len(rows) and rows[i].symbol == symbol
               and rows[i].trading_date == day and sessions[i] == session
               and _valid(rows[i])):
            if max_gap is not None and i > start and (
                rows[i].available_at - rows[i - 1].available_at
            ) > max_gap:
                break
            i += 1
        end = i
        mids = [(_price(rows[j].bid) + _price(rows[j].ask)) / 2
                for j in range(start, end)]
        prefix = [Decimal(0)]
        for mid in mids:
            prefix.append(prefix[-1] + mid)
        for origin in range(start, end):
            if origin + k >= end:
                out[origin] = Label(origin, symbol, day, None, (), "incomplete_future")
                continue
            offset = origin - start
            future_mean = (prefix[offset + k + 1] - prefix[offset + 1]) / k
            relative = (future_mean - mids[offset]) / mids[offset]
            klass = 1 if relative >= t else 3 if relative <= -t else 2
            out[origin] = Label(origin, symbol, day, klass,
                                tuple(range(origin + 1, origin + k + 1)), None)
    return tuple(out)
