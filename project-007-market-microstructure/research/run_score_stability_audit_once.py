"""D013: preregistered retrospective D012 score-stability audit.

On authenticated ORIGINAL Shenzhen 2022 sources, recreate original D012
fit, calibration and confirmation only. No new model/threshold, no tuning,
no calibration target labels, no legacy/new sealed-final model rows.
Only aggregate statistics leave the ephemeral runner.
"""
from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.chronological_baselines import make_examples, PERMITTED, continuous_phase
from microstructure.liquidity_features import make_feature_rows, SOURCE_FIELDS
from microstructure.quant_arena_pilot import convert_quote_rows, REQUIRED_FIELDS, file_sha256, PilotError
from microstructure.selective_alerts import source_past5_coverage, cutoff_by_stock, get_direction_score
from microstructure.score_stability import (
    make_rows, attach_scores, scope_groups, score_distribution, feature_distribution
)
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, checksum_from_sha256sums,
    download_member, pinned_source_url
)
from run_quote_quality_sensitivity_once import _checked_source, FROZEN_MEMBERS, FROZEN_SHA256
from run_quant_arena_panel_once import ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES
from freeze_fresh_selective_dates_once import load_fresh_manifest, fresh_selection
from freeze_chronological_dates_once import dated_inventory

STOCKS=tuple(x.removesuffix(".parquet") for x in FROZEN_MEMBERS)
BATCH_ROWS=128
EXPECTED_MATCHED={"000012.SZ":4645,"000025.SZ":4529,"000031.SZ":4645}
EXPECTED_ALERTS={"W_BALANCED":919,"W_UNWEIGHTED":882}
# Published D012 cutoffs were rounded to eight decimal places.
D012_CUTOFFS={
    "W_BALANCED":{"000012.SZ":"1.88134016","000025.SZ":"1.71470105","000031.SZ":"4.44242021"},
    "W_UNWEIGHTED":{"000012.SZ":"0.14798194","000025.SZ":"0.13696671","000031.SZ":"0.31666292"}
}


def read_audit_35_only(path,stock,dates,expected_counts):
    """Check source day and avoid ever converting reserved quote rows.

    Arrow may decompress a boundary-overlapping batch; selected original
    quote dictionaries are restricted to the first 35 dates, never final.
    """
    import pyarrow.parquet as pq
    approved=sum((dates[k] for k in ("fit","calibration","confirmation")),[])
    if (len(approved)!=35 or approved!=sorted(set(approved))
            or set(approved)&set(dates["sealed_final"])
            or approved[0]<="2022-03-07"):
        raise PilotError("D013 reader restricted to original 35 pre-final D012 dates")
    allowed=set(approved)
    final_date=approved[-1]
    source=pq.ParquetFile(path)
    columns=tuple(dict.fromkeys(REQUIRED_FIELDS+SOURCE_FIELDS))
    if any(c not in source.schema_arrow.names for c in columns):
        raise PilotError("pinned source schema lacks quote/depth fields")
    raw_by_day={d:[] for d in approved}
    saw_after=False
    for batch in source.iter_batches(batch_size=BATCH_ROWS,columns=list(columns)):
        timestamps=batch.column(batch.schema.get_field_index("available_at")).to_pylist()
        days=[t.date().isoformat() if t is not None else None for t in timestamps]
        if None in days or any(days[i]>days[i+1] for i in range(len(days)-1)):
            raise PilotError("provider dates unsorted")
        indices=[i for i,day in enumerate(days) if day in allowed]
        if indices:
            left,right=indices[0],indices[-1]+1
            if indices!=list(range(left,right)):
                raise PilotError("approved date rows not contiguous")
            for raw in batch.slice(left,right-left).to_pylist():
                day=raw["available_at"].date().isoformat()
                if day not in allowed:
                    raise AssertionError("reserved source row accessed")
                raw_by_day[day].append(raw)
        if any(d>final_date for d in days):
            saw_after=True
            break
    if not saw_after:
        raise PilotError("sealed boundary never found")
    if any(len(raw_by_day[d])!=expected_counts[d] for d in approved):
        raise PilotError("source-day row counts differ from frozen timestamp manifest")

    out={"fit":[],"calibration":[],"confirmation":[]}
    train=[]
    for part in ("fit","calibration","confirmation"):
        for day in dates[part]:
            raw=raw_by_day[day]
            quotes,source_qc=convert_quote_rows(raw,stock,[day])
            feats,book_qc=make_feature_rows(raw,stock,[day])
            if len(quotes)!=len(feats):
                raise AssertionError("source/quote feature alignment lost")
            past=source_past5_coverage(quotes) # current/past only, including calibration
            if part=="calibration":
                # CRITICAL: do not call make_examples on calibration dates.
                examples=None
                matched=None
            else:
                examples=make_examples(quotes)
                if tuple(e.b1_prediction in PERMITTED for e in examples)!=past:
                    raise AssertionError("past-only history differs from B1 history")
                matched=([e.target in PERMITTED and prior and feat is not None
                          for e,prior,feat in zip(examples,past,feats)]
                         if part=="confirmation" else None)
            rows=make_rows(
                stock,[day]*len(raw),feats,past,
                [continuous_phase(r["available_at"]) for r in raw],matched
            )
            out[part].extend(rows)
            if part=="fit":
                train.extend((f,e.target) for f,e in zip(feats,examples)
                             if f is not None and e.target in PERMITTED)
            del quotes,raw,feats
    return out,train


def _score_group(rows,cutoff,*,matched=False):
    return score_distribution(rows,cutoff,matched=matched)


def main():
    import numpy as np
    import sklearn
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    if sklearn.__version__!="1.6.1":
        raise ValueError("D012 reproduction requires pinned scikit-learn 1.6.1")
    receipt=load_fresh_manifest()
    dates=receipt["dates"]
    if not (dates["fit"][-1]<dates["calibration"][0]
            <dates["calibration"][-1]<dates["confirmation"][0]
            <dates["confirmation"][-1]<dates["sealed_final"][0]):
        raise AssertionError("frozen cohort chronology invalid")
    if receipt["cohort_date_sha256"]!="fe19d601c74f3276e13d8fda3e03ebebcc548bcdb1a2b748138c2d7040d7f3da":
        raise ValueError("D012 frozen date-list hash differs")

    fetch=HTTPRange(pinned_source_url(EXPECTED_REVISION))
    catalog,sums=_checked_source(fetch)
    all_data={"fit":[],"calibration":[],"confirmation":[]}
    fit=[]
    inventories={}
    with tempfile.TemporaryDirectory(prefix="qa-D013-disposable-source-") as td:
        for filename in FROZEN_MEMBERS:
            member=catalog.get(ROOT+filename)
            if member is None or not 0<member.size<=MAX_STOCK_BYTES:
                raise RangeSourceError("source member missing/oversized")
            if fetch.bytes_transferred+member.size>MAX_REMOTE_BYTES:
                raise RangeSourceError("source byte budget exceeded")
            digest=checksum_from_sha256sums(sums,ROOT+filename)
            if digest!=FROZEN_SHA256[filename]:
                raise RangeSourceError("publisher hash differs from source panel")
            blob=download_member(fetch,member,max_bytes=MAX_STOCK_BYTES)
            if sha256(blob).hexdigest()!=digest:
                raise RangeSourceError("source Parquet SHA256 verification failed")
            local=Path(td)/filename
            local.write_bytes(blob)
            del blob
            stock=filename.removesuffix(".parquet")
            counts,total=dated_inventory(local)  # timestamp-only all-source scan
            inventories[stock]=counts
            if total!=receipt["stock_source_provenance"][stock]["source_rows"]:
                raise PilotError("source metadata row count changed")
            for day,n in receipt["source_counts_by_selected_date"][stock].items():
                if counts.get(day)!=n:
                    raise PilotError("source date inventory changed")
            parts,training=read_audit_35_only(
                local,stock,dates,receipt["source_counts_by_selected_date"][stock]
            )
            for key in all_data:
                all_data[key].extend(parts[key])
            fit.extend(training)
            if file_sha256(local)!=digest:
                raise RangeSourceError("source member mutated during analysis")
            local.unlink()
            print("D013_SOURCE_HASH_OK:",stock,flush=True)

    recreated,_=fresh_selection(inventories)
    if recreated!=dates:
        raise AssertionError("timestamp-only cohort selection no longer reproduces")
    if len(fit)!=54290:
        raise AssertionError("D012 fit eligible row count did not reproduce")
    for stock in STOCKS:
        count=sum(r["matched"] for r in all_data["confirmation"] if r["stock"]==stock)
        if count!=EXPECTED_MATCHED[stock]:
            raise AssertionError("D012 original matched confirmation population changed")

    X=np.asarray([x for x,y in fit],dtype=float)
    y=np.asarray([target for x,target in fit],dtype=int)
    report={}
    for name,weight in (("W_BALANCED","balanced"),("W_UNWEIGHTED",None)):
        pipeline=Pipeline([
            ("scale",StandardScaler()),
            ("logit",LogisticRegression(C=1.0,class_weight=weight,
                solver="lbfgs",max_iter=400,random_state=7007))
        ])
        pipeline.fit(X,y)
        if max(pipeline.named_steps["logit"].n_iter_)>=400:
            raise AssertionError("original D012 logistic regression did not converge")
        classes=tuple(int(v) for v in pipeline.named_steps["logit"].classes_)
        if classes!=(1,2,3):
            raise AssertionError("unexpected class order")

        for part in ("calibration","confirmation"):
            attach_scores(all_data[part],pipeline,get_direction_score,classes)
        cal=all_data["calibration"]
        calrows=[(r["stock"],True) for r in cal if r["ready"]]
        calprobs=[]
        # Generate scorer probabilities in identical original sorted-stock,
        # date-preserving order. Only ready rows, NEVER calibration future targets.
        for r in cal:
            if r["ready"]:
                calprobs.append(r["feature"])
        probabilities=pipeline.predict_proba(np.asarray(calprobs,dtype=float))
        frozen,counts=cutoff_by_stock(calrows,probabilities,classes)
        if len(counts)!=3:
            raise AssertionError("all source stocks require cutoff")
        for stock in STOCKS:
            if format(frozen[stock],".8f")!=D012_CUTOFFS[name][stock]:
                raise AssertionError("D012 published original cutoff did not reproduce")

        grouped={}
        for part in ("calibration","confirmation"):
            full=all_data[part]
            buckets=scope_groups(full)
            # For pooled rows, stock-specific cutoff applied per row.
            grouped[part]={}
            for key,group in buckets.items():
                if key=="pooled":
                    totals=[]
                    for stock in STOCKS:
                        partial=[r for r in group if r["stock"]==stock]
                        totals.append(score_distribution(partial,frozen[stock]))
                    grouped[part][key]={
                        "denominator":sum(g["denominator"] for g in totals),
                        "strict_exceedances":sum(g["strict_exceedances"] for g in totals),
                        "rate":sum(g["strict_exceedances"] for g in totals)/sum(g["denominator"] for g in totals),
                        "per_stock_rule":True}
                else:
                    stock=key.split("@",1)[0]
                    grouped[part][key]={
                        "decision_population":_score_group(group,frozen[stock]),
                        "features_decision_population":feature_distribution(group,lambda r:r["ready"]),
                    }
                    if part=="confirmation":
                        grouped[part][key]["D012_matched_subset"]=_score_group(
                            group,frozen[stock],matched=True
                        )
            if part=="calibration":
                for stock in STOCKS:
                    if grouped[part][stock]["decision_population"]["exceedance_rate"]>0.02+1e-12:
                        raise AssertionError("calibration 2% cutoff violated")
        matched_total=0
        matched_alerts=0
        for stock in STOCKS:
            r=grouped["confirmation"][stock]["D012_matched_subset"]
            matched_total+=r["denominator"]
            matched_alerts+=r["strict_exceedances"]
        if matched_total!=13819 or matched_alerts!=EXPECTED_ALERTS[name]:
            raise AssertionError("original D012 published confirmation counts not reproduced")
        report[name]={
            "published_cutoffs_reproduced_eight_decimal_places":True,
            "frozen_calibration_eligible_per_stock":counts,
            "exact_frozen_cutoffs":frozen,
            "D012_confirmation_matched_reproduction":{
                "matched":matched_total,"alerts":matched_alerts},
            "diagnostics":grouped,
        }

    # Source-only feature distribution on original *fit*-label-eligible rows.
    # Original fit feature statistics are for descriptive comparisons only.
    fit_features={}
    for key,group in scope_groups(all_data["fit"]).items():
        fit_features[key]=feature_distribution(group,lambda r:r["feature"] is not None)

    output={
      "status":"D013 retrospective descriptor, NO fresh validation or model selection",
      "frozen_protocol":"research/SCORE_STABILITY_AUDIT_PROTOCOL.md",
      "source":"Quant-Arena Public L1 / Quant Arena / LaPlace's Eye / Einsia AI",
      "license":"CC BY-NC 4.0 noncommercial attribution",
      "publisher_revision":EXPECTED_REVISION,
      "source_member_sha256":FROZEN_SHA256,
      "date_manifest_sha256":receipt["cohort_date_sha256"],
      "dates_used":{part:dates[part] for part in ("fit","calibration","confirmation")},
      "model_fit_records":len(fit),
      "calibration_target_labels_computed":False,
      "original_D009_final_unscored":True,
      "D012_new_final_unscored":True,
      "raw_quotes_or_row_level_scores_exported":False,
      "no_new_threshold_model_or_feature_selection":True,
      "calibration_vs_confirmation_eligibility_aligned":True,
      "fit_feature_descriptors":fit_features,
      "models":report,
      "no_trading_profits_execution_or_causal_attribution":True
    }
    print("D013_SCORE_STABILITY_AUDIT_BEGIN",flush=True)
    print(json.dumps(output,indent=2,sort_keys=True),flush=True)
    print("D013_SCORE_STABILITY_AUDIT_END",flush=True)


if __name__=="__main__":
    main()
