"""D010: past/current-only snapshot liquidity features (NO event-level order flow).

Quant-Arena Public L1 CC BY-NC 4.0 noncommercial. This module has no
network, provider-price file IO, ML fit, or prediction-score side effects.
Only available top-of-book and displayed depth at/before source available_at
may enter predictors. No target or future quote is used for any feature.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
from math import isfinite

from .chronological_baselines import continuous_phase

LEVELS = 5
SPREAD_MAX_BPS = Decimal("100")
SOURCE_FIELDS = tuple(
    f"{side}_{kind}_{level}"
    for side in ("bid", "ask")
    for kind in ("price", "volume")
    for level in range(1, LEVELS + 1)
)
REQUIRED_FEATURE_FIELDS = (
    "available_at", "source_event_time", "stale", "missing_depth",
) + SOURCE_FIELDS


def _decimal(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return None
    return number if number.is_finite() else None


def snapshot_features(row):
    """Return (spread_bps, level1_imbalance, level1_to5_imbalance) or None.

    Fail closed on incomplete/invalid depth, future source-event timestamps,
    bad timestamps, source flags and out-of-session/closing-auction rows.
    This cannot infer changes between snapshots or trade initiator side.
    """
    if not isinstance(row, dict) or any(k not in row for k in REQUIRED_FEATURE_FIELDS):
        raise ValueError("source snapshot missing mandatory feature fields")
    if continuous_phase(row["available_at"]) is None:
        return None
    source_time = row["source_event_time"]
    if source_time is None or source_time.utcoffset() != row["available_at"].utcoffset():
        return None
    if source_time > row["available_at"]:
        raise ValueError("source event timestamp later than availability timestamp")
    if row["stale"] is not False or row["missing_depth"] is not False:
        return None
    prices = {}
    volumes = {}
    for side in ("bid", "ask"):
        prices[side] = []
        volumes[side] = []
        for level in range(1, LEVELS + 1):
            price = _decimal(row[f"{side}_price_{level}"])
            vol = row[f"{side}_volume_{level}"]
            if price is None or price <= 0 or type(vol) is not int or vol < 0:
                return None
            prices[side].append(price)
            volumes[side].append(vol)
        if side == "bid" and any(
            prices[side][i] < prices[side][i + 1] for i in range(LEVELS - 1)
        ):
            return None
        if side == "ask" and any(
            prices[side][i] > prices[side][i + 1] for i in range(LEVELS - 1)
        ):
            return None

    bid1, ask1 = prices["bid"][0], prices["ask"][0]
    if bid1 >= ask1:
        return None
    # No own-side level on either side may cross the other best quote.
    if any(x >= ask1 for x in prices["bid"]) or any(x <= bid1 for x in prices["ask"]):
        return None
    bid_sum = sum(volumes["bid"])
    ask_sum = sum(volumes["ask"])
    best_total = volumes["bid"][0] + volumes["ask"][0]
    if bid_sum <= 0 or ask_sum <= 0 or best_total <= 0:
        return None

    mid = (bid1 + ask1) / 2
    spread_bps = min(SPREAD_MAX_BPS, Decimal(10_000) * (ask1 - bid1) / mid)
    top_imbalance = Decimal(volumes["bid"][0] - volumes["ask"][0]) / best_total
    total_imbalance = Decimal(bid_sum - ask_sum) / (bid_sum + ask_sum)
    values = (float(spread_bps), float(top_imbalance), float(total_imbalance))
    if not all(isfinite(v) for v in values):
        raise ValueError("numeric source feature overflow")
    return values


def make_feature_rows(raw_rows, expected_symbol, expected_days):
    """Produce features in the ORIGINAL source order, including missing rows.

    Independent of labels; never skip raw row indices because downstream
    label-origin indices must refer to the same timestamp-ordered sequence.
    """
    allowed = set(expected_days)
    values = []
    counts = Counter()
    for i, row in enumerate(raw_rows):
        if row.get("symbol") != expected_symbol or row["available_at"].date().isoformat() not in allowed:
            raise ValueError(f"feature source stock/date differs at row {i}")
        feature = snapshot_features(row)
        values.append(feature)
        counts["accepted" if feature is not None else "not_usable"] += 1
    return tuple(values), dict(sorted(counts.items()))
