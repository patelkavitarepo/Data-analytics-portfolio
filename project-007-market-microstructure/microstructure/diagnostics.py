"""Descriptive liquidity diagnostics for an authorized *local* paired LOBSTER file.

No downloads, fits, forward labels, inferred trades, fills or trading P&L.
Complete-file audit runs first; metrics are event-weighted, not time-weighted.
"""
from collections import Counter
import csv
from decimal import Decimal
import json
from pathlib import Path

from .audit import AuditError, _book, _file_hash, _message, audit_pairs


def _bucket(timestamp, seconds):
    return (int(timestamp) // seconds) * seconds


def _name(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _new_bucket(start, seconds):
    return {
        "window_start": _name(start),
        "window_end_exclusive": _name(start + seconds),
        "event_count": 0,
        "event_types": Counter(),
        "eligible_quote_count": 0,
        "one_sided_count": 0,
        "locked_or_crossed_count": 0,
        "halt_marker_count": 0,
        "halted_event_count": 0,
        "mid_move_up_count": 0,
        "mid_move_down_count": 0,
        "mid_move_unchanged_count": 0,
        "_spread_units_sum": 0,
        "_imbalance_sum": 0.0,
    }


def _complete_bucket(b):
    b = dict(b)
    count = b["eligible_quote_count"]
    b["mean_spread_usd_event_weighted"] = (
        round(b.pop("_spread_units_sum") / count / 10000, 8) if count
        else None
    )
    b["mean_depth_imbalance_event_weighted"] = (
        round(b.pop("_imbalance_sum") / count, 8) if count else None
    )
    b["event_types"] = {str(k): v for k, v in sorted(b["event_types"].items())}
    return b


def describe_pairs(messages, orderbook, levels=1, bucket_seconds=300):
    """Fully validate *both* files first, then aggregate original post-event rows.

    Bid/ask spread measured in USD using integer price units / 10000.
    Imbalance=(bid_size-ask_size)/(bid_size+ask_size), unweighted by elapsed time.
    Mid-direction compares consecutive eligible active snapshots only; no
    forward return or label is computed. Comparison can cross bucket boundaries.
    """
    if not isinstance(bucket_seconds, int) or isinstance(bucket_seconds, bool):
        raise ValueError("bucket_seconds must be an integer")
    if not 1 <= bucket_seconds <= 86400 or 86400 % bucket_seconds:
        raise ValueError("bucket_seconds must divide 86400 and be in 1..86400")
    messages, orderbook = Path(messages), Path(orderbook)
    audit = audit_pairs(messages, orderbook, levels=levels, max_events=None)
    if audit["scope"] != "complete_pair":
        raise AuditError("diagnostics require complete-file validation")

    windows = {}
    prior_mid_twice = None
    halted = False
    counted = 0
    with messages.open(newline="", encoding="utf-8") as mf, orderbook.open(
        newline="", encoding="utf-8"
    ) as bf:
        for row_num, (m, b) in enumerate(zip(csv.reader(mf), csv.reader(bf)), 1):
            timestamp, kind, marker = _message(m, row_num)
            ask, bid = _book(b, row_num, levels)
            start = _bucket(timestamp, bucket_seconds)
            if start not in windows:
                windows[start] = _new_bucket(start, bucket_seconds)
            w = windows[start]
            w["event_count"] += 1
            w["event_types"][kind] += 1
            counted += 1

            if kind == 7:
                w["halt_marker_count"] += 1
                prior_mid_twice = None
                if marker == -1:
                    halted = True
                elif marker == 1:
                    halted = False
                if halted:
                    w["halted_event_count"] += 1
                continue
            if halted:
                w["halted_event_count"] += 1
                prior_mid_twice = None
                continue
            if not ask or not bid:
                w["one_sided_count"] += 1
                prior_mid_twice = None
                continue
            if ask[0] <= bid[0]:
                w["locked_or_crossed_count"] += 1
                prior_mid_twice = None
                continue

            w["eligible_quote_count"] += 1
            w["_spread_units_sum"] += ask[0] - bid[0]
            w["_imbalance_sum"] += (bid[1] - ask[1]) / (bid[1] + ask[1])
            current_mid_twice = ask[0] + bid[0]
            if prior_mid_twice is not None:
                if current_mid_twice > prior_mid_twice:
                    w["mid_move_up_count"] += 1
                elif current_mid_twice < prior_mid_twice:
                    w["mid_move_down_count"] += 1
                else:
                    w["mid_move_unchanged_count"] += 1
            prior_mid_twice = current_mid_twice

    if counted != audit["events_checked"]:
        raise AuditError("files changed during diagnostic pass: row count differs")
    if {str(k): _file_hash(p) for k, p in (("messages", messages), ("orderbook", orderbook))} != audit["input_sha256"]:
        raise AuditError("files changed during diagnostic pass: SHA256 differs")

    return {
        "status": "descriptive_only_no_forecast_or_execution",
        "audit": audit,
        "bucket_seconds": bucket_seconds,
        "windows": [_complete_bucket(windows[k]) for k in sorted(windows)],
        "definitions": {
            "event_count": "Number of paired event rows, including quotes repeated across events.",
            "eligible_quote_count": "Two-sided uncrossed post-event snapshots outside halted state, excluding halt markers.",
            "mean_spread_usd_event_weighted": "Arithmetic mean of ask1-bid1 divided by 10000; not time-weighted.",
            "mean_depth_imbalance_event_weighted": "Arithmetic mean of (bid1_size-ask1_size)/(bid1_size+ask1_size); not time-weighted.",
            "mid_moves": "Backward-looking change from prior eligible snapshot, integer quote midpoint x2. Reset at halts, one-sided/crossed books; first after reset has no comparison.",
        },
        "limitations": [
            "Buckets only exist when events occur; no assumption of continuous observable liquidity.",
            "Event-weighted statistics oversample periods with frequent message updates.",
            "This does not reconstruct full depth or estimate queue position or execution costs.",
            "No forward label, out-of-sample strategy, market impact, or profitable signal is computed.",
            "Aggregates from actual provider data must not be publicly posted until output rights are confirmed.",
        ],
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fully audit and describe local paired LOBSTER CSVs")
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--orderbook", type=Path, required=True)
    parser.add_argument("--levels", type=int, default=1)
    parser.add_argument("--bucket-seconds", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = describe_pairs(
            args.messages, args.orderbook, levels=args.levels,
            bucket_seconds=args.bucket_seconds,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (AuditError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Complete local paired audit and descriptive diagnostics written; no model was fitted.")


if __name__ == "__main__":
    main()
