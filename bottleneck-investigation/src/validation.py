"""Fail closed on ambiguous identity and cohort membership; retain other quality issues."""

import pandas as pd

REQUIRED = [
    "request_id",
    "created_at",
    "closed_at",
    "status",
    "category",
    "agency",
    "neighborhood",
]


def normalize(raw, mapping):
    missing = set(mapping.values()) - set(raw.columns)
    if missing:
        raise ValueError(f"Source schema missing fields: {sorted(missing)}")
    parse_issues = {}
    d = raw.rename(columns={v: k for k, v in mapping.items()})[REQUIRED].copy()
    for name in ["created_at", "closed_at"]:
        # DataSF floating timestamps are San Francisco local time.
        values = pd.to_datetime(d[name], errors="coerce", format="ISO8601")
        parse_issues[name] = int((d[name].notna() & values.isna()).sum())
        d[name] = values.dt.tz_localize(
            "America/Los_Angeles", ambiguous="NaT", nonexistent="NaT"
        ).dt.tz_convert("UTC")
    d["status"] = d.status.fillna("unknown").astype(str).str.strip().str.lower()
    for name in ["category", "agency", "neighborhood"]:
        d[name] = (
            d[name].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
        )
    d.attrs["timestamp_parse_failures"] = parse_issues
    return d


def validate(d, as_of):
    cutoff = pd.Timestamp(as_of)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    report = {
        "timestamp_parse_failures": d.attrs.get("timestamp_parse_failures", {}),
        "rows": len(d),
        "missing_ids": int(d.request_id.isna().sum() + d.request_id.eq("").sum()),
        "duplicate_ids": int(d.request_id.duplicated().sum()),
        "missing_created": int(d.created_at.isna().sum()),
        "negative_duration": int((d.closed_at < d.created_at).sum()),
        "future_created": int((d.created_at > cutoff).sum()),
        "future_closed": int((d.closed_at > cutoff).sum()),
        "closed_without_date": int((d.status.eq("closed") & d.closed_at.isna()).sum()),
        "nonclosed_with_date": int(
            (~d.status.eq("closed") & d.closed_at.notna()).sum()
        ),
        "unknown_status": int((~d.status.isin(["open", "closed"])).sum()),
        "missing_dimensions": {
            c: int(d[c].eq("Unknown").sum())
            for c in ["agency", "category", "neighborhood"]
        },
    }
    if any(
        report[k]
        for k in ["missing_ids", "duplicate_ids", "missing_created", "future_created"]
    ):
        raise ValueError(f"Identity/cohort validation failed: {report}")
    return report
