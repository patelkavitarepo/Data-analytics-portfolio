"""Streaming, strictly paired audit of locally supplied LOBSTER CSV files.

No network access, trading strategies, or causal/reconstruction claims.
Prices are fixed-point integers (USD x 10,000); time uses Decimal.
"""
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from itertools import islice, zip_longest
from pathlib import Path


class AuditError(ValueError):
    """Input violates the declared LOBSTER schema or audit invariants."""


EVENT_TYPES = {1, 2, 3, 4, 5, 6, 7}


def _integer(value, row_number, label):
    try:
        number = int(value)
    except ValueError as exc:
        raise AuditError(f"row {row_number}: invalid {label}") from exc
    return number


def _message(row, number):
    if len(row) != 6:
        raise AuditError(f"row {number}: message width must be six")
    try:
        timestamp = Decimal(row[0])
    except InvalidOperation as exc:
        raise AuditError(f"row {number}: invalid time") from exc
    if not timestamp.is_finite() or not Decimal(0) <= timestamp < Decimal(86400):
        raise AuditError(f"row {number}: time outside day or nonfinite")
    kind, oid, size, price, side = (
        _integer(value, number, label)
        for value, label in zip(row[1:], ("event type", "order id", "size", "price", "side"))
    )
    if kind not in EVENT_TYPES:
        raise AuditError(f"row {number}: unknown event type {kind}")
    if oid < 0 or size < 0:
        raise AuditError(f"row {number}: negative order id or size")
    if kind in (1, 2, 3, 4, 5) and (size == 0 or price <= 0 or side not in (-1, 1)):
        raise AuditError(f"row {number}: invalid ordinary event values")
    if kind == 7 and (oid != 0 or size != 0 or side != -1 or price not in (-1, 0, 1)):
        raise AuditError(f"row {number}: invalid halt marker")
    # Type 6 is a cross/auction trade; vendor semantics differ from resting orders.
    return timestamp, kind, price


def _book(row, number, levels):
    if len(row) != 4 * levels:
        raise AuditError(f"row {number}: book width must be {4 * levels}")
    values = [_integer(x, number, "book cell") for x in row]
    asks, bids = [], []
    for i in range(levels):
        ap, aq, bp, bq = values[4 * i:4 * i + 4]
        if aq < 0 or bq < 0:
            raise AuditError(f"row {number}: negative displayed depth")
        if aq:
            if ap <= 0:
                raise AuditError(f"row {number}: invalid occupied ask price")
            asks.append((ap, aq, i))
        if bq:
            if bp <= 0:
                raise AuditError(f"row {number}: invalid occupied bid price")
            bids.append((bp, bq, i))
    # Empty sentinel prices are intentionally ignored only when volume is zero.
    for side, items in (("ask", asks), ("bid", bids)):
        if any(level_index != position for position, (_, _, level_index) in enumerate(items)):
            raise AuditError(f"row {number}: occupied {side} after an empty level")
        prices = [price for price, _, _ in items]
        if side == "ask" and any(b <= a for a, b in zip(prices, prices[1:])):
            raise AuditError(f"row {number}: asks not strictly ascending")
        if side == "bid" and any(b >= a for a, b in zip(prices, prices[1:])):
            raise AuditError(f"row {number}: bids not strictly descending")
    return (asks[0][:2] if asks else None), (bids[0][:2] if bids else None)


def _file_hash(path):
    digest = sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_pairs(messages, orderbook, levels=1, max_events=10000):
    """Audit a paired CSV prefix; None means stream entire files.

    Equal timestamp events retain file order; no sorting, filling, or deduplication.
    A row's snapshot is the state AFTER its corresponding event, never before.
    """
    if not isinstance(levels, int) or levels < 1:
        raise ValueError("levels must be a positive integer")
    if max_events is not None and (not isinstance(max_events, int) or max_events < 1):
        raise ValueError("max_events must be positive or None")
    messages, orderbook = Path(messages), Path(orderbook)
    counts = Counter()
    rows = valid_quotes = crossed_or_locked = one_sided = timestamp_ties = 0
    sum_spread = 0
    imbalance_sum = 0.0
    previous_time = None
    previous_book = None
    trading_halted = False
    trading_halt_rows = 0
    halt_markers = Counter()

    with messages.open(newline="", encoding="utf-8") as mf, orderbook.open(
        newline="", encoding="utf-8"
    ) as bf:
        paired = zip_longest(csv.reader(mf), csv.reader(bf))
        if max_events is not None:
            paired = islice(paired, max_events)
        for rows, (message_row, book_row) in enumerate(paired, 1):
            if message_row is None or book_row is None:
                raise AuditError(f"row {rows}: message/snapshot counts differ")
            timestamp, kind, price = _message(message_row, rows)
            ask, bid = _book(book_row, rows, levels)
            current_book = tuple(cell.strip() for cell in book_row)
            if kind == 7 and previous_book is not None and current_book != previous_book:
                raise AuditError(f"row {rows}: halt marker must duplicate prior snapshot")
            previous_book = current_book
            if kind == 7:
                halt_markers[str(price)] += 1
                if price == -1:
                    trading_halted = True
                elif price == 1:
                    trading_halted = False
            trading_halt_rows += int(trading_halted)
            if previous_time is not None:
                if timestamp < previous_time:
                    raise AuditError(f"row {rows}: time reversed (no sorting allowed)")
                timestamp_ties += timestamp == previous_time
            previous_time = timestamp
            counts[kind] += 1
            if ask is None or bid is None:
                one_sided += 1
            elif ask[0] <= bid[0]:
                # Flag, never silently delete, lock/cross observations.
                crossed_or_locked += 1
            elif kind != 7 and not trading_halted:
                valid_quotes += 1
                sum_spread += ask[0] - bid[0]
                imbalance_sum += (bid[1] - ask[1]) / (bid[1] + ask[1])
    if rows == 0:
        raise AuditError("empty paired input")
    return {
        "status": "schema_audit_only_no_prediction_or_trading",
        "scope": "prefix_only" if max_events is not None else "complete_pair",
        "events_checked": rows,
        "levels": levels,
        "event_type_counts": {str(k): counts[k] for k in sorted(counts)},
        "equal_timestamp_neighbors": timestamp_ties,
        "halt_markers_by_price": {key: halt_markers[key] for key in ("-1", "0", "1")},
        "snapshots_while_trading_halted": trading_halt_rows,
        "valid_two_sided_nonhalt_quotes": valid_quotes,
        "one_sided_or_empty_quotes": one_sided,
        "locked_or_crossed_quotes": crossed_or_locked,
        "mean_spread_usd": round(sum_spread / valid_quotes / 10000, 8) if valid_quotes else None,
        "mean_best_level_imbalance": round(imbalance_sum / valid_quotes, 8)
        if valid_quotes else None,
        "input_sha256": {
            "messages": _file_hash(messages),
            "orderbook": _file_hash(orderbook),
        },
        "limitations": [
            "Sample price-range-filtered messages do not reconstruct a full exchange order book.",
            "One day or an event prefix cannot support out-of-sample trading claims.",
            "Intra-timestamp sequence is file order; no sort or inferred latency.",
            "Results describe supplied snapshots only and are not evidence of profitability.",
        ],
    }
