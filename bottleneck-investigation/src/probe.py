"""Credential-free source diagnostics. Never prints request rows or headers."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://data.sfgov.org"
DATASET = "vw6y-z8j6"
WHERE = "requested_datetime >= '2025-01-01T00:00:00' AND requested_datetime < '2026-01-01T00:00:00'"


def probe(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": []}
    checks = [
        ("metadata", f"{BASE}/api/views/{DATASET}.json", None),
        (
            "small_query",
            f"{BASE}/resource/{DATASET}.json",
            {
                "$select": "service_request_id,requested_datetime",
                "$where": WHERE,
                "$limit": 2,
            },
        ),
    ]
    ok = True
    for label, url, params in checks:
        entry = {"name": label, "url": url}
        try:
            response = requests.get(url, params=params, timeout=90)
            entry.update(
                status_code=response.status_code,
                content_type=response.headers.get("Content-Type"),
                bytes=len(response.content),
            )
            response.raise_for_status()
            result = response.json()
            if label == "metadata":
                entry.update(
                    dataset_id=result.get("id"),
                    title=result.get("name"),
                    rows_updated_at=result.get("rowsUpdatedAt"),
                    attribution=result.get("attribution"),
                    columns=[
                        {
                            k: c.get(k)
                            for k in [
                                "fieldName",
                                "name",
                                "dataTypeName",
                                "description",
                            ]
                        }
                        for c in result.get("columns", [])
                    ],
                )
                (folder / "source_metadata.json").write_text(
                    json.dumps(result, indent=2) + "\n"
                )
            else:
                entry.update(
                    returned_rows=len(result),
                    returned_fields=sorted(set().union(*(r.keys() for r in result))),
                )
        except Exception as exc:
            ok = False
            # Avoid arbitrary response text, URLs with tokens, environment variables or headers.
            entry["error_type"] = type(exc).__name__
        report["checks"].append(entry)
    report["success"] = ok
    (folder / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return ok


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raise SystemExit(0 if probe(args.output) else 1)
