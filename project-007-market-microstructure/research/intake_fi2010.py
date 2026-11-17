"""One-time source intake probe (official Fairdata metadata + researcher-hosted archive).

Publicly documented research source; ephemeral runner; no redistribution of data.
Only hashes/manifest and source metadata are printed. No model or profit scores.
"""
from hashlib import sha256
from pathlib import Path
import io
import json
import tempfile
import urllib.error
import urllib.request
import zipfile

GITHUB_ZIP = (
    "https://raw.githubusercontent.com/zcakhaa/"
    "DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/"
    "master/data/data.zip"
)
FI_RECORD = "73eb48d7-4dbc-4a10-a52a-da745b47a649"
MAX_ZIP_BYTES = 125_000_000


def probe_metadata():
    for uri in [
        "https://metax.fairdata.fi/v3/datasets/" + FI_RECORD,
        "https://metax-legacy.fairdata.fi/rest/v2/datasets/" + FI_RECORD,
    ]:
        print("OFFICIAL_METADATA_URL:", uri)
        try:
            req = urllib.request.Request(uri, headers={"Accept": "application/json", "User-Agent": "research-007/0.1"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read(400_000))
                print("OFFICIAL_HTTP:", resp.status)
                if isinstance(data, dict):
                    print("OFFICIAL_KEYS:", sorted(data.keys())[:35])
                    for k in ("license", "access_rights", "title", "issued", "persistent_identifier"):
                        if k in data:
                            print("OFFICIAL_" + k.upper() + ":", json.dumps(data[k], ensure_ascii=False)[:1500])
                    if isinstance(data.get("research_dataset"), dict):
                        for k in ("license", "access_rights"):
                            if k in data["research_dataset"]:
                                print("OFFICIAL_RESEARCH_" + k.upper() + ":", json.dumps(data["research_dataset"][k])[:1500])
        except Exception as exc:
            print("OFFICIAL_FETCH_STATUS:", type(exc).__name__, str(exc)[:180])


def inspect_research_archive():
    print("RESEARCHER_ARCHIVE_URL:", GITHUB_ZIP)
    req = urllib.request.Request(GITHUB_ZIP, headers={"User-Agent": "research-007/0.1"})
    with tempfile.TemporaryDirectory() as scratch:
        path = Path(scratch) / "data.zip"
        digest = sha256()
        size = 0
        with urllib.request.urlopen(req, timeout=60) as resp, path.open("wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ZIP_BYTES:
                    raise RuntimeError("Archive exceeds declared upper limit")
                digest.update(chunk)
                out.write(chunk)
        print("RESEARCHER_ARCHIVE_BYTES:", size)
        print("RESEARCHER_ARCHIVE_SHA256:", digest.hexdigest())
        with zipfile.ZipFile(path) as z:
            members = z.infolist()
            print("ZIP_MEMBER_COUNT:", len(members))
            print("ZIP_TOTAL_UNCOMPRESSED_BYTES:", sum(m.file_size for m in members))
            target = []
            for entry in members:
                name = entry.filename
                if name.endswith("/"):
                    continue
                if len(target) < 60:
                    target.append((name, entry.file_size, entry.compress_size))
            print("ZIP_FIRST_60_FILES:", json.dumps(target, ensure_ascii=False))
            matches = [info for info in members if info.filename.endswith(
                ("Train_Dst_NoAuction_DecPre_CF_7.txt", "Test_Dst_NoAuction_DecPre_CF_7.txt")
            )]
            print("TARGET_FOLD_FILES:", json.dumps([(x.filename, x.file_size) for x in matches]))
            print("NO_DATA_STORED_AFTER_RUN:", True)


if __name__ == "__main__":
    probe_metadata()
    try:
        inspect_research_archive()
    except Exception as exc:
        print("RESEARCHER_ARCHIVE_ERROR:", type(exc).__name__, str(exc)[:300])
        raise
