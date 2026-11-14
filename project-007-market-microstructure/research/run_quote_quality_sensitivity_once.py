"""D006 preregistered 3-stock/5-session gap and quality-flag sensitivity.

Exact pinned source/revision; noncommercial CC BY-NC 4.0; no later-date
market PRICE reads, no model, no trading, no vendor raw rows in git/logs.
No data upload; all vendor files removed after ephemeral processing.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, scan_tar, download_member, pinned_source_url,
    checksum_from_sha256sums,
)
from microstructure.quant_arena_pilot import (
    convert_quote_rows, file_sha256, PilotError,
)
from microstructure.quote_quality_sensitivity import (
    sensitivity_panel, GAP_LIMITS, FLAG_MODES,
)
from run_quant_arena_panel_once import (
    ROOT, MANIFEST, SHA256SUMS, EXPECTED_REVISION,
    MAX_STOCK_BYTES, MAX_REMOTE_BYTES, _predeclare_stock_files,
    _available_dates_only, _first_five_quote_rows,
)

FROZEN_DAYS = ("2022-01-04", "2022-01-05", "2022-01-06",
               "2022-01-07", "2022-01-10")
FROZEN_MEMBERS = (
    "000012.SZ.parquet", "000025.SZ.parquet", "000031.SZ.parquet",
)
FROZEN_SHA256 = {
    "000012.SZ.parquet": "97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af",
    "000025.SZ.parquet": "4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654",
    "000031.SZ.parquet": "3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8",
}
FROZEN_OBSERVATIONS = {
    "000012.SZ": 5078, "000025.SZ": 5077, "000031.SZ": 5078,
}


def _checked_source(fetch):
    members = scan_tar(fetch)
    catalog = {m.name: m for m in members}
    if len(members) != len(catalog):
        raise RangeSourceError("source TAR contains duplicated member names")
    selected = tuple(_predeclare_stock_files(members))
    if selected != FROZEN_MEMBERS:
        raise RangeSourceError("source stock selection changed from frozen panel")
    if MANIFEST not in catalog or SHA256SUMS not in catalog:
        raise RangeSourceError("source manifest or SHA256SUMS not available")
    manifest = catalog[MANIFEST]
    if not 0 < manifest.size <= 4_000_000:
        raise RangeSourceError("publisher manifest length changed")
    if not isinstance(json.loads(download_member(
        fetch, manifest, max_bytes=4_000_000
    )), dict):
        raise RangeSourceError("publisher manifest no longer JSON object")
    sums = catalog[SHA256SUMS]
    if not 0 < sums.size <= 200_000:
        raise RangeSourceError("publisher SHA256SUMS too large")
    data = download_member(fetch, sums, max_bytes=200_000)
    return catalog, data


def _one_stock(fetch, catalog, hashes, filename, folder):
    member = catalog.get(ROOT + filename)
    if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
        raise RangeSourceError("selected member missing or above source size cap")
    if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
        raise RangeSourceError("selective data budget exceeded")
    expected = checksum_from_sha256sums(hashes, ROOT+filename)
    if expected != FROZEN_SHA256[filename]:
        raise RangeSourceError("publisher source digest changed from prior audit")
    raw_bytes = download_member(fetch, member, max_bytes=MAX_STOCK_BYTES)
    if sha256(raw_bytes).hexdigest() != expected:
        raise RangeSourceError("downloaded stock SHA256 differs from source manifest")
    print("FROZEN_STOCK_HASH_VERIFIED:",filename,expected,flush=True)
    dest = folder / filename
    dest.write_bytes(raw_bytes)
    del raw_bytes
    symbol = filename.removesuffix(".parquet")
    days, day_rows, total, total_days = _available_dates_only(dest)
    if tuple(days) != FROZEN_DAYS:
        raise PilotError("source selected trading dates differ from prior study")
    selected_raw = _first_five_quote_rows(dest, days)
    quotes, qc = convert_quote_rows(selected_raw, symbol, days)
    if len(quotes) != FROZEN_OBSERVATIONS[symbol]:
        raise PilotError("source selected sample size changed")
    if qc["selected_rows_by_date"] != day_rows:
        raise PilotError("selected row count differs from date-only scan")
    output = sensitivity_panel(quotes, symbol, days)
    if file_sha256(dest) != expected:
        raise RangeSourceError("selected stock file changed during analysis")
    output["source_provenance"] = {
        "file": filename, "sha256": expected, "file_bytes": member.size,
        "original_stock_metadata_row_count": total,
        "original_stock_metadata_distinct_days": total_days,
        "selected_rows_by_day": day_rows,
        "publisher_sha256sums": True,
        "no_later_date_prices_inspected": True,
    }
    dest.unlink()
    print("SENSITIVITY_STOCK_DONE:",symbol,flush=True)
    return output


def _pool(out):
    scenarios = ("G15","G30","G60","G120","F0","FS","FD","FSD")
    combined={}
    ranks={}
    for key in scenarios:
        c=Counter()
        changes=Counter()
        stock_pct={}
        for result in out:
            s=result["scenarios"][key]
            v=s["pooled_counts"]
            for field in ("all","up","stationary","down","unlabelled","eligible"):
                c[field]+=v[field]
            for name,n in s["versus_G30_F0"].items():
                changes[name]+=n
            stock_pct[result["symbol"]]=v["stationary_pct_of_eligible"]
        if c["all"] != c["up"]+c["stationary"]+c["down"]+c["unlabelled"]:
            raise AssertionError("pooled class totals do not match source total")
        if c["all"] != 15233:
            raise AssertionError("source sample denominator changed")
        combined[key]={
            **dict(c),
            "stationary_percent_of_eligible": (
                round(100*c["stationary"]/c["eligible"],4) if c["eligible"] else None
            ),
            "versus_G30_F0":dict(changes),
            "stock_stationary_percent_of_eligible":stock_pct,
            "ranking_descending_stock":sorted(
                stock_pct,key=lambda stock:(
                    -stock_pct[stock] if stock_pct[stock] is not None else float("inf"),
                    stock
                )
            )
        }
    return combined


def main():
    source_url=pinned_source_url(EXPECTED_REVISION)
    fetch=HTTPRange(source_url)
    print("SOURCE_REVISION_PINNED:",EXPECTED_REVISION,flush=True)
    catalog,hashes=_checked_source(fetch)
    results=[]
    with tempfile.TemporaryDirectory(prefix="qa-quality-sensitivity-private-") as tmp:
        root=Path(tmp)
        for filename in FROZEN_MEMBERS:
            results.append(_one_stock(fetch,catalog,hashes,filename,root))
    if sum(x["source_rows"] for x in results) != 15233:
        raise AssertionError("frozen sample count changed")
    report={
        "status":"source_verified_d006_gap_flag_stress_no_model",
        "source":"Quant-Arena Public L1 / Ashitemaru / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_citation":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0, noncommercial research with attribution",
        "revision":EXPECTED_REVISION,
        "dataset_tar_source":source_url,
        "whole_archive_downloaded":False,
        "whole_archive_sha256_verified":False,
        "each_selected_file_verified_against_publisher_SHA256SUMS":True,
        "selected_file_hashes":FROZEN_SHA256,
        "dates":list(FROZEN_DAYS),
        "selected_rows":15233,
        "bytes_transferred_via_range":fetch.bytes_transferred,
        "raw_quotes_committed_or_uploaded":False,
        "heldout_dates_prices_read":False,
        "publisher_FI2010_labels_validated":False,
        "k":5,"classification_threshold":"0.002",
        "gap_scenarios_seconds":GAP_LIMITS,
        "quality_flag_counterfactuals":FLAG_MODES,
        "primary_reference":"G30 and F0: strict source flags, 30sec maximum gap",
        "stocks":results,
        "pooled":_pool(results),
        "limitations":[
            "Diagnostic counterfactual flag ignores are deliberately unsafe for interpreting executable quotes.",
            "Increasing allowed gaps does not reconstruct missing market data or prove time continuity.",
            "All scenario comparisons change eligibility as well as possibly labels; never compare percentages without denominators.",
            "Selected source days may have truncated public histories and overlapping future targets.",
            "Historical Shenzhen 2022 source is not FI-2010 Helsinki 2010; cannot validate original FI-2010 labels.",
            "No forecasts, model training, brokerage execution, fill estimates, trading profit, IID p-values or causality.",
            "Vendor full archive not acquired/hashed; three selected member hashes checked independently.",
        ],
    }
    print("QUANT_ARENA_SENSITIVITY_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("QUANT_ARENA_SENSITIVITY_END",flush=True)


if __name__=="__main__":
    main()
