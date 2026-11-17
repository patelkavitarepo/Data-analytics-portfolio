"""Predeclared panel selection tests; strictly synthetic TAR metadata and labels."""
import importlib.util
from pathlib import Path
import unittest

from microstructure.selective_tar import TarMember, RangeSourceError

research = Path(__file__).resolve().parents[1] / "research"
spec = importlib.util.spec_from_file_location(
    "qa_predeclared_panel", research / "run_quant_arena_panel_once.py"
)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


def member(name):
    return TarMember("quant-arena-public-l1-v1/" + name, 512, 128)


class PredeclaredPanelTests(unittest.TestCase):
    def test_frozen_example_plus_two_smallest_distinct(self):
        members = [
            member("000012.SZ.parquet"),
            member("000444.SZ.parquet"),
            member("000003.SZ.parquet"),
            member("000001.SZ.parquet"),
            member("000002.SZ.parquet"),
            member("manifest.json"),
            member("000000.SH.parquet"),
        ]
        chosen = panel._predeclare_stock_files(members)
        self.assertEqual(chosen, [
            "000012.SZ.parquet", "000001.SZ.parquet", "000002.SZ.parquet"
        ])
        self.assertEqual(len(set(chosen)), 3)

    def test_no_post_hoc_replacement_when_original_example_missing(self):
        with self.assertRaisesRegex(RangeSourceError, "example"):
            panel._predeclare_stock_files([
                member("000001.SZ.parquet"),
                member("000002.SZ.parquet"),
                member("000003.SZ.parquet"),
            ])

    def test_counts_denominator_excludes_unlabelled(self):
        from collections import Counter
        result = panel._counts(Counter({1: 2, 2: 6, 3: 2, None: 10}))
        self.assertEqual(result["eligible"], 10)
        self.assertEqual(result["all_observations"], 20)
        self.assertEqual(result["stationary_percent_of_eligible"], 60)

    def test_panel_horizons_are_frozen(self):
        self.assertEqual(panel.HORIZONS, (1, 2, 3, 5, 10))
        self.assertEqual(panel.THRESHOLDS, ("0.001", "0.002", "0.004"))
        self.assertEqual(panel.EXPECTED_REVISION,
                         "fa85d7b95e56e81317ac349f52e916ca482f0f68")

if __name__ == "__main__":
    unittest.main()
