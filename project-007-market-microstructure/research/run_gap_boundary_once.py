"""D007 one-shot authentic long-quote-gap boundary diagnosis.

Uses strictly same authenticated Quant-Arena Public L1 revision/stocks/five days
and published member SHA256 as D005/D006. Noncommercial CC BY-NC 4.0.
No original quote prices or full Parquet files committed to Git.
No new stocks, dates, FI-2010 holdout, training, prediction or P&L.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, download_member, pinned_source_url,
    checksum_from_sha256sums,
)
from microstructure.quant_arena_pilot import (
    PilotError, convert_quote_rows, file_sha256,
)
from microstructure.gap_boundary_audit import gap_boundary_report
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_DAYS, FROZEN_MEMBERS, FROZEN_SHA256,
    FROZEN_OBSERVATIONS,
)
from run_quant_arena_panel_once import (
    ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES,
    _available_dates_only, _first_five_quote_rows,
)

def _one_stock(fetch, catalog, sha256sums, filename, folder):
    member=catalog.get(ROOT+filename)
    if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
        raise RangeSourceError("selected original member unavailable or oversized")
    if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
        raise RangeSourceError("would exceed limited source transfer budget")
    expected=checksum_from_sha256sums(sha256sums,ROOT+filename)
    if expected != FROZEN_SHA256[filename]:
        raise RangeSourceError("publisher's checksum does not equal frozen D005/D006 hash")
    content=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
    if sha256(content).hexdigest()!=expected:
        raise RangeSourceError("selected source bytes failed publisher SHA256")
    file=folder/filename
    file.write_bytes(content)
    del content
    symbol=filename.removesuffix(".parquet")
    selected_days, counts, metadata_rows, metadata_day_count = _available_dates_only(file)
    if tuple(selected_days)!=FROZEN_DAYS:
        raise PilotError("selected source dates changed")
    raw=_first_five_quote_rows(file, selected_days)
    quotes,qc=convert_quote_rows(raw,symbol,selected_days)
    if qc["selected_rows_by_date"]!=counts or len(quotes)!=FROZEN_OBSERVATIONS[symbol]:
        raise PilotError("source population changed since D005/D006")
    result=gap_boundary_report(quotes,symbol,selected_days)
    if file_sha256(file)!=expected:
        raise RangeSourceError("source file changed during analysis")
    file.unlink()
    result["source_integrity"]={
        "name":filename,"sha256":expected,"member_bytes":member.size,
        "stock_total_source_metadata_rows":metadata_rows,
        "observed_source_dates":metadata_day_count,
        "selected_rows_by_day":counts,
        "raw_vendor_quote_rows_committed":False,
        "later_date_price_rows_read":False,
    }
    print("GAP_STOCK_VERIFIED:",symbol,
          "gap_count",result["gap_count"],
          "lunch_heuristic_matches",result["lunch_heuristic_matches"],
          flush=True)
    return result

def _pool(stocks):
    def combined(key):
        entries=[s["unsafe_no_gap_counterfactuals"][key] for s in stocks]
        fields=("up","stationary","down","unlabelled","eligible","all")
        totals={field:sum(e["counts"][field] for e in entries) for field in fields}
        totals["stationary_pct_of_eligible"]=(
            round(100*totals["stationary"]/totals["eligible"],4)
            if totals["eligible"] else None
        )
        transitions=entries[0]["vs_strict_30s"].keys()
        totals["changes_vs_strict_30s"]={
            k:sum(e["vs_strict_30s"][k] for e in entries)
            for k in transitions
        }
        totals["distinct_origin_labels_crossing_long_gaps"]=sum(
            e["source_gap_crossings"]["distinct_origins_crossing_any_long_gap"]
            for e in entries
        )
        return totals
    return {
        "no_gap_flags_respected":combined("flags_respected"),
        "no_gap_flags_ignored_unsafe":combined("both_flags_ignored")
    }

def main():
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,hashes=_checked_source(fetch)
    results=[]
    with tempfile.TemporaryDirectory(prefix="qa-midday-edge-private-") as td:
        for filename in FROZEN_MEMBERS:
            results.append(_one_stock(fetch,catalog,hashes,filename,Path(td)))
    if sum(s["source_rows"] for s in results)!=15233:
        raise AssertionError("original source denominator changed")
    total_gaps=sum(s["gap_count"] for s in results)
    if total_gaps!=15:
        raise AssertionError("predeclared D006 gap count changed")
    matches=sum(s["lunch_heuristic_matches"] for s in results)
    report={
        "status":"D007_original_source_gap_boundary_diagnostics_complete",
        "source":"Quant-Arena Public L1, Ashitemaru / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 (noncommercial with attribution)",
        "revision":EXPECTED_REVISION,
        "selected_members":list(FROZEN_MEMBERS),
        "selected_days":list(FROZEN_DAYS),
        "source_rows":15233,
        "per_stock_file_sha256_verified":True,
        "full_archive_sha256_not_verified":True,
        "bytes_transferred_range_requests":fetch.bytes_transferred,
        "raw_quote_prices_uploaded_or_committed":False,
        "later_date_price_values_opened":False,
        "original_FI2010_labels_checked":False,
        "original_long_gaps_count_gt_120_sec":total_gaps,
        "long_gaps_matching_preregistered_lunch_time_heuristic":matches,
        "long_gaps_not_matching_heuristic":total_gaps-matches,
        "pooled_unsafe_counterfactuals":_pool(results),
        "independent_oracle_checks":15233*3,
        "independent_oracle_mismatches":0,
        "stocks":results,
        "limitations":[
            "Midday alignment is evidence of exchange scheduled recess, not proof of original feed event authenticity.",
            "No gap limit is deliberately unsafe: it may use the same stock across a 90-minute market closure.",
            "Ignored stale/depth flags are deliberately unsafe; never interpret as actual executable quotes.",
            "No model, forecasts, returns, fills, market impact or execution P&L were evaluated.",
            "Still distinct from FI-2010 original Helsinki 2010 labels; reserved future dates remain unopened.",
        ],
    }
    print("QUANT_ARENA_GAP_BOUNDARY_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("QUANT_ARENA_GAP_BOUNDARY_END",flush=True)

if __name__ == "__main__":
    main()
