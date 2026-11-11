"""Independent recalculation of descriptive liquidity reports.

Uses its own CSV decoding and aggregation, not the project's audit/diagnostics
parsers. No provider download or predictive/trading outputs are supported.
"""
import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path

from .paths import safe_report_output


class VerificationError(ValueError):
    """Reported statistics are stale, incomplete, inconsistent or corrupted."""


def _sha256(path):
    digest = sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _check(actual, expected, label):
    if actual != expected:
        raise VerificationError(f"{label}: independent mismatch: observed {actual!r}, reported {expected!r}")


def _metric(actual, expected, label, atol="0.00000002"):
    if expected is None:
        _check(actual, None, label)
        return
    if actual is None:
        raise VerificationError(f"{label}: reported nonempty mean with zero denominator")
    try:
        delta = abs(Decimal(str(actual)) - Decimal(str(expected)))
    except (InvalidOperation, TypeError) as exc:
        raise VerificationError(f"{label}: reported metric is invalid") from exc
    if not delta.is_finite() or delta > Decimal(atol):
        raise VerificationError(
            f"{label}: independent mismatch: observed {actual!r}, reported {expected!r}"
        )


def _bucket(t, size):
    start = int(t) // size * size
    return f"{start // 3600:02d}:{start % 3600 // 60:02d}:{start % 60:02d}"


def _window():
    return {
        "event_count": 0, "event_types": Counter(),
        "eligible_quote_count": 0, "one_sided_count": 0,
        "locked_or_crossed_count": 0, "halt_marker_count": 0,
        "halted_event_count": 0, "mid_move_up_count": 0,
        "mid_move_down_count": 0, "mid_move_unchanged_count": 0,
        "spread_sum": 0, "imbalance_sum": Decimal(0),
    }


def independently_verify(messages, orderbook, report):
    """Recompute a complete local report from raw records using separate math."""
    messages, orderbook = Path(messages), Path(orderbook)
    if isinstance(report, (str, Path)):
        report = json.loads(Path(report).read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("status") != "descriptive_only_no_forecast_or_execution":
        raise VerificationError("expected a descriptive report, not a model or trading result")
    audit = report.get("audit")
    if not isinstance(audit, dict) or audit.get("scope") != "complete_pair":
        raise VerificationError("only full-file paired audits can be independently verified")
    levels, seconds = audit.get("levels"), report.get("bucket_seconds")
    if type(levels) is not int or levels < 1:
        raise VerificationError("invalid declared depth")
    if type(seconds) is not int or seconds < 1 or 86400 % seconds:
        raise VerificationError("invalid declared window size")
    original_hashes = audit.get("input_sha256")
    hashes = {"messages": _sha256(messages), "orderbook": _sha256(orderbook)}
    _check(hashes, original_hashes, "source file SHA256")

    windows = {}
    event_types, halt_markers = Counter(), Counter()
    total_rows = ties = one_sided = locked = eligible = halted_count = 0
    spread_sum = 0
    imbalance_sum = Decimal(0)
    previous_time = previous_mid = None
    halted = False

    # Independent math uses Decimal ratios and no shared parsing functions.
    with localcontext() as ctx:
        ctx.prec = 34
        with messages.open(newline="", encoding="utf-8") as fm, orderbook.open(
            newline="", encoding="utf-8"
        ) as fb:
            for index, (m, b) in enumerate(zip_longest(csv.reader(fm), csv.reader(fb)), 1):
                if m is None or b is None:
                    raise VerificationError(f"row {index}: unequal paired lengths")
                if len(m) != 6 or len(b) != levels * 4:
                    raise VerificationError(f"row {index}: unexpected message/book width")
                try:
                    timestamp = Decimal(m[0])
                    event = int(m[1])
                    marker = int(m[4])
                    cells = [int(v) for v in b]
                except (InvalidOperation, ValueError, OverflowError) as exc:
                    raise VerificationError(f"row {index}: invalid numerical data") from exc
                if not timestamp.is_finite() or not 0 <= timestamp < 86400:
                    raise VerificationError(f"row {index}: invalid timestamp")
                if previous_time is not None:
                    if timestamp < previous_time:
                        raise VerificationError(f"row {index}: reversed timestamp")
                    ties += timestamp == previous_time
                previous_time = timestamp
                key = _bucket(timestamp, seconds)
                if key not in windows:
                    windows[key] = _window()
                w = windows[key]
                total_rows += 1
                w["event_count"] += 1
                w["event_types"][event] += 1
                event_types[event] += 1

                if event == 7:
                    w["halt_marker_count"] += 1
                    halt_markers[str(marker)] += 1
                    if marker == -1:
                        halted = True
                    elif marker == 1:
                        halted = False
                    if halted:
                        w["halted_event_count"] += 1
                        halted_count += 1
                    previous_mid = None
                    continue
                if halted:
                    w["halted_event_count"] += 1
                    halted_count += 1
                    previous_mid = None
                    continue

                # Read the first occupied price level from each *side*.
                # Do not use the production _book() logic.
                asks = [(cells[i], cells[i + 1]) for i in range(0, len(cells), 4) if cells[i + 1] > 0]
                bids = [(cells[i + 2], cells[i + 3]) for i in range(0, len(cells), 4) if cells[i + 3] > 0]
                if not asks or not bids:
                    w["one_sided_count"] += 1
                    one_sided += 1
                    previous_mid = None
                    continue
                ask_price, ask_size = asks[0]
                bid_price, bid_size = bids[0]
                if ask_price <= bid_price:
                    w["locked_or_crossed_count"] += 1
                    locked += 1
                    previous_mid = None
                    continue
                if ask_size <= 0 or bid_size <= 0:
                    raise VerificationError("invalid displayed depth")

                w["eligible_quote_count"] += 1
                eligible += 1
                diff = ask_price - bid_price
                w["spread_sum"] += diff
                spread_sum += diff
                imbalance = (Decimal(bid_size) - Decimal(ask_size)) / Decimal(bid_size + ask_size)
                w["imbalance_sum"] += imbalance
                imbalance_sum += imbalance
                mid_twice = ask_price + bid_price
                if previous_mid is not None:
                    field = ("mid_move_up_count" if mid_twice > previous_mid
                             else "mid_move_down_count" if mid_twice < previous_mid
                             else "mid_move_unchanged_count")
                    w[field] += 1
                previous_mid = mid_twice

        # Detect edits that happened during our independent re-reading.
        _check({"messages": _sha256(messages), "orderbook": _sha256(orderbook)}, hashes,
               "source file stability")
        if total_rows == 0:
            raise VerificationError("empty report source")
        _check(total_rows, audit.get("events_checked"), "overall row count")
        _check({str(k): v for k, v in sorted(event_types.items())},
               audit.get("event_type_counts"), "overall event counts")
        _check(ties, audit.get("equal_timestamp_neighbors"), "equal timestamp count")
        _check({key: halt_markers[key] for key in ("-1", "0", "1")},
               audit.get("halt_markers_by_price"), "halt marker counts")
        _check(halted_count, audit.get("snapshots_while_trading_halted"), "halted row count")
        _check(eligible, audit.get("valid_two_sided_nonhalt_quotes"), "eligible quote count")
        _check(one_sided, audit.get("one_sided_or_empty_quotes"), "one-sided quote count")
        _check(locked, audit.get("locked_or_crossed_quotes"), "locked/crossed quote count")
        _metric(spread_sum / eligible / 10000 if eligible else None,
                audit.get("mean_spread_usd"), "overall spread")
        _metric(imbalance_sum / Decimal(eligible) if eligible else None,
                audit.get("mean_best_level_imbalance"), "overall imbalance")

        reported = report.get("windows")
        if not isinstance(reported, list):
            raise VerificationError("no reported windows")
        _check(len(windows), len(reported), "window count")
        names = sorted(windows)
        for index, (key, expected) in enumerate(zip(names, reported), 1):
            if not isinstance(expected, dict):
                raise VerificationError(f"window {index}: not an object")
            w = windows[key]
            prefix = f"window {key}"
            _check(key, expected.get("window_start"), f"{prefix} start")
            start = int(key[:2]) * 3600 + int(key[3:5]) * 60 + int(key[6:8])
            ending = start + seconds
            _check(f"{ending // 3600:02d}:{ending % 3600 // 60:02d}:{ending % 60:02d}",
                   expected.get("window_end_exclusive"), f"{prefix} end")
            for field in (
                "event_count", "eligible_quote_count", "one_sided_count",
                "locked_or_crossed_count", "halt_marker_count", "halted_event_count",
                "mid_move_up_count", "mid_move_down_count", "mid_move_unchanged_count"
            ):
                _check(w[field], expected.get(field), f"{prefix} {field}")
            _check({str(k): v for k, v in sorted(w["event_types"].items())},
                   expected.get("event_types"), f"{prefix} event types")
            n = w["eligible_quote_count"]
            _metric(w["spread_sum"] / n / 10000 if n else None,
                    expected.get("mean_spread_usd_event_weighted"), f"{prefix} mean spread")
            _metric(w["imbalance_sum"] / Decimal(n) if n else None,
                    expected.get("mean_depth_imbalance_event_weighted"),
                    f"{prefix} mean depth imbalance")
    return {
        "status": "independently_verified_descriptive_report",
        "source_sha256": hashes,
        "events_verified": total_rows,
        "windows_verified": len(windows),
        "method": "separate complete CSV pass, Decimal depth ratios, independent window recomputation",
        "limitations": [
            "Only internal arithmetic reproducibility, not economic validity or vendor permission.",
            "No price prediction, fills, queue-position inference, or trading returns evaluated.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Independently verify a local descriptive report")
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--orderbook", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report_path = safe_report_output(args.report)
        output_path = safe_report_output(args.output)
        if output_path == report_path:
            raise VerificationError("verification output cannot overwrite report under review")
        verified = independently_verify(args.messages, args.orderbook, report_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(verified, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    except (VerificationError, ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print("Independent recomputation passed. This does NOT establish market validity.")


if __name__ == "__main__":
    main()
