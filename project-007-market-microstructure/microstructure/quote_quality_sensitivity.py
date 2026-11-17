"""Noncommercial source-quote quality sensitivity, descriptive only.

D006 predeclared modes: G15,G30,G60,G120 and F0,FS,FD,FSD at k=5,
threshold ±0.002. Gap/flag stress settings NEVER replace the primary G30/F0
analysis, never alter vendor data or allow invalid prices.
"""
from collections import Counter
from dataclasses import replace
from decimal import Decimal, InvalidOperation

from .stockday_labels import labels_from_quotes
from .stockday_oracle import verify_labels


HORIZON = 5
THRESHOLD = "0.002"
GAP_LIMITS = {"G15": 15, "G30": 30, "G60": 60, "G120": 120}
FLAG_MODES = {
    "F0": (False, False),
    "FS": (True, False),
    "FD": (False, True),
    "FSD": (True, True),
}
# 000012.SZ / 000025.SZ / 000031.SZ (all/up/stationary/down/excluded)
FROZEN_PRIMARY = {
    "000012.SZ": (5078, 122, 4438, 126, 392),
    "000025.SZ": (5077, 58, 4267, 39, 713),
    "000031.SZ": (5078, 308, 4107, 271, 392),
}


def _counts(labels):
    classes = Counter(x.classification for x in labels)
    excluded = Counter(x.excluded for x in labels if x.excluded is not None)
    eligible = sum(classes[c] for c in (1, 2, 3))
    n = len(labels)
    if eligible + classes[None] != n:
        raise AssertionError("not all source origins accounted for")
    return {
        "all": n, "up": classes[1], "stationary": classes[2],
        "down": classes[3], "unlabelled": classes[None],
        "eligible": eligible, "stationary_pct_of_eligible": (
            round(100 * classes[2] / eligible, 4) if eligible else None
        ),
        "exclusions": {
            "invalid_or_stale_quote": excluded["invalid_or_stale_quote"],
            "incomplete_future": excluded["incomplete_future"],
        },
    }


def _price_valid(q):
    try:
        bid, ask = Decimal(str(q.bid)), Decimal(str(q.ask))
        return bid.is_finite() and ask.is_finite() and bid > 0 and ask > bid
    except (InvalidOperation, TypeError, ValueError):
        return False


def source_quality(quotes):
    """Mutually exclusive 8-way flag/price combination plus gap histogram.

    The price-valid indicator is false for missing, nonfinite, crossed, locked
    or nonpositive first-level quotes. No quote values leave this process.
    """
    combos = Counter()
    gaps = Counter({str(n): 0 for n in GAP_LIMITS.values()})
    by_day = {}
    prev = None
    for q in quotes:
        key = f"stale={int(bool(q.stale))},missing_depth={int(bool(q.missing_depth))},bad_price={int(not _price_valid(q))}"
        combos[key] += 1
        if q.trading_date not in by_day:
            by_day[q.trading_date] = {"quote_rows": 0, "invalid_price": 0,
                                      "stale": 0, "missing_depth": 0}
        d = by_day[q.trading_date]
        d["quote_rows"] += 1
        d["stale"] += bool(q.stale)
        d["missing_depth"] += bool(q.missing_depth)
        d["invalid_price"] += not _price_valid(q)
        if prev is not None and q.symbol == prev.symbol and q.trading_date == prev.trading_date:
            gap = (q.available_at - prev.available_at).total_seconds()
            for limit in GAP_LIMITS.values():
                if gap > limit:
                    gaps[str(limit)] += 1
        prev = q
    if sum(combos.values()) != len(quotes):
        raise AssertionError("quality categories do not partition rows")
    if len(set(x.symbol for x in quotes)) != 1:
        raise AssertionError("quality audit must contain exactly one stock")
    return {
        "exclusive_quality_crosstab": dict(sorted(combos.items())),
        "adjacent_same_stock_day_gap_gt_seconds": dict(sorted(gaps.items(), key=lambda x: int(x[0]))),
        "daily_source_quality": dict(sorted(by_day.items())),
    }


def _compare(primary, alternative):
    if len(primary) != len(alternative):
        raise AssertionError("scenario changes source origin count")
    new_eligible = new_excluded = class_changes = future_changes = reason_changes = 0
    for a, b in zip(primary, alternative):
        if a.row_index != b.row_index or a.symbol != b.symbol or a.trading_date != b.trading_date:
            raise AssertionError("source origin identity changed in sensitivity")
        if a.classification is None and b.classification is not None:
            new_eligible += 1
        elif a.classification is not None and b.classification is None:
            new_excluded += 1
        elif a.classification is not None and b.classification is not None:
            class_changes += a.classification != b.classification
            future_changes += a.target_indices != b.target_indices
        else:
            reason_changes += a.excluded != b.excluded
    return {
        "newly_eligible_from_excluded": new_eligible,
        "newly_excluded_from_eligible": new_excluded,
        "still_eligible_class_changed": class_changes,
        "still_eligible_future_indices_changed": future_changes,
        "still_excluded_reason_changed": reason_changes,
    }


def _transform_flags(quotes, mode):
    ignore_stale, ignore_missing = FLAG_MODES[mode]
    if not ignore_stale and not ignore_missing:
        return quotes
    return tuple(replace(
        q, stale=False if ignore_stale else q.stale,
        missing_depth=False if ignore_missing else q.missing_depth
    ) for q in quotes)


def _scenario(quotes, days, *, primary, gap, mode):
    changed = _transform_flags(quotes, mode)
    labels = labels_from_quotes(changed, HORIZON, THRESHOLD, max_gap_seconds=gap)
    check = verify_labels(changed, HORIZON, THRESHOLD, max_gap_seconds=gap)
    if check["rows_verified"] != len(quotes) or check["mismatched_rows"] != 0:
        raise AssertionError("independent sensitivity oracle failure")
    per_day = {}
    for day in days:
        one_day = tuple(x for x in labels if x.trading_date == day)
        one_base = tuple(x for x in primary if x.trading_date == day)
        if len(one_day) != len(one_base):
            raise AssertionError("daily source origin denominator changed")
        per_day[day] = {
            "counts": _counts(one_day),
            "versus_G30_F0": _compare(one_base, one_day),
        }
    return {
        "gap_seconds": gap,
        "stale_ignored_counterfactual": FLAG_MODES[mode][0],
        "missing_depth_ignored_counterfactual": FLAG_MODES[mode][1],
        "pooled_counts": _counts(labels),
        "versus_G30_F0": _compare(primary, labels),
        "per_day": per_day,
        "oracle_verified_origins": check["rows_verified"],
        "oracle_disagreements": 0,
    }


def sensitivity_panel(quotes, symbol, days):
    """Return source-only aggregate diagnostics, no raw market observations."""
    quotes = tuple(quotes)
    days = tuple(days)
    if symbol not in FROZEN_PRIMARY:
        raise ValueError("not a preregistered stock")
    if not days or len(days) != 5 or len(set(days)) != len(days):
        raise ValueError("expected five distinct frozen dates")
    if not quotes or any(q.symbol != symbol or q.trading_date not in days for q in quotes):
        raise ValueError("unexpected stock/day input")
    primary = labels_from_quotes(quotes, HORIZON, THRESHOLD, max_gap_seconds=30)
    base = _counts(primary)
    observed = tuple(base[key] for key in ("all", "up", "stationary", "down", "unlabelled"))
    if observed != FROZEN_PRIMARY[symbol]:
        raise AssertionError("frozen reference source or algorithm no longer matches")
    out = {}
    for mode, gap in GAP_LIMITS.items():
        out[mode] = _scenario(
            quotes, days, primary=primary, gap=gap, mode="F0"
        )
    for mode in FLAG_MODES:
        out[mode] = _scenario(
            quotes, days, primary=primary, gap=30, mode=mode
        )
    if out["G30"]["pooled_counts"] != out["F0"]["pooled_counts"]:
        raise AssertionError("reference sensitivity modes differ")
    if any(out[ref]["versus_G30_F0"][k] != 0 for ref in ("G30", "F0")
           for k in out[ref]["versus_G30_F0"]):
        raise AssertionError("reference scenarios unexpectedly modified labels")
    return {
        "symbol": symbol,
        "source_rows": len(quotes),
        "days": list(days),
        "strict_primary_reference": base,
        "quality": source_quality(quotes),
        "scenarios": out,
        "all_eight_modes_oracle_verified": True,
        "total_primary_oracle_checks": len(quotes)*len(out),
        "interpretation": "G15/G60/G120 and FS/FD/FSD are diagnostic alternatives, not improved models or safe execution policies.",
    }
