"""D015 availability-aware abstention policies; pure and provider-free.

No targets or current-day future observations enter decisions or cutoffs.
"""
from math import isfinite
from datetime import date
from .adaptive_alerts import ORIGINAL_CUTOFFS, STOCKS
from .selective_alerts import frozen_high_quantile

LOOKBACK=10
MIN_SOURCE_COVERAGE=.50
STATUSES=("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY",
          "NO_SIGNAL","ALERT_UP","ALERT_DOWN")
POLICIES=("STATIC_BASELINE","STATIC_HEALTH","ROLLING_HEALTH")


def freeze_calendar(warmup,confirmation,sealed):
    parts=(tuple(warmup),tuple(confirmation),tuple(sealed))
    if tuple(map(len,parts))!=(20,10,10):
        raise ValueError("D015 requires exactly 20/10/10 observed common dates")
    all_days=sum((list(x) for x in parts),[])
    if len(set(all_days))!=40 or all_days!=sorted(all_days) or all_days[0]<="2022-07-12":
        raise ValueError("D015 must be new and strictly after D014 final")
    for d in all_days:
        if date.fromisoformat(d).isoformat()!=d:
            raise ValueError("noncanonical source date")
    return parts


def _validated_day(day, scores, source_n):
    if date.fromisoformat(day).isoformat()!=day or not isinstance(source_n,int) or source_n<=0:
        raise ValueError("invalid source calendar day or source count")
    if len(scores)!=source_n:
        raise ValueError("must account for every source origin")
    eligible=[]
    for x in scores:
        if x is None:continue
        if (not isinstance(x,tuple) or len(x)!=2
                or not isfinite(x[0]) or x[0]<0 or x[1] not in (1,3)):
            raise ValueError("invalid score/direction; missing origin must be None")
        eligible.append(float(x[0]))
    return tuple(eligible)


def historical_gate(history,decision_day):
    """All immediately preceding ten observed common days, including bad ones.

    Return (healthy, cutoff or None, coverage metadata); no current day read.
    """
    if len(history)<LOOKBACK:
        raise ValueError("ten past observed common days required")
    last=history[-LOOKBACK:]
    prev=None
    scores=[]
    coverages=[]
    for d,items,source_n in last:
        if d>=decision_day or prev is not None and d<=prev:
            raise ValueError("same-day or future leakage in history")
        valid=_validated_day(d,items,source_n)
        coverages.append(len(valid)/source_n)
        scores.extend(valid)
        prev=d
    healthy=all(v>=MIN_SOURCE_COVERAGE for v in coverages)
    return (healthy,frozen_high_quantile(scores) if healthy else None,
            {"past_days":tuple(d for d,_,_ in last),
             "past_coverage":tuple(coverages),
             "minimum_past_coverage":min(coverages)})


def replay(warmup,confirmation,sealed,source_by_day,stock,model):
    """Source origins include invalid rows as None. No target input possible.

    For each day: first compute history gate; then classify each current origin;
    only AFTER completing that day, append its source-only scores to history.
    """
    freeze_calendar(warmup,confirmation,sealed)
    if stock not in STOCKS or model not in ORIGINAL_CUTOFFS:
        raise ValueError("original model/stock panel only")
    allowed=tuple(warmup)+tuple(confirmation)
    if set(source_by_day)!=set(allowed):
        raise ValueError("missing, extra or sealed source date")
    history=[]
    for d in warmup:
        items=tuple(source_by_day[d])
        _validated_day(d,items,len(items))
        history.append((d,items,len(items)))
    result={}
    fixed=ORIGINAL_CUTOFFS[model][stock]
    for d in confirmation:
        healthy,rolling,metadata=historical_gate(history,d)
        items=tuple(source_by_day[d])
        _validated_day(d,items,len(items))
        day={}
        for policy in POLICIES:
            cutoff=rolling if policy=="ROLLING_HEALTH" else fixed
            states=[]
            for x in items:
                if x is None:
                    state="DATA_UNAVAILABLE_CURRENT"
                elif policy!="STATIC_BASELINE" and not healthy:
                    state="DATA_UNAVAILABLE_HISTORY"
                elif x[0]>cutoff:
                    state="ALERT_UP" if x[1]==1 else "ALERT_DOWN"
                else:
                    state="NO_SIGNAL"
                states.append(state)
            if any(s not in STATUSES for s in states):
                raise AssertionError("unknown D015 decision state")
            day[policy]={"statuses":tuple(states),
                         "cutoff":cutoff,
                         "source_n":len(items),
                         "history_healthy":healthy if policy!="STATIC_BASELINE" else None}
        day["historical_source_coverage"]=metadata
        result[d]=day
        history.append((d,items,len(items)))
    return result


def aggregate_states(states):
    states=tuple(states)
    if any(x not in STATUSES for x in states):
        raise ValueError("unknown state")
    counts={k:states.count(k) for k in STATUSES}
    if sum(counts.values())!=len(states):
        raise AssertionError("all source origins must be represented")
    n=len(states)
    alerts=counts["ALERT_UP"]+counts["ALERT_DOWN"]
    capable=counts["NO_SIGNAL"]+alerts
    return {"source_n":n,"counts":counts,"alerts":alerts,
            "capable":capable,
            "alert_rate_all_source":alerts/n if n else None,
            "alert_rate_capable":alerts/capable if capable else None,
            "source_unavailable_rate":(counts["DATA_UNAVAILABLE_CURRENT"]+
                counts["DATA_UNAVAILABLE_HISTORY"])/n if n else None}


def matched_outcomes(statuses,actual):
    """Only verifiable future labels, never treat unknown as stationary."""
    statuses=tuple(statuses);actual=tuple(actual)
    if len(statuses)!=len(actual):
        raise ValueError("unaligned origin population")
    if any(s not in STATUSES for s in statuses):
        raise ValueError("unknown status")
    if any(y not in (None,1,2,3) for y in actual):
        raise ValueError("bad or fabricated future label")
    paired=[(s,y) for s,y in zip(statuses,actual) if y is not None]
    correct=sum((s=="ALERT_UP" and y==1) or (s=="ALERT_DOWN" and y==3) for s,y in paired)
    alert=sum(s in ("ALERT_UP","ALERT_DOWN") for s,y in paired)
    wrong=alert-correct
    return {"matched_n":len(paired),"correct":correct,"wrong":wrong,
            "alerts":alert,"precision":correct/alert if alert else None,
            "hypothetical_4to1_units":correct-4*wrong,
            "hypothetical_1to1_units":correct-wrong,
            "hypothetical_9to1_units":correct-9*wrong,
            "up_support":sum(y==1 for _,y in paired),
            "down_support":sum(y==3 for _,y in paired),
            "up_detected":sum(s=="ALERT_UP" and y==1 for s,y in paired),
            "down_detected":sum(s=="ALERT_DOWN" and y==3 for s,y in paired),
            "directional_movement_unavailable":sum(
                s in ("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY")
                and y in (1,3) for s,y in paired),
            "future_label_unknown_n":len(actual)-len(paired)}
