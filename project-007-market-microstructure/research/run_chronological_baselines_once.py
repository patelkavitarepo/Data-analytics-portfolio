"""D009 one-shot 20-train/5-validation historical classification baselines.

Prerequisite: commit the D009 timestamp-only source split manifest FIRST.
Ten prospective final held-out dates are NEVER analyzed or used to choose
the models. The whole Parquet member is downloaded for SHA256 provenance;
within Parquet, a decoded batch may overlap the validation boundary, but
only rows from explicitly allowed TRAIN/VALIDATION dates enter computations.
Noncommercial CC BY-NC 4.0; no raw quotes, predictions or rows in output.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from microstructure.quant_arena_pilot import (
    convert_quote_rows, file_sha256, PilotError, REQUIRED_FIELDS
)
from microstructure.chronological_baselines import (
    make_examples, choose_training_majority, summarize_validation,
)
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_MEMBERS, FROZEN_SHA256, FROZEN_DAYS
)
from run_quant_arena_panel_once import (
    ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
)
from freeze_chronological_dates_once import (
    dated_inventory, select_dates, canonical_manifest_hash
)

MANIFEST_PATH = Path(__file__).with_name("CHRONOLOGICAL_SPLIT_MANIFEST.json")
MINIMUM_DATA_DAYS = 35
BATCH_ROWS = 128


def load_manifest(path=MANIFEST_PATH):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("status") != "D009_METADATA_ONLY_SPLIT_PROPOSED_FOR_FREEZE":
        raise ValueError("must first commit authenticated D009 date-only manifest")
    if raw.get("publisher_revision") != EXPECTED_REVISION:
        raise ValueError("source version differs from frozen receipt")
    if tuple(raw.get("selected_members", ())) != FROZEN_MEMBERS:
        raise ValueError("source stock set differs from frozen receipt")
    dates = raw["dates"]
    if tuple(dates.get("discovery", ())) != FROZEN_DAYS:
        raise ValueError("source discovery dates differ")
    if any(len(dates.get(key,())) != n
           for key,n in (("train",20),("validation",5),("holdout",10))):
        raise ValueError("invalid chronological split lengths")
    all_dates = sum((dates[key] for key in ("discovery","train","validation","holdout")),[])
    if all_dates != sorted(all_dates) or len(set(all_dates)) != 40:
        raise ValueError("dates not strictly increasing/disjoint")
    digest = canonical_manifest_hash(
        [s.removesuffix(".parquet") for s in FROZEN_MEMBERS], dates
    )
    if digest != raw.get("date_list_sha256"):
        raise ValueError("date-list checksum does not match committed manifest")
    if raw.get("source_prices_or_flags_accessed") is not False or raw.get("holdout_sealed") is not True:
        raise ValueError("metadata source receipt lacks sealed holdout assertions")
    return raw


def read_train_validation_rows(path, symbol, dates, expected_counts):
    """Stop at first post-validation date. No future market row admitted.

    A batch may physically decompress rows after val end (at most the batch
    overhang); all such rows are discarded without conversion to source
    examples/features/labels. We never deliberately decode later batches.
    """
    import pyarrow.parquet as pq
    allowed = set(dates["train"] + dates["validation"])
    last_validation = dates["validation"][-1]
    date_rows = {day: [] for day in dates["train"] + dates["validation"]}
    source = pq.ParquetFile(path)
    if any(col not in source.schema_arrow.names for col in REQUIRED_FIELDS):
        raise PilotError("verified source Parquet missing expected columns")
    saw_later = False
    batches = 0
    for batch in source.iter_batches(batch_size=BATCH_ROWS, columns=list(REQUIRED_FIELDS)):
        batches += 1
        for record in batch.to_pylist():
            dt = record["available_at"]
            if dt is None:
                raise PilotError("null availability date before validation cutoff")
            day = dt.date().isoformat()
            if day > last_validation:
                saw_later = True
                break
            if day in allowed:
                date_rows[day].append(record)
        if saw_later:
            break
    if not saw_later:
        raise PilotError("final test boundary absent from input stream")
    quotes_train, quotes_validation = [], []
    per_date_counts = {}
    for day in dates["train"] + dates["validation"]:
        raw_rows = date_rows[day]
        if len(raw_rows) != expected_counts[day]:
            raise PilotError(f"source-day row coverage differs from timestamp-only inventory: {symbol}/{day}")
        converted, q = convert_quote_rows(raw_rows, symbol, [day])
        if len(converted) != len(raw_rows):
            raise PilotError("source date/stock conversion coverage mismatch")
        if day in dates["train"]:
            quotes_train.extend(converted)
        else:
            quotes_validation.extend(converted)
        per_date_counts[day] = len(converted)
    return tuple(quotes_train),tuple(quotes_validation),{
        "train_source_rows":len(quotes_train),
        "validation_source_rows":len(quotes_validation),
        "selected_day_counts":per_date_counts,
        "parquet_batches_decoded_until_test_boundary":batches,
        "later_row_admitted_to_feature_or_label_computation":False,
        "batch_boundary_caveat":"A decoded Parquet batch may physically contain post-validation rows; rows outside train/validation dates are not converted or used.",
    }


def main():
    manifest = load_manifest()
    dates = manifest["dates"]
    fetch = HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog, sums = _checked_source(fetch)
    inventory = {}
    all_train,all_validation = [],[]
    qc = {}
    with tempfile.TemporaryDirectory(prefix="qa-d009-only-train-validation-") as folder:
        for filename in FROZEN_MEMBERS:
            member = catalog.get(ROOT+filename)
            if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
                raise RangeSourceError("verified selected stock member missing/oversized")
            if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
                raise RangeSourceError("publisher member bytes would exceed predefined download budget")
            expected = checksum_from_sha256sums(sums, ROOT+filename)
            if expected != FROZEN_SHA256[filename]:
                raise RangeSourceError("publisher member SHA256 changed from prior audit")
            content = download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(content).hexdigest() != expected:
                raise RangeSourceError("publisher Parquet member SHA256 does not match original")
            path=Path(folder)/filename
            path.write_bytes(content)
            del content
            stock=filename.removesuffix(".parquet")
            count, all_count = dated_inventory(path)
            if manifest["source_provenance"][stock]["metadata_rows"] != all_count:
                raise PilotError("metadata row count differs from locked manifest")
            if count != {} and len(count) != manifest["source_provenance"][stock]["distinct_observed_dates"]:
                raise PilotError("source date inventory differs from frozen receipt")
            for day, n in manifest["source_date_counts_for_selected_days"][stock].items():
                if count.get(day) != n:
                    raise PilotError("selected date population differs from frozen source")
            inventory[stock]=count
            train,validation, source_stats=read_train_validation_rows(
                path,stock,dates,manifest["source_date_counts_for_selected_days"][stock]
            )
            train_ex=make_examples(train)
            val_ex=make_examples(validation)
            all_train.extend(train_ex)
            all_validation.extend(val_ex)
            qc[stock]={
                "source_sha256":expected,
                "file_bytes":member.size,
                "train_validation_reader":source_stats,
                "train_label_valid":sum(x.target is not None for x in train_ex),
                "val_label_valid":sum(x.target is not None for x in val_ex),
                "train_B1_predicted_at_eligible_origins":sum(
                    x.target is not None and x.b1_prediction is not None for x in train_ex
                ),
            }
            if file_sha256(path) != expected:
                raise RangeSourceError("publisher file mutated during evaluation")
            path.unlink()
            print("D009_BENCHMARK_STOCK_FINISHED:",stock, flush=True)
    expected_dates,_ = select_dates(inventory)
    if expected_dates != dates:
        raise AssertionError("manifest date selection differs from authenticated file inventories")
    majority,train_classes = choose_training_majority(all_train)
    result=summarize_validation(all_validation,majority)
    report={
        "status":"D009_train_only_baselines_validated_sealed_final_test",
        "source":"Quant-Arena Public L1, Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0, noncommercial research",
        "source_revision":EXPECTED_REVISION,
        "date_manifest_sha256":manifest["date_list_sha256"],
        "source_member_sha256":FROZEN_SHA256,
        "calendar_dates":dates,
        "model_target":"average of next five valid midpoints at fixed ±0.2%, same continuous session",
        "model_features":"B1 origin midpoint relative to mean five contiguous previous midpoints",
        "continuous_phases":"09:30–11:30 inclusive; 13:00–14:57 exclusive; closing call auction excluded",
        "maximum_quote_gap_seconds":30,
        "B0_frozen_tie_priority":[2,1,3],
        "B0_trained_majority":majority,
        "B0_training_label_counts":train_classes,
        "training_source_origins":len(all_train),
        "training_label_eligible":sum(x.target is not None for x in all_train),
        "validation_metrics":result,
        "source_quality":qc,
        "provider_bytes_transferred":fetch.bytes_transferred,
        "entire_archive_downloaded_or_hashed":False,
        "raw_market_rows_committed":False,
        "final_10_date_price_or_label_used_for_training_or_scoring":False,
        "final_holdout_sealed":True,
        "physical_download_caveat":"Whole stock Parquet member bytes are necessarily fetched for SHA256; only train/validation date rows are admitted to model calculations. Iterator batches could physically decompress some holdout rows at split boundary, which are immediately discarded.",
        "no_fi2010_holdout_read":True,
        "not_a_trading_backtest":True,
        "limitations":[
            "This tests three-class label prediction, not executable spreads, queue fills, fees or profitable trading.",
            "B1 is an unfitted fixed backward-looking heuristic, not learned feature-based order-book model.",
            "15-second historical Shenzhen quotes are sampled data with potential missing and stale observations.",
            "Overlap among 5-forward-quote target windows makes IID p-values inappropriate.",
            "A class imbalance can make accuracy high without capturing minority up/down cases.",
            "The 14:57–15:00 closing auction excluded by predeclared future prediction population.",
            "Any post-hoc refinement requires a separate validation protocol; final 10 dates remain sealed.",
            "Shenzhen source cannot validate FI-2010 original Helsinki 2010 publisher labels.",
        ],
    }
    print("QUANT_ARENA_D009_BASELINES_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("QUANT_ARENA_D009_BASELINES_END",flush=True)


if __name__ == "__main__":
    main()
