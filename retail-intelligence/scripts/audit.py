"""Reproducible first-pass audit of UCI Online Retail II.

Do not silently remove rows or interpret line totals as finalized revenue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

DATA_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
FIELDS = (
    "invoice_no", "stock_code", "description", "quantity", "invoice_date",
    "unit_price", "customer_id", "country",
)
ALIASES = {
    "invoice": "invoice_no", "invoiceno": "invoice_no",
    "stockcode": "stock_code", "description": "description", "quantity": "quantity",
    "invoicedate": "invoice_date", "price": "unit_price", "unitprice": "unit_price",
    "customerid": "customer_id", "country": "country",
}


def download_workbook(destination: Path) -> None:
    """Download the official ZIP and extract only its matching workbook."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": "retail-intelligence-audit/0.1"})
    with tempfile.TemporaryFile() as temporary:
        with urllib.request.urlopen(request, timeout=120) as response:
            shutil.copyfileobj(response, temporary)
        temporary.seek(0)
        with zipfile.ZipFile(temporary) as archive:
            matches = [n for n in archive.namelist() if Path(n).name.lower() == "online_retail_ii.xlsx"]
            if len(matches) != 1:
                raise ValueError(f"Expected one Online Retail II workbook; found {len(matches)}")
            with archive.open(matches[0]) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Map both original years' Excel headers to a common eight-field schema."""
    renamed = {}
    for col in frame.columns:
        key = re.sub(r"[^a-z0-9]", "", str(col).lower())
        if key not in ALIASES:
            raise ValueError(f"Unrecognized source field: {col!r}")
        renamed[col] = ALIASES[key]
    if set(renamed.values()) != set(FIELDS) or len(renamed) != len(FIELDS):
        raise ValueError(f"Expected eight distinct fields; found {list(renamed.values())}")
    return frame.rename(columns=renamed).loc[:, list(FIELDS)]


def audit_frames(sheets: dict[str, pd.DataFrame]) -> dict:
    if not sheets:
        raise ValueError("Workbook contained no sheets")
    frames = []
    sizes = {}
    for sheet, raw in sheets.items():
        normalized = normalize_columns(raw)
        frames.append(normalized)
        sizes[str(sheet)] = len(normalized)
    data = pd.concat(frames, ignore_index=True)
    inv = data["invoice_no"].astype("string").str.strip()
    quantities = pd.to_numeric(data["quantity"], errors="coerce")
    prices = pd.to_numeric(data["unit_price"], errors="coerce")
    dates = pd.to_datetime(data["invoice_date"], errors="coerce")
    missing = {
        col: int((data[col].isna() | data[col].astype("string").str.strip().eq("").fillna(False)).sum())
        for col in FIELDS
    }
    return {
        "status": "observed_by_local_audit",
        "source": "UCI Online Retail II (dataset 502)",
        "unit_of_observation": "invoice line item, not unique order",
        "rows": int(len(data)),
        "rows_by_sheet": sizes,
        "unique_nonmissing_invoice_ids": int(inv.replace("", pd.NA).nunique()),
        "missing_or_blank_by_field": missing,
        "exact_duplicate_lines_across_eight_fields": int(data.duplicated(subset=list(FIELDS)).sum()),
        "invoice_codes_starting_c_rows": int(inv.str.upper().str.startswith("C").fillna(False).sum()),
        "negative_quantity_rows": int((quantities < 0).sum()),
        "zero_quantity_rows": int((quantities == 0).sum()),
        "non_numeric_quantity_rows": int(quantities.isna().sum() - data["quantity"].isna().sum()),
        "negative_unit_price_rows": int((prices < 0).sum()),
        "zero_unit_price_rows": int((prices == 0).sum()),
        "non_numeric_unit_price_rows": int(prices.isna().sum() - data["unit_price"].isna().sum()),
        "invalid_or_missing_dates": int(dates.isna().sum()),
        "earliest_invoice_date": dates.min().isoformat() if dates.notna().any() else None,
        "latest_invoice_date": dates.max().isoformat() if dates.notna().any() else None,
        "distinct_countries": int(data["country"].dropna().nunique()),
        "cleaning_decisions": "None; this is a raw-data audit only.",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/initial_audit.json"))
    parser.add_argument("--download", action="store_true", help="Download original workbook from UCI")
    args = parser.parse_args()
    if args.download:
        download_workbook(args.workbook)
    if not args.workbook.is_file():
        parser.error(f"Workbook not found at {args.workbook}; use --download to obtain it")
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    result = audit_frames(sheets)
    result["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
