"""D014 source-verified one-time adaptive-vs-static alert experiment.

Use immutable 2022 D012 fitting dates + NEW metadata-frozen D014 warmup and
one-time confirmation dates ONLY. No quote/features/labels/scores from D009
reserved, D012 reserved or D014 reserved final. Never compute warmup targets.
Provider rows and per-origin scores remain ephemeral, results aggregate only.
License: Quant-Arena Public L1 CC BY-NC 4.0 noncommercial attribution.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from microstructure.chronological_baselines import make_examples, PERMITTED, continuous_phase
from microstructure.liquidity_features import make_feature_rows, SOURCE_FIELDS
from microstructure.quant_arena_pilot import convert_quote_rows, REQUIRED_FIELDS, PilotError, file_sha256
from microstructure.selective_alerts import source_past5_coverage, get_direction_score
from microstructure.adaptive_alerts import (
    STOCKS, ORIGINAL_CUTOFFS, validate_calendar,
    daily_threshold_replay, labelled_alert_metrics, cluster_bootstrap_day_sums
)
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from run_quote_quality_sensitivity_once import _checked_source, FROZEN_MEMBERS, FROZEN_SHA256
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
from freeze_chronological_dates_once import dated_inventory
from freeze_fresh_selective_dates_once import load_fresh_manifest
from freeze_adaptive_dates_once import load_manifest as load_adaptive_manifest, select_dates

BATCH_ROWS=128
TRAIN_EXPECTED_N=54290
ALLOWED_MODEL_NAMES=("W_BALANCED","W_UNWEIGHTED")
MODEL_WEIGHTS=(("W_BALANCED","balanced"),("W_UNWEIGHTED",None))


def _read_authorized_days(path,stock,original,new,expected_old,expected_new):
    """Only D012 old fit + D014 fresh warmup/confirmation become quote objects.

    We must authenticate entire per-stock source members; Arrow may physically
    decompress boundary-overlapping batches. Filter timestamps before converting
    any original price/volume/depth row to an analytical observation.
    """
    old_fit=list(original["fit"])
    fresh=list(new["warmup"])+list(new["confirmation"])
    if (len(old_fit)!=20 or len(fresh)!=30
            or old_fit!=sorted(set(old_fit))
            or fresh!=sorted(set(fresh))
            or old_fit[-1]>="2022-04-07"
            or fresh[0]<="2022-05-16"
            or set(old_fit)&set(fresh)
            or set(old_fit)&set(original["calibration"]+original["confirmation"]+original["sealed_final"])
            or set(fresh)&set(new["sealed_final"])):
        raise PilotError("D014 strict authorized source-date isolation failed")
    allowed=old_fit+fresh
    allowed_set=set(allowed)
    stop_at=fresh[-1]
    import pyarrow.parquet as pq
    source=pq.ParquetFile(path)
    columns=tuple(dict.fromkeys(REQUIRED_FIELDS+SOURCE_FIELDS))
    if any(c not in source.schema_arrow.names for c in columns):
        raise PilotError("publisher schema no longer has registered source inputs")
    by_day={d:[] for d in allowed}
    saw_new_sealed_boundary=False
    for batch in source.iter_batches(batch_size=BATCH_ROWS,columns=list(columns)):
        stamp=batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        day_arr=[ts.date().isoformat() if ts is not None else None for ts in stamp]
        if (None in day_arr
                or any(day_arr[i]>day_arr[i+1] for i in range(len(day_arr)-1))):
            raise PilotError("original publisher source chronology corrupted")
        indexes=[i for i,d in enumerate(day_arr) if d in allowed_set]
        if indexes:
            l,r=indexes[0],indexes[-1]+1
            if indexes!=list(range(l,r)):
                raise PilotError("approved dates not contiguous inside data batch")
            for raw in batch.slice(l,r-l).to_pylist():
                d=raw["available_at"].date().isoformat()
                if d not in allowed_set:
                    raise AssertionError("data leak into unapproved D014 source dates")
                by_day[d].append(raw)
        if any(d>stop_at for d in day_arr):
            saw_new_sealed_boundary=True
            break
    if not saw_new_sealed_boundary:
        raise PilotError("D014 new final start never observed")

    for d in old_fit:
        if len(by_day[d])!=expected_old[d]:
            raise PilotError("D012 original fit source-day cardinality changed")
    for d in fresh:
        if len(by_day[d])!=expected_new[d]:
            raise PilotError("D014 frozen metadata source-day cardinality changed")

    fit=[]
    future={}
    quality={"source_days_fit":len(old_fit),
             "source_days_warmup":len(new["warmup"]),
             "source_days_confirmation":len(new["confirmation"]),
             "source_rows_fit":sum(len(by_day[d]) for d in old_fit),
             "source_rows_warmup":sum(len(by_day[d]) for d in new["warmup"]),
             "source_rows_confirmation":sum(len(by_day[d]) for d in new["confirmation"]),
             "warmup_future_target_labels_computed":False,
             "new_final_row_converted":False,
             "D012_earlier_final_row_converted":False,
             "D009_earlier_final_row_converted":False}
    for part,dates in (("fit",old_fit),("warmup",new["warmup"]),("confirmation",new["confirmation"])):
        for day in dates:
            raw=by_day[day]
            quotes,qc=convert_quote_rows(raw,stock,[day])
            features,book_qc=make_feature_rows(raw,stock,[day])
            if not len(quotes)==len(features)==len(raw):
                raise AssertionError("model source row alignment changed")
            if part=="fit":
                examples=make_examples(quotes)
                fit.extend((feature,e.target) for feature,e in zip(features,examples)
                           if feature is not None and e.target in PERMITTED)
            else:
                past=source_past5_coverage(quotes) # no future targets
                if part=="warmup":
                    examples=None # explicit irreversible label-free protocol
                else:
                    examples=make_examples(quotes) # ONLY new one-time confirmation
                    if tuple(e.b1_prediction in PERMITTED for e in examples)!=past:
                        raise AssertionError("D014 past-only history differs from B1")
                ready=[]
                for i,(feature,prior) in enumerate(zip(features,past)):
                    if prior and feature is not None:
                        truth=(examples[i].target if examples is not None else None)
                        ready.append({"source_row":i,"feature":feature,
                                      "truth":truth})
                if not ready:
                    raise PilotError("D014 complete observed stock/day has no decision-ready scores")
                future[day]=ready
            del quotes,features,raw
    return fit,future,quality


def _summarize_policy(rows,decisions):
    """Retrospective metrics on future-verifiable subset, separate decision N."""
    if len(rows)!=len(decisions):
        raise ValueError("prediction/source row alignment differs")
    matched=[(r["truth"],p) for r,p in zip(rows,decisions) if r["truth"] in PERMITTED]
    metrics=labelled_alert_metrics([y for y,p in matched],[p for y,p in matched])
    signal_n=sum(p is not None for p in decisions)
    metrics.update({
        "decision_time_n":len(rows),
        "decision_time_alerts":signal_n,
        "decision_time_rate":signal_n/len(rows),
        "absolute_2pct_budget_error":abs(signal_n/len(rows)-.02),
        "over_4pct_alerts":signal_n/len(rows)>.04,
        "utility_at_false_cost_1":metrics["correct"]-metrics["false"],
        "utility_at_false_cost_9":metrics["correct"]-9*metrics["false"],
        "label_verifiable_selection":len(matched)/len(rows),
    })
    if metrics["matched_n"]>len(rows):
        raise AssertionError("future-label eligibility cannot exceed source decisions")
    return metrics


def _pool_metrics(leaves):
    if not leaves:
        raise ValueError("missing D014 source-day results")
    sums={k:sum(m[k] for m in leaves) for k in
          ("matched_n","alerts","correct","false","abstain",
           "decision_time_n","decision_time_alerts","up_support","down_support",
           "utility_units","utility_at_false_cost_1","utility_at_false_cost_9")}
    if sums["alerts"]!=sums["correct"]+sums["false"]:
        raise AssertionError("reconstructed matched alert arithmetic failed")
    sums["decision_time_alert_rate"]=sums["decision_time_alerts"]/sums["decision_time_n"]
    sums["direction_precision"]=sums["correct"]/sums["alerts"] if sums["alerts"] else None
    sums["false_alerts_per_1000_matched"]=1000*sums["false"]/sums["matched_n"]
    sums["absolute_pooled_2pct_error"]=abs(sums["decision_time_alert_rate"]-.02)
    sums["stock_days_over_4pct"]=sum(m["over_4pct_alerts"] for m in leaves)
    sums["total_stock_days"]=len(leaves)
    return sums


def main():
    import numpy as np
    import sklearn
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    if sklearn.__version__!="1.6.1":
        raise ValueError("D014 fit reproduction requires exact sklearn 1.6.1")
    old=load_fresh_manifest()
    fresh=load_adaptive_manifest()
    new_dates=fresh["dates"]
    validate_calendar(new_dates["warmup"],new_dates["confirmation"],new_dates["sealed_final"])
    if set(STOCKS)!={x.removesuffix(".parquet") for x in FROZEN_MEMBERS}:
        raise AssertionError("original three stock members changed")
    if old["dates"]["sealed_final"][-1]!="2022-05-16":
        raise ValueError("D012 final boundary changed")

    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    training=[]
    record={}
    coverage={}
    inventories={}
    with tempfile.TemporaryDirectory(prefix="qa-D014-private-noncommercial-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("pinned source member missing or oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("source byte ceiling exceeded")
            expected=checksum_from_sha256sums(sums,ROOT+filename)
            if expected!=FROZEN_SHA256[filename] or expected!=fresh["member_sha256"][filename]:
                raise RangeSourceError("publisher SHA256 changed from precommitted member")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=expected:
                raise RangeSourceError("invalid source data authentication")
            local=Path(td)/filename
            local.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            counts,total=dated_inventory(local) # all dates TIMESTAMP ONLY
            inventories[stock]=counts
            if total!=fresh["source_provenance"][stock]["source_rows"]:
                raise ValueError("timestamp-only source total changed")
            for d,n in fresh["source_counts_by_date"][stock].items():
                if counts.get(d)!=n:
                    raise ValueError("pre-price D014 inventory differs")
            fit,other,qc=_read_authorized_days(
                local,stock,old["dates"],new_dates,
                old["source_counts_by_selected_date"][stock],
                fresh["source_counts_by_date"][stock])
            training.extend(fit)
            record[stock]=other
            coverage[stock]=qc
            if file_sha256(local)!=expected:
                raise RangeSourceError("publisher Parquet changed during analysis")
            local.unlink()
            print("D014_MEMBER_SHA256_OK:",stock,flush=True)
    check,_=select_dates(inventories)
    if check!=new_dates:
        raise ValueError("D014 timestamp precommitted common dates differ")
    if len(training)!=TRAIN_EXPECTED_N:
        raise AssertionError("D012 original fit 54,290 examples not reproduced")
    x=np.asarray([v for v,y in training],dtype=float)
    y=np.asarray([target for v,target in training],dtype=int)

    model_output={}
    for name,weight in MODEL_WEIGHTS:
        model=Pipeline([
            ("scale",StandardScaler()),
            ("logit",LogisticRegression(
                C=1.0,solver="lbfgs",max_iter=400,
                random_state=7007,class_weight=weight))
        ])
        model.fit(x,y)
        estimator=model.named_steps["logit"]
        if max(estimator.n_iter_)>=400 or tuple(int(c) for c in estimator.classes_)!=(1,2,3):
            raise AssertionError("original D012 model failed convergence/classes")
        stock_results={}
        for stock in STOCKS:
            by_day={}
            for d in new_dates["warmup"]+new_dates["confirmation"]:
                rows=record[stock][d]
                scores=model.predict_proba(
                    np.asarray([r["feature"] for r in rows],dtype=float))
                if len(rows)!=len(scores):
                    raise AssertionError("D014 source prediction identity mismatch")
                by_day[d]=tuple(get_direction_score(p,estimator.classes_) for p in scores)
            decisions=daily_threshold_replay(
                new_dates["warmup"],new_dates["confirmation"],by_day,
                ORIGINAL_CUTOFFS[name][stock])
            stock_results[stock]={}
            for d in new_dates["confirmation"]:
                rows=record[stock][d]
                case=decisions[d]
                stock_results[stock][d]={
                    "static_cutoff_frozen_D012":case["static_cutoff"],
                    "adaptive_cutoff_previous_ten_complete_days":case["rolling_cutoff"],
                    "static":_summarize_policy(rows,case["static"]),
                    "rolling":_summarize_policy(rows,case["rolling"]),
                }
        comparison={}
        for policy in ("static","rolling"):
            leaves=[stock_results[s][d][policy] for d in new_dates["confirmation"] for s in STOCKS]
            pooled=_pool_metrics(leaves)
            day_groups=[]
            for d in new_dates["confirmation"]:
                group=[stock_results[s][d][policy] for s in STOCKS]
                day_groups.append((
                    sum(v["correct"] for v in group),
                    sum(v["false"] for v in group),
                    sum(v["matched_n"] for v in group)
                ))
            pooled["cluster_bootstrap_10_common_days"]=cluster_bootstrap_day_sums(day_groups)
            pooled["per_stock"]={
                s:_pool_metrics([stock_results[s][d][policy] for d in new_dates["confirmation"]])
                for s in STOCKS
            }
            pooled["per_day"]={
                d:_pool_metrics([stock_results[s][d][policy] for s in STOCKS])
                for d in new_dates["confirmation"]
            }
            comparison[policy]=pooled
        comparison["paired_stock_day_absolute_2pct_error"]={
            "stock_days":30,
            "mean_rolling_minus_static":sum(
                stock_results[s][d]["rolling"]["absolute_2pct_budget_error"]
                -stock_results[s][d]["static"]["absolute_2pct_budget_error"]
                for s in STOCKS for d in new_dates["confirmation"]
            )/30,
            "rolling_better_stock_days":sum(
                stock_results[s][d]["rolling"]["absolute_2pct_budget_error"]
                <stock_results[s][d]["static"]["absolute_2pct_budget_error"]
                for s in STOCKS for d in new_dates["confirmation"]
            ),
            "static_better_stock_days":sum(
                stock_results[s][d]["rolling"]["absolute_2pct_budget_error"]
                >stock_results[s][d]["static"]["absolute_2pct_budget_error"]
                for s in STOCKS for d in new_dates["confirmation"]
            ),
        }
        model_output[name]={"by_stock_date":stock_results,"pooled":comparison}

    report={
        "status":"D014_ONE_TIME_FRESH_CONFIRMATION_NO_FINAL_ACCESS_NO_MODEL_PROMOTION",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "license":"CC BY-NC 4.0 noncommercial with attribution",
        "publisher_revision":EXPECTED_REVISION,
        "authenticated_publisher_member_sha256":FROZEN_SHA256,
        "old_D012_date_sha256":old["cohort_date_sha256"],
        "new_D014_date_sha256":fresh["date_list_sha256"],
        "old_model_fit_examples_reproduced":len(training),
        "original_D012_model_training_dates":old["dates"]["fit"],
        "fresh_warmup_date_list":new_dates["warmup"],
        "fresh_confirmation_dates":new_dates["confirmation"],
        "calibration_and_warmup_target_labels_computed":False,
        "first_D009_reserved_final_scored":False,
        "D012_reserved_final_scored":False,
        "D014_new_reserved_final_scored":False,
        "raw_quotes_or_row_predictions_committed":False,
        "trading_PnL_or_fills_evaluated":False,
        "hypothetical_cost_primary":{"correct":1,"false":-4,"abstain":0,
            "break_even_directional_precision_if_alerting":0.8,
            "not_trading_returns_or_measured_user_cost":True},
        "source_coverage":coverage,
        "models":model_output,
        "source_bytes_fetched":fetch.bytes_transferred,
        "whole_source_archive_downloaded":False,
        "limitations":[
            "Rolling 10 prior days are label-free, but past score distributions can still fail to generalize.",
            "This ten-day confirm period is one-time historical data, not live deployment or calibration of probabilities.",
            "No-alert means abstention and cannot be equated with stationary forecast.",
            "Hypothetical 1:-4 alert utility is not measured PnL, investor preference, or transaction costs.",
            "Overlapping quote targets, stock/date clustering and only ten common confirmation days prevent quote-IID inference.",
            "The original D012 and old D009 reserved periods stay sealed and are earlier than D014; the D014 final stays unscored.",
        ]
    }
    print("D014_ADAPTIVE_CONFIRMATION_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("D014_ADAPTIVE_CONFIRMATION_END",flush=True)


if __name__=="__main__":
    main()
