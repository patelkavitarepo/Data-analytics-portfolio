"""Synthetic-only prospective label and chronological split prototypes.

NO real-market ingestion, performance scoring, model fit, or execution inference.
This module deliberately consumes explicit in-memory snapshots rather than
loading provider CSVs; its rules are *proposals* pending human horizon signoff.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal, Sequence


State = Literal["active", "halt", "unusable"]


@dataclass(frozen=True)
class Snapshot:
    session: str  # strict ISO 8601 trading-date string
    time: Decimal  # seconds since midnight at exchange-local time
    state: State
    bid_price: int | None = None  # USD x 10,000
    ask_price: int | None = None
    bid_size: int | None = None
    ask_size: int | None = None


@dataclass(frozen=True)
class ProspectiveLabel:
    session: str
    origin_index: int
    origin_time: Decimal
    origin_imbalance: Decimal | None
    target_index: int | None
    target_time: Decimal | None
    direction: int | None   # -1: down, 0: unchanged, +1: up
    reason: str | None      # excluded states are always explicitly retained


@dataclass(frozen=True)
class SessionPlan:
    train: tuple[str, ...]
    embargo_train_validation: tuple[str, ...]
    validation: tuple[str, ...]
    embargo_validation_holdout: tuple[str, ...]
    holdout: tuple[str, ...]


def _time(value):
    if isinstance(value, bool):
        raise ValueError("bool is not a valid time")
    try:
        result = Decimal(str(value))
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("time must be finite seconds") from exc
    if not result.is_finite():
        raise ValueError("time must be finite seconds")
    return result


def _valid(snapshot):
    if snapshot.state != "active":
        return False
    p = (snapshot.bid_price, snapshot.ask_price, snapshot.bid_size, snapshot.ask_size)
    if any(type(x) is not int for x in p):
        return False
    bid, ask, bs, ass = p
    return bid > 0 and ask > bid and bs > 0 and ass > 0


def _check_snapshots(rows: Sequence[Snapshot]):
    """Refuse out-of-order, overlapping, or invalid session/time metadata."""
    last_date = None
    last_time = None
    for i, row in enumerate(rows):
        if not isinstance(row, Snapshot):
            raise ValueError(f"row {i}: expected Snapshot")
        try:
            parsed_date = date.fromisoformat(row.session)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"row {i}: invalid ISO session") from exc
        if row.session != parsed_date.isoformat():
            raise ValueError(f"row {i}: session must be canonical YYYY-MM-DD")
        t = _time(row.time)
        if t < 0 or t >= 86400:
            raise ValueError(f"row {i}: time outside exchange-local day")
        if row.state not in ("active", "halt", "unusable"):
            raise ValueError(f"row {i}: invalid state")
        if last_date is not None:
            if parsed_date < last_date or (parsed_date == last_date and t < last_time):
                raise ValueError(f"row {i}: unsorted sessions or reversed timestamps")
        if last_date != parsed_date:
            last_time = None
        last_date, last_time = parsed_date, t


def label_after_elapsed_time(rows: Sequence[Snapshot], horizon_seconds):
    """Return one label record per supplied row; no hidden row removal.

    The target is the first VALID post-event quote at/after origin+h, with
    STRICTLY later timestamp, in the SAME contiguous active segment/day.
    At equal timestamps, source ordering is preserved but no same-time row can
    serve as a target. Halts/unusable/locked/crossed/one-sided rows break a
    segment; never silently bridge a gap. Zero-change is a real class.
    No fill probabilities or alpha predictions are inferred.
    """
    horizon = _time(horizon_seconds)
    if horizon <= 0 or horizon >= 86400:
        raise ValueError("horizon must be >0 and <86400 seconds")
    rows = tuple(rows)
    _check_snapshots(rows)
    output: list[ProspectiveLabel | None] = [None] * len(rows)
    i = 0
    while i < len(rows):
        item = rows[i]
        if not _valid(item):
            output[i] = ProspectiveLabel(
                item.session, i, _time(item.time), None, None, None, None,
                "unusable_origin" if item.state == "active" else item.state,
            )
            i += 1
            continue
        start = i
        session = item.session
        while i < len(rows) and rows[i].session == session and _valid(rows[i]):
            i += 1
        end = i
        interrupted = i < len(rows) and rows[i].session == session
        pointer = start + 1
        for origin in range(start, end):
            current = rows[origin]
            current_time = _time(current.time)
            pointer = max(pointer, origin + 1)
            threshold = current_time + horizon
            while pointer < end and _time(rows[pointer].time) < threshold:
                pointer += 1
            target = pointer if pointer < end else None
            origin_imbalance = (
                Decimal(current.bid_size - current.ask_size)
                / Decimal(current.bid_size + current.ask_size)
            )
            if target is None:
                output[origin] = ProspectiveLabel(
                    session, origin, current_time, origin_imbalance,
                    None, None, None,
                    "interrupted_before_horizon" if interrupted else "end_of_session",
                )
            else:
                future = rows[target]
                current_mid_twice = current.bid_price + current.ask_price
                future_mid_twice = future.bid_price + future.ask_price
                direction = (future_mid_twice > current_mid_twice) - (
                    future_mid_twice < current_mid_twice
                )
                output[origin] = ProspectiveLabel(
                    session, origin, current_time, origin_imbalance,
                    target, _time(future.time), direction, None,
                )
    return tuple(output)


def prototype_session_partition(
    sessions: Sequence[str],
    train_count: int,
    validation_count: int,
    holdout_count: int,
    embargo_sessions: int = 1,
):
    """Separate full chronological sessions, including embargo sessions.

    Deliberately refuses one-day samples, unsorted or duplicated sessions,
    unallocated days and implicit randomized splits. Holdout is *planned* only;
    nothing here reads or evaluates its prices/outcomes.
    """
    numbers = (train_count, validation_count, holdout_count, embargo_sessions)
    if any(type(n) is not int for n in numbers):
        raise ValueError("partition sizes must be integers")
    if min(train_count, validation_count, holdout_count) < 1 or embargo_sessions < 1:
        raise ValueError("positive groups and at least one embargo session required")
    days = tuple(sessions)
    parsed = []
    for session in days:
        if type(session) is not str:
            raise ValueError("sessions must be ISO date strings")
        try:
            d = date.fromisoformat(session)
        except ValueError as exc:
            raise ValueError("invalid ISO date") from exc
        if d.isoformat() != session:
            raise ValueError("session not canonical")
        parsed.append(d)
    if any(b <= a for a, b in zip(parsed, parsed[1:])):
        raise ValueError("sessions must be strictly increasing and unique")
    required = train_count + validation_count + holdout_count + 2 * embargo_sessions
    if len(days) != required:
        raise ValueError(
            f"need exactly {required} distinct sessions for this provisional plan; got {len(days)}"
        )
    k = 0
    train = days[k:k + train_count]
    k += train_count
    gap1 = days[k:k + embargo_sessions]
    k += embargo_sessions
    valid = days[k:k + validation_count]
    k += validation_count
    gap2 = days[k:k + embargo_sessions]
    k += embargo_sessions
    holdout = days[k:k + holdout_count]
    return SessionPlan(train, gap1, valid, gap2, holdout)
