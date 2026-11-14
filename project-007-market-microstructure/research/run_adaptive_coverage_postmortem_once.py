"""D014 source-only current/past coverage postmortem after fail-closed run.

NO FUTURE TARGETS for warmup or confirmation; NO model, score, threshold,
trading or final-date features. Aggregates only. Quant-Arena Public L1
CC BY-NC 4.0 noncommercial with attribution, immutable publisher member SHA.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from microstructure.chronological_baselines import continuous_phase
from microstructure.liquidity_features import make_feature_rows, SOURCE_FIELDS
from microstructure.quant_arena_pilot import convert_quote_rows, REQUIRED_FIELDS, PilotError, file_sha256
from microstructure.selective_alerts import source_past5_coverage
from microstructure.adaptive_alerts import STOCKS, validate_calendar
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from run_quote_quality_sensitivity_once import _checked_source,FROZEN_MEMBERS,FROZEN_SHA256
from run_quant_arena_panel_once import ROOT,EXPECTED_REVISION,MAX_STOCK_BYTES,MAX_REMOTE_BYTES
from freeze_chronological_dates_once import dated_inventory
from freeze_adaptive_dates_once import load_manifest,select_dates

BATCH_ROWS=128
EXPECTED_DATE_SHA256="953b173e4b0ba4b6968ce6113e8345c85e942dbe6b46b31ca722968a98f208c8"


def _read_30_only(path,stock,dates,expected_day_counts):
    """Filter by authenticated timestamp before any raw row/feature conversion."""
    allowed=list(dates["warmup"])+list(dates["confirmation"])
    if (len(allowed)!=30 or allowed!=sorted(set(allowed))
            or allowed[0]<="2022-05-16"
            or allowed[-1]>=dates["sealed_final"][0]
            or set(allowed)&set(dates["sealed_final"])):
        raise PilotError("D014 coverage audit restricted to nonfinal new dates")
    import pyarrow.parquet as pq
    source=pq.ParquetFile(path)
    fields=tuple(dict.fromkeys(REQUIRED_FIELDS+SOURCE_FIELDS))
    if any(name not in source.schema_arrow.names for name in fields):
        raise PilotError("required source snapshot schema differs")
    by_day={d:[] for d in allowed}
    saw_final_boundary=False
    for batch in source.iter_batches(batch_size=BATCH_ROWS,columns=list(fields)):
        ts=batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        days=[v.date().isoformat() if v is not None else None for v in ts]
        if None in days or any(days[i]>days[i+1] for i in range(len(days)-1)):
            raise PilotError("source quote date order changed")
        indexes=[i for i,d in enumerate(days) if d in by_day]
        if indexes:
            left,right=indexes[0],indexes[-1]+1
            if indexes!=list(range(left,right)):
                raise PilotError("approved price rows not contiguous inside batch")
            for raw in batch.slice(left,right-left).to_pylist():
                d=raw["available_at"].date().isoformat()
                if d not in by_day:
                    raise AssertionError("unapproved source price row converted")
                by_day[d].append(raw)
        if any(d>allowed[-1] for d in days):
            saw_final_boundary=True
            break
    if not saw_final_boundary:
        raise PilotError("final boundary was never reached")
    if any(len(by_day[d])!=expected_day_counts[d] for d in allowed):
        raise PilotError("source date-row count mismatch")

    aggregate={}
    for d in allowed:
        source_rows=by_day[d]
        quotes,qc=convert_quote_rows(source_rows,stock,[d])
        books,book_qc=make_feature_rows(source_rows,stock,[d])
        past=source_past5_coverage(quotes) # NO FUTURE LABELS, either part
        if not len(books)==len(past)==len(source_rows):
            raise AssertionError("source row alignment lost")
        session={}
        for phase in ("morning","afternoon"):
            sub=[i for i,row in enumerate(source_rows)
                 if continuous_phase(row["available_at"])==phase]
            session[phase]={
                "source_rows":len(sub),
                "complete_book":sum(books[i] is not None for i in sub),
                "past_five_covered":sum(past[i] for i in sub),
                "decision_ready":sum(past[i] and books[i] is not None for i in sub),
            }
        count={
            "source_rows":len(source_rows),
            "valid_current_five_level_snapshot":sum(b is not None for b in books),
            "source_quote_has_five_past_valid":sum(past),
            "decision_ready_intersection":sum(past[i] and books[i] is not None
                                               for i in range(len(books))),
            "stale_flag_not_healthy":sum(row["stale"] is not False for row in source_rows),
            "missing_depth_flag_not_healthy":sum(
                row["missing_depth"] is not False for row in source_rows),
            "missing_source_event_time":sum(
                row["source_event_time"] is None for row in source_rows),
            "sessions":session,
        }
        if count["decision_ready_intersection"]>count["valid_current_five_level_snapshot"]:
            raise AssertionError("current/past eligibility arithmetic corrupted")
        aggregate[d]=count
    return aggregate


def main():
    receipt=load_manifest()
    if receipt["date_list_sha256"]!=EXPECTED_DATE_SHA256:
        raise ValueError("frozen metadata-only D014 date SHA changed")
    dates=receipt["dates"]
    validate_calendar(dates["warmup"],dates["confirmation"],dates["sealed_final"])
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    inventories={}
    by_stock={}
    with tempfile.TemporaryDirectory(prefix="qa-D014-coverage-only-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("pinned source member missing or oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("source byte limit violated")
            digest=checksum_from_sha256sums(sums,ROOT+filename)
            if digest!=FROZEN_SHA256[filename] or digest!=receipt["member_sha256"][filename]:
                raise RangeSourceError("publisher original stock digest changed")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=digest:
                raise RangeSourceError("publisher stock SHA256 failed")
            local=Path(td)/filename
            local.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            inventory,total=dated_inventory(local)
            inventories[stock]=inventory
            if total!=receipt["source_provenance"][stock]["source_rows"]:
                raise PilotError("timestamp source population changed")
            for d,n in receipt["source_counts_by_date"][stock].items():
                if inventory.get(d)!=n:
                    raise PilotError("pre-price selected day count changed")
            by_stock[stock]=_read_30_only(
                local,stock,dates,receipt["source_counts_by_date"][stock])
            if file_sha256(local)!=digest:
                raise RangeSourceError("source file modified while auditing")
            local.unlink()
            print("D014_COVERAGE_SOURCE_SHA256_OK",stock,flush=True)
    recreated,_=select_dates(inventories)
    if recreated!=dates:
        raise AssertionError("frozen post-D012 common date calendar differs")
    source_zeros=[{"stock":s,"day":d,"part":("warmup" if d in dates["warmup"]
                  else "confirmation"),"counts":by_stock[s][d]}
                  for s in STOCKS for d in dates["warmup"]+dates["confirmation"]
                  if by_stock[s][d]["decision_ready_intersection"]==0]
    report={
        "status":"D014_FAIL_CLOSED_SOURCE_COVERAGE_DIAGNOSTIC_NOT_ALERT_EVALUATION",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 noncommercial with attribution",
        "publisher_revision":EXPECTED_REVISION,
        "original_stock_member_sha256":FROZEN_SHA256,
        "D014_frozen_date_sha256":receipt["date_list_sha256"],
        "source_coverage_by_stock_day":by_stock,
        "zero_decision_ready_stock_days":source_zeros,
        "zero_decision_ready_stock_days_count":len(source_zeros),
        "warmup_future_target_labels_computed":False,
        "confirmation_future_target_labels_computed":False,
        "models_fit_or_scored":False,
        "cutoff_reestimated_or_selected":False,
        "D009_earlier_final_scored":False,
        "D012_previous_final_scored":False,
        "D014_new_final_scored":False,
        "new_final_quote_rows_admitted":False,
        "raw_vendor_quotes_or_row_predictions_committed":False,
        "full_source_archive_downloaded":False,
        "source_bytes_transferred":fetch.bytes_transferred,
        "scope":"current/past input eligibility only; no labels, scores, model or profit"
    }
    print("D014_SOURCE_COVERAGE_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("D014_SOURCE_COVERAGE_END",flush=True)


if __name__=="__main__":
    main()
