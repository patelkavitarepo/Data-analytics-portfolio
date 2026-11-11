"""Ephemeral selective Quant-Arena pilot: one published stock, first two trading days.

No archive-wide download; no forecasting model; no FI-2010 data access.
Publishes only aggregate class counts, source manifests and uncertainty notes.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    PUBLIC_SOURCE, HTTPRange, RangeSourceError, scan_tar, download_member,
)
from microstructure.quant_arena_pilot import audit_local_parquet

STOCK = "000012.SZ"  # Publisher's example stock; selected before accessing labels
STOCK_FILE = STOCK + ".parquet"
RELATIVE_STOCK = "quant-arena-public-l1-v1/" + STOCK_FILE
MANIFEST = "quant-arena-public-l1-v1/manifest.json"
MAX_BYTES_TRANSFERRED = 75_000_000  # protect research runner
MAX_STOCK_MEMBER = 65_000_000


def _manifest_digest(data, filename):
    """Find one unambiguous expected file SHA from original publisher metadata."""
    try:
        document = json.loads(data)
    except (UnicodeError, ValueError) as exc:
        raise RangeSourceError("publisher manifest is not valid UTF-8 JSON") from exc
    found = []
    def visit(node, ancestors=()):
        if isinstance(node, dict):
            candidate = node.get("sha256")
            names = list(ancestors[-2:])
            names += [str(node.get(k, "")) for k in (
                "name", "path", "filename", "file", "symbol"
            )]
            if isinstance(candidate, str) and any(
                value == filename
                or value.endswith("/" + filename)
                or value == filename.removesuffix(".parquet")
                for value in names
            ):
                found.append(candidate.lower())
            for k, v in node.items():
                visit(v, ancestors + (str(k),))
        elif isinstance(node, list):
            for value in node:
                visit(value, ancestors)
    visit(document)
    found = list(dict.fromkeys(found))
    if len(found) != 1 or re.fullmatch(r"[0-9a-f]{64}", found[0]) is None:
        raise RangeSourceError(
            "cannot resolve a unique SHA-256 for selected stock from official manifest"
        )
    return found[0]


def _first_dates(source):
    """Choose first two observed calendar dates, not favorable label outcomes."""
    import pyarrow.parquet as pq
    pqfile = pq.ParquetFile(source)
    if "available_at" not in pqfile.schema_arrow.names:
        raise RangeSourceError("no availability timestamp in source Parquet")
    observed = []
    for batch in pqfile.iter_batches(batch_size=8192, columns=["available_at"]):
        for value in batch.column(0).to_pylist():
            if value is None:
                raise RangeSourceError("missing exchange-local availability timestamp")
            d = value.date().isoformat()
            if not observed or observed[-1] != d:
                if d in observed or (observed and d < observed[-1]):
                    raise RangeSourceError("source dates are out of order")
                observed.append(d)
            if len(observed) >= 3:
                break
        if len(observed) >= 3:
            break
    if len(observed) < 2:
        raise RangeSourceError("need two authentic distinct stock trading days")
    return observed[:2]


def main():
    fetch = HTTPRange(PUBLIC_SOURCE)
    files = scan_tar(fetch)
    by_name = {m.name: m for m in files}
    if len(files) != len(by_name):
        raise RangeSourceError("duplicate archive member names")
    if MANIFEST not in by_name or RELATIVE_STOCK not in by_name:
        raise RangeSourceError("expected stock file/manifest not present in TAR")
    manifest = by_name[MANIFEST]
    if not 0 < manifest.size <= 4_000_000:
        raise RangeSourceError("publisher manifest size outside research cap")
    metadata = download_member(fetch, manifest, max_bytes=4_000_000)
    expected_sha = _manifest_digest(metadata, STOCK_FILE)
    member = by_name[RELATIVE_STOCK]
    if not 0 < member.size <= MAX_STOCK_MEMBER:
        raise RangeSourceError("selected stock file exceeds pilot limit")
    stock_bytes = download_member(fetch, member, max_bytes=MAX_STOCK_MEMBER)
    if fetch.bytes_transferred > MAX_BYTES_TRANSFERRED:
        raise RangeSourceError("total range bytes exceed noncommercial pilot cap")
    observed_sha = sha256(stock_bytes).hexdigest()
    if observed_sha != expected_sha:
        raise RangeSourceError("stock Parquet SHA256 mismatches publisher manifest")
    with tempfile.TemporaryDirectory(prefix="quantarena-private-") as folder:
        local = Path(folder) / STOCK_FILE
        local.write_bytes(stock_bytes)
        days = _first_dates(local)
        result = audit_local_parquet(local, STOCK, days, expected_sha)
    result["acquisition"] = {
        "source": PUBLIC_SOURCE,
        "source_dataset": "Ashitemaru/Quant-Arena-Public-L1",
        "public_dataset_commit_prefix": "fa85d7b",
        "publisher_license": "CC BY-NC 4.0",
        "original_archive_fully_downloaded": False,
        "original_archive_sha256_not_checked": True,
        "one_stock_member_sha256_verified_by_manifest": True,
        "archive_members_seen": len(files),
        "remote_range_bytes_received": fetch.bytes_transferred,
        "archive_size_from_content_range": fetch.total_size,
        "data_committed_or_uploaded": False,
        "stock_selection_policy": "000012.SZ, publisher's documented example, chosen before seeing outcomes",
        "dates_selection_policy": "earliest two distinct dates in that stock Parquet",
    }
    print("QUANT_ARENA_ONE_STOCK_PILOT_BEGIN")
    print(json.dumps(result, sort_keys=True, indent=2))
    print("QUANT_ARENA_ONE_STOCK_PILOT_END")


if __name__ == "__main__":
    main()
