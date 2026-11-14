"""D009: metadata-only chronological source-date inventory and 20/5/10 manifest.

No market price, volume, quality flag, label, feature, forecast or holdout
value is read. Acquires only three exact, publisher SHA256-authenticated
per-stock Parquet members of Quant-Arena Public L1, CC BY-NC 4.0.

Printed JSON is metadata only and must be committed *before* any later-price
training/validation audit. One-shot runner, no recurring provider downloads.
"""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_MEMBERS, FROZEN_SHA256, FROZEN_DAYS,
)
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES

MAX_SOURCE_ROWS = 1_500_000


def canonical_manifest_hash(stocks, dates):
    """Hash canonical selected full date lists, not any price or class data."""
    payload = {
        "stocks": list(stocks),
        "discovery": list(dates["discovery"]),
        "train": list(dates["train"]),
        "validation": list(dates["validation"]),
        "holdout": list(dates["holdout"]),
    }
    message = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(message.encode("utf-8")).hexdigest()


def dated_inventory(path):
    """Read only availability timestamp column, checked against Parquet metadata."""
    import pyarrow.parquet as pq
    from datetime import timedelta
    source = pq.ParquetFile(path)
    if "available_at" not in source.schema_arrow.names:
        raise ValueError("publisher file has no available_at time column")
    if source.metadata.num_rows > MAX_SOURCE_ROWS:
        raise ValueError("source stock exceeds bounded row cap")
    counts = {}
    before = None
    seen = 0
    for batch in source.iter_batches(batch_size=4096, columns=["available_at"]):
        for ts in batch.column(0).to_pylist():
            seen += 1
            if ts is None or ts.tzinfo is None or ts.utcoffset() != timedelta(hours=8):
                raise ValueError("nonlocal or null source availability timestamp")
            if before is not None and ts <= before:
                raise ValueError("publisher source time not strictly increasing")
            before = ts
            date = ts.date().isoformat()
            counts[date] = counts.get(date, 0) + 1
    if seen != source.metadata.num_rows:
        raise ValueError("timestamp-only inventory does not reconcile to file metadata")
    if not list(counts)[:5] == list(FROZEN_DAYS):
        raise ValueError("discovery dates shifted since prior authenticated audit")
    return counts, seen


def select_dates(inventories):
    if set(inventories) != {s.removesuffix(".parquet") for s in FROZEN_MEMBERS}:
        raise ValueError("inventory stock set not frozen")
    common = sorted(set.intersection(*(set(a) for a in inventories.values())))
    discovery = list(FROZEN_DAYS)
    if common[:5] != discovery:
        raise ValueError("stock-common discovery dates changed")
    later = [d for d in common if d > discovery[-1]]
    if len(later) < 35:
        raise ValueError("fewer than 35 future common observed dates")
    selection = {
        "discovery": discovery,
        "train": later[:20],
        "validation": later[20:25],
        "holdout": later[25:35],
    }
    if len(set(sum(selection.values(), []))) != 40:
        raise ValueError("split date duplicates or overlap")
    return selection, {
        "common_dates": len(common), "later_common_dates": len(later),
        "stock_calendar_intersection_only": True
    }


def main():
    fetch = HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog, sums = _checked_source(fetch)
    inventories = {}
    source_provenance = {}
    print("DATE_ONLY_STAGE_BEGIN", flush=True)
    with TemporaryDirectory(prefix="qa-date-inventory-private-") as folder:
        for filename in FROZEN_MEMBERS:
            member = catalog.get(ROOT + filename)
            if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
                raise RangeSourceError("frozen selected member missing or oversized")
            if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
                raise RangeSourceError("metadata acquisition exceeded transfer budget")
            expected = checksum_from_sha256sums(sums, ROOT + filename)
            if expected != FROZEN_SHA256[filename]:
                raise RangeSourceError("publisher file hash differs from frozen source")
            data = download_member(fetch, member, max_bytes=MAX_STOCK_BYTES)
            if sha256(data).hexdigest() != expected:
                raise RangeSourceError("source member failed sha256sum comparison")
            path = Path(folder) / filename
            path.write_bytes(data)
            del data
            symbol = filename.removesuffix(".parquet")
            counts, total = dated_inventory(path)
            inventories[symbol] = counts
            source_provenance[symbol] = {
                "source_sha256": expected,
                "source_member_bytes": member.size,
                "metadata_rows": total,
                "distinct_observed_dates": len(counts),
            }
            path.unlink()
            print("DATE_ONLY_STOCK_VERIFIED:",symbol,flush=True)
    selected, calendar = select_dates(inventories)
    digest = canonical_manifest_hash(
        [name.removesuffix(".parquet") for name in FROZEN_MEMBERS],
        selected
    )
    report = {
        "status": "D009_METADATA_ONLY_SPLIT_PROPOSED_FOR_FREEZE",
        "source": "Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "license": "CC BY-NC 4.0, noncommercial",
        "source_url": "https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "publisher_revision": EXPECTED_REVISION,
        "selected_members": list(FROZEN_MEMBERS),
        "source_provenance": source_provenance,
        "calendar": calendar,
        "dates": selected,
        "date_list_sha256": digest,
        "canonical_digest_rule": "sha256(UTF8 JSON sort_keys=True,separators=(',',':') over {stocks,discovery,train,validation,holdout})",
        "source_date_counts_for_selected_days": {
            sym: {d: inv[d] for d in sum(selected.values(), [])}
            for sym, inv in inventories.items()
        },
        "downloaded_pinned_member_bytes_total": fetch.bytes_transferred,
        "full_archive_acquired_or_verified": False,
        "source_prices_or_flags_accessed": False,
        "train_validation_prices_accessed": False,
        "holdout_prices_or_labels_accessed": False,
        "holdout_sealed": True,
        "selection_policy": "intersection of observed date identifiers, first 20 later common dates train, next 5 validation, next 10 sealed",
        "note": "Full member bytes were downloaded for source SHA256, but Parquet access was timestamp-only; source pricing/target columns not loaded.",
    }
    print("QUANT_ARENA_DATE_MANIFEST_BEGIN", flush=True)
    print(json.dumps(report, sort_keys=True, indent=2), flush=True)
    print("QUANT_ARENA_DATE_MANIFEST_END", flush=True)


if __name__ == "__main__":
    main()
