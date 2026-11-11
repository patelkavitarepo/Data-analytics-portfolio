"""Separate FI-2010 benchmark intake, not a LOBSTER event-stream adapter.

Works ONLY on locally supplied official NoAuction/DecPre 149-by-N benchmark
matrices. Scores a majority-class benchmark on day 8 using days 1-7 labels,
never accesses days 9/10, and NEVER treats preprocessed features as raw
exchange messages, reconstructs a book, or computes live trading performance.
"""
from collections import Counter
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from .paths import safe_report_output


class BenchmarkError(ValueError):
    """A benchmark file fails to match the declared testable format."""


HORIZONS = (1, 2, 3, 5, 10)
N_ROWS = 149
LABEL_START_ROW = 144
TRAIN_FILENAME = "Train_Dst_NoAuction_DecPre_CF_7.txt"
DAY8_FILENAME = "Test_Dst_NoAuction_DecPre_CF_7.txt"
CLASSES = (1, 2, 3)  # publisher paper: 1=up, 2=stationary, 3=down


def _digest(path):
    hasher = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_matrix_labels(path, horizon):
    """Bounded-memory row stream: all numeric cells checked; only labels retained.

    FI-2010 format is 144 feature rows followed by five labelled rows, one
    column per preprocessed event snapshot. No column-wise entire-file copy.
    """
    path = Path(path)
    which = LABEL_START_ROW + HORIZONS.index(horizon)
    n_columns = None
    chosen = None
    row_count = 0
    try:
        with path.open("r", encoding="utf-8") as stream:
            for row_count, raw in enumerate(stream, 1):
                if row_count > N_ROWS:
                    raise BenchmarkError(f"{path.name}: more than 149 rows")
                tokens = raw.split()
                if not tokens:
                    raise BenchmarkError(f"{path.name}: empty feature/label row {row_count}")
                if n_columns is None:
                    n_columns = len(tokens)
                    if n_columns < 2:
                        raise BenchmarkError(f"{path.name}: fewer than two observations")
                elif n_columns != len(tokens):
                    raise BenchmarkError(
                        f"{path.name}: inconsistent observations in row {row_count}"
                    )
                if row_count <= LABEL_START_ROW:
                    for token in tokens:
                        try:
                            f = float(token)
                        except ValueError as exc:
                            raise BenchmarkError(
                                f"{path.name}: nonnumeric feature row {row_count}"
                            ) from exc
                        if not math.isfinite(f):
                            raise BenchmarkError(
                                f"{path.name}: nonfinite feature row {row_count}"
                            )
                else:
                    parsed = Counter()
                    for token in tokens:
                        try:
                            f = float(token)
                        except ValueError as exc:
                            raise BenchmarkError(
                                f"{path.name}: malformed label row {row_count}"
                            ) from exc
                        if not math.isfinite(f) or f not in CLASSES:
                            raise BenchmarkError(
                                f"{path.name}: unexpected label row {row_count}"
                            )
                        parsed[int(f)] += 1
                    if row_count - 1 == which:
                        chosen = parsed
    except UnicodeError as exc:
        raise BenchmarkError(f"{path.name}: expected a UTF-8 text matrix") from exc
    if row_count != N_ROWS or n_columns is None or chosen is None:
        raise BenchmarkError(f"{path.name}: expected precisely 149 matrix rows")
    if sum(chosen.values()) != n_columns:
        raise BenchmarkError(f"{path.name}: label totals do not match columns")
    return n_columns, chosen


def _safe_input(path, required_name):
    p = Path(path)
    if p.name != required_name:
        raise BenchmarkError(
            f"Expected {required_name}; cannot infer day identities from other folds"
        )
    if p.is_symlink() or not p.is_file():
        raise BenchmarkError("Use a regular, local file with no symlink")
    return p


def _macro_f1_constant(y, chosen):
    """Exact per-class F1 for a constant prediction; no modelling dependency."""
    n = sum(y.values())
    tp = y[chosen]
    f1_chosen = (2 * tp / (n + tp)) if (n + tp) else 0.0
    return round(f1_chosen / len(CLASSES), 8)


def evaluate_majority_baseline(train, day8, horizon=5):
    """Train days 1-7; validate on day 8 ONLY. Days 9/10 never opened.

    Upstream benchmark labels are trusted provisionally as labels only.
    Derived scores are not execution P&L, market alpha, or pristine holdout.
    """
    if type(horizon) is not int or horizon not in HORIZONS:
        raise BenchmarkError("horizon must be one of 1,2,3,5,10 sampled observations")
    train = _safe_input(train, TRAIN_FILENAME)
    day8 = _safe_input(day8, DAY8_FILENAME)
    if train.resolve() == day8.resolve():
        raise BenchmarkError("training and day-8 sources must differ")

    initial = {"train": _digest(train), "day8": _digest(day8)}
    n_train, train_counts = _read_matrix_labels(train, horizon)
    n_day8, day8_counts = _read_matrix_labels(day8, horizon)
    final = {"train": _digest(train), "day8": _digest(day8)}
    if final != initial:
        raise BenchmarkError("source file modified during verification")

    # Break exact ties in favor of stationary, then down, then up;
    # no validation information is used to select this constant predictor.
    winner = max((2, 1, 3), key=lambda label: train_counts[label])
    n_correct = day8_counts[winner]
    accuracy = n_correct / n_day8
    return {
        "status": "local_fi2010_day8_majority_baseline_not_holdout",
        "dataset_family": "FI-2010 / NoAuction / DecPre / official CF7 fold",
        "dataset_presentation": "149-by-N source-preprocessed matrix; labels supplied by benchmark",
        "horizon_sampled_observations": horizon,
        "train_period": "benchmark days 1-7 (Train_CF_7)",
        "evaluation_period": "benchmark day 8 (Test_CF_7)",
        "reserved_unread": ["benchmark day 9 (Test_CF_8)", "benchmark day 10 (Test_CF_9)"],
        "train_observations": n_train,
        "day8_observations": n_day8,
        "train_class_counts": {str(k): train_counts[k] for k in CLASSES},
        "day8_class_counts": {str(k): day8_counts[k] for k in CLASSES},
        "constant_prediction_class": winner,
        "day8_accuracy": round(accuracy, 8),
        "day8_macro_f1": _macro_f1_constant(day8_counts, winner),
        "source_sha256": initial,
        "source_files": [train.name, day8.name],
        "limitations": [
            "No original event timestamps or raw order messages; benchmark sample horizon != elapsed seconds.",
            "Preprocessed/normalized features cannot justify raw-size imbalance, spread, or fill inference.",
            "Benchmark supplier's labels have not been independently reconstructed.",
            "A ten-day 2010 benchmark cannot establish current market predictability or execution profits.",
            "Only a train-class-prior baseline; no trained predictive features or risk model.",
            "Further publication requires retaining proper FI-2010 author attribution and source-use evidence.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="FI-2010 local training-prior vs day-8 baseline")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--day8", type=Path, required=True)
    parser.add_argument("--horizon", type=int, default=5, choices=HORIZONS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = safe_report_output(args.output)
        report = evaluate_majority_baseline(args.train, args.day8, horizon=args.horizon)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (BenchmarkError, ValueError, OSError) as exc:
        parser.error(str(exc))
    print("Wrote local day-8 baseline; reserved days 9 and 10 were not read.")


if __name__ == "__main__":
    main()
