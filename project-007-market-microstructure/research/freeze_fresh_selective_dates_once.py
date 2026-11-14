"""D012 source-date-only fresh chronological cohort freeze.

Reads ONLY the timestamp column from original 3 SHA256 authenticated
Quant-Arena Public L1 Parquet members (CC BY-NC 4.0 noncommercial).
DO NOT access D012 prices, depth, quality flags, labels or scores here.
The legacy D009 February-March holdout stays unscored and never becomes
a valid chronological test of a model trained after March 7, 2022.
"""
import json
from hashlib import sha256
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from run_quote_quality_sensitivity_once import _checked_source, FROZEN_MEMBERS, FROZEN_SHA256
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
from freeze_chronological_dates_once import dated_inventory
from run_chronological_baselines_once import load_manifest

AFTER_LEGACY_TEST = "2022-03-07"
STUDY_PARTS = (("fit",20),("calibration",10),("confirmation",5),("sealed_final",10))
MANIFEST_PATH = Path(__file__).with_name("FRESH_SELECTIVE_DATE_MANIFEST.json")


def fresh_selection(inventories):
    expected={s.removesuffix(".parquet") for s in FROZEN_MEMBERS}
    if set(inventories)!=expected:
        raise ValueError("source stock inventory differs from fixed three-stock panel")
    shared=sorted(set.intersection(*(set(c) for c in inventories.values())))
    later=[day for day in shared if day > AFTER_LEGACY_TEST]
    if len(later)<45:
        raise ValueError("at least 45 source-common post-March7 dates required")
    picked=later[:45]
    selections={}
    offset=0
    for label,n in STUDY_PARTS:
        selections[label]=picked[offset:offset+n]
        offset+=n
    if (offset!=45 or picked != sorted(set(picked))
            or any(day<=AFTER_LEGACY_TEST for day in picked)):
        raise ValueError("fresh post-legacy chronology collision")
    return selections, {"common_source_dates":len(shared),"post_legacy_common_source_dates":len(later)}


def fresh_sha(stocks,dates):
    if set(dates)!={k for k,n in STUDY_PARTS}:
        raise ValueError("fresh date manifest has wrong partition names")
    raw={"stocks":list(stocks)}
    for key,n in STUDY_PARTS:
        if len(dates[key])!=n:
            raise ValueError("fresh date manifest has changed partition sizes")
        raw[key]=list(dates[key])
    canonical=json.dumps(raw,sort_keys=True,separators=(",",":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def load_fresh_manifest(path=MANIFEST_PATH):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    original=load_manifest()
    if payload.get("status")!="D012_TIMESTAMP_ONLY_COHORT_FROZEN":
        raise ValueError("missing previously committed D012 metadata-only cohort")
    if payload.get("publisher_revision")!=EXPECTED_REVISION:
        raise ValueError("D012 publisher revision differs")
    if payload.get("legacy_manifest_sha256")!=original["date_list_sha256"]:
        raise ValueError("legacy manifest changed")
    if tuple(payload.get("selected_members",()))!=FROZEN_MEMBERS:
        raise ValueError("D012 source member identity changed")
    if payload.get("source_prices_flags_labels_accessed") is not False:
        raise ValueError("D012 metadata-only source privacy guarantee failed")
    if payload.get("new_final_sealed") is not True or payload.get("old_final_sealed") is not True:
        raise ValueError("D012 or legacy final test has been released")
    chosen=payload.get("dates",{})
    all_dates=sum((chosen[k] for k,n in STUDY_PARTS),[])
    if (len(all_dates)!=45 or len(set(all_dates))!=45
            or all_dates!=sorted(all_dates) or all_dates[0]<=AFTER_LEGACY_TEST):
        raise ValueError("D012 cohort does not have strictly post-legacy chronology")
    checksum=fresh_sha([s.removesuffix(".parquet") for s in FROZEN_MEMBERS],chosen)
    if checksum!=payload.get("cohort_date_sha256"):
        raise ValueError("fresh cohort manifest checksum differs")
    return payload


def main():
    old=load_manifest()
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    inventories={}
    provenance={}
    with tempfile.TemporaryDirectory(prefix="qa-newcohort-date-only-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("stock member not in original bounded source")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("exceeded source byte budget")
            original_hash=checksum_from_sha256sums(sums,ROOT+filename)
            if original_hash!=FROZEN_SHA256[filename]:
                raise RangeSourceError("source publisher checksum differs")
            content=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(content).hexdigest()!=original_hash:
                raise RangeSourceError("source member verification failed")
            local=Path(td)/filename
            local.write_bytes(content)
            del content
            stock=filename.removesuffix(".parquet")
            counts,total=dated_inventory(local)
            if total!=old["source_provenance"][stock]["metadata_rows"]:
                raise ValueError("source rows no longer match original date-only manifest")
            if len(counts)!=old["source_provenance"][stock]["distinct_observed_dates"]:
                raise ValueError("source date count changed")
            inventories[stock]=counts
            provenance[stock]={
                "sha256":original_hash,"source_rows":total,
                "distinct_dates":len(counts)
            }
            local.unlink()
            print("D012_METADATA_STOCK_AUTHENTICATED:",stock,flush=True)
    dates,calendar=fresh_selection(inventories)
    selected=sum((dates[name] for name,n in STUDY_PARTS),[])
    chosen_hash=fresh_sha([x.removesuffix(".parquet") for x in FROZEN_MEMBERS],dates)
    receipt={
        "status":"D012_TIMESTAMP_ONLY_COHORT_FROZEN",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "license":"CC BY-NC 4.0 noncommercial with attribution",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "publisher_revision":EXPECTED_REVISION,
        "selected_members":list(FROZEN_MEMBERS),
        "stock_source_provenance":provenance,
        "legacy_manifest_sha256":old["date_list_sha256"],
        "old_legacy_test_end":AFTER_LEGACY_TEST,
        "old_final_sealed":True,
        "new_final_sealed":True,
        "source_prices_flags_labels_accessed":False,
        "dates":dates,
        "cohort_date_sha256":chosen_hash,
        "canonical_rule":"sha256(utf8 json sort_keys=True,separators=(',',':') of {stocks,fit,calibration,confirmation,sealed_final})",
        "source_counts_by_selected_date":{
            sym:{d:counts[d] for d in selected}
            for sym,counts in inventories.items()
        },
        "calendar":calendar,
        "source_bytes_fetched":fetch.bytes_transferred,
        "whole_archive_downloaded":False,
        "note":"Complete three member Parquet blobs downloaded for SHA256; only available_at timestamp columns opened. No D012 price/volume/flag/target columns accessed.",
        "no_model_fitted_or_validation_scored":True
    }
    print("D012_FRESH_DATE_MANIFEST_BEGIN",flush=True)
    print(json.dumps(receipt,indent=2,sort_keys=True),flush=True)
    print("D012_FRESH_DATE_MANIFEST_END",flush=True)


if __name__=="__main__":
    main()
