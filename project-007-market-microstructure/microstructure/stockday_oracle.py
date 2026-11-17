"""Independent quadratic stock/day prospective-label oracle.

Deliberately does not reuse the optimized midpoint/prefix-sum code. It
recomputes the mean from explicit future quotes and refuses cross-day/stock
or stale/gapped segments. Used for verification, not prediction.
"""
from decimal import Decimal

from .stockday_labels import labels_from_quotes


def _eligible(item):
    if item.stale or item.missing_depth or item.bid is None or item.ask is None:
        return False
    b, a = Decimal(str(item.bid)), Decimal(str(item.ask))
    return b.is_finite() and a.is_finite() and b > 0 and a > b


def slow_labels(quotes, k, threshold="0.002", max_gap_seconds=30):
    threshold = Decimal(str(threshold))
    observations = tuple(quotes)
    labels = []
    for i, current in enumerate(observations):
        if not _eligible(current):
            labels.append((None, (), "invalid_or_stale_quote"))
            continue
        futures = []
        previous = current
        for j in range(i + 1, min(i + k + 1, len(observations))):
            candidate = observations[j]
            if (candidate.symbol != current.symbol
                    or candidate.trading_date != current.trading_date
                    or not _eligible(candidate)
                    or (max_gap_seconds is not None and
                        (candidate.available_at - previous.available_at).total_seconds()
                        > max_gap_seconds)):
                break
            futures.append(j)
            previous = candidate
        if len(futures) != k:
            labels.append((None, (), "incomplete_future"))
            continue
        mid_origin = (Decimal(str(current.bid)) + Decimal(str(current.ask))) / 2
        total_future_mid = sum(
            ((Decimal(str(observations[j].bid))
               + Decimal(str(observations[j].ask))) / 2 for j in futures),
            Decimal(0)
        )
        ratio = (total_future_mid / k - mid_origin) / mid_origin
        label = 1 if ratio >= threshold else 3 if ratio <= -threshold else 2
        labels.append((label, tuple(futures), None))
    return tuple(labels)


def verify_labels(quotes, k, threshold="0.002", max_gap_seconds=30):
    """Verify every row including excluded records; raise on first mismatch."""
    observations = tuple(quotes)
    optimized = labels_from_quotes(
        observations, k, threshold, max_gap_seconds=max_gap_seconds
    )
    independent = slow_labels(
        observations, k, threshold, max_gap_seconds=max_gap_seconds
    )
    if len(optimized) != len(independent):
        raise AssertionError("independent oracle length mismatch")
    for i, (row, expected) in enumerate(zip(optimized, independent)):
        actual = (row.classification, row.target_indices, row.excluded)
        if actual != expected:
            raise AssertionError(
                f"row {i}, horizon {k}: optimized label disagrees with independent quote oracle"
            )
    return {
        "status": "all_optimized_labels_match_independent_source_quote_oracle",
        "horizon": k,
        "rows_verified": len(optimized),
        "mismatched_rows": 0,
        "future_label_results_are_not_trade_forecasts": True,
    }
