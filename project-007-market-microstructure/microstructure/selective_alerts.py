"""D012: past-only selective directional alerts, with *unlabelled* calibration.

Scores are model outputs, not independently calibrated probabilities or alpha.
A no-alert outcome is abstention, NOT evidence that price stays stationary.
This module has no data download, provider quote IO, or model fitting.
"""
from collections import Counter
from datetime import timedelta
from math import ceil, isfinite
from .chronological_baselines import continuous_phase, _valid, _confusion, PERMITTED
from .stockday_labels import Quote

GAP=timedelta(seconds=30)
HISTORY=5
BUDGET=0.02


def source_past5_coverage(quotes):
    """Current/past-only history gate; does NOT compute future targets."""
    rows=tuple(quotes)
    allowed=[]
    previous_key=None
    run_start=0
    for i,q in enumerate(rows):
        if not isinstance(q,Quote) or not q.symbol or q.available_at.date().isoformat()!=q.trading_date:
            raise ValueError(f"malformed quote/source date at index {i}")
        key=(q.trading_date,q.symbol,q.available_at)
        if previous_key is not None and key<=previous_key:
            raise ValueError("quote availability not strictly increasing")
        previous_key=key
        phase=continuous_phase(q.available_at)
        if phase is None or not _valid(q):
            allowed.append(False)
            run_start=i+1
            continue
        if i>run_start:
            prior=rows[i-1]
            if (q.symbol!=prior.symbol or q.trading_date!=prior.trading_date
                    or phase!=continuous_phase(prior.available_at)
                    or q.available_at-prior.available_at>GAP):
                run_start=i
        allowed.append(i-run_start>=HISTORY)
    return tuple(allowed)


def get_direction_score(probability,classes):
    """Return (score, direction) using only a current-row probability vector."""
    if len(probability)!=3 or tuple(map(int,classes))!=(1,2,3):
        raise ValueError("three-class probability order 1,2,3 required")
    up,stationary,down=map(float,probability)
    if (not all(isfinite(v) and 0<=v<=1 for v in (up,stationary,down))
            or abs(up+stationary+down-1)>1e-6):
        raise ValueError("malformed model probabilities")
    return max(up,down)/(stationary+1e-12), (1 if up>=down else 3)


def frozen_high_quantile(scores,q=0.98):
    """Deterministic 98th percentile 'higher' with strict > to break ties safely."""
    if not isinstance(scores,(tuple,list)) or not scores:
        raise ValueError("calibration score list must be nonempty")
    if q!=0.98:
        raise ValueError("D012 only authorizes frozen 2 percent alert budget")
    if any(not isfinite(float(value)) or float(value)<0 for value in scores):
        raise ValueError("invalid calibration scores")
    ordered=sorted(float(value) for value in scores)
    position=ceil((len(ordered)-1)*q)
    return ordered[position]


def cutoff_by_stock(rows,probabilities,classes):
    """Calibrate on pairs (stock, accepted_now_and_past) WITHOUT any target.

    rows contains ONLY stock identity, source-only readiness; no labels, target
    class, future target indices or true outcomes are ever required or used.
    """
    if len(rows)!=len(probabilities):
        raise ValueError("source rows and model outputs differ")
    per_stock={}
    for (symbol,ready),prob in zip(rows,probabilities):
        if ready:
            score,_=get_direction_score(prob,classes)
            per_stock.setdefault(symbol,[]).append(score)
    if set(per_stock)!={"000012.SZ","000025.SZ","000031.SZ"}:
        raise ValueError("frozen three stocks lack calibration features/history")
    thresholds={sym:frozen_high_quantile(per_stock[sym]) for sym in sorted(per_stock)}
    counts={sym:len(per_stock[sym]) for sym in sorted(per_stock)}
    return thresholds,counts


def emit_alert(score,direction,cutoff):
    """At decision time, alert if score STRICTLY exceeds frozen cutoff."""
    if not isfinite(float(score)) or not isfinite(float(cutoff)):
        raise ValueError("nonfinite score/cutoff")
    if direction not in (1,3):
        raise ValueError("alert only up or down")
    return direction if score>cutoff else None


def alert_report(examples,predictions,reference_majority):
    """Same-origin retrospective diagnostics (no-alert is NOT a class label)."""
    if len(examples)!=len(predictions):
        raise ValueError("mismatched labels and decision count")
    if not examples:
        raise ValueError("zero eligible confirmation examples")
    if any(e.target not in PERMITTED for e in examples):
        raise ValueError("confirmation must have known future target for scoring")
    if reference_majority not in PERMITTED:
        raise ValueError("invalid fit-only majority class")
    n=len(examples)
    choices=[]
    for result in predictions:
        if result is not None and result not in (1,3):
            raise ValueError("invalid directional alert class")
        choices.append(result)
    nalert=sum(v is not None for v in choices)
    good=sum(v==e.target for e,v in zip(examples,choices) if v is not None)
    bad=nalert-good
    class_counts=Counter(e.target for e in examples)
    up_true,down_true=class_counts[1],class_counts[3]
    got_up=sum(v==1 and e.target==1 for e,v in zip(examples,choices))
    got_down=sum(v==3 and e.target==3 for e,v in zip(examples,choices))
    # Classifying no-alert as 2 is only an artificial diagnostic proxy.
    proxy={e.row_index:(v if v is not None else 2)
           for e,v in zip(examples,choices)}
    if len(proxy)!=len(examples):
        raise ValueError("source-origin index must be unique per scored stock/date group")
    threeclass=_confusion(examples,lambda e:proxy[e.row_index])
    return {
        "eligible":n,"directional_alerts":nalert,
        "true_direction_alerts":good,"false_direction_alerts":bad,
        "alert_rate_per_1000":1000*nalert/n,
        "false_alerts_per_1000":1000*bad/n,
        "directional_precision":good/nalert if nalert else None,
        "up_recall":got_up/up_true if up_true else None,
        "down_recall":got_down/down_true if down_true else None,
        "up_true_support":up_true,"down_true_support":down_true,
        "no_alert_count":n-nalert,
        "note":"No-alert is abstention, not proof of stationary. Three-class proxy maps no-alert to stationary only for comparison.",
        "no_alert_as_stationary_three_class_PROXY":threeclass,
    }
