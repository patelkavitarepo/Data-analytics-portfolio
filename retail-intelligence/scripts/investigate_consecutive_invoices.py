"""Study consecutive invoice numbers on otherwise identical line records.

Cross-invoice *near duplicates* are an observed matching pattern, not proof of
double entry or repeated physical inventory movements. No source rows are changed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import FIELDS, normalize_columns, sha256_file
except ModuleNotFoundError:
    from audit import FIELDS, normalize_columns, sha256_file


SIGNATURE = [name for name in FIELDS if name != "invoice_no"]


def _consecutive_distinct_numbers(series: pd.Series) -> int:
    ids = series.dropna().drop_duplicates().astype("int64").sort_values().reset_index(drop=True)
    return int(ids.diff().eq(1).sum())


def analyze_consecutive_invoices(sheets: dict[str, pd.DataFrame]) -> dict:
    """Find identical seven-field lines on DIFFERENT, consecutive numeric invoice IDs."""
    if not sheets:
        raise ValueError("Workbook has no worksheets")

    parts = []
    for name, raw in sheets.items():
        df = normalize_columns(raw).copy()
        df["_sheet"] = str(name)
        df["_excel_row"] = range(2, len(df) + 2)
        parts.append(df)
    full = pd.concat(parts, ignore_index=True)
    ids = full["invoice_no"].astype("string").str.strip()
    digits = ids.str.fullmatch(r"[0-9]+").fillna(False)
    numeric = full.loc[digits].copy()
    numeric["_id_str"] = ids.loc[digits]
    numeric["_id_num"] = numeric["_id_str"].astype("int64")
    numeric["_qty_num"] = pd.to_numeric(numeric["quantity"], errors="coerce")
    numeric["_sig_group"] = numeric.groupby(
        SIGNATURE, dropna=False, sort=False
    ).ngroup()

    # A line can be repeated multiple times inside a single invoice. The
    # following examines DISTINCT invoice IDs per exact seven-field signature.
    unique = numeric.drop_duplicates(["_sig_group", "_id_str"]).copy()
    unique = unique.sort_values(
        ["_sig_group", "_id_num", "_excel_row"], kind="mergesort"
    )
    group = unique.groupby("_sig_group", sort=False)
    previous = group["_id_num"].shift(1)
    previous_id = group["_id_str"].shift(1)
    previous_sheet = group["_sheet"].shift(1)
    previous_row = group["_excel_row"].shift(1)
    consecutive = previous.notna() & unique["_id_num"].sub(previous).eq(1)
    matched = unique.loc[consecutive].copy()
    matched["_previous_id_num"] = previous.loc[consecutive].astype("int64")
    matched["_previous_id_str"] = previous_id.loc[consecutive]
    matched["_previous_sheet"] = previous_sheet.loc[consecutive]
    matched["_previous_excel_row"] = previous_row.loc[consecutive].astype("int64")
    matched["_adjacent_excel_rows"] = (
        matched["_sheet"].eq(matched["_previous_sheet"])
        & matched["_excel_row"].sub(matched["_previous_excel_row"]).eq(1)
    )

    negative = numeric["_qty_num"].lt(0).fillna(False)
    neg_unique = unique["_qty_num"].lt(0).fillna(False)
    neg_pairs = matched.loc[matched["_qty_num"].lt(0).fillna(False)]
    pair_ids = matched[["_previous_id_num", "_id_num"]].drop_duplicates()
    neg_pair_ids = neg_pairs[["_previous_id_num", "_id_num"]].drop_duplicates()
    all_consecutive_ids = _consecutive_distinct_numbers(numeric["_id_num"])
    negative_consecutive_ids = _consecutive_distinct_numbers(
        numeric.loc[negative, "_id_num"]
    )
    all_unique_ids = int(numeric["_id_num"].nunique())
    sig_sizes = unique.groupby("_sig_group").size()
    neg_sig_sizes = unique.loc[neg_unique].groupby("_sig_group").size()

    target = neg_pairs.loc[
        neg_pairs["_previous_id_num"].eq(556690)
        & neg_pairs["_id_num"].eq(556691)
        & neg_pairs["stock_code"].astype("string").str.strip().eq("23005")
        & neg_pairs["_qty_num"].eq(-9600)
    ]

    examples = neg_pairs.assign(
        _abs_qty=neg_pairs["_qty_num"].abs()
    ).sort_values(["_abs_qty", "_id_num"], ascending=[False, True]).head(15)
    return {
        "status": "observed_from_original_workbook",
        "raw_rows": int(len(full)),
        "raw_rows_with_numeric_invoice_id": int(len(numeric)),
        "distinct_numeric_invoice_ids": all_unique_ids,
        "numeric_invoice_ids_with_consecutive_neighbors_pairs": all_consecutive_ids,
        "same_signature_unique_invoice_pairs_all_distances": int(
            ((sig_sizes * (sig_sizes - 1)) // 2).sum()
        ),
        "same_signature_unique_invoice_pairs_consecutive": int(len(matched)),
        "distinct_consecutive_invoice_number_pairs_with_any_matching_seven_field_line": int(len(pair_ids)),
        "matched_consecutive_pairs_on_adjacent_excel_rows": int(matched["_adjacent_excel_rows"].sum()),
        "negative_non_c": {
            "raw_rows": int(negative.sum()),
            "distinct_numeric_invoice_ids": int(numeric.loc[negative, "_id_num"].nunique()),
            "consecutive_numeric_invoice_id_pairs_within_cohort": negative_consecutive_ids,
            "seven_field_matching_pairs_different_invoice_ids_any_distance": int(
                ((neg_sig_sizes * (neg_sig_sizes - 1)) // 2).sum()
            ),
            "seven_field_matching_pairs_consecutive_ids": int(len(neg_pairs)),
            "distinct_consecutive_invoice_number_pairs_matching": int(len(neg_pair_ids)),
            "matching_pairs_adjacent_excel_rows": int(neg_pairs["_adjacent_excel_rows"].sum()),
        },
        "target_556690_556691": {
            "matching_seven_fields_and_consecutive_ids": bool(len(target)),
            "number_of_matching_pair_records": int(len(target)),
            "pairs": [
                {
                    "invoice_a": str(x["_previous_id_str"]),
                    "invoice_b": str(x["_id_str"]),
                    "source_sheet_a": str(x["_previous_sheet"]),
                    "source_excel_row_a": int(x["_previous_excel_row"]),
                    "source_sheet_b": str(x["_sheet"]),
                    "source_excel_row_b": int(x["_excel_row"]),
                    "adjacent_source_rows": bool(x["_adjacent_excel_rows"]),
                    "stock_code": str(x["stock_code"]),
                    "quantity_each": int(x["quantity"]),
                    "timestamp": pd.Timestamp(x["invoice_date"]).isoformat(),
                }
                for _, x in target.iterrows()
            ],
        },
        "largest_magnitude_negative_non_c_consecutive_examples": [
            {
                "invoice_a": str(x["_previous_id_str"]),
                "invoice_b": str(x["_id_str"]),
                "stock_code": str(x["stock_code"]),
                "description": None if pd.isna(x["description"]) else str(x["description"]),
                "quantity_each": int(x["quantity"]),
                "timestamp": pd.Timestamp(x["invoice_date"]).isoformat(),
                "adjacent_source_rows": bool(x["_adjacent_excel_rows"]),
            }
            for _, x in examples.iterrows()
        ],
        "seven_field_signature_without_invoice": SIGNATURE,
        "limits": [
            "Matching seven fields and consecutive invoice IDs is an observational pattern, NOT evidence of accidental duplication.",
            "Invoice ID numbers represent source identifiers, not verified event counts or independent disposal batches.",
            "This analysis considers numeric-only invoice IDs, not C-prefixed cancellation IDs.",
            "Many distinct invoice numbers normally occur consecutively; compare with the measured baseline.",
            "No lines were deleted or assigned a business-cause label.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/consecutive_invoice_investigation.json"))
    args = parser.parse_args()
    if not args.workbook.is_file():
        parser.error(f"Missing workbook: {args.workbook}")
    report = analyze_consecutive_invoices(
        pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    )
    report["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
