"""D007: timestamp-gap source diagnosis, independent labels, unsafe stress only.

Official SZSE schedule has continuous auctions 09:30–11:30 and 13:00–14:57
Asia/Shanghai. A near-lunch classification is a documented heuristic, not
an inference that the publisher's timestamps are authentic exchange events.

Uses same noncommercial CC BY-NC 4.0 source, three stocks/five dates only.
Never emits bid/ask prices, raw rows, predictive scores, or trading results.
"""
from collections import Counter
from datetime import time
from dataclasses import replace

from .quote_quality_sensitivity import (
    FROZEN_PRIMARY, _counts, _compare, _price_valid, _transform_flags
)
from .stockday_labels import labels_from_quotes
from .stockday_oracle import verify_labels


HORIZON = 5
THRESHOLD = "0.002"
PRIMARY_GAP_SECONDS = 30
LONG_GAP_SECONDS = 120
EXPECTED_LONG_GAPS_PER_STOCK = 5
BEFORE_WINDOW = (time(11, 28, 0), time(11, 30, 30))
AFTER_WINDOW = (time(12, 59, 0), time(13, 2, 0))


def _lunch_match(before, after):
    return (BEFORE_WINDOW[0] <= before.timetz().replace(tzinfo=None) <= BEFORE_WINDOW[1]
            and AFTER_WINDOW[0] <= after.timetz().replace(tzinfo=None) <= AFTER_WINDOW[1])


def _long_gap_edges(quotes, symbol):
    gaps = []
    for i in range(1, len(quotes)):
        before, after = quotes[i - 1], quotes[i]
        if before.symbol != symbol or after.symbol != symbol:
            raise ValueError("unregistered symbol in quote panel")
        if before.trading_date != after.trading_date:
            continue  # session transitions are NOT intraday gaps
        delta = (after.available_at - before.available_at).total_seconds()
        if delta <= 0:
            raise ValueError("source time not strictly increasing")
        if delta <= LONG_GAP_SECONDS:
            continue
        gaps.append({
            "left_index": i - 1, "right_index": i,
            "day": before.trading_date,
            "start_local": before.available_at.time().isoformat(timespec="seconds"),
            "end_local": after.available_at.time().isoformat(timespec="seconds"),
            "duration_seconds": int(delta) if delta.is_integer() else delta,
            "matches_frozen_lunch_time_heuristic": _lunch_match(
                before.available_at, after.available_at
            ),
            "before": {
                "stale": bool(before.stale),
                "missing_depth": bool(before.missing_depth),
                "price_valid": _price_valid(before),
            },
            "after": {
                "stale": bool(after.stale),
                "missing_depth": bool(after.missing_depth),
                "price_valid": _price_valid(after),
            },
        })
    return gaps


def _spans(labels, gaps):
    """Count labels that actually use a future quote across each large gap."""
    by_gap = []
    total_crossing_origins = set()
    for gap in gaps:
        pivot = gap["left_index"]
        origins = []
        for label in labels:
            if label.classification is None or not label.target_indices:
                continue
            if label.row_index <= pivot < label.target_indices[-1]:
                origins.append(label.row_index)
        by_gap.append(len(origins))
        total_crossing_origins.update(origins)
    return {"distinct_origins_crossing_any_long_gap": len(total_crossing_origins),
            "crossing_labels_per_gap_in_source_order": by_gap}


def _one_mode(quotes, base, gaps, days, *, name, flags_ignored):
    selected = _transform_flags(quotes, "FSD") if flags_ignored else quotes
    no_gap = labels_from_quotes(
        selected, HORIZON, THRESHOLD, max_gap_seconds=None
    )
    oracle = verify_labels(
        selected, HORIZON, THRESHOLD, max_gap_seconds=None
    )
    if oracle["rows_verified"] != len(quotes) or oracle["mismatched_rows"] != 0:
        raise AssertionError("no-gap quote-level oracle mismatch")
    daily = {}
    for day in days:
        a = [r for r in base if r.trading_date == day]
        b = [r for r in no_gap if r.trading_date == day]
        day_gaps = [g for g in gaps if g["day"] == day]
        daily[day] = {
            "counts": _counts(b),
            "comparison_to_strict_30s": _compare(a, b),
            "crossing_long_gap_count": _spans(no_gap, day_gaps)[
                "distinct_origins_crossing_any_long_gap"
            ],
        }
    return {
        "scenario": name,
        "intent": "unsafe diagnostic; not a valid production label rule",
        "all_source_quotes_maintain_exact_row_identity": True,
        "quality_flags_ignored": flags_ignored,
        "max_gap_seconds": None,
        "counts": _counts(no_gap),
        "vs_strict_30s": _compare(base, no_gap),
        "source_gap_crossings": _spans(no_gap, gaps),
        "by_day": daily,
        "independent_oracle_rows": oracle["rows_verified"],
        "independent_oracle_mismatches": oracle["mismatched_rows"],
    }


def gap_boundary_report(quotes, symbol, days):
    """Single-stock metadata audit, strict frozen label counts, no-gap stress.

    Entries contain source timestamps and quality flags only (no prices).
    """
    quotes, days = tuple(quotes), tuple(days)
    if symbol not in FROZEN_PRIMARY or len(days) != 5 or len(set(days)) != 5:
        raise ValueError("nonpreregistered stock or date count")
    if len(quotes) < 2 or any(q.symbol != symbol or q.trading_date not in days for q in quotes):
        raise ValueError("quote identity / dates mismatch")
    base = labels_from_quotes(
        quotes, HORIZON, THRESHOLD, max_gap_seconds=PRIMARY_GAP_SECONDS
    )
    c = _counts(base)
    if tuple(c[x] for x in ("all", "up", "stationary", "down", "unlabelled")) != FROZEN_PRIMARY[symbol]:
        raise AssertionError("original frozen strict reference is no longer reproducible")
    check = verify_labels(
        quotes, HORIZON, THRESHOLD, max_gap_seconds=PRIMARY_GAP_SECONDS
    )
    if check["mismatched_rows"] != 0:
        raise AssertionError("baseline independent oracle disagrees")
    gaps = _long_gap_edges(quotes, symbol)
    if len(gaps) != EXPECTED_LONG_GAPS_PER_STOCK:
        raise AssertionError("source long-gap count differs from D006 published receipt")
    by_day = Counter(g["day"] for g in gaps)
    if any(by_day[day] != 1 for day in days):
        raise AssertionError("expected one source long gap on each of five days")
    for i, gap in enumerate(gaps):
        if gap["day"] not in days:
            raise AssertionError("long gap belongs to unseen date")
    strict_crossings = _spans(base, gaps)
    if strict_crossings["distinct_origins_crossing_any_long_gap"] != 0:
        raise AssertionError("strict published labels illegally bridge long source gap")
    strict = _one_mode(
        quotes, base, gaps, days, name="no_time_gap_limit_flags_respected",
        flags_ignored=False
    )
    ignored = _one_mode(
        quotes, base, gaps, days, name="no_time_gap_limit_both_flags_ignored",
        flags_ignored=True
    )
    return {
        "symbol": symbol,
        "selected_days": list(days),
        "source_rows": len(quotes),
        "predeclared_heuristic": (
            "prior time 11:28:00–11:30:30 and next time "
            "12:59:00–13:02:00 in Asia/Shanghai"
        ),
        "official_exchange_break": "11:30–13:00 continuous-auction midday break",
        "long_source_gaps_gt_120_sec": gaps,
        "gap_count": len(gaps),
        "lunch_heuristic_matches": sum(
            g["matches_frozen_lunch_time_heuristic"] for g in gaps
        ),
        "unexplained_by_lunch_heuristic": sum(
            not g["matches_frozen_lunch_time_heuristic"] for g in gaps
        ),
        "strict_reference_labels": c,
        "strict_reference_gap_crossings": strict_crossings,
        "unsafe_no_gap_counterfactuals": {
            "flags_respected": strict,
            "both_flags_ignored": ignored,
        },
        "oracle_verified_origin_count": len(quotes) * 3,
        "oracle_mismatches": 0,
        "limitations": [
            "Source timestamp alignment is evidence of recess, not proof of raw exchange event fidelity.",
            "No-gap and flags-ignored modes can create artificial target windows across scheduled nontrading time.",
            "A long gap could coincide with invalid quotes, which are still excluded even in stress modes.",
            "No later-date prices, executable fills, market prediction or FI-2010 original labels inspected.",
        ],
    }
