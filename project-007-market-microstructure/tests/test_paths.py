import tempfile
import unittest
from pathlib import Path

from microstructure.paths import LOCAL_ARTIFACT_ROOT, safe_report_output


class OutputPathTests(unittest.TestCase):
    def test_accepts_only_ignored_local_artifact_json(self):
        expected = LOCAL_ARTIFACT_ROOT / "local-summary.json"
        self.assertEqual(safe_report_output(expected), expected)

    def test_rejects_nonignored_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            targets = [
                Path(tmp) / "output.json",
                LOCAL_ARTIFACT_ROOT.parent / "README.json",
                LOCAL_ARTIFACT_ROOT / "sample.csv",
                LOCAL_ARTIFACT_ROOT,
            ]
            for target in targets:
                with self.subTest(path=str(target)), self.assertRaises(ValueError):
                    safe_report_output(target)

    def test_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            # This check only changes a synthetic temporary path, not project data.
            target = Path(tmp) / "outside.json"
            link = LOCAL_ARTIFACT_ROOT / "synthetic-test-link"
            LOCAL_ARTIFACT_ROOT.mkdir(exist_ok=True)
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("test environment cannot create symlinks")
            try:
                with self.assertRaises(ValueError):
                    safe_report_output(link)
            finally:
                link.unlink()


if __name__ == "__main__":
    unittest.main()
