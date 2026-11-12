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
