"""Case 005: inspect complete invoices and local neighborhoods around suspicious lines.

Read-only investigation of invoice composition, nearby numeric invoice IDs,
and same-minute activity. These are patterns, not inferred operational causes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import normalize_columns, sha256_file
except ModuleNotFoundError:
    from audit import normalize_columns, sha256_file


CASES = (
    {"name": "smudged_printing", "invoice_ids": ("556690", "556691"),
     "stock_code": "23005", "quantity": -9600},
    {"name": "given_away_chain", "invoice_ids": ("515459", "515460", "515461"),
     "stock_code": "20852", "quantity": -1000},
    {"name": "one_unit_adjustment", "invoice_ids": ("540678", "540679"),
     "stock_code": "21667", "quantity": -1},
)


def _as_iso(value) -> str | None:
    return None if pd.isna(value) else pd.Timestamp(value).isoformat()


def _invoice_summary(lines: pd.DataFrame) -> dict:
    """Aggregate all lines in one invoice without combining units or prices."""
    qty = lines["_qty"]
    price = lines["_price"]
    descriptions = lines["description"].dropna().astype("string").str.strip()
    descriptions = descriptions[descriptions.ne("")]
    return {
        "invoice_id": str(lines["_invoice"].iloc[0]),
        "source_sheet": str(lines["_sheet"].iloc[0]),
        "line_count": int(len(lines)),
        "negative_quantity_lines": int(qty.lt(0).sum()),
        "positive_quantity_lines": int(qty.gt(0).sum()),
        "zero_quantity_lines": int(qty.eq(0).sum()),
        "zero_price_lines": int(price.eq(0).sum()),
        "missing_customer_id_lines": int(lines["customer_id"].isna().sum()),
        "distinct_stock_codes": int(lines["stock_code"].nunique(dropna=True)),
        "description_examples": descriptions.drop_duplicates().head(5).tolist(),
        "first_timestamp": _as_iso(lines["_dt"].min()),
        "last_timestamp": _as_iso(lines["_dt"].max()),
        "source_excel_row_min": int(lines["_excel_row"].min()),
        "source_excel_row_max": int(lines["_excel_row"].max()),
    }


def examine_batches(
    sheets: dict[str, pd.DataFrame],
    cases: tuple[dict, ...] = CASES,
    neighbor_radius: int = 8,
) -> dict:
    if not sheets:
        raise ValueError("No workbook sheets supplied")
    if neighbor_radius < 0:
        raise ValueError("neighbor_radius must be nonnegative")
    frames = []
    for sheet, raw in sheets.items():
        f = normalize_columns(raw).copy()
        f["_sheet"] = str(sheet)
        f["_excel_row"] = range(2, len(f) + 2)
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    df["_invoice"] = df["invoice_no"].astype("string").str.strip()
    numeric_invoice = df["_invoice"].str.fullmatch(r"\d+").fillna(False)
    df["_invoice_num"] = pd.to_numeric(
        df["_invoice"].where(numeric_invoice), errors="coerce"
    ).astype("Int64")
    df["_dt"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["_qty"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["_operational_shape"] = (
        df["_qty"].lt(0).fillna(False)
        & df["_price"].eq(0).fillna(False)
        & df["customer_id"].isna()
        & numeric_invoice
    )
    reports = []
    for case in cases:
        ids = tuple(case["invoice_ids"])
        # Restrict to the target product and quantity to resolve the source
        # sheet if two years happen to reuse an invoice ID.
        target = df.loc[
            df["_invoice"].isin(ids)
            & df["stock_code"].astype("string").str.strip().eq(str(case["stock_code"]))
            & df["_qty"].eq(case["quantity"])
        ].copy()
        if target.empty:
            reports.append({"name": case["name"], "status": "target_not_found", "expected_invoice_ids": list(ids)})
            continue
        sheet = str(target["_sheet"].value_counts().index[0])
        sheet_df = df.loc[df["_sheet"].eq(sheet)]
        anchor = sheet_df.loc[sheet_df["_invoice"].isin(ids)]
        anchor_target = target.loc[target["_sheet"].eq(sheet)]
        anchor_start = anchor_target["_dt"].min()
        anchor_end = anchor_target["_dt"].max()
        id_numbers = [int(x) for x in ids]
        lo, hi = min(id_numbers), max(id_numbers)
        neighbors = sheet_df.loc[
            sheet_df["_invoice_num"].between(lo - neighbor_radius, hi + neighbor_radius).fillna(False)
        ]
        # Group by invoice ID; aggregate *all* lines of each selected ID.
        neighbor_invoices = [
            _invoice_summary(rows)
            for _, rows in neighbors.groupby("_invoice", sort=False)
        ]
        neighbor_invoices.sort(key=lambda x: int(x["invoice_id"]))

        center = anchor_start
        same_minute = sheet_df.loc[sheet_df["_dt"].eq(center)]
        within_five = sheet_df.loc[
            sheet_df["_dt"].between(anchor_start - pd.Timedelta(minutes=5),
                                     anchor_end + pd.Timedelta(minutes=5)).fillna(False)
        ]
        same_others = same_minute.loc[~same_minute["_invoice"].isin(ids)]
        same_other_ids = sorted(same_others["_invoice"].dropna().unique().tolist())
        five_others = within_five.loc[~within_five["_invoice"].isin(ids)]
        reports.append({
            "name": case["name"],
            "status": "observed",
            "source_sheet": sheet,
            "expected_invoice_ids": list(ids),
            "matching_target_line_counts_by_invoice": {
                x: int((anchor_target["_invoice"] == x).sum()) for x in ids
            },
            "expected_target_invoice_ids_present": sorted(anchor_target["_invoice"].unique().tolist()),
            "target_invoice_full_contents": [
                _invoice_summary(rows) for _, rows in anchor.groupby("_invoice", sort=False)
            ],
            "target_source_rows": [
                {
                    "invoice_id": str(r["_invoice"]),
                    "stock_code": str(r["stock_code"]),
                    "description": None if pd.isna(r["description"]) else str(r["description"]),
                    "quantity": int(r["_qty"]),
                    "unit_price": float(r["_price"]),
                    "timestamp": _as_iso(r["_dt"]),
                    "customer_id_present": bool(pd.notna(r["customer_id"])),
                    "source_excel_row": int(r["_excel_row"]),
                }
                for _, r in anchor_target.head(16).iterrows()
            ],
            "numeric_invoice_neighbor_radius": neighbor_radius,
            "neighbor_invoice_ids_present": len(neighbor_invoices),
            "neighbor_invoice_summary": neighbor_invoices,
            "same_timestamp_summary": {
                "timestamp": _as_iso(center),
                "line_count": int(len(same_minute)),
                "distinct_invoice_ids": int(same_minute["_invoice"].nunique()),
                "distinct_other_invoice_ids": len(same_other_ids),
                "other_invoice_ids_first_20": same_other_ids[:20],
                "operational_shape_lines": int(same_minute["_operational_shape"].sum()),
                "zero_price_lines": int(same_minute["_price"].eq(0).sum()),
            },
            "within_five_minutes_summary": {
                "window_start": _as_iso(anchor_start - pd.Timedelta(minutes=5)),
                "window_end": _as_iso(anchor_end + pd.Timedelta(minutes=5)),
                "lines": int(len(within_five)),
                "distinct_invoice_ids": int(within_five["_invoice"].nunique()),
                "other_invoice_ids": int(five_others["_invoice"].nunique()),
                "operational_shape_lines": int(within_five["_operational_shape"].sum()),
                "operational_shape_lines_other_invoices": int(five_others["_operational_shape"].sum()),
            },
            "limitations": [
                "Numeric invoice adjacency and shared timestamps describe recording patterns, not proven business batches.",
                "Each invoice summary includes every source line for that ID within the target sheet.",
                "The same-minute/within-five-minute windows are local context, not independent controls or probabilities.",
                "No customer IDs are exported; only missingness is counted.",
                "No lines were deleted, reclassified, or combined into inventory loss or revenue.",
            ],
        })
    return {
        "source": "UCI Online Retail II (dataset 502)",
        "status": "read_only_observational_batch_neighborhood_audit",
        "raw_rows": int(len(df)),
        "cases": reports,
        "no_cleaning": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/invoice_batch_neighborhoods.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    report = examine_batches(sheets)
    report["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
