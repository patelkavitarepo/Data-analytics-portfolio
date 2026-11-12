"""D018 timestamp-ONLY selection, before ANY new quote or label access.

Authenticate three already pinned Quant-Arena Public L1 Parquet members and
choose first 40 common observed dates AFTER D017's sealed final January 5, 2023.
Source CC BY-NC 4.0 noncommercial with attribution. No outcome queries.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from microstructure.availability_alerts import freeze_calendar as validate_calendar
from run_quote_quality_sensitivity_once import _checked_source, FROZEN_MEMBERS, FROZEN_SHA256
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
from freeze_chronological_dates_once import dated_inventory
from freeze_replication_dates_once import load_manifest as load_previous_manifest

AFTER_SEALED_D017="2023-01-05"
PARTS=(("warmup",20),("confirmation",10),("sealed_final",10))
MANIFEST_PATH=Path(__file__).with_name("FRESH_REPLICATION_DATE_MANIFEST.json")
STOCKS=tuple(x.removesuffix(".parquet") for x in FROZEN_MEMBERS)


def select_dates(inventory):
    if set(inventory)!=set(STOCKS):
        raise ValueError("wrong immutable three-stock panel")
    common=sorted(set.intersection(*(set(inventory[s]) for s in STOCKS)))
    later=[d for d in common if d>AFTER_SEALED_D017]
    if len(later)<40:
        raise ValueError("insufficient source dates beyond sealed D017")
    picked=later[:40]
    result={}
    cursor=0
    for key,n in PARTS:
        result[key]=picked[cursor:cursor+n]
        cursor+=n
    validate_calendar(*(result[k] for k,n in PARTS))
    return result,{"all_common_dates":len(common),
                   "post_D017_sealed_common_dates":len(later)}


def checksum(dates):
    if set(dates)!={part for part,n in PARTS}:
        raise ValueError("wrong D018 parts")
    validate_calendar(*(dates[k] for k,n in PARTS))
    payload={"stocks":list(STOCKS)}
    payload.update({part:list(dates[part]) for part,n in PARTS})
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def load_manifest(path=MANIFEST_PATH):
    receipt=json.loads(Path(path).read_text(encoding="utf-8"))
    previous=load_previous_manifest()
    if receipt.get("status")!="D018_PREPRICE_TIMESTAMP_ONLY_FROZEN":
        raise ValueError("D018 manifest not yet precommitted")
    if receipt.get("publisher_revision")!=EXPECTED_REVISION:
        raise ValueError("source revision changed")
    if receipt.get("previous_D017_date_sha256")!=previous["date_list_sha256"]:
        raise ValueError("previous D017 calendar changed")
    if receipt.get("price_or_label_columns_read") is not False:
        raise ValueError("D018 source isolation violated")
    if receipt.get("prior_D009_D012_D014_D015_D016_D017_finals_sealed") is not True:
        raise ValueError("prior sealed dates not preserved")
    if receipt.get("new_final_sealed") is not True:
        raise ValueError("D018 final must be sealed")
    if tuple(receipt.get("selected_members",()))!=FROZEN_MEMBERS:
        raise ValueError("pinned source stock members changed")
    if receipt.get("date_list_sha256")!=checksum(receipt["dates"]):
        raise ValueError("D018 date manifest SHA256 differs")
    return receipt


def main():
    previous=load_previous_manifest()
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    inventories={}
    provenance={}
    with tempfile.TemporaryDirectory(prefix="qa-D018-timestamp-only-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("pinned source stock missing or oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("source transfer byte limit")
            original=checksum_from_sha256sums(sums,ROOT+filename)
            if original!=FROZEN_SHA256[filename]:
                raise RangeSourceError("published SHA256 changed from original")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=original:
                raise RangeSourceError("source member digest differs")
            file=Path(td)/filename
            file.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            counts,total=dated_inventory(file)
            if total!=previous["source_provenance"][stock]["source_rows"]:
                raise ValueError("stock row inventory differs")
            if len(counts)!=previous["source_provenance"][stock]["distinct_dates"]:
                raise ValueError("source stock observed-date inventory differs")
            inventories[stock]=counts
            provenance[stock]={"source_rows":total,"distinct_dates":len(counts),
                               "sha256":original}
            file.unlink()
            print("D018_TIMESTAMP_SOURCE_OK",stock,flush=True)
    dates,calendar=select_dates(inventories)
    chosen=[d for key,n in PARTS for d in dates[key]]
    receipt={
        "status":"D018_PREPRICE_TIMESTAMP_ONLY_FROZEN",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 noncommercial with attribution",
        "publisher_revision":EXPECTED_REVISION,
        "selected_members":list(FROZEN_MEMBERS),
        "member_sha256":FROZEN_SHA256,
        "source_provenance":provenance,
        "previous_D017_date_sha256":previous["date_list_sha256"],
        "date_rule":"first 40 common observed dates strictly after 2023-01-05; 20 warmup/10 confirmation/10 sealed final",
        "dates":dates,
        "date_list_sha256":checksum(dates),
        "source_counts_by_date":{
            s:{d:inventories[s][d] for d in chosen} for s in STOCKS
        },
        "common_date_inventory":calendar,
        "prior_D009_D012_D014_D015_D017_finals_sealed":True,
        "new_final_sealed":True,
        "price_or_label_columns_read":False,
        "source_member_bytes_authenticated":True,
        "full_archive_downloaded":False,
        "source_bytes_transferred":fetch.bytes_transferred,
        "note":"Only source timestamps were decompressed into observations, despite full stock-byte authentication. No market price/depth/source quality or target was opened."
    }
    print("D018_TIMESTAMP_MANIFEST_BEGIN",flush=True)
    print(json.dumps(receipt,indent=2,sort_keys=True),flush=True)
    print("D018_TIMESTAMP_MANIFEST_END",flush=True)


if __name__=="__main__":
    main()
