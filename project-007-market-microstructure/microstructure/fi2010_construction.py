"""Cross-horizon FI-2010 publisher-label construction diagnostics.

This program never downloads data, fits predictors, or reads held-out folds.
It consumes only CF7 train and day-8 test members of a caller-supplied
provenance-pinned ZIP. An empirical run must check archive checksum separately.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
import zipfile

TRAIN = "Train_Dst_NoAuction_DecPre_CF_7.txt"
DAY8 = "Test_Dst_NoAuction_DecPre_CF_7.txt"
HORIZONS = (1, 2, 3, 5, 10)
CLASSES = (1, 2, 3)  # original paper: up/stationary/down


class ConstructionError(ValueError):
    """Unrecognized structure or invalid publisher target label."""


def read_labels_only(archive: zipfile.ZipFile, filename):
    """Read exactly the five last rows of 149-by-N file; no features loaded.

    The 144 source-preprocessed feature rows are skipped. This method is
    complementary to the full-file validation in fi2010_baseline.py.
    """
    if filename not in (TRAIN, DAY8):
        raise ConstructionError("only declared train/day-8 fold filenames are permitted")
    if not isinstance(archive, zipfile.ZipFile):
        raise ConstructionError("expected local verified ZIP")
    candidates = [item for item in archive.infolist() if item.filename == filename]
    if len(candidates) != 1:
        raise ConstructionError("missing or ambiguous fold member")
    labels = []
    with archive.open(candidates[0]) as src:
        for index, row in enumerate(src):
            if index >= 149:
                raise ConstructionError("excess rows")
            if index < 144:
                continue
            tokens = row.split()
            values = bytearray()
            for token in tokens:
                try:
                    value = Decimal(token.decode("ascii"))
                except (UnicodeError, InvalidOperation) as exc:
                    raise ConstructionError("invalid label token in original publisher matrix") from exc
                if not value.is_finite() or value not in (1, 2, 3):
                    raise ConstructionError("invalid label token in original publisher matrix")
                values.append(int(value))
            labels.append(values)
    if len(labels) != 5 or not all(labels):
        raise ConstructionError("expected exactly 149 rows and five nonempty label rows")
    n = len(labels[0])
    if len({len(x) for x in labels}) != 1:
        raise ConstructionError("horizons have unequal observation counts")
    return {k: labels[i] for i, k in enumerate(HORIZONS)}, n


def summarize_labels(train, day8):
    """Summarize class drift without using label outcomes to select a model."""
    outputs = {}
    raw = {}
    for name, labels in (("train", train), ("day8", day8)):
        if set(labels) != set(HORIZONS):
            raise ConstructionError("missing horizon")
        n = len(labels[1])
        if n < 1 or any(len(labels[h]) != n for h in HORIZONS):
            raise ConstructionError("horizon count mismatch")
        raw[name] = {}
        for h in HORIZONS:
            c = Counter(labels[h])
            if set(c).difference(CLASSES):
                raise ConstructionError("unknown label")
            raw[name][h] = {
                "n": n,
                "counts": {str(k): c[k] for k in CLASSES},
                "pct": {str(k): round(100 * c[k] / n, 4) for k in CLASSES},
            }

    for h in HORIZONS:
        a, b = raw["train"][h], raw["day8"][h]
        n_a, n_b = a["n"], b["n"]
        share_change = {
            str(k): round(100 * (b["counts"][str(k)] / n_b - a["counts"][str(k)] / n_a), 4)
            for k in CLASSES
        }
        tv = sum(abs(b["counts"][str(k)] / n_b - a["counts"][str(k)] / n_a)
                 for k in CLASSES) / 2
        outputs[str(h)] = {
            "train": a, "day8": b,
            "difference_day8_minus_train_percentage_points": share_change,
            "total_variation_distance": round(tv, 6),
            "day8_stationary_share_exceeds_training": b["counts"]["2"] / n_b > a["counts"]["2"] / n_a,
        }

    return {
        "status": "empirical_label_construction_diagnostics_not_alpha",
        "horizons_sampled_representations": list(HORIZONS),
        "source_class_codes": {"1": "up", "2": "stationary", "3": "down"},
        "paper_label_threshold": "relative mid-price change >= 0.002 up; <= -0.002 down; otherwise stationary",
        "study_uses_raw_event_timestamps": False,
        "by_horizon": outputs,
        "limitations": [
            "Describes publisher-assigned labels; cannot independently certify how they were created.",
            "Same 0.2% threshold across horizons can mechanically change the stationary frequency.",
            "Changes in label mix cannot distinguish market behavior from stock mixture or upstream preprocessing.",
            "All observations are correlated; percentages and TV are descriptive, not p-values.",
            "Cannot isolate per-stock/per-day contributors from these pooled files.",
            "The training-day label-boundary lookahead question remains open.",
            "Day 9/10 ZIP members are never opened.",
            "No model fitting, trading P&L or new performance metrics are computed.",
        ],
    }


def inspect_archive(archive):
    """Caller must verify pinned SHA256 first; archive read remains two folds."""
    with zipfile.ZipFile(archive) as z:
        train, ntrain = read_labels_only(z, TRAIN)
        day8, ntest = read_labels_only(z, DAY8)
    summary = summarize_labels(train, day8)
    summary["train_observations"] = ntrain
    summary["day8_observations"] = ntest
    summary["files_read"] = [TRAIN, DAY8]
    summary["reserved_files_read"] = []
    return summary
