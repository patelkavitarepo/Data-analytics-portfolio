import io
import unittest
import zipfile
from microstructure.fi2010_construction import (
    HORIZONS, TRAIN, DAY8, ConstructionError, inspect_archive, summarize_labels
)


def build_fake_zip(train, day8, *, bad=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, labels in ((TRAIN, train), (DAY8, day8)):
            lines = ["1.5 2.5" for _ in range(144)]
            for i, horizon in enumerate(HORIZONS):
                values = list(labels[horizon])
                if bad and name == DAY8 and i == 3:
                    values[0] = 9
                lines.append(" ".join(str(x) for x in values))
            z.writestr(name, "\n".join(lines) + "\n")
        z.writestr("Test_Dst_NoAuction_DecPre_CF_8.txt", "RESERVED DAY9")
        z.writestr("Test_Dst_NoAuction_DecPre_CF_9.txt", "RESERVED DAY10")
    buf.seek(0)
    return buf


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.train = {h: bytearray([1, 2]) for h in HORIZONS}
        self.day8 = {h: bytearray([2, 2]) for h in HORIZONS}

    def test_all_horizons_and_pct_shift(self):
        s = summarize_labels(self.train, self.day8)
        self.assertEqual(set(s["by_horizon"]), {"1", "2", "3", "5", "10"})
        fifth = s["by_horizon"]["5"]
        self.assertEqual(fifth["difference_day8_minus_train_percentage_points"]["2"], 50.0)
        self.assertEqual(fifth["total_variation_distance"], 0.5)
        self.assertTrue(fifth["day8_stationary_share_exceeds_training"])

    def test_zip_reader_ignores_reserved_members(self):
        result = inspect_archive(build_fake_zip(self.train, self.day8))
        self.assertEqual(result["train_observations"], 2)
        self.assertEqual(result["reserved_files_read"], [])
        self.assertEqual(result["files_read"], [TRAIN, DAY8])

    def test_rejects_bad_publisher_label(self):
        with self.assertRaisesRegex(ConstructionError, "invalid label"):
            inspect_archive(build_fake_zip(self.train, self.day8, bad=True))

    def test_rejects_missing_horizon(self):
        incomplete = dict(self.train)
        del incomplete[5]
        with self.assertRaisesRegex(ConstructionError, "missing horizon"):
            summarize_labels(incomplete, self.day8)

    def test_rejects_invalid_class(self):
        corrupt = dict(self.day8)
        corrupt[1] = bytearray([2, 5])
        with self.assertRaisesRegex(ConstructionError, "unknown label"):
            summarize_labels(self.train, corrupt)


if __name__ == "__main__":
    unittest.main()
