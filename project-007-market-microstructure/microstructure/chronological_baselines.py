"""D009 chronological *baseline-only* research, CC BY-NC Quant-Arena L1.

No model learns from validation, and holdout is absent. Source quote features
are computed at/before current available_at; labels use only future snapshots
within the same stock/date/continuous-trading phase. Out-of-session and closing
auction origins and future targets are excluded. Not trading profitability.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from .stockday_labels import Quote

PERMITTED = (1, 2, 3)
B0_TIE_PRIORITY = (2, 1, 3)
K = 5
NEUTRAL_BAND = Decimal("0.002")
MAX_GAP = timedelta(seconds=30)
EXCHANGE_OFFSET = timedelta(hours=8)


@dataclass(frozen=True)
class Example:
    row_index: int
    symbol: str
    trading_date: str
    target: int | None
    b1_prediction: int | None
    exclusion: str | None
    target_indices: tuple[int, ...]


def continuous_phase(ts):
    """Source-operational continuous-auction filter. Closing call excluded."""
    if (not isinstance(ts, datetime) or ts.tzinfo is None
            or ts.utcoffset() != EXCHANGE_OFFSET):
        raise ValueError("source timestamp must have exchange-local UTC+08:00")
    t = ts.timetz().replace(tzinfo=None)
    if time(9, 30) <= t <= time(11, 30):
        return "morning"
    if time(13, 0) <= t < time(14, 57):
        return "afternoon"
    return None


def _decimal(number):
    if number is None or isinstance(number, bool):
        return None
    try:
        result = Decimal(str(number))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def _valid(q):
    b, a = _decimal(q.bid), _decimal(q.ask)
    return (q.stale is False and q.missing_depth is False
            and b is not None and a is not None and b > 0 and a > b)


def _classify(relative_change):
    return 1 if relative_change >= NEUTRAL_BAND else (
        3 if relative_change <= -NEUTRAL_BAND else 2
    )


def make_examples(quotes):
    """Generate B1 past-only predictions and future targets in O(number rows)."""
    rows = tuple(quotes)
    sessions = []
    previous_key = None
    for index, q in enumerate(rows):
        if not isinstance(q, Quote) or not isinstance(q.symbol, str) or not q.symbol:
            raise ValueError(f"row {index}: invalid source quote")
        try:
            trading = date.fromisoformat(q.trading_date)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"row {index}: invalid source date") from exc
        if trading.isoformat() != q.trading_date:
            raise ValueError(f"row {index}: noncanonical ISO date")
        session = continuous_phase(q.available_at)
        if q.available_at.date() != trading:
            raise ValueError(f"row {index}: exchange date/availability mismatch")
        key = (q.trading_date, q.symbol, q.available_at)
        if previous_key is not None and key <= previous_key:
            raise ValueError(f"row {index}: duplicate or unsorted quote time")
        previous_key = key
        sessions.append(session)

    output = [None] * len(rows)
    i = 0
    while i < len(rows):
        original = rows[i]
        if sessions[i] is None:
            output[i] = Example(i, original.symbol, original.trading_date,
                                None, None, "outside_continuous_auction", ())
            i += 1
            continue
        if not _valid(original):
            output[i] = Example(i, original.symbol, original.trading_date,
                                None, None, "invalid_or_stale_quote", ())
            i += 1
            continue
        first, symbol, day, session = i, original.symbol, original.trading_date, sessions[i]
        while (i < len(rows) and rows[i].symbol == symbol
               and rows[i].trading_date == day and sessions[i] == session
               and _valid(rows[i])):
            if i > first and rows[i].available_at - rows[i - 1].available_at > MAX_GAP:
                break
            i += 1
        end = i
        midpoint = [(_decimal(rows[j].bid) + _decimal(rows[j].ask)) / 2
                    for j in range(first, end)]
        prefix = [Decimal(0)]
        for value in midpoint:
            prefix.append(prefix[-1] + value)
        for origin in range(first, end):
            idx = origin-first
            b1 = None
            if idx >= K:
                prev_mean = (prefix[idx] - prefix[idx-K]) / K
                b1 = _classify((midpoint[idx] - prev_mean) / prev_mean)
            if idx + K >= len(midpoint):
                output[origin] = Example(origin, symbol, day,
                                         None, b1, "incomplete_future", ())
                continue
            future_mean = (prefix[idx+K+1] - prefix[idx+1]) / K
            label = _classify((future_mean - midpoint[idx]) / midpoint[idx])
            output[origin] = Example(
                origin, symbol, day, label, b1, None,
                tuple(range(origin+1, origin+K+1)),
            )
    return tuple(output)


def choose_training_majority(training):
    eligible = [x.target for x in training if x.target in PERMITTED]
    if not eligible:
        raise ValueError("no eligible training labels")
    counts = Counter(eligible)
    return min(PERMITTED, key=lambda c: (-counts[c], B0_TIE_PRIORITY.index(c))), {
        str(c): counts[c] for c in PERMITTED
    }


def _confusion(rows, predictor):
    """Fixed 3-class confusion and macro metrics; missing true class recall=0."""
    matrix = {str(actual): {str(pred): 0 for pred in PERMITTED} for actual in PERMITTED}
    for row in rows:
        actual, guess = row.target, predictor(row)
        if actual not in PERMITTED or guess not in PERMITTED:
            raise ValueError("scored row lacks permitted target or prediction")
        matrix[str(actual)][str(guess)] += 1
    true_counts = {c: sum(matrix[str(c)].values()) for c in PERMITTED}
    recalls = {}
    f1s = {}
    for c in PERMITTED:
        tp = matrix[str(c)][str(c)]
        predicted = sum(matrix[str(actual)][str(c)] for actual in PERMITTED)
        true = true_counts[c]
        recalls[c] = tp / true if true else 0.0
        denom = true + predicted
        f1s[c] = 2 * tp / denom if denom else 0.0
    n = len(rows)
    return {
        "n": n, "correct": sum(matrix[str(c)][str(c)] for c in PERMITTED),
        "accuracy": sum(matrix[str(c)][str(c)] for c in PERMITTED)/n if n else None,
        "macro_f1_three_class": sum(f1s.values())/3 if n else None,
        "balanced_accuracy_three_class": sum(recalls.values())/3 if n else None,
        "true_class_recall_zero_when_no_support": {str(c): recalls[c] for c in PERMITTED},
        "true_support": {str(c): true_counts[c] for c in PERMITTED},
        "confusion_true_rows_predicted_columns": matrix,
        "note": "Three-class macro averaging includes unsupported true classes with recall 0; no naive IID uncertainty."
    }


def summarize_validation(validation, train_majority):
    rows = tuple(validation)
    eligible = tuple(x for x in rows if x.target in PERMITTED)
    covered = tuple(x for x in eligible if x.b1_prediction in PERMITTED)
    unavailable = Counter(x.exclusion for x in rows if x.target is None)
    result = {
        "all_source_origins": len(rows),
        "eligible_targets": len(eligible),
        "source_exclusions": dict(sorted(unavailable.items())),
        "b1_covered_targets": len(covered),
        "b1_abstentions_among_target_eligible": len(eligible)-len(covered),
        "b1_coverage_pct_eligible": 100*len(covered)/len(eligible) if eligible else None,
        "B0_all_eligible": _confusion(eligible, lambda _:train_majority),
        "B0_on_B1_covered": _confusion(covered, lambda _:train_majority),
        "B1_on_same_covered": _confusion(covered, lambda x:x.b1_prediction),
        "by_stock": {},
        "by_stock_date": {},
    }
    for symbol in sorted({x.symbol for x in rows}):
        symbol_rows = tuple(x for x in rows if x.symbol == symbol)
        valid = tuple(x for x in symbol_rows if x.target is not None)
        common = tuple(x for x in valid if x.b1_prediction is not None)
        result["by_stock"][symbol] = {
            "source_rows":len(symbol_rows), "eligible":len(valid),
            "B0_all":_confusion(valid,lambda _:train_majority),
            "B0_covered":_confusion(common,lambda _:train_majority),
            "B1_covered":_confusion(common,lambda x:x.b1_prediction),
            "covered":len(common),
        }
        for day in sorted({x.trading_date for x in symbol_rows}):
            date_rows=tuple(x for x in symbol_rows if x.trading_date==day)
            dv=tuple(x for x in date_rows if x.target is not None)
            dc=tuple(x for x in dv if x.b1_prediction is not None)
            result["by_stock_date"][symbol+"@"+day]={
                "source_rows":len(date_rows), "eligible":len(dv),
                "B0_all":_confusion(dv,lambda _:train_majority),
                "B0_covered":_confusion(dc,lambda _:train_majority),
                "B1_covered":_confusion(dc,lambda x:x.b1_prediction),
                "covered":len(dc),
            }
    return result
