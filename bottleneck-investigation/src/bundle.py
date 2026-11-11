"""Only verified, hash-matched public bundles may enter the dashboard."""

import hashlib
import json
from pathlib import Path
import pandas as pd
from src.analytics import COUNTS, DIMENSIONS


def load_bundle(folder):
    folder = Path(folder)
    meta = json.loads((folder / "provenance.json").read_text())
    if meta.get("status") != "verified_public_extract":
        return meta, None
    if (
        meta.get("synthetic") is not False
        or not meta.get("source_url")
        or not meta.get("extracted_at")
    ):
        raise ValueError("Incomplete public provenance")
    path = folder / "cube.parquet"
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta.get("sha256"):
        raise ValueError("Aggregate hash mismatch")
    d = pd.read_parquet(path)
    if not set(DIMENSIONS + COUNTS + ["duration_day"]).issubset(d.columns):
        raise ValueError("Invalid aggregate schema")
    if d[COUNTS].isna().any().any() or (d[COUNTS] < 0).any().any():
        raise ValueError("Invalid aggregate counts")
    for h in [7, 30]:
        if (d[f"closed{h}"] > d[f"eligible{h}"]).any() or (
            d[f"eligible{h}"] > d.requests
        ).any():
            raise ValueError("Invalid cohort denominators")
    if int(d.requests.sum()) != meta.get("rows"):
        raise ValueError("Aggregate row reconciliation failed")
    return meta, d
