"""D014: fixed/static vs label-blind rolling score cutoffs, no provider IO.

Only source scores from COMPLETE preceding dates may set a rolling cutoff.
This code never touches future targets or true directions to choose a cutoff.
Neither a 2% budget nor a high model score proves calibrated probability.
"""
from datetime import date
from math import isfinite
from .selective_alerts import frozen_high_quantile,emit_alert

STOCKS=("000012.SZ","000025.SZ","000031.SZ")
ROLLING_DAYS=10
CUTOFF_Q=0.98
BUDGET=0.02
ORIGINAL_CUTOFFS={
    "W_BALANCED":{
        "000012.SZ":1.8813401620922308,
        "000025.SZ":1.7147010499926065,
        "000031.SZ":4.442420213860148,
    },
    "W_UNWEIGHTED":{
        "000012.SZ":0.14798194444582438,
        "000025.SZ":0.1369667126660083,
        "000031.SZ":0.316662917969446,
    },
}


def validate_calendar(warmup, confirmation, sealed):
    """Must not borrow from earlier held-out blocks or first evaluation day."""
    parts=[tuple(x) for x in (warmup,confirmation,sealed)]
    if [len(x) for x in parts]!=[20,10,10]:
        raise ValueError("D014 needs exactly 20/10/10 source days")
    dates=sum((list(x) for x in parts),[])
    if (len(set(dates))!=40 or dates!=sorted(dates)
            or dates[0]<="2022-05-16"):
        raise ValueError("new D014 calendar must be strictly after sealed D012")
    for d in dates:
        if date.fromisoformat(d).isoformat()!=d:
            raise ValueError("noncanonical source day")
    return tuple(parts)


def _check_scores(values):
    values=tuple(float(x) for x in values)
    if not values or any((not isfinite(x) or x<0) for x in values):
        raise ValueError("each day must have valid nonnegative scores")
    return values


def rolling_cutoff_before_day(past_day_scores, decision_day):
    """Input is a strictly ordered historical sequence, never current day.

    All last 10 days are required; no date-level future or same-date peeking.
    """
    if len(past_day_scores)<ROLLING_DAYS:
        raise ValueError("need ten complete preceding dates")
    selected=past_day_scores[-ROLLING_DAYS:]
    preceding=None
    all_scores=[]
    for day, scores in selected:
        if date.fromisoformat(day).isoformat()!=day:
            raise ValueError("invalid date")
        if day>=decision_day or preceding is not None and day<=preceding:
            raise ValueError("rolling calibration cannot use current/future scores")
        preceding=day
        all_scores.extend(_check_scores(scores))
    return frozen_high_quantile(all_scores)


def daily_threshold_replay(warmup, confirmation, by_day, fixed_cutoff):
    """Replay both policies without true targets; fully sealed days prohibited.

    Values in by_day are ordered (score, direction) for past/current origins.
    Each confirmation day is first scored against a cutoff derived ONLY from
    earlier complete days; its scores enter history *after* decisions.
    """
    warmup=tuple(warmup); confirmation=tuple(confirmation)
    if len(warmup)!=20 or len(confirmation)!=10:
        raise ValueError("frozen D014 20 warmup / 10 confirm required")
    if (list(warmup)+list(confirmation)!=sorted(set(warmup+confirmation))
            or warmup[0]<="2022-05-16"):
        raise ValueError("D014 day order or source exclusivity violated")
    if set(by_day)!=set(warmup+confirmation):
        raise ValueError("scores include missing, extra, or sealed dates")
    if not isfinite(fixed_cutoff) or fixed_cutoff<0:
        raise ValueError("bad original D012 cutoff")
    history=[]
    for d in warmup:
        row_values=by_day[d]
        _check_scores(score for score, side in row_values)
        if any(side not in (1,3) for score,side in row_values):
            raise ValueError("direction must be up or down")
        history.append((d,tuple(score for score,side in row_values)))
    result={}
    for d in confirmation:
        adaptive=rolling_cutoff_before_day(history,d)
        pairs=tuple(by_day[d])
        _check_scores(score for score, side in pairs)
        if any(side not in (1,3) for score,side in pairs):
            raise ValueError("direction must be up or down")
        fixed_signals=tuple(emit_alert(score,side,fixed_cutoff)
                            for score,side in pairs)
        rolling_signals=tuple(emit_alert(score,side,adaptive)
                              for score,side in pairs)
        result[d]={
            "static_cutoff":fixed_cutoff,
            "rolling_cutoff":adaptive,
            "source_decisions":len(pairs),
            "static":fixed_signals,
            "rolling":rolling_signals,
        }
        # Never use any target; only now-completed day's current/past-only scores.
        history.append((d,tuple(score for score,side in pairs)))
    return result


def labelled_alert_metrics(actual, predicted, *, false_cost=4):
    """Abstention stays distinct from an actual stationary label."""
    actual=tuple(actual); predicted=tuple(predicted)
    if len(actual)!=len(predicted):
        raise ValueError("prediction/target count mismatch")
    if any(v not in (1,2,3) for v in actual):
        raise ValueError("need real future targets only for retrospective scoring")
    if any(v not in (None,1,3) for v in predicted):
        raise ValueError("no-alert is abstention only")
    up=sum(v==1 for v in actual)
    down=sum(v==3 for v in actual)
    ok=sum(v==y for v,y in zip(predicted,actual) if v is not None)
    alerts=sum(v is not None for v in predicted)
    mistakes=alerts-ok
    detected_up=sum(v==1 and y==1 for v,y in zip(predicted,actual))
    detected_down=sum(v==3 and y==3 for v,y in zip(predicted,actual))
    if false_cost<0:
        raise ValueError("negative hypothetical loss")
    return {
        "matched_n":len(actual),
        "alerts":alerts,
        "correct":ok,
        "false":mistakes,
        "abstain":len(actual)-alerts,
        "precision":ok/alerts if alerts else None,
        "false_per_1000":1000*mistakes/len(actual) if actual else None,
        "up_support":up,"down_support":down,
        "up_recall":detected_up/up if up else None,
        "down_recall":detected_down/down if down else None,
        "utility_units":ok-false_cost*mistakes,
    }


def cluster_bootstrap_day_sums(per_day, *, iterations=2000, seed=7007):
    """Resample full common dates (all 3 stocks together), not quote rows.

    Each day contains aggregate correct/false counts from all stocks on the
    same originally-matched source population.
    """
    from random import Random
    if len(per_day)!=10 or iterations!=2000 or seed!=7007:
        raise ValueError("frozen ten-day 2000-iteration bootstrap only")
    data=tuple(per_day)
    if any(c<0 or f<0 or n<0 or c+f>n for c,f,n in data):
        raise ValueError("invalid day aggregate")
    random=Random(seed)
    values=[]
    precisions=[]
    for _ in range(iterations):
        chosen=[data[random.randrange(10)] for i in range(10)]
        correct=sum(item[0] for item in chosen)
        false=sum(item[1] for item in chosen)
        values.append(correct-4*false)
        if correct+false:
            precisions.append(correct/(correct+false))
    def nearest_quantile(xs,q):
        if not xs:return None
        return sorted(xs)[round((len(xs)-1)*q)]
    return {
        "resampling_unit":"common trading day, three stocks together",
        "replications":iterations,"seed":seed,
        "utility_units_q025":nearest_quantile(values,.025),
        "utility_units_q975":nearest_quantile(values,.975),
        "precision_q025":nearest_quantile(precisions,.025),
        "precision_q975":nearest_quantile(precisions,.975),
        "caveat":"Only ten clustered dates; descriptive interval, not evidence of independent markets."
    }
