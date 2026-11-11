"""Exploratory source-label construction check using publisher-processed quotes.

NOT independent reproduction of original Nasdaq messages/prices. Works on
training CF7 only; exact paper formula uses the MEAN of future mid-prices.
Price units may be different in the transformed DecPre input. Does not
fit predictive models, evaluate holdouts or infer returns.
"""
from array import array
import math
import zipfile


class LabelReconstructionError(ValueError):
    pass


TRAIN_FILENAME = "Train_Dst_NoAuction_DecPre_CF_7.txt"
HORIZONS = (1, 5)


def _float_row(stream):
    items = array("d")
    for token in stream.split():
        try:
            v = float(token)
        except ValueError as exc:
            raise LabelReconstructionError("nonnumeric transformed price/label") from exc
        if not math.isfinite(v):
            raise LabelReconstructionError("nonfinite transformed price/label")
        items.append(v)
    if len(items) < 2:
        raise LabelReconstructionError("too few samples")
    return items


def read_minimal_rows(archive):
    """Read only first-level ask/bid and h1/h5 publisher labels from train."""
    with zipfile.ZipFile(archive) as source:
        members = [m for m in source.infolist() if m.filename == TRAIN_FILENAME]
        if len(members) != 1:
            raise LabelReconstructionError("expected one original CF7 training member")
        selected = {}
        with source.open(members[0]) as stream:
            for i, line in enumerate(stream):
                if i in (0, 2, 144, 147):
                    selected[i] = _float_row(line)
                if i > 147:
                    break
    if len(selected) != 4 or len({len(v) for v in selected.values()}) != 1:
        raise LabelReconstructionError("unexpected publisher row widths")
    for label_row in (144, 147):
        if any(v not in (1.0, 2.0, 3.0) for v in selected[label_row]):
            raise LabelReconstructionError("unexpected source label code")
    return selected


def reconstruct_publisher_rule(ask, bid, labels, horizon, threshold=0.002):
    """Apply paper's future-average midpoint formula to processed row order.

    No future values are used as predictor inputs: this is a retrospective
    check of ALREADY-PUBLISHED labels, not a forecast/backtest.
    """
    if horizon not in HORIZONS or not 0 < threshold < 1:
        raise ValueError("unsupported horizon or threshold")
    n = len(ask)
    if n != len(bid) or n != len(labels):
        raise ValueError("row width mismatch")
    if n <= horizon:
        raise ValueError("insufficient samples")
    total = valid = matches = borderline = invalid_quote = 0
    tally = {(1, 1): 0, (1, 2): 0, (1, 3): 0,
             (2, 1): 0, (2, 2): 0, (2, 3): 0,
             (3, 1): 0, (3, 2): 0, (3, 3): 0}
    mids = [(a+b)/2 for a,b in zip(ask, bid)]
    for i in range(n-horizon):
        total += 1
        # Only interpret quotes when the published ask is above bid and both
        # transformed values are positive. Do not forward-fill invalid inputs.
        if any(not math.isfinite(mids[j]) or ask[j] <= bid[j] or bid[j] <= 0
               for j in range(i,i+horizon+1)):
            invalid_quote += 1
            continue
        m0 = mids[i]
        future_mean = math.fsum(mids[i+1:i+horizon+1])/horizon
        delta = (future_mean-m0)/m0
        if abs(abs(delta)-threshold) < 1e-8:
            borderline += 1
        observed = int(labels[i])
        if observed not in (1,2,3):
            raise LabelReconstructionError("invalid publisher label")
        candidate = 1 if delta >= threshold else 3 if delta <= -threshold else 2
        tally[(observed,candidate)] += 1
        valid += 1
        matches += observed==candidate
    return {
        "status": "transformed_quote_label_consistency_only",
        "horizon": horizon,
        "source_label_rule": "mean of next k midpoints relative to origin vs +/-0.002",
        "observations_considered": total,
        "valid_processed_quote_windows": valid,
        "invalid_quote_windows": invalid_quote,
        "agreement_pct": round(matches/valid*100,4) if valid else None,
        "near_threshold_windows": borderline,
        "confusion_publisher_rows_candidate_columns": {
            str(i): {str(j): tally[(i,j)] for j in (1,2,3)}
            for i in (1,2,3)
        },
        "limitations": [
            "The source was decimal-precision-transformed, not original exchange prices.",
            "Original security/session identity is not supplied in these pooled features.",
            "Row-to-row series may cross hidden stock/session boundaries.",
            "A mismatch cannot identify whether preprocessing, scale or original source labels caused it.",
            "Only train-days-1–7 labels inspected; day 8 feature labels and days 9/10 not used.",
        ],
    }


def inspect_training_source(archive):
    rows=read_minimal_rows(archive)
    return {str(h): reconstruct_publisher_rule(
        rows[0],rows[2],rows[144 if h==1 else 147],h)
        for h in HORIZONS}
