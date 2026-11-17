"""Case 016 source-origin audit joins; no vendor access, no model fitting."""
from .information_audit import prevalence,average_precision,calibration,descriptive_top_fraction

def audit_stock_day(up_prob,down_prob,labels,feature_ready):
    """All arrays aligned to source-origin index; unknown truth stays unknown."""
    up_prob=tuple(up_prob);down_prob=tuple(down_prob)
    labels=tuple(labels);feature_ready=tuple(feature_ready)
    n=len(labels)
    if not(len(up_prob)==len(down_prob)==len(feature_ready)==n):
        raise ValueError("source-origin alignment mismatch")
    if any(type(x) is not bool for x in feature_ready):
        raise ValueError("feature readiness must be Boolean")
    if any((a is None)!=(b is None) for a,b in zip(up_prob,down_prob)):
        raise ValueError("up/down probability missingness differs")
    if any((a is not None)!=ready for a,ready in zip(up_prob,feature_ready)):
        raise ValueError("source-only feature readiness disagrees with score availability")
    if any(a is not None and (a+b>1+1e-8) for a,b in zip(up_prob,down_prob)):
        raise ValueError("direction probabilities exceed unit mass")
    population=prevalence(labels)
    ready_labels=tuple(y for y,ok in zip(labels,feature_ready) if ok)
    available=prevalence(ready_labels)
    if population["source_n"]!=n or available["source_n"]!=sum(feature_ready):
        raise AssertionError("lost source origins")
    directions={}
    for direction,prob in ((1,up_prob),(3,down_prob)):
        matched=[(p,y) for p,y in zip(prob,labels) if p is not None and y is not None]
        support=sum(y==direction for _,y in matched)
        directions[str(direction)]={
            "matched_n":len(matched),"positive_support":support,
            "base_rate":support/len(matched) if matched else None,
            "average_precision":average_precision(prob,labels,direction),
            "calibration":calibration(prob,labels,direction),
            "descriptive_top_fraction":{
                str(f):descriptive_top_fraction(prob,labels,direction,f)
                for f in (.01,.02,.05)}
        }
    return {"all_source":population,"feature_ready":available,
            "current_unavailable_n":n-available["source_n"],
            "future_label_unverifiable_n":population["unknown_n"],
            "directions":directions,
            "not_an_executable_policy":True}
