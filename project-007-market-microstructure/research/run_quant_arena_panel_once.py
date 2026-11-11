"""D005: PREDECLARED three-stock/five-session source-label construction panel.

Noncommercial Quant-Arena Public L1 (CC BY-NC 4.0), distinct from FI-2010.
No strategy, model fitting, execution claims, provider credential, data upload,
unlimited downloader, or later-date target evaluation.

Source-admission gates:
  * Exact previously verified immutable publisher revision.
  * Bounded HTTP 206 TAR-header scan; publisher manifest & SHA256SUMS.
  * Previously reviewed 000012.SZ and two smallest distinct .SZ Parquets.
  * Exactly the earliest five observed sessions, chosen from timestamps alone.
  * Strict source-file checksum and per-origin independent oracle.
Output: attribution-bearing, source-verifiable AGGREGATES only.
"""
from collections import Counter
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, scan_tar, download_member, pinned_source_url,
    checksum_from_sha256sums,
)
from microstructure.quant_arena_pilot import (
    REQUIRED_FIELDS, PilotError, convert_quote_rows, pilot_summary,
)
from microstructure.stockday_labels import labels_from_quotes
from microstructure.stockday_oracle import verify_labels

EXPECTED_REVISION = "fa85d7b95e56e81317ac349f52e916ca482f0f68"
ROOT = "quant-arena-public-l1-v1/"
STOCK_EXAMPLE = "000012.SZ.parquet"
MANIFEST = ROOT + "manifest.json"
SHA256SUMS = ROOT + "SHA256SUMS"
MAX_STOCK_BYTES = 75_000_000
MAX_REMOTE_BYTES = 205_000_000
HORIZONS = (1, 2, 3, 5, 10)
THRESHOLDS = ("0.001", "0.002", "0.004")


def _predeclare_stock_files(members):
    names = sorted({
        m.name[len(ROOT):] for m in members
        if m.name.startswith(ROOT)
        and re.fullmatch(r"[0-9]{6}\.SZ\.parquet", m.name[len(ROOT):])
    })
    if STOCK_EXAMPLE not in names or len(names) < 3:
        raise RangeSourceError("predeclared example or sufficient .SZ stock files absent")
    first_two = [name for name in names if name != STOCK_EXAMPLE][:2]
    chosen = [STOCK_EXAMPLE, *first_two]
    if len(set(chosen)) != 3:
        raise RangeSourceError("stock selection produced duplicates")
    return chosen


def _available_dates_only(source):
    """Inspect ALL availability timestamps, but no later-date PRICES or labels."""
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(source)
    if "available_at" not in parquet.schema_arrow.names:
        raise PilotError("source missing available_at")
    seen = []
    counts = Counter()
    previous = None
    n = 0
    for batch in parquet.iter_batches(batch_size=8192, columns=["available_at"]):
        for ts in batch.column(0).to_pylist():
            n += 1
            if ts is None or ts.utcoffset() != timedelta(hours=8):
                raise PilotError("source availability timestamps missing or wrong timezone")
            if previous is not None and ts <= previous:
                raise PilotError("full-stock availability chronology repeated or reversed")
            previous = ts
            day = ts.date().isoformat()
            if not seen or day != seen[-1]:
                if day in counts or (seen and day < seen[-1]):
                    raise PilotError("source trading dates out of order")
                seen.append(day)
            counts[day] += 1
    if n != parquet.metadata.num_rows:
        raise PilotError("source chronology count does not match Parquet metadata")
    if len(seen) < 6:
        raise PilotError("need five source dates and at least one reserved later date")
    selected = seen[:5]
    if any(counts[d] < 2 for d in selected):
        raise PilotError("predeclared five source dates include an undersized session")
    # Later dates are never named, scored or used to select the five.
    return selected, {d: counts[d] for d in selected}, n, len(seen)


def _first_five_quote_rows(source, selected_dates):
    """Stream only early quote batches; never process price labels after date five."""
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(source)
    if any(k not in parquet.schema_arrow.names for k in REQUIRED_FIELDS):
        raise PilotError("required fields absent from publisher Parquet")
    selected = set(selected_dates)
    rows = []
    stopped = False
    for batch in parquet.iter_batches(
        batch_size=1024, columns=list(REQUIRED_FIELDS)
    ):
        for item in batch.to_pylist():
            available = item.get("available_at")
            if available is None:
                raise PilotError("null source availability on early price rows")
            if available.date().isoformat() not in selected:
                stopped = True
                break
            rows.append(item)
        if stopped:
            break
    return rows


def _threshold_by_day(quotes, days):
    result = {}
    for threshold in THRESHOLDS:
        labels = labels_from_quotes(
            quotes, 5, threshold=threshold, max_gap_seconds=30
        )
        # Distinct math/loop oracle for each predeclared threshold.
        check = verify_labels(
            quotes, 5, threshold=threshold, max_gap_seconds=30
        )
        if check["mismatched_rows"] != 0:
            raise AssertionError("threshold oracle mismatch")
        c = Counter(x.classification for x in labels)
        if sum(c.values()) != len(quotes):
            raise AssertionError("threshold labels do not cover input rows")
        by_day = {}
        for day in days:
            values = Counter(
                x.classification for x in labels if x.trading_date == day
            )
            by_day[day] = _counts(values)
        result[threshold] = {"pooled": _counts(c), "by_day": by_day}
    return result


def _counts(c):
    total = sum(c.values())
    eligible = c[1] + c[2] + c[3]
    return {
        "up": c[1], "stationary": c[2], "down": c[3],
        "unlabelled": c[None],
        "all_observations": total, "eligible": eligible,
        "stationary_percent_of_eligible": (
            round(100*c[2]/eligible, 4) if eligible else None
        ),
    }


def _audit_stock(source_file, symbol, digest):
    days, seen_counts, source_rows, source_dates = _available_dates_only(source_file)
    raw = _first_five_quote_rows(source_file, days)
    quotes, quality = convert_quote_rows(raw, symbol, days)
    if quality["selected_rows_by_date"] != seen_counts:
        raise PilotError("read-only selected-day quote rows differ from availability scan")
    # Production summary and independent all-row oracle.
    descriptive = pilot_summary(quotes, symbol, days)
    independent = {
        str(h): verify_labels(quotes, h, max_gap_seconds=30)
        for h in HORIZONS
    }
    if any(v["rows_verified"] != len(quotes) or v["mismatched_rows"] != 0
           for v in independent.values()):
        raise AssertionError("independent label/origin verification failed")
    per_horizon = {}
    for h in HORIZONS:
        observed = descriptive["counts_by_horizon"][str(h)]
        per_day = {}
        for day, item in observed["daily_class_counts"].items():
            c = Counter({1:item["up"], 2:item["stationary"],
                         3:item["down"], None:item["unlabelled"]})
            per_day[day] = _counts(c)
        pooled = Counter({1:observed["up"],2:observed["stationary"],
                          3:observed["down"],None:observed["unlabelled"]})
        if sum(v["all_observations"] for v in per_day.values()) != len(quotes):
            raise AssertionError("daily count reconciliation failed")
        per_horizon[str(h)] = {
            "pooled": _counts(pooled), "by_day": per_day,
            "excluded_reason_counts": observed["excluded_reasons"],
            "oracle_verified_rows": independent[str(h)]["rows_verified"],
            "oracle_mismatches": 0,
        }
    return {
        "symbol":symbol, "dates":days, "rows_by_day":seen_counts,
        "original_stock_rows":source_rows,
        "original_stock_distinct_days":source_dates,
        "selected_rows":len(quotes),
        "parquet_sha256":digest,
        "parquet_size_bytes":source_file.stat().st_size,
        "actual_schema_columns":__import__("pyarrow.parquet",fromlist=["ParquetFile"]).ParquetFile(source_file).schema_arrow.names,
        "source_quality_counts":descriptive["selected_observation_quality_counts"],
        "source_selection_quality":quality,
        "by_horizon":per_horizon,
        "threshold_sensitivity_at_horizon_5": _threshold_by_day(quotes, days),
    }


def main():
    source_url = pinned_source_url(EXPECTED_REVISION)
    print("PINNED_PUBLISHER_REVISION:",EXPECTED_REVISION,flush=True)
    fetch = HTTPRange(source_url)
    members = scan_tar(fetch)
    entries = {m.name:m for m in members}
    if len(entries) != len(members):
        raise RangeSourceError("duplicate source member paths")
    selected = _predeclare_stock_files(members)
    print("FROZEN_PANEL_STOCK_FILES:",",".join(selected),flush=True)
    if MANIFEST not in entries or SHA256SUMS not in entries:
        raise RangeSourceError("publisher manifest/checksum list missing")
    manifest = entries[MANIFEST]
    if not 0 < manifest.size <= 4_000_000:
        raise RangeSourceError("publisher manifest too large")
    parsed_manifest = json.loads(download_member(fetch,manifest,max_bytes=4_000_000))
    if not isinstance(parsed_manifest,dict):
        raise RangeSourceError("publisher manifest must be JSON object")
    checksums=entries[SHA256SUMS]
    if not 0 < checksums.size <= 200_000:
        raise RangeSourceError("publisher checksums too large")
    digests=download_member(fetch,checksums,max_bytes=200_000)

    results=[]
    with tempfile.TemporaryDirectory(prefix="qa-panel-private-") as td:
        for stock_filename in selected:
            member=entries.get(ROOT+stock_filename)
            if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
                raise RangeSourceError("selected publisher stock member missing/oversized")
            if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
                raise RangeSourceError("predeclared panel would exceed selective transfer cap")
            expected=checksum_from_sha256sums(digests,ROOT+stock_filename)
            content=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            actual=sha256(content).hexdigest()
            if actual != expected:
                raise RangeSourceError("stock member SHA256 differs from publisher SHA256SUMS")
            stock=stock_filename.removesuffix(".parquet")
            print("AUTHENTICATED_STOCK_FILE:",stock,actual,flush=True)
            destination=Path(td)/stock_filename
            destination.write_bytes(content)
            del content
            result=_audit_stock(destination,stock,actual)
            if sha256(destination.read_bytes()).hexdigest() != actual:
                raise RangeSourceError("source changed during label audit")
            destination.unlink()
            results.append(result)
            print("SOURCE_DAYS_CHECKED:",stock,",".join(result["dates"]),flush=True)

    # Explicit row-weighted pooling, not unqualified averaging of percentages.
    pooled={}
    for h in HORIZONS:
        counter=Counter()
        for stock in results:
            c=stock["by_horizon"][str(h)]["pooled"]
            for cls,field in ((1,"up"),(2,"stationary"),(3,"down"),(None,"unlabelled")):
                counter[cls]+=c[field]
        pooled[str(h)]=_counts(counter)
    threshold_pooled={}
    for t in THRESHOLDS:
        counter=Counter()
        for stock in results:
            c=stock["threshold_sensitivity_at_horizon_5"][t]["pooled"]
            for cls,field in ((1,"up"),(2,"stationary"),(3,"down"),(None,"unlabelled")):
                counter[cls]+=c[field]
        threshold_pooled[t]=_counts(counter)

    report={
        "status":"three_stock_five_day_label_construction_replication_no_model",
        "citation":"Quant-Arena Public L1 (Ashitemaru / LaPlace's Eye / Einsia AI), CC BY-NC 4.0; publisher dataset https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "publisher_revision":EXPECTED_REVISION,
        "tar_source":source_url,
        "archive_total_bytes":fetch.total_size,
        "whole_archive_downloaded":False,
        "whole_archive_hash_verified":False,
        "selected_files_verified_against_publisher_SHA256SUMS":True,
        "selected_file_policy":"000012.SZ plus two lexicographically smallest other .SZ Parquet filenames",
        "selected_day_policy":"earliest five chronologically distinct observed days per file, based on availability timestamps only",
        "later_date_price_targets_examined":False,
        "full_stock_date_order_verified_from_availability_timestamps_only":True,
        "data_committed_or_uploaded":False,
        "bytes_transferred_in_http_ranges":fetch.bytes_transferred,
        "label_rule":"next-k mean midpoint relative to origin, class 1 up / 2 stationary / 3 down, thresholds fixed",
        "eligibility":"same stock/date valid contiguous quotes with gaps at most 30 sec, no interpolation",
        "horizons":[*HORIZONS],"primary_threshold":0.002,
        "descriptive_thresholds_at_k5":[0.001,0.002,0.004],
        "stocks":results,
        "row_weighted_pooled_by_horizon":pooled,
        "row_weighted_pooled_threshold_sensitivity_k5":threshold_pooled,
        "limitations":[
            "Different market, stocks, years, time grid and license than FI-2010; no original publisher label replication.",
            "Quote-level future labels, NOT model predictions or trading returns.",
            "15-second quote grid; records with missing/invalid/stale quotes or long gaps excluded, not imputed.",
            "Stock/date identities preserved, but sampled dates are observed days, not independently certified complete exchange sessions.",
            "No independence or standard-error claims: overlapping targets and stock/time clustering.",
            "Whole archive was not downloaded or checksum-verified; each selected stock member was SHA256-verified.",
            "No later-date PRICE outcomes, trading P&L, fills or real-time signals were evaluated.",
        ],
    }
    print("QUANT_ARENA_PANEL_BEGIN",flush=True)
    print(json.dumps(report,sort_keys=True,indent=2),flush=True)
    print("QUANT_ARENA_PANEL_END",flush=True)


if __name__ == "__main__":
    main()
