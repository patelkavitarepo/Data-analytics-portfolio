"""Page-bounded public acquisition; review artifacts only, never raw-record output."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.analytics import aggregate, COUNTS, DIMENSIONS
from src.validation import normalize, validate
from src.probe import BASE, DATASET, WHERE

MAPPING = {
    "request_id": "service_request_id",
    "created_at": "requested_datetime",
    "closed_at": "closed_date",
    "status": "status_description",
    "category": "service_name",
    "agency": "agency_responsible",
    "neighborhood": "neighborhoods_sffind_boundaries",
}
EXPECTED_TYPES = {
    "service_request_id": "number",
    "requested_datetime": "calendar_date",
    "closed_date": "calendar_date",
    "status_description": "text",
    "service_name": "text",
    "agency_responsible": "text",
    "neighborhoods_sffind_boundaries": "text",
}


def get(session, url, params=None):
    response = session.get(url, params=params, timeout=(15, 120))
    print(
        json.dumps(
            {
                "event": "http",
                "endpoint": "metadata" if "/api/views/" in url else "query",
                "status_code": response.status_code,
            }
        ),
        flush=True,
    )
    response.raise_for_status()
    return response.json()


def verify_metadata(meta):
    fields = {c["fieldName"]: c for c in meta.get("columns", [])}
    if meta.get("id") != DATASET or meta.get("name") != "311 Cases":
        raise ValueError(
            "Dataset identity not verified: expected official vw6y-z8j6 / 311 Cases"
        )
    for name, expected in EXPECTED_TYPES.items():
        if name not in fields or fields[name].get("dataTypeName") != expected:
            raise ValueError(f"Source schema differs for {name}; expected {expected}")
    if meta.get("rowsUpdatedAt") is None:
        raise ValueError("Source update marker missing")
    return fields


def merge_quality(total, page):
    for key, value in page.items():
        if isinstance(value, dict):
            existing = total.setdefault(key, {})
            for k, v in value.items():
                existing[k] = existing.get(k, 0) + v
        else:
            total[key] = total.get(key, 0) + value


def extract(folder, page_size=10000):
    """Raw pages stay in memory; only transient IDs and aggregate shards reach disk."""
    import duckdb  # acquisition/development dependency, not needed by visitors

    if page_size < 1:
        raise ValueError("page_size must be positive")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    start = datetime.now(timezone.utc).isoformat()
    metadata_url = f"{BASE}/api/views/{DATASET}.json"
    url = f"{BASE}/resource/{DATASET}.json"
    meta = get(session, metadata_url)
    fields = verify_metadata(meta)
    count_query = {"$select": "count(*) as n", "$where": WHERE}
    expected = int(get(session, url, count_query)[0]["n"])
    if expected == 0:
        raise ValueError("No source records; evidence remains pending")
    quality, statuses, pages, downloaded, last = {}, Counter(), 0, 0, None
    min_created, max_created = None, None
    with tempfile.TemporaryDirectory(prefix="case002-") as scratch:
        scratch = Path(scratch)
        with sqlite3.connect(scratch / "identity.sqlite") as ids:
            ids.execute("CREATE TABLE ids (id TEXT PRIMARY KEY) WITHOUT ROWID")
            while downloaded < expected:
                where = (
                    WHERE
                    if last is None
                    else f"({WHERE}) AND service_request_id > {last}"
                )
                rows = get(
                    session,
                    url,
                    {
                        "$select": ",".join(MAPPING.values()),
                        "$where": where,
                        "$order": "service_request_id ASC",
                        "$limit": page_size,
                    },
                )
                if not rows:
                    raise ValueError("Extraction ended before expected source count")
                raw = pd.DataFrame(rows).reindex(columns=list(MAPPING.values()))
                d = normalize(raw, MAPPING)
                q = validate(d, start)
                # Parse numeric keys before constructing the next SoQL cursor.
                try:
                    numeric = [Decimal(str(x)) for x in d.request_id]
                    if any(
                        not x.is_finite() or x != x.to_integral_value() for x in numeric
                    ):
                        raise ValueError("Nonintegral request identifier")
                    if numeric != sorted(numeric) or (
                        last is not None and numeric[0] <= Decimal(last)
                    ):
                        raise ValueError("Nonmonotonic source pagination")
                    ids.executemany(
                        "INSERT INTO ids VALUES (?)", [(str(x),) for x in numeric]
                    )
                except (InvalidOperation, sqlite3.IntegrityError) as exc:
                    raise ValueError(
                        "Invalid or duplicate request IDs across pages"
                    ) from exc
                local = d.created_at.dt.tz_convert("America/Los_Angeles")
                if not local.dt.year.eq(2025).all():
                    raise ValueError("Out-of-scope cohort")
                lo, hi = local.min().isoformat(), local.max().isoformat()
                min_created = min(min_created, lo) if min_created else lo
                max_created = max(max_created, hi) if max_created else hi
                merge_quality(quality, q)
                statuses.update(d.status.tolist())
                page_cube = aggregate(d, start)
                with duckdb.connect() as parity:
                    parity.register("requests", d)
                    sql = (
                        Path(__file__).resolve().parents[1]
                        / "sql/cohort_aggregates.sql"
                    ).read_text()
                    sql_cube = parity.execute(sql, {"as_of": start}).df()
                sort_keys = DIMENSIONS + ["duration_day"]
                pd.testing.assert_frame_equal(
                    page_cube.sort_values(sort_keys).reset_index(drop=True),
                    sql_cube[page_cube.columns]
                    .sort_values(sort_keys)
                    .reset_index(drop=True),
                    check_dtype=False,
                )
                page_cube.to_parquet(scratch / f"part-{pages:05}.parquet", index=False)
                downloaded += len(rows)
                pages += 1
                last = str(numeric[-1])
                print(
                    json.dumps(
                        {
                            "event": "page_validated",
                            "page": pages,
                            "downloaded": downloaded,
                            "expected": expected,
                        }
                    ),
                    flush=True,
                )
            unique_ids = ids.execute("SELECT count(*) FROM ids").fetchone()[0]
        after = get(session, metadata_url)
        verify_metadata(after)
        count_after = int(get(session, url, count_query)[0]["n"])
        if (
            expected != count_after
            or downloaded != expected
            or unique_ids != expected
            or meta["rowsUpdatedAt"] != after["rowsUpdatedAt"]
        ):
            raise ValueError(
                "Source changed or counts/IDs failed reconciliation; rerun for stable extraction"
            )
        keys = DIMENSIONS + ["duration_day"]
        selects = ",".join(keys + [f"CAST(sum({c}) AS BIGINT) AS {c}" for c in COUNTS])
        con = duckdb.connect()
        con.execute("SET memory_limit='1GB'")
        con.execute("SET temp_directory = ?", [str(scratch / "spill")])
        con.read_parquet(str(scratch / "part-*.parquet")).create_view("shards")
        cube = con.execute(f"SELECT {selects} FROM shards GROUP BY ALL").df()
        con.close()
        if int(cube.requests.sum()) != expected:
            raise ValueError("Aggregate reconciliation failed")
        temp = folder / "cube.parquet.tmp"
        cube.to_parquet(temp, index=False)
    end = datetime.now(timezone.utc).isoformat()
    provenance = {
        "status": "verified_public_extract",
        "synthetic": False,
        "review_status": "unreviewed_artifact",
        "source_url": url,
        "metadata_url": metadata_url,
        "dataset_id": DATASET,
        "dataset_title": meta["name"],
        "mapping": MAPPING,
        "source_columns": [
            {k: c.get(k) for k in ["fieldName", "dataTypeName", "description"]}
            for c in fields.values()
        ],
        "source_rows_updated_at": meta["rowsUpdatedAt"],
        "extraction_started_at": start,
        "extracted_at": end,
        "as_of": start,
        "cohort": "2025 local San Francisco calendar year",
        "where": WHERE,
        "rows": expected,
        "source_count_before": expected,
        "source_count_after": count_after,
        "downloaded_rows": downloaded,
        "unique_request_ids": unique_ids,
        "sql_python_parity_pages": pages,
        "pages": pages,
        "page_size": page_size,
        "pagination": "ascending numeric request-ID keyset",
        "min_created_local": min_created,
        "max_created_local": max_created,
        "quality": quality,
        "status_counts": dict(statuses),
        "sha256": hashlib.sha256(temp.read_bytes()).hexdigest(),
        "cube_rows": len(cube),
        "cube_bytes": temp.stat().st_size,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "git_commit": os.getenv("GITHUB_SHA"),
        "completeness": "Count-reconciled API extraction with unique IDs and unchanged dataset update marker; not an immutable snapshot or proof all service events were reported.",
        "limitations": [
            "Administrative closure does not confirm resolution.",
            "Current snapshot; status histories unavailable.",
            "Category/month matching does not remove subcategory complexity or establish causality.",
            "Repeated reports do not identify repeated failures at a location.",
            "Closed-case duration quantiles are floored day bins (<1 day rounding error) and exclude unresolved cases.",
        ],
    }
    temp.replace(folder / "cube.parquet")
    pending = folder / "provenance.json.tmp"
    pending.write_text(json.dumps(provenance, indent=2) + "\n")
    pending.replace(folder / "provenance.json")
    return provenance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Review artifact directory; do not target bundled data before review",
    )
    parser.add_argument("--page-size", type=int, default=10000)
    args = parser.parse_args()
    print(json.dumps(extract(args.output, args.page_size), indent=2))
