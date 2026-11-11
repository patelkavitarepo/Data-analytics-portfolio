"""One-time, source-pinned training-only label-formula consistency check.

No models, no day-eight feature reads or holdout data. An agreement or mismatch
in the transformed price columns does not prove original label construction.
"""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.fi2010_label_reconstruction import inspect_training_source
from run_fi2010_once import _download, EXPECTED_ARCHIVE_SHA256


def main():
    with tempfile.TemporaryDirectory(prefix="fi2010-labelcheck-") as d:
        path = Path(d) / "pinned-source.zip"
        n = _download(path)
        result = inspect_training_source(path)
        print("FI2010_TRAIN_LABEL_FORMULA_CHECK_BEGIN")
        print(json.dumps({
            "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "source_archive_bytes": n,
            "status": "train_only_construction_consistency_not_model_performance",
            "checks": result,
            "days_8_9_10_feature_files_read": False,
        }, sort_keys=True, indent=2))
        print("FI2010_TRAIN_LABEL_FORMULA_CHECK_END")


if __name__ == "__main__":
    main()
