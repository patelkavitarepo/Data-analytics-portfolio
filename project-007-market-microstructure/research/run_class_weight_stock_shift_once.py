"""D011 preregistered class-weight/stock-feature-shift diagnostics, FIT DATES ONLY.

Quant-Arena Public L1 CC BY-NC 4.0 noncommercial, publisher SHA256-pinned.
NO price/feature/label/model records from D010 Feb 7-14 confirmation, original
Feb 15-21 validation, or Feb 22-Mar 7 sealed test are used or converted.

Predeclared source 14 D010 fitting dates: first 10 fit, next four diagnose.
D010's previous internal confirmation was inspected; these four dates are
NOT an independent untouched out-of-sample test. Report aggregates ONLY.
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
    download_member, pinned_source_url,
)
from microstructure.quant_arena_pilot import (
    convert_quote_rows, file_sha256, REQUIRED_FIELDS, PilotError,
)
from microstructure.liquidity_features import make_feature_rows, SOURCE_FIELDS
from microstructure.chronological_baselines import (
    choose_training_majority, make_examples, _confusion, PERMITTED,
)
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_MEMBERS, FROZEN_SHA256,
)
from run_chronological_baselines_once import load_manifest
from freeze_chronological_dates_once import dated_inventory, select_dates

FIT_DATES = 10
INTERNAL_DIAG_DATES = 4
MAX_ALLOWED_DATES = 14
BATCH_ROWS = 128
FEATURE_NAMES = (
    "spread_bps_clip100",
    "level1_bid_ask_displayed_volume_imbalance",
    "first5_bid_ask_displayed_volume_imbalance",
)
EXPECTED_MANIFEST = "50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6"


def read_first_14_dates_only(path, stock, allowed_dates, frozen_counts):
    """Return 10-fit and 4-diagnostic same-row (label, features) records.

    Arrow may physically decode a batch with a post-Jan-28 row, but only
    the timestamp column of the batch is converted before slicing. Only
    allowed first-14-day rows ever become Python quote/depth objects.
    """
    import pyarrow.parquet as pq
    if len(allowed_dates) != MAX_ALLOWED_DATES or tuple(sorted(allowed_dates)) != tuple(allowed_dates):
        raise PilotError("D011 must use fourteen chronological registered fit dates")
    approved = set(allowed_dates)
    cutoff = allowed_dates[-1]
    source = pq.ParquetFile(path)
    fields = tuple(dict.fromkeys(REQUIRED_FIELDS + SOURCE_FIELDS))
    if any(field not in source.schema_arrow.names for field in fields):
        raise PilotError("frozen publisher member lacks mandatory 5-level book columns")
    records = {day: [] for day in allowed_dates}
    batches = 0
    stopped_at_cutoff = False
    for batch in source.iter_batches(batch_size=BATCH_ROWS, columns=list(fields)):
        batches += 1
        timestamp_index = batch.schema.get_field_index("available_at")
        dates = [
            t.date().isoformat() if t is not None else None
            for t in batch.column(timestamp_index).to_pylist()
        ]
        if None in dates or any(dates[i] > dates[i + 1] for i in range(len(dates)-1)):
            raise PilotError("unexpected source date chronology or null timestamp")
        allowed_idx = [i for i, date in enumerate(dates) if date in approved]
        if allowed_idx:
            start, end = allowed_idx[0], allowed_idx[-1]+1
            if allowed_idx != list(range(start,end)):
                raise PilotError("source date subset not contiguous within Parquet batch")
            for row in batch.slice(start,end-start).to_pylist():
                day = row["available_at"].date().isoformat()
                if day not in approved:
                    raise PilotError("non-fit-period source price/feature admitted")
                records[day].append(row)
        if any(day > cutoff for day in dates):
            stopped_at_cutoff = True
            break
    if not stopped_at_cutoff:
        raise PilotError("source stream ended before confirmed later-date cutoff")
    for day in allowed_dates:
        if len(records[day]) != frozen_counts[day]:
            raise PilotError(f"frozen publisher date count differs for {stock}/{day}")

    output = []
    qc = []
    for period in (allowed_dates[:FIT_DATES], allowed_dates[FIT_DATES:]):
        quote_rows, book_rows = [], []
        for day in period:
            converted, summary = convert_quote_rows(records[day],stock,[day])
            if len(converted) != frozen_counts[day]:
                raise PilotError("source-converted quote/date count mismatch")
            quote_rows.extend(converted)
            book_rows.extend(records[day])
        book_features, depth_counts = make_feature_rows(book_rows,stock,period)
        if len(quote_rows) != len(book_features):
            raise AssertionError("D011 source label/feature index desynchronized")
        examples = make_examples(quote_rows)
        if len(examples) != len(quote_rows):
            raise AssertionError("D011 source quote/label cardinality differs")
        output.append(tuple(zip(examples,book_features)))
        qc.append({
            "source_rows":len(quote_rows),
            "depth_snapshot_quality":depth_counts,
            "future_label_eligible":sum(e.target in PERMITTED for e in examples),
            "complete_depth_and_label_eligible":sum(
                e.target in PERMITTED and v is not None for e,v in zip(examples,book_features)
            ),
            "B1_covered_eligible":sum(
                e.target in PERMITTED and e.b1_prediction in PERMITTED for e in examples
            ),
        })
    return output[0], output[1], {
        "first10_fit":qc[0],"last4_internal_diagnostic":qc[1],
        "source_batches_until_14_fit_dates_end":batches,
        "future_date_quotes_admitted":False,
        "caveat":"Publisher entire member bytes and possibly Arrow boundary batch are processed for source SHA256; no quote/feature/label objects formed after Jan 28.",
    }


def _feature_stats(rows):
    """Snapshot description on future-target-eligible records only; aggregated."""
    import numpy as np
    good = [(e,v) for e,v in rows if e.target in PERMITTED and v is not None]
    labels = Counter(e.target for e,v in good)
    if not good:
        return {
            "eligible_complete_depth":0,
            "class_counts":{str(c):0 for c in PERMITTED},
            "feature_stats":None,
        }
    x = np.asarray([v for e,v in good],dtype=float)
    if x.shape[1] != 3 or not np.isfinite(x).all():
        raise AssertionError("nonfinite or changed liquidity feature dimensions")
    per_feature={}
    for k,name in enumerate(FEATURE_NAMES):
        col=x[:,k]
        per_feature[name]={
            "mean":round(float(np.mean(col)),7),
            "p10":round(float(np.percentile(col,10)),7),
            "median":round(float(np.median(col)),7),
            "p90":round(float(np.percentile(col,90)),7),
        }
    return {
        "eligible_complete_depth":len(good),
        "class_counts":{str(c):int(labels[c]) for c in PERMITTED},
        "feature_stats":per_feature
    }


def _metrics(rows,predictor):
    if len(rows)==0:
        raise AssertionError("empty D011 stock/date comparison slice")
    examples=[e for e,v in rows]
    return _confusion(examples,lambda e:predictor[(e.symbol,e.trading_date,e.row_index)])


def _predict_map(rows,preds):
    if len(rows)!=len(preds):
        raise AssertionError("classification output count differs from eligible matched rows")
    lookup={}
    for (e,v),prediction in zip(rows,preds):
        key=(e.symbol,e.trading_date,e.row_index)
        if key in lookup or int(prediction) not in PERMITTED:
            raise AssertionError("duplicate source origin or unknown predicted class")
        lookup[key]=int(prediction)
    return lookup


def _explain_metrics(score):
    cm=score["confusion_true_rows_predicted_columns"]
    freq={str(c):sum(cm[str(t)][str(c)] for t in PERMITTED) for c in PERMITTED}
    precisions={}
    for c in (1,3):
        selected=freq[str(c)]
        precisions[str(c)]=(
            cm[str(c)][str(c)]/selected if selected else None
        )
    return {
        "predicted_class_count":freq,
        "predicted_up_down_precision":precisions,
        "stationary_prediction_rate":freq["2"]/score["n"],
        "predicted_direction_rate":(freq["1"]+freq["3"])/score["n"],
    }


def _compare_models(rows, maps):
    result={}
    for name, prediction_map in maps.items():
        metric=_metrics(rows,prediction_map)
        result[name]={"metrics":metric, "prediction_diagnostics":_explain_metrics(metric)}
    return result


def main():
    import sklearn
    import numpy as np
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    manifest=load_manifest()
    if manifest["date_list_sha256"]!=EXPECTED_MANIFEST:
        raise ValueError("published 20/5/10 source-date manifest changed")
    dates=manifest["dates"]
    only14=dates["train"][:MAX_ALLOWED_DATES]
    if len(only14)!=14 or only14[0]!="2022-01-11" or only14[-1]!="2022-01-28":
        raise ValueError("expected frozen Jan11–Jan28 source-date fitting window")
    ten=only14[:FIT_DATES]
    four=only14[FIT_DATES:]
    if set(only14)&set(dates["train"][14:]+dates["validation"]+dates["holdout"]):
        raise AssertionError("fit diagnostic dates overlap reserved blocks")

    reader=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,checksums=_checked_source(reader)
    all_fit,all_diagnostic=[],[]
    stock_qc={}
    source_calendar={}
    with tempfile.TemporaryDirectory(prefix="qa-d011-only-fit-period-") as scratch:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("original source stock member not available within cap")
            if reader.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("publisher stock request exceeds bounded byte budget")
            expected=checksum_from_sha256sums(checksums,ROOT+filename)
            if expected != FROZEN_SHA256[filename]:
                raise RangeSourceError("publisher source stock hash differs from registered source")
            binary=download_member(reader,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(binary).hexdigest()!=expected:
                raise RangeSourceError("publisher SHA256 check of selected source failed")
            local=Path(scratch)/filename
            local.write_bytes(binary)
            del binary
            stock=filename.removesuffix(".parquet")
            inventory,total=dated_inventory(local)
            source_calendar[stock]=inventory
            if total!=manifest["source_provenance"][stock]["metadata_rows"]:
                raise PilotError("source metadata size changed since date freeze")
            for date,count in manifest["source_date_counts_for_selected_days"][stock].items():
                if inventory.get(date)!=count:
                    raise PilotError("source date count changed from original manifest")
            fit,diagnostic,qc=read_first_14_dates_only(
                local,stock,only14,manifest["source_date_counts_for_selected_days"][stock]
            )
            all_fit.extend(fit)
            all_diagnostic.extend(diagnostic)
            stock_qc[stock]={"source_member_sha256":expected,"reader_qc":qc}
            if file_sha256(local)!=expected:
                raise RangeSourceError("authenticated source file mutated during diagnostic")
            local.unlink()
            print("D011_SOURCE_ONLY_FIT_STOCK_VERIFIED:",stock,flush=True)
    selected,_=select_dates(source_calendar)
    if selected!=dates:
        raise AssertionError("published date ordering differs from frozen source receipt")

    fit_eligible=[(e,v) for e,v in all_fit if e.target in PERMITTED and v is not None]
    diagnostic_eligible=[(e,v) for e,v in all_diagnostic if e.target in PERMITTED and v is not None]
    matched=[(e,v) for e,v in diagnostic_eligible if e.b1_prediction in PERMITTED]
    if not fit_eligible or not matched:
        raise AssertionError("D011 no source-valid book observations")
    y=np.asarray([e.target for e,v in fit_eligible],dtype=int)
    X=np.asarray([v for e,v in fit_eligible],dtype=float)
    if set(map(int,np.unique(y)))!=set(PERMITTED):
        raise AssertionError("D011 training classes not full three-class support")
    X_diag=np.asarray([v for e,v in matched],dtype=float)
    majority,train_support=choose_training_majority([e for e,v in all_fit])
    maps={
        "B0_majority":_predict_map(matched,[majority]*len(matched)),
        "B1_backward_trend":_predict_map(matched,[e.b1_prediction for e,v in matched]),
    }
    fitted={}
    for key,weight in (
        ("W_BALANCED","balanced"),
        ("W_UNWEIGHTED",None),
    ):
        pipeline=Pipeline([
            ("scale",StandardScaler()),
            ("logit",LogisticRegression(
                C=1.0,class_weight=weight,solver="lbfgs",max_iter=400,
                random_state=7007
            )),
        ])
        pipeline.fit(X,y)
        estimator=pipeline.named_steps["logit"]
        if not estimator.n_iter_.size or max(estimator.n_iter_)>=400:
            raise AssertionError("frozen class-weight diagnostic model failed convergence gate")
        predictions=pipeline.predict(X_diag)
        maps[key]=_predict_map(matched,predictions)
        fitted[key]={
            "class_weight_mode":weight if weight is not None else "none",
            "classes":list(map(int,estimator.classes_)),
            "iterations":list(map(int,estimator.n_iter_)),
            "scaler_feature_mean":[round(float(v),7) for v in pipeline.named_steps["scale"].mean_],
            "scaler_feature_scale":[round(float(v),7) for v in pipeline.named_steps["scale"].scale_],
            "standardized_feature_coefficients":[
                [round(float(c),7) for c in row] for row in estimator.coef_
            ],
            "standardized_feature_intercepts":[round(float(c),7) for c in estimator.intercept_],
        }

    fit_descriptive={}
    diag_descriptive={}
    all_symbols=sorted({e.symbol for e,v in all_fit})
    feature_center_shift={}
    train_scaler_mean=np.asarray(fitted["W_BALANCED"]["scaler_feature_mean"])
    train_scaler_scale=np.asarray(fitted["W_BALANCED"]["scaler_feature_scale"])
    for symbol in all_symbols:
        fit_rows=[(e,v) for e,v in all_fit if e.symbol==symbol]
        diag_rows=[(e,v) for e,v in all_diagnostic if e.symbol==symbol]
        fit_descriptive[symbol]=_feature_stats(fit_rows)
        diag_descriptive[symbol]=_feature_stats(diag_rows)
        centers={}
        for name,rows in (("first10",fit_rows),("last4",diag_rows)):
            clean=np.asarray([v for e,v in rows if e.target in PERMITTED and v is not None],dtype=float)
            centers[name]=[
                round(float(v),5) for v in
                ((clean.mean(axis=0)-train_scaler_mean)/train_scaler_scale)
            ]
        feature_center_shift[symbol]=centers

    by_stock={}
    by_day={}
    for symbol in all_symbols:
        group=[(e,v) for e,v in matched if e.symbol==symbol]
        by_stock[symbol]=_compare_models(group,maps)
        for day in four:
            portion=[(e,v) for e,v in group if e.trading_date==day]
            by_day[symbol+"@"+day]=_compare_models(portion,maps)

    report={
        "status":"D011_fit_period_only_class_weight_and_stock_shift_diagnosis_no_reserved_evaluation",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 noncommercial, with attribution",
        "source_revision":EXPECTED_REVISION,
        "source_member_sha256":FROZEN_SHA256,
        "date_manifest_sha256":manifest["date_list_sha256"],
        "first10_fit_dates":ten,
        "last4_diagnostic_dates":four,
        "excluded_D010_internal_confirmation_dates":dates["train"][14:],
        "excluded_original_validation_dates":dates["validation"],
        "excluded_sealed_final_test_dates":dates["holdout"],
        "source_data_scope":"Only previously inspected first 14 D010 FIT dates admitted to feature/label evaluation",
        "model_lookups_or_validations_after_Jan28":False,
        "no_original_5day_validation_or_10day_test_scoring":True,
        "source_stock_quality":stock_qc,
        "fit_source_origins":len(all_fit),
        "diagnostic_source_origins":len(all_diagnostic),
        "fit_label_eligible":sum(e.target in PERMITTED for e,v in all_fit),
        "fit_depth_complete_eligible":len(fit_eligible),
        "diagnostic_label_eligible":sum(e.target in PERMITTED for e,v in all_diagnostic),
        "diagnostic_depth_complete_eligible":len(diagnostic_eligible),
        "diagnostic_identical_B0_B1_weighted_unweighted_count":len(matched),
        "fit_majority":majority,
        "fit_training_class_support":train_support,
        "fit_stock_feature_summary":fit_descriptive,
        "diagnostic_stock_feature_summary":diag_descriptive,
        "stock_feature_center_shift_in_train_global_standard_deviation_units":feature_center_shift,
        "fixed_class_weight_models":fitted,
        "diagnostic_pooled":_compare_models(matched,maps),
        "diagnostic_by_stock":by_stock,
        "diagnostic_by_stock_date":by_day,
        "scikit_learn_version":sklearn.__version__,
        "source_range_download_bytes":reader.bytes_transferred,
        "full_archive_downloaded_or_verified":False,
        "vendor_quote_rows_or_example_predictions_committed":False,
        "holdout_statistical_isolation":True,
        "holdout_byte_level_secrecy_not_claimed":True,
        "model_promotion":False,
        "limitations":[
            "These are previously used 14 D010 fit dates; the four-day comparison is NOT an untouched independent test.",
            "Two predeclared models differ only in class_weight; no source-day model tuning or model selection is justified.",
            "Stock-specific model errors can reflect other unmeasured factors; center shifts and weight effects are noncausal descriptions.",
            "Overlapping labels and clustering by day and stock mean row-level IID significance is inappropriate.",
            "The periodic order book snapshots cannot identify genuine event-level order flow, queue priority, fills or profitability.",
            "The D010 six internal confirmation days, original five validation days and ten final holdout days remain unscored.",
        ]
    }
    print("QUANT_ARENA_D011_DIAGNOSTIC_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("QUANT_ARENA_D011_DIAGNOSTIC_END",flush=True)


if __name__=="__main__":
    main()
