"""Run: python -m src.ingest. No token, billing project, or raw records committed."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests
from src.analytics import aggregate
from src.validation import normalize, validate

BASE = "https://data.sfgov.org"
DATASET = (
    "vw6y-z8j6"  # candidate ID; metadata and fields must pass verification at runtime
)
MAPPING = {
    "request_id": "service_request_id",
    "created_at": "requested_datetime",
    "closed_at": "closed_date",
    "status": "status_description",
    "category": "service_name",
    "agency": "responsible_agency",
    "neighborhood": "neighborhoods_sffind_boundaries",
}
WHERE = "requested_datetime >= '2025-01-01T00:00:00' AND requested_datetime < '2026-01-01T00:00:00'"


def get(session, url, params=None):
    response = session.get(url, params=params, timeout=120)
    response.raise_for_status()
    return response.json()


def extract(folder, page_size=10000):
    folder = Path(folder)
    session = requests.Session()
    start = datetime.now(timezone.utc).isoformat()
    metadata_url = f"{BASE}/api/views/{DATASET}.json"
    meta = get(session, metadata_url)
    fields = {c["fieldName"] for c in meta["columns"]}
    if not set(MAPPING.values()).issubset(fields):
        raise ValueError(
            f"Schema differs; inspect metadata and revise mapping: {sorted(fields)}"
        )
    if "311" not in meta.get("name", ""):
        raise ValueError("Dataset identity not verified")
    url = f"{BASE}/resource/{DATASET}.json"
    count_query = {"$select": "count(*) as n", "$where": WHERE}
    expected = int(get(session, url, count_query)[0]["n"])
    pages, offset = [], 0
    while offset < expected:
        rows = get(
            session,
            url,
            {
                "$select": ",".join(MAPPING.values()),
                "$where": WHERE,
                "$order": "service_request_id",
                "$limit": page_size,
                "$offset": offset,
            },
        )
        if not rows:
            raise ValueError("Extraction ended before expected source count")
        pages.extend(rows)
        offset += len(rows)
    after = get(session, metadata_url)
    count_after = int(get(session, url, count_query)[0]["n"])
    if (
        expected != count_after
        or len(pages) != expected
        or meta.get("rowsUpdatedAt") != after.get("rowsUpdatedAt")
    ):
        raise ValueError(
            "Source changed during extraction; retry for a stable snapshot"
        )
    if not expected:
        raise ValueError("No source records; verified bundle not published")
    raw = pd.DataFrame(pages).reindex(columns=list(MAPPING.values()))
    d = normalize(raw, MAPPING)
    end = datetime.now(timezone.utc).isoformat()
    quality = validate(d, end)
    # Verify local calendar-year scope independently of the source predicate.
    local = d.created_at.dt.tz_convert("America/Los_Angeles")
    if not local.dt.year.eq(2025).all():
        raise ValueError("Out-of-scope cohort")
    cube = aggregate(d, end)
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / "cube.parquet.tmp"
    cube.to_parquet(temp, index=False)
    provenance = {
        "status": "verified_public_extract",
        "synthetic": False,
        "source_url": url,
        "metadata_url": metadata_url,
        "dataset_title": meta["name"],
        "mapping": MAPPING,
        "source_columns": sorted(fields),
        "source_rows_updated_at": meta.get("rowsUpdatedAt"),
        "extraction_started_at": start,
        "extracted_at": end,
        "as_of": end,
        "cohort": "2025 local San Francisco calendar year",
        "rows": expected,
        "source_count_before": expected,
        "source_count_after": count_after,
        "completeness": "Count-reconciled stable API extraction; not proof all service events were reported.",
        "quality": quality,
        "sha256": hashlib.sha256(temp.read_bytes()).hexdigest(),
        "limitations": [
            "Current snapshot; historical status transitions unavailable.",
            "Administrative closure does not confirm resolution.",
            "Repeated category reports do not identify repeat failures at a location.",
            "Duration quantiles use floored elapsed-day bins; error is less than one day.",
        ],
    }
    # Metadata published last: interrupted refreshes fail hash verification.
    temp.replace(folder / "cube.parquet")
    pending = folder / "provenance.json.tmp"
    pending.write_text(json.dumps(provenance, indent=2) + "\n")
    pending.replace(folder / "provenance.json")
    return provenance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "data"
    )
    args = parser.parse_args()
    print(json.dumps(extract(args.output), indent=2))
