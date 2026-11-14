"""D010 one-shot noncommercial source-verifiable training-only liquidity study.

Full SHA256-pinned Quant-Arena Public L1 Parquet members downloaded into
ephemeral CI storage (CC BY-NC 4.0). Only the original 20 TRAINING dates
are admitted as market-price and quote-feature data. Split is first 14
training dates fit and last six internal confirmation. Original five-date
validation and sealed ten-date test are NEVER scored or used to select rules.

Produces aggregate classification/coverage only; not execution profitability.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from microstructure.quant_arena_pilot import (
    convert_quote_rows, file_sha256, REQUIRED_FIELDS, PilotError
)
from microstructure.chronological_baselines import (
    make_examples, choose_training_majority, _confusion, PERMITTED
)
from microstructure.liquidity_features import (
    make_feature_rows, SOURCE_FIELDS
)
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_MEMBERS, FROZEN_SHA256
)
from run_quant_arena_panel_once import (
    ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
)
from freeze_chronological_dates_once import (
    dated_inventory, select_dates
)
from run_chronological_baselines_once import load_manifest

FIT_DAYS = 14
CONFIRM_DAYS = 6
BATCH_ROWS = 128


def read_training_only(path, stock, train_dates, source_count):
    """Decompress source in batches; materialize ONLY first 20 training days.

    Source Parquet record batches may physically decompress future values on
    an overhanging batch; only exchange-local availability timestamps are
    examined for the boundary and only selected TRAIN slices are converted
    to Python pricing/volume objects. No later source batch is requested.
    """
    import pyarrow.parquet as pq
    source = pq.ParquetFile(path)
    fields = tuple(dict.fromkeys(REQUIRED_FIELDS + SOURCE_FIELDS))
    if any(field not in source.schema_arrow.names for field in fields):
        raise PilotError("published source lacks mandatory level 1–5 price/volume columns")
    if len(train_dates) != 20 or tuple(train_dates) != tuple(sorted(train_dates)):
        raise PilotError("expected exactly 20 distinct chronological training dates")
    first, last = train_dates[0], train_dates[-1]
    allowed = set(train_dates)
    gathered = {day: [] for day in train_dates}
    batches_decoded = 0
    saw_later = False
    for batch in source.iter_batches(batch_size=BATCH_ROWS, columns=list(fields)):
        batches_decoded += 1
        timestamps = batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        days = []
        for dt in timestamps:
            if dt is None:
                raise PilotError("null source availability timestamp")
            days.append(dt.date().isoformat())
        if any(days[i] > days[i+1] for i in range(len(days)-1)):
            raise PilotError("source batch dates are not chronological")
        selected_idx = [i for i, day in enumerate(days) if day in allowed]
        if selected_idx:
            if selected_idx != list(range(selected_idx[0], selected_idx[-1]+1)):
                raise PilotError("source training dates are not contiguous in a batch")
            first_idx, end_idx = selected_idx[0], selected_idx[-1]+1
            for row in batch.slice(first_idx, end_idx-first_idx).to_pylist():
                day = row["available_at"].date().isoformat()
                if day not in allowed:
                    raise PilotError("nontraining source quote reached feature admission")
                gathered[day].append(row)
        if any(day > last for day in days):
            saw_later = True
            break
    if not saw_later:
        raise PilotError("no later-date boundary encountered")
    for day in train_dates:
        if len(gathered[day]) != source_count[day]:
            raise PilotError(f"training-only source row count differs for {stock} on {day}")

    fit_raw = [row for day in train_dates[:FIT_DAYS] for row in gathered[day]]
    confirmation_raw = [row for day in train_dates[FIT_DAYS:] for row in gathered[day]]
    fit_quote = []
    confirmation_quote = []
    for i, day in enumerate(train_dates):
        converted, audit = convert_quote_rows(gathered[day], stock, [day])
        if len(converted) != source_count[day]:
            raise PilotError("unaccounted source quote in per-day conversion")
        if i < FIT_DAYS:
            fit_quote.extend(converted)
        else:
            confirmation_quote.extend(converted)
    fit_features, fit_counts = make_feature_rows(fit_raw, stock, train_dates[:FIT_DAYS])
    confirm_features, confirm_counts = make_feature_rows(
        confirmation_raw, stock, train_dates[FIT_DAYS:]
    )
    return ((tuple(fit_quote), fit_features),
            (tuple(confirmation_quote), confirm_features),
            {
                "source_fit_rows": len(fit_quote),
                "source_internal_confirmation_rows":len(confirmation_quote),
                "fit_depth_coverage": fit_counts,
                "confirmation_depth_coverage": confirm_counts,
                "parquet_batches_read_until_fit_date_end": batches_decoded,
                "later_date_source_rows_admitted": False,
                "physical_data_caveat":"Whole member verified by SHA256. An Arrow batch may decode beyond training date boundary; no later market rows were converted to features, targets or predictor scores."
            })


def _training_records(quotes, features):
    examples = make_examples(quotes)
    if len(features) != len(examples):
        raise AssertionError("quote-index/feature-index source alignment mismatch")
    return tuple(zip(examples, features))


def _selected_common(rows):
    return tuple((e, features) for e, features in rows
                 if e.target in PERMITTED
                 and e.b1_prediction in PERMITTED
                 and features is not None)


def _prediction_map(records, predictions):
    if len(records) != len(predictions):
        raise AssertionError("prediction shape differs from matched coverage")
    mapping={}
    for (e,_),p in zip(records,predictions):
        key=(e.symbol,e.trading_date,e.row_index)
        if key in mapping or int(p) not in PERMITTED:
            raise AssertionError("invalid or duplicate source-origin prediction key")
        mapping[key]=int(p)
    return mapping


def _metric_pair(matched, majority, predictions):
    examples=[e for e,_ in matched]
    b2=_prediction_map(matched,predictions)
    return {
        "B0_majority":_confusion(examples,lambda _:majority),
        "B1_backward_trend":_confusion(examples,lambda e:e.b1_prediction),
        "B2_book_snapshot":_confusion(
            examples,lambda e:b2[(e.symbol,e.trading_date,e.row_index)]
        )
    }


def main():
    import sklearn
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    manifest=load_manifest()
    dates=manifest["dates"]
    train_days=dates["train"]
    if len(train_days)!=20 or set(train_days)&set(dates["validation"]+dates["holdout"]):
        raise AssertionError("frozen training/validation/test partitions overlap")
    fit_days=train_days[:FIT_DAYS]
    confirm_days=train_days[FIT_DAYS:]

    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    source_calendar={}
    fit_records=[]
    confirmation_records=[]
    stock_quality={}
    with tempfile.TemporaryDirectory(prefix="qa-d010-training-only-book-") as tmp:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
                raise RangeSourceError("frozen stock member absent/oversized")
            if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
                raise RangeSourceError("selective publisher access would exceed source budget")
            expected=checksum_from_sha256sums(sums,ROOT+filename)
            if expected != FROZEN_SHA256[filename]:
                raise RangeSourceError("publisher selected stock member SHA256 changed")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest() != expected:
                raise RangeSourceError("selected stock data fail publisher checksum")
            local=Path(tmp)/filename
            local.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            counts,total=dated_inventory(local)
            source_calendar[stock]=counts
            if total != manifest["source_provenance"][stock]["metadata_rows"]:
                raise PilotError("stock total metadata changed from frozen date manifest")
            for day,rows in manifest["source_date_counts_for_selected_days"][stock].items():
                if counts.get(day)!=rows:
                    raise PilotError("source-date population no longer matches frozen receipt")
            (fit,confirm,info)=read_training_only(
                local,stock,train_days,
                manifest["source_date_counts_for_selected_days"][stock]
            )
            f=_training_records(*fit)
            c=_training_records(*confirm)
            fit_records.extend(f)
            confirmation_records.extend(c)
            stock_quality[stock]={
                "sha256":expected,
                "full_stock_file_bytes":member.size,
                "source":info,
                "fit_targets_eligible":sum(e.target in PERMITTED for e,_ in f),
                "fit_targets_with_complete_book":sum(
                    e.target in PERMITTED and x is not None for e,x in f
                ),
                "confirmation_targets_eligible":sum(e.target in PERMITTED for e,_ in c),
                "confirmation_targets_with_complete_book":sum(
                    e.target in PERMITTED and x is not None for e,x in c
                ),
            }
            if file_sha256(local)!=expected:
                raise RangeSourceError("authenticated source member changed during run")
            local.unlink()
            print("D010_BOOK_SOURCE_VERIFIED:",stock,flush=True)
    selected,_=select_dates(source_calendar)
    if selected != dates:
        raise AssertionError("source dates differ from preregistered 20/5/10 split")
    fit_examples=[e for e,_ in fit_records]
    majority, fit_target_support=choose_training_majority(fit_examples)
    train_set=[(e,f) for e,f in fit_records if e.target in PERMITTED and f is not None]
    matched=_selected_common(confirmation_records)
    if not train_set or not matched:
        raise AssertionError("book feature train/internal-confirmation coverage is empty")
    labels=[e.target for e,_ in train_set]
    if set(labels)!=set(PERMITTED):
        raise AssertionError("train-only book model lacks registered three-class support")
    pipeline=Pipeline([
        ("scale",StandardScaler()),
        ("book_logit",LogisticRegression(
            C=1.0,class_weight="balanced",solver="lbfgs",
            max_iter=400,random_state=7007,multi_class="multinomial"
        ))
    ])
    pipeline.fit([f for _,f in train_set],labels)
    if not pipeline.named_steps["book_logit"].n_iter_.size or max(
        pipeline.named_steps["book_logit"].n_iter_
    )>=400:
        raise AssertionError("frozen logistic regression failed convergence gate")
    predicted=pipeline.predict([f for _,f in matched])
    metrics=_metric_pair(matched,majority,predicted)
    stock_metrics={}
    date_metrics={}
    pred_map=_prediction_map(matched,predicted)
    for stock in sorted({e.symbol for e,_ in confirmation_records}):
        stock_rows=[pair for pair in matched if pair[0].symbol==stock]
        predictions=[pred_map[(e.symbol,e.trading_date,e.row_index)] for e,_ in stock_rows]
        stock_metrics[stock]=_metric_pair(stock_rows,majority,predictions)
        for day in confirm_days:
            day_rows=[pair for pair in stock_rows if pair[0].trading_date==day]
            preds=[pred_map[(e.symbol,e.trading_date,e.row_index)] for e,_ in day_rows]
            date_metrics[stock+"@"+day]=_metric_pair(day_rows,majority,preds)
    count_confirm=Counter({
        "all_source_origins":len(confirmation_records),
        "future_label_eligible":sum(e.target in PERMITTED for e,_ in confirmation_records),
        "feature_depth_accepted_eligible":sum(
            e.target in PERMITTED and x is not None for e,x in confirmation_records
        ),
        "B1_past_history_covered_eligible":sum(
            e.target in PERMITTED and e.b1_prediction in PERMITTED
            for e,_ in confirmation_records
        ),
        "matched_B0_B1_B2":len(matched),
    })
    exclusion=Counter(
        e.exclusion for e,_ in confirmation_records if e.target is None
    )
    report={
        "status":"D010_training_only_book_liquidity_internal_confirmation_no_holdout",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 (noncommercial)",
        "revision":EXPECTED_REVISION,
        "date_manifest_sha256":manifest["date_list_sha256"],
        "source_member_sha256":FROZEN_SHA256,
        "fit_dates":fit_days,
        "internal_confirmation_dates":confirm_days,
        "prior_original_validation_dates_UNOPENED":dates["validation"],
        "sealed_final_dates_UNOPENED":dates["holdout"],
        "model_and_feature_choices_frozen_pre_read":True,
        "model":"StandardScaler + LogisticRegression(C=1,balanced,lbfgs,400 iterations,multinomial)",
        "scikit_learn_version":sklearn.__version__,
        "features":["spread_bps_clip100","top1_bid_ask_volume_imbalance","five_level_bid_ask_volume_imbalance"],
        "feature_source_limitation":"15s snapshot depth is not exchange-level order flow or event/message volume.",
        "training_fit_source_rows":len(fit_records),
        "training_fit_label_eligible":sum(e.target in PERMITTED for e,_ in fit_records),
        "training_fit_complete_depth_label_eligible":len(train_set),
        "training_fit_class_counts":fit_target_support,
        "training_only_majority":majority,
        "training_model_iterations":[int(x) for x in pipeline.named_steps["book_logit"].n_iter_],
        "training_feature_scale_fitted_on_train_only":True,
        "confirmation_coverage":dict(count_confirm),
        "confirmation_exclusion_reason_counts":dict(sorted(exclusion.items())),
        "metrics_on_identical_matched_rows":metrics,
        "metrics_on_identical_matched_rows_by_stock":stock_metrics,
        "metrics_on_identical_matched_rows_by_stock_date":date_metrics,
        "per_stock_source_quality":stock_quality,
        "source_bytes_transferred":fetch.bytes_transferred,
        "full_archive_downloaded":False,
        "raw_quotes_committed_or_uploaded":False,
        "original_five_day_validation_prices_used":False,
        "final_holdout_prices_or_labels_admitted":False,
        "note_about_storage":"Whole member downloaded for publisher SHA256; a Parquet record batch could physically decompress beyond fit-date boundary, but later rows are never converted to features, labels or predictions.",
        "no_execution_or_trading_claim":True,
        "limitations":[
            "Confirmation is a single internal split of previously allocated TRAINING dates, not a new untouched external validation.",
            "Overlapping next-five labels and same-stock/day dependence invalidate naive IID significance.",
            "Class-weighted logistic model may trade false directional alerts for minority recall.",
            "Source snapshot depth does not reveal individual order messages, true flow, queue fills or transaction costs.",
            "The earlier five validation dates and ten sealed final dates remain closed to this D010 iteration.",
            "No claim of stock forecasting generalization, profitability, modern market execution or original FI-2010 Helsinki label fidelity.",
        ],
    }
    print("QUANT_ARENA_D010_LIQUIDITY_BEGIN",flush=True)
    print(json.dumps(report,sort_keys=True,indent=2),flush=True)
    print("QUANT_ARENA_D010_LIQUIDITY_END",flush=True)


if __name__=="__main__":
    main()
