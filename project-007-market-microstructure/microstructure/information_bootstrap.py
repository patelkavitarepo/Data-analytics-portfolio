"""D016 descriptive day-cluster bootstrap; no refitting or market source IO.

Resample entire trading dates with all stocks and both original models paired.
Intervals describe variability of the *mean stock-day AP minus base rate*;
they are NOT pooled AP confidence intervals or independent test evidence.
"""
import random
from math import isfinite

SEED=7007
REPLICATES=2000

def _percentile(values,p):
    values=sorted(values)
    if not values:raise ValueError("empty bootstrap distribution")
    index=(len(values)-1)*p
    low=int(index);high=min(low+1,len(values)-1)
    return values[low]+(values[high]-values[low])*(index-low)

def day_cluster_ap_lift(model_stock_day,seed=SEED,replicates=REPLICATES):
    """Input model->stock->date->audit_stock_day aggregate."""
    if not model_stock_day or type(replicates) is not int or replicates<1:
        raise ValueError("invalid model/day bootstrap input")
    models=sorted(model_stock_day)
    stocks=sorted(next(iter(model_stock_day.values())))
    dates=sorted(next(iter(next(iter(model_stock_day.values())).values())))
    if not stocks or not dates:raise ValueError("empty stocks/dates")
    for model in models:
        if sorted(model_stock_day[model])!=stocks:raise ValueError("stock mismatch")
        for stock in stocks:
            if sorted(model_stock_day[model][stock])!=dates:
                raise ValueError("unpaired date population")
    by_day={}
    for model in models:
        for direction in ("1","3"):
            by_day[(model,direction)]=[]
            for day in dates:
                diffs=[]
                for stock in stocks:
                    x=model_stock_day[model][stock][day]["directions"][direction]
                    ap=x["average_precision"];base=x["base_rate"]
                    if ap is None or base is None or not all(isfinite(v) for v in (ap,base)):
                        raise ValueError("missing/nonfinite stock-day AP or base rate")
                    diffs.append(ap-base)
                by_day[(model,direction)].append(sum(diffs)/len(diffs))
    rng=random.Random(seed)
    draws=[tuple(rng.randrange(len(dates)) for _ in dates)
           for _ in range(replicates)]
    out={}
    for (model,direction),daily in by_day.items():
        observed=sum(daily)/len(daily)
        sampled=[sum(daily[i] for i in indices)/len(indices) for indices in draws]
        out.setdefault(model,{})[direction]={
            "mean_stock_day_ap_minus_base":observed,
            "day_cluster_percentile_95_interval":[
                _percentile(sampled,.025),_percentile(sampled,.975)],
            "n_cluster_days":len(dates),
            "n_stocks_per_day":len(stocks),
            "bootstrap_replicates":replicates,
            "bootstrap_seed":seed,
            "not_pooled_ap":True}
    return out


def paired_model_ap_lift_difference(model_stock_day,first,second,seed=SEED,replicates=REPLICATES):
    """Paired-day bootstrap of (first - second) stock-day AP lift.

    Shared dates and stocks are resampled together. This is descriptive, not
    an independent holdout or a pooled average-precision comparison.
    """
    if first==second or first not in model_stock_day or second not in model_stock_day:
        raise ValueError("require two distinct present models")
    if type(replicates) is not int or replicates<1:
        raise ValueError("invalid replicate count")
    stocks=sorted(model_stock_day[first])
    if not stocks or sorted(model_stock_day[second])!=stocks:
        raise ValueError("unpaired stocks")
    dates=sorted(model_stock_day[first][stocks[0]])
    if not dates:
        raise ValueError("empty dates")
    for model in (first,second):
        for stock in stocks:
            if sorted(model_stock_day[model][stock])!=dates:
                raise ValueError("unpaired calendar")
    rng=random.Random(seed)
    draws=[tuple(rng.randrange(len(dates)) for _ in dates)
           for _ in range(replicates)]
    result={}
    for direction in ("1","3"):
        daily=[]
        for day in dates:
            paired=[]
            for stock in stocks:
                vals=[]
                for model in (first,second):
                    d=model_stock_day[model][stock][day]["directions"][direction]
                    ap=d["average_precision"];base=d["base_rate"]
                    if ap is None or base is None or not all(isfinite(v) for v in (ap,base)):
                        raise ValueError("missing/nonfinite paired AP or prevalence")
                    vals.append(ap-base)
                paired.append(vals[0]-vals[1])
            daily.append(sum(paired)/len(paired))
        sampled=[sum(daily[i] for i in draw)/len(draw) for draw in draws]
        result[direction]={
            "mean_paired_stock_day_ap_lift_difference":sum(daily)/len(daily),
            "day_cluster_percentile_95_interval":[_percentile(sampled,.025),_percentile(sampled,.975)],
            "first_model":first,"second_model":second,
            "n_cluster_days":len(dates),"bootstrap_replicates":replicates,
            "bootstrap_seed":seed,"not_pooled_ap":True}
    return result


def missingness_aware_ap_lift(model_stock_day,seed=SEED,replicates=REPLICATES):
    """Report availability before estimating *complete-day* descriptive AP lift.

    A trading day contributes only when all stocks have finite AP and base rate
    for a model/direction. Never impute undefined AP, silently omit a day, or
    report an interval when fewer than two complete trading days exist.
    Missingness is reported separately for each model/direction.
    """
    if not model_stock_day or type(replicates) is not int or replicates<1:
        raise ValueError("invalid bootstrap input")
    models=sorted(model_stock_day)
    stocks=sorted(model_stock_day[models[0]])
    if not stocks:raise ValueError("no stocks")
    dates=sorted(model_stock_day[models[0]][stocks[0]])
    if not dates:raise ValueError("no dates")
    for model in models:
        if sorted(model_stock_day[model])!=stocks:
            raise ValueError("unpaired stock panel")
        for stock in stocks:
            if sorted(model_stock_day[model][stock])!=dates:
                raise ValueError("unpaired dates")
    output={}
    for model in models:
        output[model]={}
        for direction in ("1","3"):
            usable=[];missing=[]
            for day in dates:
                lifts=[];reasons=[]
                for stock in stocks:
                    metric=model_stock_day[model][stock][day]["directions"][direction]
                    ap=metric["average_precision"];base=metric["base_rate"]
                    if ap is None or base is None:
                        reasons.append({"stock":stock,"reason":"undefined_ap_or_base"})
                    elif not isinstance(ap,(int,float)) or not isinstance(base,(int,float)) or not all(isfinite(v) for v in (ap,base)):
                        reasons.append({"stock":stock,"reason":"nonfinite_ap_or_base"})
                    else:
                        lifts.append(ap-base)
                if reasons:missing.append({"day":day,"unavailable":reasons})
                else:usable.append((day,sum(lifts)/len(stocks)))
            result={"total_days":len(dates),"complete_days":len(usable),
                    "incomplete_days":len(missing),"incomplete_day_details":missing,
                    "stock_day_slots":len(dates)*len(stocks),
                    "unavailable_stock_day_slots":sum(len(x["unavailable"]) for x in missing),
                    "estimand":"mean AP minus matched prevalence across complete three-stock days only",
                    "selection_warning":"Complete-day restriction may bias results; no imputation",
                    "bootstrap_replicates":replicates,"bootstrap_seed":seed,
                    "mean_complete_day_ap_lift":None,
                    "day_cluster_percentile_95_interval":None,
                    "interval_status":"insufficient_complete_days"}
            if len(usable)>=2:
                daily=[v for _,v in usable]
                rng=random.Random(seed)
                draws=[sum(daily[rng.randrange(len(daily))] for _ in daily)/len(daily)
                       for _ in range(replicates)]
                result["mean_complete_day_ap_lift"]=sum(daily)/len(daily)
                result["day_cluster_percentile_95_interval"]=[
                    _percentile(draws,.025),_percentile(draws,.975)]
                result["interval_status"]="descriptive_complete_day_only"
            output[model][direction]=result
    return output
