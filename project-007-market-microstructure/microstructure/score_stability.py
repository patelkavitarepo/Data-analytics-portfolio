"""D013 synthetic-only, target-blind tail/eligibility diagnostic utilities.

No provider IO, model fitting, threshold selection, or final-date access.
Quote rows cluster; summary statistics are descriptive only.
"""
from math import ceil, isfinite

QUANTILES = (0.10, 0.50, 0.90, 0.95, 0.98, 0.99)
FEATURE_NAMES = ("spread_bps", "best_imbalance", "five_level_imbalance")


def higher_quantile(numbers, p):
    """Fixed numpy-"higher" percentile convention used for reporting."""
    if not numbers:
        return None
    if not 0 <= p <= 1:
        raise ValueError("invalid percentile")
    if any(not isfinite(float(v)) for v in numbers):
        raise ValueError("nonfinite source data")
    ordered = sorted(float(v) for v in numbers)
    return ordered[ceil((len(ordered)-1)*p)]


def distribution(numbers):
    numbers = tuple(numbers)
    if not numbers:
        return {"n": 0, "p10": None, "median": None,
                "p90": None, "p95": None, "p98": None, "p99": None,
                "maximum": None}
    return {"n": len(numbers), "p10": higher_quantile(numbers,.10),
            "median": higher_quantile(numbers,.50),
            "p90": higher_quantile(numbers,.90),
            "p95": higher_quantile(numbers,.95),
            "p98": higher_quantile(numbers,.98),
            "p99": higher_quantile(numbers,.99),
            "maximum": max(numbers)}


def feature_distribution(records, selector=lambda r: True):
    features = [r["feature"] for r in records
                if r["feature"] is not None and selector(r)]
    output = {"eligible_rows": len(features)}
    for i, name in enumerate(FEATURE_NAMES):
        values = [f[i] for f in features]
        output[name] = {key: val for key, val in distribution(values).items()
                        if key in ("n","p10","median","p90")}
    return output


def score_distribution(records, cutoff, *, matched=False):
    """Score rows must already be decision-time eligible; match restriction optional.

    No target CLASS is ever consulted. "matched" is a post-outcome
    diagnostic membership bit, not an eligibility decision.
    """
    if not isfinite(float(cutoff)) or cutoff < 0:
        raise ValueError("invalid frozen cutoff")
    eligible = [r for r in records if r["ready"]]
    selected = [r for r in eligible if not matched or r["matched"]]
    scores = [r["score"] for r in selected]
    if any(s is None for s in scores):
        raise ValueError("missing frozen-model score on eligible row")
    alerts = sum(s > cutoff for s in scores)
    return {
        "source_rows_in_group": len(records),
        "book_feature_valid": sum(r["feature"] is not None for r in records),
        "past_history_valid": sum(r["past_covered"] for r in records),
        "decision_time_eligible": len(eligible),
        "target_verifiable_decision_rows": sum(r["matched"] for r in eligible),
        "denominator": len(scores),
        "strict_exceedances": alerts,
        "exceedance_rate": alerts/len(scores) if scores else None,
        "frozen_cutoff": cutoff,
        "distribution": distribution(scores),
        "population": "retrospectively_target_matched" if matched
                      else "current_and_past_only",
    }


def make_rows(stock, raw_days, features, past_covered, phase, matched=None):
    """Build ephemeral audit records without target classes or market prices."""
    n=len(raw_days)
    if len(features)!=n or len(past_covered)!=n or len(phase)!=n:
        raise ValueError("source row dimensions differ")
    if matched is None:
        matched=[False]*n
    if len(matched)!=n:
        raise ValueError("matched dimensions differ")
    records=[]
    previous_day=None
    for d, feature, past, sess, target_ok in zip(
            raw_days, features, past_covered, phase, matched):
        if previous_day is not None and d < previous_day:
            raise ValueError("source day chronology reversed")
        previous_day=d
        if sess not in ("morning","afternoon",None):
            raise ValueError("invalid session")
        if feature is not None and (
                len(feature)!=3 or not all(isfinite(float(v)) for v in feature)):
            raise ValueError("invalid three source features")
        ready = bool(feature is not None and past)
        if target_ok and not ready:
            raise ValueError("target-matched D012 row must have complete past and book")
        records.append({"stock": stock, "day": d, "phase": sess,
                        "feature": feature, "past_covered": bool(past),
                        "ready": ready, "matched": bool(target_ok),
                        "score": None})
    return records


def attach_scores(records, model, get_direction_score, classes):
    """Attach current-row scores; never use targets to select scored rows."""
    valid=[r for r in records if r["ready"]]
    if not valid:
        return
    import numpy as np
    values=np.asarray([r["feature"] for r in valid], dtype=float)
    probabilities=model.predict_proba(values)
    if len(probabilities)!=len(valid):
        raise AssertionError("model/source score dimensions differ")
    for record,proba in zip(valid,probabilities):
        record["score"]=get_direction_score(proba,classes)[0]


def scope_groups(records, *, by_phase=True):
    """Only controlled aggregate groups are suitable for publication."""
    groups={"pooled": records}
    for stock in sorted({r["stock"] for r in records}):
        stock_rows=[r for r in records if r["stock"]==stock]
        groups[stock]=stock_rows
        for day in sorted({r["day"] for r in stock_rows}):
            date_rows=[r for r in stock_rows if r["day"]==day]
            groups[stock+"@"+day]=date_rows
            if by_phase:
                for phase in ("morning","afternoon"):
                    groups[stock+"@"+day+"@"+phase]=[
                        r for r in date_rows if r["phase"]==phase
                    ]
    return groups
