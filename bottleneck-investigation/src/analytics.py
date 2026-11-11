"""Cohort metrics from additive counts; administrative closure is not resolution."""

import math
import numpy as np
import pandas as pd

DIMENSIONS = ["created_date", "category", "agency", "neighborhood"]
COUNTS = ["requests", "eligible7", "closed7", "eligible30", "closed30", "closed_valid"]


def aggregate(records, as_of):
    d = records.copy()
    cutoff = pd.Timestamp(as_of)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    age = (cutoff - d.created_at).dt.total_seconds() / 86400
    elapsed = (d.closed_at - d.created_at).dt.total_seconds() / 86400
    valid = (
        d.status.eq("closed")
        & elapsed.ge(0)
        & d.closed_at.le(cutoff)
        & ~d.get("timestamp_uncertain", pd.Series(False, index=d.index))
    )
    d["created_date"] = d.created_at.dt.tz_convert("America/Los_Angeles").dt.strftime(
        "%Y-%m-%d"
    )
    d["duration_day"] = np.where(valid, np.floor(elapsed.fillna(-1)), -1).astype(int)
    d["requests"] = 1
    d["closed_valid"] = valid.astype(int)
    for h in [7, 30]:
        d[f"eligible{h}"] = age.ge(h).astype(int)
        d[f"closed{h}"] = (age.ge(h) & valid & elapsed.le(h)).astype(int)
    return (
        d.groupby(DIMENSIONS + ["duration_day"], dropna=False)[COUNTS]
        .sum()
        .reset_index()
    )


def weighted_quantile(d, q):
    h = d[d.duration_day.ge(0)].groupby("duration_day").closed_valid.sum().sort_index()
    if h.sum() == 0:
        return float("nan")
    return float(h.index[h.cumsum().ge(math.ceil(q * h.sum()))][0])


def metrics(d):
    n = d[COUNTS].sum()
    return {
        **n.to_dict(),
        "rate7": n.closed7 / n.eligible7 if n.eligible7 else float("nan"),
        "rate30": n.closed30 / n.eligible30 if n.eligible30 else float("nan"),
        "median_days": weighted_quantile(d, 0.5),
        "p90_days": weighted_quantile(d, 0.9),
    }


def summary(d, keys):
    if d.empty:
        return pd.DataFrame(columns=keys + list(metrics(d)))
    return pd.DataFrame(
        [
            {**dict(zip(keys, k if isinstance(k, tuple) else (k,))), **metrics(g)}
            for k, g in d.groupby(keys, dropna=False)
        ]
    )


def adjusted(d, unit="agency", minimum=30):
    """Within month/category, compare a unit with all OTHER units. Local mix weights."""
    d = d.assign(month=d.created_date.str[:7])
    cells = (
        d.groupby(["month", "category", unit])[["eligible30", "closed30"]]
        .sum()
        .reset_index()
    )
    totals = cells.groupby(["month", "category"])[["eligible30", "closed30"]].transform(
        "sum"
    )
    cells["peer_n"] = totals.eligible30 - cells.eligible30
    cells["peer_closed"] = totals.closed30 - cells.closed30
    cells = cells[(cells.eligible30 >= minimum) & (cells.peer_n >= minimum)].copy()
    cells["rate30"] = cells.closed30 / cells.eligible30
    cells["peer_rate30"] = cells.peer_closed / cells.peer_n
    cells["gap_pp"] = 100 * (cells.rate30 - cells.peer_rate30)
    return cells


def persistent(d, threshold=10, unit="agency", minimum=30):
    cells = adjusted(d, unit, minimum)
    output = []
    for (name, category), g in cells.groupby([unit, "category"]):
        months = len(g)
        bad = int(g.gap_pp.le(-threshold).sum())
        n = int(g.eligible30.sum())
        output.append(
            {
                unit: name,
                "category": category,
                "months": months,
                "comparable_requests": n,
                "qualifying_months": bad,
                "gap_pp": np.average(g.gap_pp, weights=g.eligible30),
                "candidate": months >= 3
                and n >= 90
                and bad >= max(2, math.ceil(months / 2)),
            }
        )
    return pd.DataFrame(
        output,
        columns=[
            unit,
            "category",
            "months",
            "comparable_requests",
            "qualifying_months",
            "gap_pp",
            "candidate",
        ],
    )
