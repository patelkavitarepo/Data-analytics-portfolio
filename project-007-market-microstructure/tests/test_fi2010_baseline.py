"""Every FI-2010 format fixture here is synthetic, not original exchange data."""
import tempfile
import unittest
from pathlib import Path
from microstructure.fi2010_baseline import (
    BenchmarkError, TRAIN_FILENAME, DAY8_FILENAME, evaluate_majority_baseline,
)


def write_matrix(path, row_labels=None, n=6, wrong_row=None):
    """Generate a strict 149-by-N matrix with synthetic normalized features."""
    if row_labels is None:
        row_labels = [1, 1, 2, 2, 3, 3]
    with path.open("w", encoding="utf-8") as stream:
        for row in range(149):
            if row < 144:
                stream.write(" ".join([str(row / 149)] * n) + "\n")
            else:
                values = list(row_labels)
                if row == wrong_row:
                    values[0] = 9
                stream.write(" ".join(map(str, values)) + "\n")


class FI2010BaselineTests(unittest.TestCase):
    def setUp(self):
        ctx = tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.folder = Path(ctx.name)
        self.train = self.folder / TRAIN_FILENAME
        self.day8 = self.folder / DAY8_FILENAME

    def test_train_prior_only_and_known_day8_accuracy(self):
        write_matrix(self.train, [1, 2, 2, 2, 3, 1])
        write_matrix(self.day8, [1, 1, 1, 2, 3, 3])
        result = evaluate_majority_baseline(self.train, self.day8, 5)
        self.assertEqual(result["constant_prediction_class"], 2)
        self.assertEqual(result["day8_accuracy"], round(1 / 6, 8))
        self.assertEqual(result["day8_macro_f1"], round((2 / 7) / 3, 8))
        self.assertEqual(result["train_observations"], 6)
        self.assertEqual(result["evaluation_period"], "benchmark day 8 (Test_CF_7)")

    def test_all_label_horizons_available_without_horizon_leakage(self):
        write_matrix(self.train)
        write_matrix(self.day8)
        for horizon in (1, 2, 3, 5, 10):
            with self.subTest(horizon=horizon):
                self.assertEqual(
                    evaluate_majority_baseline(self.train, self.day8, horizon)["horizon_sampled_observations"],
                    horizon,
                )

    def test_changing_day8_labels_does_not_change_training_choice(self):
        write_matrix(self.train, [1, 1, 1, 1, 2, 3])
        write_matrix(self.day8, [3, 3, 3, 3, 3, 3])
        first = evaluate_majority_baseline(self.train, self.day8)
        write_matrix(self.day8, [1, 1, 1, 1, 1, 1])
        second = evaluate_majority_baseline(self.train, self.day8)
        self.assertEqual(first["constant_prediction_class"], 1)
        self.assertEqual(second["constant_prediction_class"], 1)
        self.assertNotEqual(first["day8_accuracy"], second["day8_accuracy"])

    def test_non_finite_feature_rejected(self):
        write_matrix(self.train)
        self.train.write_text(
            self.train.read_text().replace("0.0", "nan", 1), encoding="utf-8"
        )
        write_matrix(self.day8)
        with self.assertRaisesRegex(BenchmarkError, "nonfinite feature"):
            evaluate_majority_baseline(self.train, self.day8)

    def test_unexpected_class_in_unused_label_row_still_rejected(self):
        write_matrix(self.train, wrong_row=144)
        write_matrix(self.day8)
        with self.assertRaisesRegex(BenchmarkError, "unexpected label"):
            evaluate_majority_baseline(self.train, self.day8, 5)

    def test_inconsistent_matrix_width_rejected(self):
        write_matrix(self.train)
        write_matrix(self.day8)
        contents = self.day8.read_text().splitlines()
        contents[2] += " 10"
        self.day8.write_text("\n".join(contents) + "\n")
        with self.assertRaisesRegex(BenchmarkError, "inconsistent observations"):
            evaluate_majority_baseline(self.train, self.day8)

    def test_reject_wrong_fold_or_transposed_data(self):
        write_matrix(self.train)
        write_matrix(self.day8)
        wrong = self.folder / "Test_Dst_NoAuction_DecPre_CF_8.txt"
        wrong.write_bytes(self.day8.read_bytes())
        with self.assertRaisesRegex(BenchmarkError, "Expected"):
            evaluate_majority_baseline(self.train, wrong)
        transposed = "\n".join(["1 2 3 4 5 6"] * 6)
        self.day8.write_text(transposed)
        with self.assertRaisesRegex(BenchmarkError, "precisely 149"):
            evaluate_majority_baseline(self.train, self.day8)

    def test_reject_invalid_horizon_and_independent_sources(self):
        write_matrix(self.train)
        write_matrix(self.day8)
        with self.assertRaises(BenchmarkError):
            evaluate_majority_baseline(self.train, self.day8, 50)
        with self.assertRaises(BenchmarkError):
            evaluate_majority_baseline(self.train, self.train)

    def test_training_only_tie_policy(self):
        write_matrix(self.train, [1, 1, 2, 2, 3, 3])
        write_matrix(self.day8)
        self.assertEqual(
            evaluate_majority_baseline(self.train, self.day8)["constant_prediction_class"], 2
        )


if __name__ == "__main__":
    unittest.main()
