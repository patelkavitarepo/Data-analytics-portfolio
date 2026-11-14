import io
import unittest
import zipfile

from microstructure.fi2010_independent import (
    IndependentLabelError, verify_raw_label_tallies
)


def make_zip(train_labels, test_labels):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, values in (("train.txt", train_labels), ("day8.txt", test_labels)):
            rows = ["0.1 " * len(values)] * 144
            for i in range(5):
                rows.append(" ".join(map(str, values)))
            z.writestr(name, "\n".join(rows))
        z.writestr("reserved-day9.txt", "SECRET")
    stream.seek(0)
    return stream


class FI2010IndependentOracleTests(unittest.TestCase):
    def test_exact_fraction_recalculation(self):
        stream = make_zip([1, 1, 2, 3], [1, 2, 2, 3])
        report = {
            "horizon_sampled_observations": 5,
            "train_class_counts": {"1": 2, "2": 1, "3": 1},
            "day8_class_counts": {"1": 1, "2": 2, "3": 1},
            "constant_prediction_class": 1,
            "day8_accuracy": .25,
            "day8_macro_f1": 2 / (3 * 5),
        }
        with zipfile.ZipFile(stream) as z:
            got = verify_raw_label_tallies(z, "train.txt", "day8.txt", report)
        self.assertEqual(got["status"], "independent_raw_label_row_recalculation_passed")
        self.assertEqual(got["accuracy_exact_ratio"], "1/4")
        self.assertEqual(got["macro_f1_exact_ratio"], "2/15")

    def test_corrupted_publisher_label_count_rejected(self):
        stream = make_zip([1, 1, 2, 3], [1, 2, 2, 3])
        report = {
            "horizon_sampled_observations": 5,
            "train_class_counts": {"1": 2, "2": 1, "3": 1},
            "day8_class_counts": {"1": 2, "2": 2, "3": 1},
            "constant_prediction_class": 1,
            "day8_accuracy": .25,
            "day8_macro_f1": 2 / 15,
        }
        with zipfile.ZipFile(stream) as z:
            with self.assertRaisesRegex(IndependentLabelError, "disagree"):
                verify_raw_label_tallies(z, "train.txt", "day8.txt", report)

    def test_nonfinite_labels_rejected(self):
        stream = make_zip([1, 1, 2, 3], [1, "NaN", 2, 3])
        report = {"horizon_sampled_observations": 5}
        with zipfile.ZipFile(stream) as z:
            with self.assertRaisesRegex(IndependentLabelError, "unexpected"):
                verify_raw_label_tallies(z, "train.txt", "day8.txt", report)


if __name__ == "__main__":
    unittest.main()
