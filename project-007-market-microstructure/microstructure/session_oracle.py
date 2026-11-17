"""Independent, intentionally O(N*k) D008 session-label verification oracle.

Does not call the optimized segment builder, its session classifier, or its
price helper. Source-local and non-predictive; cross-session future windows
are rejected even when there is no maximum time-gap restriction.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from .session_labels import session_labels_from_quotes


def _session(dt):
    if not isinstance(dt, datetime) or dt.utcoffset() != timedelta(hours=8):
        raise ValueError("source timestamp is not aware UTC+08:00")
    hms = dt.timetz().replace(tzinfo=None)
    if time(9,30) <= hms <= time(11,30):
        return 1
    if time(13,0) <= hms <= time(15,0):
        return 2
    return 0


def _usable(q):
    if q.stale is not False or q.missing_depth is not False:
        return False
    try:
        b, a = Decimal(str(q.bid)), Decimal(str(q.ask))
    except (ValueError, TypeError, InvalidOperation):
        return False
    return b.is_finite() and a.is_finite() and b > 0 and a > b


def independent_session_labels(quotes, k, threshold="0.002", max_gap_seconds=30):
    """Compute an oracle tuple for each row: (class, future indices, reason)."""
    obs = tuple(quotes)
    limit = Decimal(str(threshold))
    output = []
    for i, origin in enumerate(obs):
        current_session = _session(origin.available_at)
        if not current_session:
            output.append((None, (), "outside_session"))
            continue
        if not _usable(origin):
            output.append((None, (), "invalid_or_stale_quote"))
            continue
        previous = origin
        target = []
        for j in range(i + 1, min(len(obs), i + k + 1)):
            future = obs[j]
            if (future.symbol != origin.symbol
                    or future.trading_date != origin.trading_date
                    or _session(future.available_at) != current_session
                    or not _usable(future)
                    or (max_gap_seconds is not None
                        and (future.available_at - previous.available_at).total_seconds()
                        > max_gap_seconds)):
                break
            target.append(j)
            previous = future
        if len(target) != k:
            output.append((None, (), "incomplete_future"))
            continue
        current_mid = (Decimal(str(origin.ask)) + Decimal(str(origin.bid))) / 2
        mids = [(Decimal(str(obs[j].ask)) + Decimal(str(obs[j].bid))) / 2
                for j in target]
        avg_future = sum(mids, Decimal(0)) / k
        change = (avg_future - current_mid) / current_mid
        category = 1 if change >= limit else 3 if change <= -limit else 2
        output.append((category, tuple(target), None))
    return tuple(output)


def verify_session_labels(quotes, k, threshold="0.002", max_gap_seconds=30):
    rows = tuple(quotes)
    actual = session_labels_from_quotes(rows, k, threshold, max_gap_seconds)
    expected = independent_session_labels(rows, k, threshold, max_gap_seconds)
    if len(actual) != len(expected):
        raise AssertionError("oracle/source label record count mismatch")
    for idx, (source, independent) in enumerate(zip(actual, expected)):
        if (source.classification, source.target_indices, source.excluded) != independent:
            raise AssertionError(
                f"session oracle disagreement at row {idx}, horizon {k}"
            )
    return {
        "rows_verified": len(rows),
        "mismatches": 0,
        "independent_verification": True,
        "not_a_forecast": True,
    }
