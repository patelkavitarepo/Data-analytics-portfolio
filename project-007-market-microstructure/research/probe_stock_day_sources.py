"""One-off metadata-only provenance probe for original FI-2010 stock/day sequences.

No private raw Nasdaq data downloads, bypasses, mirroring, credentials,
dataset reconstruction, uploads, model fits or holdout access.
"""
import json
import urllib.error
import urllib.request
from urllib.parse import quote

ID = "73eb48d7-4dbc-4a10-a52a-da745b47a649"
URLS = (
    ("canonical_dataset", "https://metax.fairdata.fi/v3/datasets/" + ID),
    ("canonical_file_list", "https://metax.fairdata.fi/v3/datasets/" + ID + "/files?page_size=40"),
    ("canonical_directories", "https://metax.fairdata.fi/v3/datasets/" + ID + "/directories?page_size=40"),
    ("retired_stock_day_csv_repo", "https://api.github.com/repos/simaki/fi2010"),
)
ACCEPTED_FIELDS = {
    "fileset", "remote_resources", "total_files_count", "total_files_size",
    "storage_service", "results", "next", "count", "path", "title", "name",
    "filename", "file_name", "file_characteristics", "size", "file_size",
    "total_size", "description", "state", "url", "identifier", "access_rights",
    "csc_project", "directories", "files", "id", "error", "detail",
}


def slim(obj, depth=0):
    if depth >= 4:
        return str(obj)[:180]
    if isinstance(obj, dict):
        return {key: slim(val, depth + 1) for key, val in obj.items()
                if key in ACCEPTED_FIELDS or key.lower().endswith("name")}
    if isinstance(obj, list):
        return [slim(v, depth + 1) for v in obj[:25]]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return str(obj)[:240] if isinstance(obj, str) else obj
    return type(obj).__name__


for label, url in URLS:
    print("PROBE_START", label, url)
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Project007-MetadataOnly/1.0 (noncommercial academic research)",
    })
    try:
        with urllib.request.urlopen(req, timeout=16) as stream:
            status, headers = stream.status, stream.headers
            body = stream.read(500_000)
            print("HTTP", status, "BYTES_READ", len(body),
                  "CONTENT_TYPE", headers.get("Content-Type"))
            try:
                data = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                print("NON_JSON_METADATA"); continue
            print("METADATA", json.dumps(slim(data), ensure_ascii=False)[:16000])
    except urllib.error.HTTPError as exc:
        print("HTTP", exc.code, "ERROR", str(exc.reason)[:200])
    except Exception as exc:
        print("FETCH_ERROR", type(exc).__name__, str(exc)[:300])
    print("PROBE_END", label)
