"""Read-only metadata probe for official FI-2010 Fairdata record.

No data payload download, credentials, artifact upload, or rights inference.
Safe output is minimal textual metadata from the source record.
"""
import json
import urllib.error
import urllib.request

UUID = "73eb48d7-4dbc-4a10-a52a-da745b47a649"
ENDPOINTS = (
    "https://metax.fairdata.fi/v3/datasets/" + UUID,
    "https://metax.fairdata.fi/v3/datasets/" + UUID + "/files?page_size=10",
    "https://metax-legacy.fairdata.fi/rest/v2/datasets/" + UUID,
)

for url in ENDPOINTS:
    print("SOURCE:", url)
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "ResearchAudit-Project007/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=22) as response:
            raw = response.read(500000)
            print("HTTP:", response.status, "media:", response.headers.get("Content-Type"))
            try:
                data = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                print("Unexpected JSON response; no contents published")
                continue
            if isinstance(data, dict):
                print("TOP_LEVEL_KEYS:", sorted(data.keys())[:45])
                for field in (
                    "title", "id", "identifier", "persistent_identifier", "access_rights",
                    "license", "issued", "fileset", "data_catalog", "file_storage",
                    "total_files_count", "total_files_size", "results", "count",
                ):
                    if field in data:
                        value = json.dumps(data[field], ensure_ascii=False)
                        print(field + ":", value[:5000])
                if "research_dataset" in data:
                    rd = data["research_dataset"]
                    if isinstance(rd, dict):
                        for field in ("title", "access_rights", "license", "description", "creator"):
                            if field in rd:
                                print("research_dataset." + field, json.dumps(rd[field], ensure_ascii=False)[:2000])
            else:
                print("JSON_TYPE", type(data).__name__)
    except urllib.error.HTTPError as exc:
        print("HTTP:", exc.code)
    except Exception as exc:
        print("PROBE_ERROR:", type(exc).__name__, str(exc)[:200])
