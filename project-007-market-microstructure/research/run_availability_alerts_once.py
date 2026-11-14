"""D015 one-time empirical runner. Frozen source/date/model; no final price rows.

Source: Quant-Arena Public L1, CC BY-NC 4.0 noncommercial, attribution
Quant Arena / LaPlace's Eye / Einsia AI. Outputs aggregate-only research.
"""
from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from microstructure.chronological_baselines import make_examples,PERMITTED
from microstructure.liquidity_features import make_feature_rows,SOURCE_FIELDS
from microstructure.quant_arena_pilot import convert_quote_rows,REQUIRED_FIELDS,PilotError,file_sha256
from microstructure.selective_alerts import source_past5_coverage,get_direction_score
from microstructure.availability_alerts import freeze_calendar,replay,aggregate_states,matched_outcomes,POLICIES
from microstructure.adaptive_alerts import STOCKS,ORIGINAL_CUTOFFS
from microstructure.selective_tar import HTTPRange,RangeSourceError,checksum_from_sha256sums,download_member,pinned_source_url
from run_quote_quality_sensitivity_once import _checked_source,FROZEN_MEMBERS,FROZEN_SHA256
from run_quant_arena_panel_once import ROOT,EXPECTED_REVISION,MAX_STOCK_BYTES,MAX_REMOTE_BYTES
from freeze_chronological_dates_once import dated_inventory
from freeze_fresh_selective_dates_once import load_fresh_manifest
from freeze_availability_dates_once import load_manifest,select_dates

BATCH_ROWS=128
TRAIN_EXPECTED_N=54290
MODEL_WEIGHTS=(("W_BALANCED","balanced"),("W_UNWEIGHTED",None))
DATE_SHA="0a594c1d46a4e1b415b390ada8fe8db76ce5401d8b8d1c15d87d7750bbc92a14"


def read_permitted(path,stock,old,new,old_counts,new_counts):
    """Timestamp-filter BEFORE converting any price/depth/volume row."""
    fit=list(old["fit"])
    warm=list(new["warmup"])
    confirm=list(new["confirmation"])
    freeze_calendar(warm,confirm,new["sealed_final"])
    if (len(fit)!=20 or fit!=sorted(set(fit)) or fit[-1]>="2022-04-07"
            or set(fit)&set(warm+confirm+new["sealed_final"])
            or set(fit)&set(old["calibration"]+old["confirmation"]+old["sealed_final"])):
        raise PilotError("D015 original fit/new source isolation violated")
    approved=set(fit+warm+confirm)
    rows={d:[] for d in approved}
    import pyarrow.parquet as pq
    src=pq.ParquetFile(path)
    columns=tuple(dict.fromkeys(REQUIRED_FIELDS+SOURCE_FIELDS))
    if any(c not in src.schema_arrow.names for c in columns):
        raise PilotError("source schema differs from frozen feature schema")
    boundary=False
    for batch in src.iter_batches(batch_size=BATCH_ROWS,columns=list(columns)):
        stamps=batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        days=[v.date().isoformat() if v is not None else None for v in stamps]
        if None in days or days!=sorted(days):
            raise PilotError("publisher source chronology invalid")
        ix=[i for i,d in enumerate(days) if d in approved]
        if ix:
            if ix!=list(range(ix[0],ix[-1]+1)):
                raise PilotError("authorized timestamps not contiguous within batch")
            for raw in batch.slice(ix[0],len(ix)).to_pylist():
                day=raw["available_at"].date().isoformat()
                if day not in approved:raise AssertionError("unauthorized price row converted")
                rows[day].append(raw)
        if any(d>confirm[-1] for d in days):
            boundary=True
            break
    if not boundary:raise PilotError("D015 final source boundary not reached")
    for d in fit:
        if len(rows[d])!=old_counts[d]:raise PilotError("original fit source counts changed")
    for d in warm+confirm:
        if len(rows[d])!=new_counts[d]:raise PilotError("pre-price frozen source counts changed")
    training=[]
    observations={}
    for part,dates in (("fit",fit),("warmup",warm),("confirmation",confirm)):
        for d in dates:
            raw=rows[d]
            quotes,_=convert_quote_rows(raw,stock,[d])
            features,_=make_feature_rows(raw,stock,[d])
            if len(quotes)!=len(features) or len(features)!=len(raw):
                raise AssertionError("origin alignment corrupted")
            if part=="fit":
                labels=make_examples(quotes)
                training.extend((f,e.target) for f,e in zip(features,labels)
                                if f is not None and e.target in PERMITTED)
            else:
                past=source_past5_coverage(quotes)
                labels=None if part=="warmup" else make_examples(quotes)
                if labels is not None and tuple(e.b1_prediction in PERMITTED for e in labels)!=past:
                    raise AssertionError("past-only feature readiness differs from original B1")
                observations[d]={
                    "features":tuple(f if f is not None and past[i] else None
                                     for i,f in enumerate(features)),
                    "truth":None if labels is None else tuple(
                        labels[i].target if labels[i].target in PERMITTED else None
                        for i in range(len(raw))),
                    "source_n":len(raw),
                    "current_ready_n":sum(f is not None and past[i]
                                          for i,f in enumerate(features))
                }
    return training,observations


def fit_original(training):
    import sklearn
    import numpy as np
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    if sklearn.__version__!="1.6.1":
        raise ValueError("original sklearn 1.6.1 required")
    if len(training)!=TRAIN_EXPECTED_N:
        raise AssertionError("original 54290 fit examples not reproduced")
    x=np.asarray([a for a,b in training],dtype=float)
    y=np.asarray([b for a,b in training],dtype=int)
    models={}
    for name,weight in MODEL_WEIGHTS:
        pipe=Pipeline([("scale",StandardScaler()),
            ("logit",LogisticRegression(C=1.0,solver="lbfgs",max_iter=400,
                                     random_state=7007,class_weight=weight))])
        pipe.fit(x,y)
        logit=pipe.named_steps["logit"]
        if max(logit.n_iter_)>=400 or tuple(map(int,logit.classes_))!=(1,2,3):
            raise AssertionError("original fit classes/convergence changed")
        models[name]=pipe
    return models


def score_source(model,observations):
    import numpy as np
    classes=model.named_steps["logit"].classes_
    out={}
    for day,entry in observations.items():
        features=entry["features"]
        valid=[(i,f) for i,f in enumerate(features) if f is not None]
        scores=[None]*len(features)
        if valid:
            p=model.predict_proba(np.asarray([f for i,f in valid],dtype=float))
            for (i,_),prob in zip(valid,p):
                scores[i]=get_direction_score(prob,classes)
        out[day]=tuple(scores)
    return out


def pool(leaves):
    counts={k:sum(x["state"]["counts"][k] for x in leaves)
            for k in ("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY",
                      "NO_SIGNAL","ALERT_UP","ALERT_DOWN")}
    n=sum(x["state"]["source_n"] for x in leaves)
    matched=sum(x["outcome"]["matched_n"] for x in leaves)
    correct=sum(x["outcome"]["correct"] for x in leaves)
    wrong=sum(x["outcome"]["wrong"] for x in leaves)
    alerts=counts["ALERT_UP"]+counts["ALERT_DOWN"]
    if sum(counts.values())!=n:raise AssertionError("full source denominator lost")
    return {"source_n":n,"status_counts":counts,
            "all_source_alerts":alerts,"alert_rate_all_source":alerts/n,
            "decision_capable":counts["NO_SIGNAL"]+alerts,
            "matched_n":matched,"correct":correct,"wrong":wrong,
            "matched_alerts":correct+wrong,
            "directional_precision":correct/(correct+wrong) if correct+wrong else None,
            "false_alerts_per_1000_matched":1000*wrong/matched if matched else None,
            "hypothetical_4to1_units":correct-4*wrong,
            "zero_alert_reference_units":0,
            "stock_days_over_4pct_all_source":sum(
                x["state"]["alert_rate_all_source"]>.04 for x in leaves)}


def main():
    receipt=load_manifest()
    if receipt["date_list_sha256"]!=DATE_SHA:
        raise ValueError("D015 pre-price date manifest SHA changed")
    new=receipt["dates"]
    freeze_calendar(new["warmup"],new["confirmation"],new["sealed_final"])
    old=load_fresh_manifest()
    if old["dates"]["sealed_final"][-1]!="2022-05-16":
        raise ValueError("original D012 sealed boundary changed")
    if set(STOCKS)!={s.removesuffix(".parquet") for s in FROZEN_MEMBERS}:
        raise ValueError("source stock identities changed")
    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    fit=[]
    source={}
    inventories={}
    with tempfile.TemporaryDirectory(prefix="qa-D015-noncommercial-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("pinned stock member missing/oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("source byte ceiling")
            digest=checksum_from_sha256sums(sums,ROOT+filename)
            if digest!=FROZEN_SHA256[filename] or digest!=receipt["member_sha256"][filename]:
                raise RangeSourceError("publisher original member digest changed")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=digest:
                raise RangeSourceError("authenticated publisher member hash mismatch")
            local=Path(td)/filename
            local.write_bytes(blob);del blob
            stock=filename.removesuffix(".parquet")
            inventory,total=dated_inventory(local)
            inventories[stock]=inventory
            if total!=receipt["source_provenance"][stock]["source_rows"]:
                raise PilotError("publisher source row population changed")
            for d,n in receipt["source_counts_by_date"][stock].items():
                if inventory.get(d)!=n:
                    raise PilotError("D015 pre-price timestamp counts differ")
            train,other=read_permitted(
                local,stock,old["dates"],new,
                old["source_counts_by_selected_date"][stock],
                receipt["source_counts_by_date"][stock])
            fit.extend(train);source[stock]=other
            if file_sha256(local)!=digest:raise RangeSourceError("source member changed")
            local.unlink()
            print("D015_SOURCE_MEMBER_AUTHENTICATED",stock,flush=True)
    check,_=select_dates(inventories)
    if check!=new:raise ValueError("D015 source date selection changed")
    models=fit_original(fit)
    results={}
    for model_name,model in models.items():
        by_policy={p:[] for p in POLICIES}
        per_stock={}
        for stock in STOCKS:
            scored=score_source(model,source[stock])
            decisions=replay(new["warmup"],new["confirmation"],new["sealed_final"],
                             scored,stock,model_name)
            stock_out={}
            for day in new["confirmation"]:
                truth=source[stock][day]["truth"]
                if truth is None:raise AssertionError("confirmation truth absent")
                stock_out[day]={}
                for policy in POLICIES:
                    states=decisions[day][policy]["statuses"]
                    state=aggregate_states(states)
                    outcome=matched_outcomes(states,truth)
                    leaf={"state":state,"outcome":outcome}
                    by_policy[policy].append(leaf)
                    stock_out[day][policy]={
                        "source_n":state["source_n"],
                        "source_valid_n":source[stock][day]["current_ready_n"],
                        "state_counts":state["counts"],
                        "alerts":state["alerts"],
                        "alert_rate_all_source":state["alert_rate_all_source"],
                        "alert_rate_capable":state["alert_rate_capable"],
                        "matched_n":outcome["matched_n"],
                        "correct":outcome["correct"],"wrong":outcome["wrong"],
                        "up_support":outcome["up_support"],
                        "down_support":outcome["down_support"],
                        "up_detected":outcome["up_detected"],
                        "down_detected":outcome["down_detected"],
                        "directional_movement_unavailable":outcome["directional_movement_unavailable"],
                        "history_healthy":decisions[day][policy]["history_healthy"],
                        "minimum_prior_day_coverage":decisions[day]["historical_source_coverage"]["minimum_past_coverage"]
                    }
            per_stock[stock]=stock_out
        results[model_name]={"pooled":{p:pool(by_policy[p]) for p in POLICIES},
                             "per_stock_day":per_stock}
    report={
        "status":"D015_ONE_TIME_CONFIRMATION_NO_FINAL_ACCESS",
        "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
        "license":"CC BY-NC 4.0 noncommercial with attribution",
        "publisher_revision":EXPECTED_REVISION,
        "authenticated_member_sha256":FROZEN_SHA256,
        "frozen_D015_date_sha256":DATE_SHA,
        "original_D012_fit_n":len(fit),
        "warmup_future_labels_computed":False,
        "old_D009_D012_D014_final_scored":False,
        "new_D015_final_scored":False,
        "raw_vendor_quotes_committed":False,
        "trading_PnL_evaluated":False,
        "source_bytes_transferred":fetch.bytes_transferred,
        "models":results
    }
    print("D015_CONFIRMATION_AGGREGATES_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("D015_CONFIRMATION_AGGREGATES_END",flush=True)


if __name__=="__main__":
    main()
