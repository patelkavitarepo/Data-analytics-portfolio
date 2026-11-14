"""Ephemeral, source-pinned FI-2010 label-construction audit.

The official paper defines five source-processed horizon labels. This examines
publisher label composition only, not independently reconstructed market returns.
Never extracts or opens CF8/CF9 reserved folds. Does not fit or score models.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.fi2010_construction import (
    HORIZONS, TRAIN, DAY8, inspect_archive, read_labels_only,
)
from run_fi2010_once import _download, EXPECTED_ARCHIVE_SHA256, LEGAL_RECORD, SOURCE


def contiguous_quintiles(array):
    """Observation-order quintiles, never mislabeled as wall-clock intervals."""
    n = len(array)
    result = []
    for i in range(5):
        lo, hi = n * i // 5, n * (i + 1) // 5
        part = array[lo:hi]
        result.append({
            "segment": i + 1,
            "range": [lo, hi],
            "n": len(part),
            "stationary_share_pct": round(100 * part.count(2) / len(part), 4),
        })
    return result


def horizon_agreement(data, first, second):
    if len(data[first]) != len(data[second]):
        raise ValueError("unequal label lengths")
    n = len(data[first])
    return round(sum(x == y for x, y in zip(data[first], data[second])) / n, 6)


def main():
    with tempfile.TemporaryDirectory(prefix="fi2010-construction-") as d:
        archive_path = Path(d) / "source.zip"
        nbytes = _download(archive_path)
        result = inspect_archive(archive_path)
        with zipfile.ZipFile(archive_path) as z:
            tr, ntr = read_labels_only(z, TRAIN)
            day, nday = read_labels_only(z, DAY8)
        if ntr != 254750 or nday != 55478:
            raise ValueError("Unexpected fold observation count")
        result["day8_contiguous_observation_quintiles_h5"] = contiguous_quintiles(day[5])
        result["training_horizon_agreement_1_vs_5"] = horizon_agreement(tr, 1, 5)
        result["day8_horizon_agreement_1_vs_5"] = horizon_agreement(day, 1, 5)
        result["provenance"] = {
            "original_catalog": LEGAL_RECORD,
            "source": SOURCE,
            "source_sha256": EXPECTED_ARCHIVE_SHA256,
            "archive_bytes": nbytes,
            "binary_identity_with_original_fairdata": "unverified",
            "publisher": "Ntakaris et al., Journal of Forecasting (2018), DOI 10.1002/for.2543",
            "license": "CC BY 4.0 from Fairdata official metadata",
            "raw_data_committed": False,
            "reserved_days_9_10_read": False,
        }
        print("FI2010_CONSTRUCTION_SUMMARY_BEGIN")
        print(json.dumps(result, sort_keys=True, indent=2))
        print("FI2010_CONSTRUCTION_SUMMARY_END")


if __name__ == "__main__":
    main()
