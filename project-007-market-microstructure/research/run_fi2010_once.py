"""Controlled first actual-data FI-2010 run on an ephemeral GitHub Actions runner.

Source: Oxford DeepLOB research authors' 56.3 MB publicly published data.zip
Fairdata original FI-2010 metadata records Open / CC BY 4.0.
No raw dataset committed or uploaded. Only training days 1-7 and day 8 opened.
This does not reconstruct labels or verify upstream training/label boundaries.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.fi2010_baseline import (
    evaluate_majority_baseline, TRAIN_FILENAME, DAY8_FILENAME,
)
from microstructure.fi2010_independent import verify_raw_label_tallies

SOURCE = (
    "https://raw.githubusercontent.com/zcakhaa/"
    "DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/"
    "master/data/data.zip"
)
EXPECTED_ARCHIVE_SHA256 = "7a5564290a504bdc104dccaf44aa6c0b3857bf1db6b0517b9b88577c2def3e5f"
EXPECTED_ARCHIVE_BYTES = 56_278_154
MAX_BYTES = 70_000_000
HORIZON = 5
LEGAL_RECORD = "https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649"


def _download(zip_path):
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Project007-FI2010-Research/0.1"})
    digest = sha256()
    count = 0
    with urllib.request.urlopen(req, timeout=90) as response, zip_path.open("wb") as dst:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > MAX_BYTES:
                raise RuntimeError("Archive size exceeds cap")
            digest.update(chunk)
            dst.write(chunk)
    if digest.hexdigest() != EXPECTED_ARCHIVE_SHA256 or count != EXPECTED_ARCHIVE_BYTES:
        raise RuntimeError("Archive contents changed since reviewed intake")
    return count


def _extract_exact(z, name, target, max_uncompressed_size):
    matching = [member for member in z.infolist() if member.filename == name]
    if len(matching) != 1:
        raise RuntimeError("Missing or duplicated official benchmark fold name: " + name)
    item = matching[0]
    if item.file_size <= 0 or item.file_size > max_uncompressed_size:
        raise RuntimeError("Unexpected member size: " + name)
    with z.open(item) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    if target.stat().st_size != item.file_size:
        raise RuntimeError("Extraction size mismatch")
    return item.file_size


def main():
    with tempfile.TemporaryDirectory(prefix="fi2010-private-") as folder:
        root = Path(folder)
        archive = root / "source-data.zip"
        size = _download(archive)
        with zipfile.ZipFile(archive) as z:
            entries = {member.filename for member in z.infolist() if not member.is_dir()}
            expected = {
                TRAIN_FILENAME,
                DAY8_FILENAME,
                "Test_Dst_NoAuction_DecPre_CF_8.txt",
                "Test_Dst_NoAuction_DecPre_CF_9.txt",
            }
            if entries != expected:
                raise RuntimeError("Unexpected archive contents; fail closed")
            train = root / TRAIN_FILENAME
            test = root / DAY8_FILENAME
            train_bytes = _extract_exact(z, TRAIN_FILENAME, train, 700_000_000)
            test_bytes = _extract_exact(z, DAY8_FILENAME, test, 175_000_000)
            # This pipeline NEVER calls ZipFile.open on reserved day 9/10 members.
        report = evaluate_majority_baseline(train, test, horizon=HORIZON)
        with zipfile.ZipFile(archive) as source:
            independent = verify_raw_label_tallies(source, TRAIN_FILENAME, DAY8_FILENAME, report)
        output = {
            "provenance": {
                "original_dataset": LEGAL_RECORD,
                "source_dataset": SOURCE,
                "research_mirror_verified_identical_to_original": False,
                "attribution": (
                    "Ntakaris, Magris, Kanniainen, Gabbouj & Iosifidis (2018), "
                    "Benchmark Dataset for Mid-Price Forecasting of Limit Order "
                    "Book Data with Machine Learning Methods, Journal of Forecasting, "
                    "DOI: 10.1002/for.2543; re-hosted by DeepLOB researchers"
                ),
                "license": "CC BY 4.0 (official Fairdata metadata, verified from API)",
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "archive_bytes": size,
                "train_bytes": train_bytes,
                "day8_bytes": test_bytes,
                "reserved_day9_day10_read": False,
                "raw_samples_committed_or_uploaded": False,
            },
            "baseline": report,
            "independent_raw_label_oracle": independent,
        }
        # Public aggregate scores with dataset authorship/licensing included;
        # no row-level data, original file payloads or user secrets printed.
        print("FI2010_DAY8_REAL_DATA_RESULT_JSON_BEGIN")
        print(json.dumps(output, sort_keys=True, indent=2))
        print("FI2010_DAY8_REAL_DATA_RESULT_JSON_END")


if __name__ == "__main__":
    main()
