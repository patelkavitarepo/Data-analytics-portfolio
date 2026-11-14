"""D012 one-shot source-verified *selective directional alerts* (not trading).

This runner refuses to run until the D012 metadata-only 20/10/5/10 cohort
manifest has been separately committed. Authenticates original 3 Quant-Arena
Public L1 stock Parquet members, CC BY-NC 4.0 noncommercial. Reads quote
price/depth rows ONLY from fresh fit/calibration/confirmation dates after
March 7 2022. NEVER forms targets for the 10 calibration dates.
NEVER forms features/targets/scores for D012 10 sealed-final dates or D009
legacy February-March reserved block. One ephemeral CI run, no raw exports.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange,RangeSourceError,checksum_from_sha256sums,
    download_member,pinned_source_url
)
from microstructure.quant_arena_pilot import (
    convert_quote_rows,file_sha256,REQUIRED_FIELDS,PilotError
)
from microstructure.chronological_baselines import (
    choose_training_majority,make_examples,_confusion,PERMITTED
)
from microstructure.liquidity_features import make_feature_rows,SOURCE_FIELDS
from microstructure.selective_alerts import (
    source_past5_coverage,cutoff_by_stock,get_direction_score,
    emit_alert,alert_report
)
from run_quote_quality_sensitivity_once import (
    _checked_source,FROZEN_MEMBERS,FROZEN_SHA256
)
from run_quant_arena_panel_once import (
    ROOT,EXPECTED_REVISION,MAX_STOCK_BYTES,MAX_REMOTE_BYTES
)
from freeze_chronological_dates_once import dated_inventory
from freeze_fresh_selective_dates_once import (
    fresh_selection,load_fresh_manifest,STUDY_PARTS
)

BATCH_ROWS=128
STOCKS=tuple(f.removesuffix(".parquet") for f in FROZEN_MEMBERS)
REPORT_SOURCE_STATUS="D012_NEW_CHRONOLOGICAL_TRAIN_CALIBRATION_CONFIRMATION_ONLY"


def read_fresh_35_only(path,stock,dates,expected_counts):
    """After metadata authentication, admit only 20 fit + 10 calib + 5 confirm.

    Arrow may physically decode a mixed boundary batch, but only the quote
    rows selected strictly inside the authorized 35 dates are converted.
    The last ten sealed dates are never admitted to feature/label objects.
    """
    allowed=sum((dates[k] for k in ("fit","calibration","confirmation")),[])
    if (len(allowed)!=35 or allowed!=sorted(set(allowed))
            or set(allowed)&set(dates["sealed_final"])
            or allowed[0]<="2022-03-07"):
        raise PilotError("D012 authorized 35 fresh source dates only")
    import pyarrow.parquet as pq
    final_confirm=allowed[-1]
    allowed_set=set(allowed)
    source=pq.ParquetFile(path)
    fields=tuple(dict.fromkeys(REQUIRED_FIELDS+SOURCE_FIELDS))
    if any(c not in source.schema_arrow.names for c in fields):
        raise PilotError("source file lacks registered quote/depth columns")
    per_day={d:[] for d in allowed}
    batches=0
    passed_confirmation=False
    for batch in source.iter_batches(batch_size=BATCH_ROWS,columns=list(fields)):
        batches+=1
        ts=batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        day_arr=[t.date().isoformat() if t is not None else None for t in ts]
        if None in day_arr or any(day_arr[i]>day_arr[i+1] for i in range(len(day_arr)-1)):
            raise PilotError("source date chronology inconsistent")
        approved=[i for i,day in enumerate(day_arr) if day in allowed_set]
        if approved:
            left,right=approved[0],approved[-1]+1
            if approved!=list(range(left,right)):
                raise PilotError("noncontiguous source dates in selected batch")
            for row in batch.slice(left,right-left).to_pylist():
                day=row["available_at"].date().isoformat()
                if day not in allowed_set:
                    raise PilotError("unapproved quote row admitted to model")
                per_day[day].append(row)
        if any(day>final_confirm for day in day_arr):
            passed_confirmation=True
            break
    if not passed_confirmation:
        raise PilotError("never observed start of sealed source block")
    for day in allowed:
        if len(per_day[day])!=expected_counts[day]:
            raise PilotError("publisher day/source cardinality differs from frozen metadata")

    out={}
    qc={}
    for key in ("fit","calibration","confirmation"):
        period=dates[key]
        original=[]
        quotes=[]
        for day in period:
            rows=per_day[day]
            converted,source_qc=convert_quote_rows(rows,stock,[day])
            if len(converted)!=len(rows):
                raise PilotError("source conversion lost quote rows")
            original.extend(rows)
            quotes.extend(converted)
        features,book_qc=make_feature_rows(original,stock,period)
        if len(features)!=len(quotes):
            raise AssertionError("feature/quote source row identity lost")
        # Only fit & confirmation may receive future-label construction.
        if key=="calibration":
            readiness=source_past5_coverage(quotes)
            if len(readiness)!=len(quotes):
                raise AssertionError("calibration past-only eligibility mismatch")
            out[key]=(None,features,readiness,tuple(q.symbol for q in quotes))
            qc["calibration_future_labels_computed"]=False
            qc["calibration_past_only_ready_count"]=sum(
                x and f is not None for x,f in zip(readiness,features)
            )
        else:
            examples=make_examples(quotes)
            out[key]=(examples,features,None,tuple(q.symbol for q in quotes))
            qc[key+"_target_eligible_count"]=sum(e.target in PERMITTED for e in examples)
        qc[key+"_source_rows"]=len(quotes)
        qc[key+"_depth_book_coverage"]=book_qc
    qc["parquet_batches_read_until_new_final_boundary"]=batches
    qc["reserved_final_row_admitted"]=False
    qc["legacy_sealed_block_row_admitted"]=False
    return out,qc


def _selection_candidates(examples,features):
    if examples is None or len(examples)!=len(features):
        raise AssertionError("expected legitimate confirmation source-target rows")
    return tuple((e,f) for e,f in zip(examples,features)
                 if e.target in PERMITTED
                 and e.b1_prediction in PERMITTED and f is not None)


def _summarize_candidates(candidates,majority,alert_maps):
    examples=[e for e,v in candidates]
    if not examples:
        raise AssertionError("D012 no source-valid future-target comparison rows")
    groups={}
    groups["B0_majority_threeclass"]=_confusion(examples,lambda e:majority)
    groups["B1_fixed_past_trend_threeclass"]=_confusion(examples,lambda e:e.b1_prediction)
    for name,pred in alert_maps.items():
        keys=[(e.symbol,e.trading_date,e.row_index) for e in examples]
        groups[name+"_selective_alerts"]=alert_report(
            examples,[pred[k] for k in keys],majority
        )
    return groups


def main():
    import sklearn
    import numpy as np
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    receipt=load_fresh_manifest()
    dates=receipt["dates"]
    if (dates["fit"][-1]>=dates["calibration"][0]
            or dates["calibration"][-1]>=dates["confirmation"][0]
            or dates["confirmation"][-1]>=dates["sealed_final"][0]):
        raise AssertionError("source-date model chronology not strictly future")
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    calendar={}
    book_fit=[]
    for_calibration={}
    for_confirmation=[]
    sources={}
    with tempfile.TemporaryDirectory(prefix="qa-D012-fresh-alert-private-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("source member missing or oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("three-member source byte budget exceeded")
            digest=checksum_from_sha256sums(sums,ROOT+filename)
            if digest!=FROZEN_SHA256[filename]:
                raise RangeSourceError("original publisher source SHA256 changed")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=digest:
                raise RangeSourceError("source member SHA256 verification failed")
            local=Path(td)/filename
            local.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            perday,total=dated_inventory(local)
            calendar[stock]=perday
            if total!=receipt["stock_source_provenance"][stock]["source_rows"]:
                raise PilotError("timestamp-only source population no longer matches")
            for day,n in receipt["source_counts_by_selected_date"][stock].items():
                if perday.get(day)!=n:
                    raise PilotError("fresh source-day counts differ from pre-price manifest")
            selected,qc=read_fresh_35_only(
                local,stock,dates,receipt["source_counts_by_selected_date"][stock]
            )
            ft,ff,_,_=selected["fit"]
            fit_rows=list(zip(ft,ff))
            if sum(1 for e,f in fit_rows if e.target in PERMITTED and f is not None)==0:
                raise AssertionError("new source model fit pool unexpectedly empty")
            book_fit.extend(fit_rows)
            cal_ex,cal_features,cal_past,cal_symbols=selected["calibration"]
            if cal_ex is not None:
                raise AssertionError("D012 calibration must never have true future labels")
            # Only these current-source keys, no target, are admitted.
            for_calibration[stock]=[
                (feature,ready and feature is not None)
                for feature,ready in zip(cal_features,cal_past)
            ]
            confirm_ex,confirm_features,_,_=selected["confirmation"]
            for_confirmation.extend(_selection_candidates(confirm_ex,confirm_features))
            sources[stock]={
                "source_member_sha256":digest,
                "selected_market_rows":qc,
                "fit_valid_future_labels":sum(e.target in PERMITTED for e in ft),
                "confirmation_valid_future_labels":sum(e.target in PERMITTED for e in confirm_ex),
            }
            if file_sha256(local)!=digest:
                raise RangeSourceError("source member altered during experiment")
            local.unlink()
            print("D012_NEW_COHORT_SOURCE_MEMBER_VERIFIED:",stock,flush=True)

    reconstructed,details=fresh_selection(calendar)
    if reconstructed!=dates:
        raise AssertionError("timestamp-only D012 source split is not reproducible")
    fit_eligible=[(e,f) for e,f in book_fit if e.target in PERMITTED and f is not None]
    if {e.target for e,f in fit_eligible}!={1,2,3}:
        raise AssertionError("D012 training sample lacks all three label classes")
    majority,train_support=choose_training_majority([e for e,f in book_fit])
    X=np.asarray([f for e,f in fit_eligible],dtype=float)
    y=np.asarray([e.target for e,f in fit_eligible],dtype=int)
    if len(for_confirmation)==0:
        raise AssertionError("D012 no eligible new confirmation origins")
    confirmation_X=np.asarray([f for e,f in for_confirmation],dtype=float)
    alerts={}
    cutoff_receipts={}
    convergence={}
    for name,weight in (("W_BALANCED","balanced"),("W_UNWEIGHTED",None)):
        pipeline=Pipeline([
            ("scale",StandardScaler()),
            ("logit",LogisticRegression(
                C=1.0,class_weight=weight,solver="lbfgs",
                max_iter=400,random_state=7007
            ))
        ])
        pipeline.fit(X,y)
        estimator=pipeline.named_steps["logit"]
        if not estimator.n_iter_.size or max(estimator.n_iter_)>=400:
            raise AssertionError("D012 predeclared model failed convergence")
        classes=tuple(int(v) for v in estimator.classes_)
        if classes!=(1,2,3):
            raise AssertionError("D012 model class ordering differs")
        cal_rows=[]
        cal_features=[]
        for stock in sorted(for_calibration):
            for feature,ready in for_calibration[stock]:
                if ready:
                    cal_rows.append((stock,True))
                    cal_features.append(feature)
        if not cal_rows:
            raise AssertionError("D012 no calibration observations with history")
        cal_pred=pipeline.predict_proba(np.asarray(cal_features,dtype=float))
        thresholds,counts=cutoff_by_stock(cal_rows,cal_pred,classes)
        cutoff_receipts[name]={
            "calibration_stock_counts":counts,
            "calibration_score_cutoffs_no_target_labels":thresholds,
            "fixed_cutoff_quantile":0.98,
            "strict_greater_than":True,
            "calibration_target_labels_calculated":False
        }
        predicted=pipeline.predict_proba(confirmation_X)
        pred_map={}
        for (example,feature),proba in zip(for_confirmation,predicted):
            score,side=get_direction_score(proba,classes)
            alert=emit_alert(score,side,thresholds[example.symbol])
            key=(example.symbol,example.trading_date,example.row_index)
            if key in pred_map:
                raise AssertionError("D012 duplicate scored source-origin key")
            pred_map[key]=alert
        alerts[name]=pred_map
        convergence[name]={
            "iterations":[int(x) for x in estimator.n_iter_],
            "class_weight":weight if weight else "none",
            "model_probability_caveat":"predict_proba is model score; no independent probability calibration",
        }

    pooled=_summarize_candidates(for_confirmation,majority,alerts)
    by_stock={}
    by_stock_date={}
    for stock in STOCKS:
        chosen=[record for record in for_confirmation if record[0].symbol==stock]
        by_stock[stock]=_summarize_candidates(chosen,majority,alerts)
        for day in dates["confirmation"]:
            current=[record for record in chosen if record[0].trading_date==day]
            by_stock_date[stock+"@"+day]=_summarize_candidates(current,majority,alerts)

    result={
        "status":REPORT_SOURCE_STATUS,
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 noncommercial",
        "publisher_revision":EXPECTED_REVISION,
        "source_member_sha256":FROZEN_SHA256,
        "fresh_cohort_sha256":receipt["cohort_date_sha256"],
        "legacy_cohort_sha256":receipt["legacy_manifest_sha256"],
        "partition_dates":dates,
        "original_D009_reserved_test_scored":False,
        "new_D012_sealed_final_scored":False,
        "source_statistical_sealing_caveat":"Whole member SHA256 bytes verified; Parquet batch boundary could decompress later rows but none are admitted to features/labels/scores.",
        "training_label_eligible_complete_depth":len(fit_eligible),
        "training_majority_class":majority,
        "training_class_support":train_support,
        "model_configuration":"StandardScaler + fixed three-feature LogisticRegression(C=1,lbfgs,max_iter=400,seed=7007), weight balanced versus none",
        "models":convergence,
        "calibration_target_labels_accessed":False,
        "calibration_receipts":cutoff_receipts,
        "confirmation_same_origin_count":len(for_confirmation),
        "confirmation_pooled":pooled,
        "confirmation_by_stock":by_stock,
        "confirmation_by_stock_date":by_stock_date,
        "source_stock_integrity_and_coverage":sources,
        "publisher_source_bytes_transferred":fetch.bytes_transferred,
        "full_source_archive_downloaded":False,
        "raw_quotes_or_example_predictions_committed":False,
        "model_promoted":False,
        "trading_PnL_or_fills_evaluated":False,
        "limitations":[
            "This is a one-time future chronological confirmation only; no tuning after scoring.",
            "2 percent is a per-stock *calibration* score budget, not a guaranteed confirmation alert rate.",
            "Classifier scores are not calibrated or causal probabilities.",
            "No-alert means abstention, not a prediction of unchanged price.",
            "Label windows overlap and quote rows cluster by stock/date; no IID p-values.",
            "No actual executed order flow, queue fills, fees, latency or tradable alpha demonstrated.",
            "Both original D009 and new D012 final holdouts remain reserved and unscored.",
        ],
    }
    print("D012_FRESH_ALERTS_BEGIN",flush=True)
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
    print("D012_FRESH_ALERTS_END",flush=True)


if __name__=="__main__":
    main()
