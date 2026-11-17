"""Independent FI-2010 raw ZIP label-row oracle (separate from baseline parser).

Reads only the specified publisher label row from each named fold in a pinned
locally accessible archive. Uses Decimal + Fraction, no NumPy or baseline
parser, and never opens reserved fold files.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import zipfile


class IndependentLabelError(ValueError):
    """The independent label tally disagrees with the expected file format."""


PUBLISHER_HORIZONS = (1, 2, 3, 5, 10)


def _read_class_counts_from_zip(archive, filename, horizon):
    if horizon not in PUBLISHER_HORIZONS:
        raise IndependentLabelError("unrecognized publisher horizon")
    expected_index = 144 + PUBLISHER_HORIZONS.index(horizon)
    count = Counter()
    found = False
    with archive.open(filename, "r") as source:
        for row_index, line in enumerate(source):
            if row_index != expected_index:
                continue
            found = True
            for token in line.split():
                try:
                    label = Decimal(token.decode("ascii"))
                except (UnicodeError, InvalidOperation) as exc:
                    raise IndependentLabelError("nonnumeric publisher label") from exc
                if label not in (Decimal(1), Decimal(2), Decimal(3)):
                    raise IndependentLabelError("unexpected publisher class code")
                count[int(label)] += 1
            break
    if not found or not sum(count.values()):
        raise IndependentLabelError("publisher label row absent or empty")
    return {str(i): count[i] for i in (1, 2, 3)}


def verify_raw_label_tallies(archive, train_filename, day8_filename, report):
    """Return counts/scores independently reconstructed from archive label rows."""
    if not isinstance(archive, zipfile.ZipFile):
        raise TypeError("archive must be an open local ZipFile")
    horizon = report["horizon_sampled_observations"]
    tr = _read_class_counts_from_zip(archive, train_filename, horizon)
    ev = _read_class_counts_from_zip(archive, day8_filename, horizon)
    if tr != report["train_class_counts"] or ev != report["day8_class_counts"]:
        raise IndependentLabelError("independent raw label rows disagree with benchmark report")
    training_counts = {int(k): v for k, v in tr.items()}
    winner = max((2, 1, 3), key=lambda k: training_counts[k])
    if winner != report["constant_prediction_class"]:
        raise IndependentLabelError("reported constant predictor not derived from training")
    n = sum(ev.values())
    accuracy = Fraction(ev[str(winner)], n)
    macro_f1 = Fraction(2 * ev[str(winner)], 3 * (n + ev[str(winner)]))
    if abs(float(accuracy) - report["day8_accuracy"]) > 1e-8:
        raise IndependentLabelError("reported accuracy does not match exact count ratio")
    if abs(float(macro_f1) - report["day8_macro_f1"]) > 1e-8:
        raise IndependentLabelError("reported macro-F1 does not match exact class formula")
    return {
        "status": "independent_raw_label_row_recalculation_passed",
        "train_counts": tr, "day8_counts": ev,
        "train_observations": sum(tr.values()), "day8_observations": n,
        "constant_prediction_class": winner,
        "accuracy_exact_ratio": str(accuracy),
        "macro_f1_exact_ratio": str(macro_f1),
        "reserved_folds_opened": False,
    }
