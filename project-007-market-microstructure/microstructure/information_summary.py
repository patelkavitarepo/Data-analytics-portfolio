"""Aggregate Case 016 day-level reports without pretending mean AP is pooled AP.

No source data access. In particular, AP cannot be reconstructed exactly from
per-stock-day AP summaries; pooled ranking requires origin-level scores.
"""
from math import isfinite

def summarize_information_days(daily_by_stock, direction):
    key=str(direction)
    if direction not in (1,3):
        raise ValueError("direction must be 1 or 3")
    if not daily_by_stock:
        raise ValueError("no stock/day observations")
    source=ready=verifiable=matched=positive=0
    weighted_brier=0.
    per_day=[]
    for stock,days in sorted(daily_by_stock.items()):
        if not days:raise ValueError("stock has no dates")
        for day,entry in sorted(days.items()):
            whole=entry["all_source"]
            current=entry["feature_ready"]
            metric=entry["directions"][key]
            n=whole["source_n"]
            r=current["source_n"]
            m=metric["matched_n"]
            if not(0<=m<=r<=n) or current["verifiable_n"]!=m:
                raise ValueError("origin or matched-label denominators inconsistent")
            if whole["verifiable_n"]<m or whole["verifiable_n"]>n:
                raise ValueError("future-verifiability denominator inconsistent")
            support=metric["positive_support"]
            if not 0<=support<=m:raise ValueError("positive support inconsistent")
            brier=metric["calibration"]["brier"]
            if m and (brier is None or not isfinite(brier) or not 0<=brier<=1):
                raise ValueError("missing/invalid Brier")
            if not m and brier is not None:raise ValueError("empty Brier must be null")
            source+=n;ready+=r;verifiable+=whole["verifiable_n"]
            matched+=m;positive+=support
            weighted_brier+=m*(brier or 0)
            per_day.append({"stock":stock,"day":day,"matched_n":m,
                            "positive_support":support,
                            "base_rate":support/m if m else None,
                            "average_precision":metric["average_precision"],
                            "brier":brier})
    return {"source_n":source,"current_feature_ready_n":ready,
            "future_label_verifiable_n":verifiable,
            "matched_n":matched,"positive_support":positive,
            "matched_base_rate":positive/matched if matched else None,
            "matched_weighted_brier":weighted_brier/matched if matched else None,
            "per_stock_day":per_day,
            "pooled_average_precision":None,
            "pooled_AP_note":"Not identifiable from per-stock/day AP aggregates; no pooled AP claim.",
            "not_a_trading_strategy":True}
