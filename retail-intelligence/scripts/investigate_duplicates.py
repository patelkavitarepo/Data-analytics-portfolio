"""Inspect exact duplicate invoice lines before considering deduplication.

Observational audit only. No source rows are dropped, and identical invoice
lines are not automatically classified as data errors.
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


def diagnose_duplicates(sheets: dict[str, pd.DataFrame]) -> dict:
    if not sheets:
        raise ValueError("No sheets supplied")
    parts = []
    for sheet, raw in sheets.items():
        part = normalize_columns(raw).copy()
        part["_source_sheet"] = str(sheet)
        # Excel row numbers: 1-based header + rows starting at 2.
        part["_excel_row"] = range(2, len(part) + 2)
        parts.append(part)
    df = pd.concat(parts, ignore_index=True)
    keys = list(FIELDS)
    first_seen = df.duplicated(subset=keys, keep="first")
    repeated = df.duplicated(subset=keys, keep=False)
    invoice = df["invoice_no"].astype("string").str.strip()
    c_prefix = invoice.str.upper().str.startswith("C").fillna(False)
    qty = pd.to_numeric(df["quantity"], errors="coerce")
    neg_non_c = (qty < 0).fillna(False) & ~c_prefix
    neg_c = (qty < 0).fillna(False) & c_prefix
    other = ~(neg_non_c | neg_c)

    # Detailed group statistics are computed only on repeated rows, not all
    # one million lines. groupby(dropna=False) treats missing fields as equal.
    repeated_rows = df.loc[repeated].copy()
    groups = (
        repeated_rows.groupby(keys, dropna=False, sort=False)
        .size()
        .reset_index(name="rows_in_group")
    )
    assert int((groups["rows_in_group"] - 1).sum()) == int(first_seen.sum())
    assert len(repeated_rows) == int(groups["rows_in_group"].sum())
    assert int((neg_non_c | neg_c | other).sum()) == len(df)
    cohorts = {}
    for name, mask in [
        ("negative_non_c", neg_non_c),
        ("negative_c", neg_c),
        ("all_other_rows", other),
    ]:
        cohorts[name] = {
            "rows": int(mask.sum()),
            "extra_exact_copies_after_first": int((mask & first_seen).sum()),
            "rows_part_of_exact_duplicate_groups": int((mask & repeated).sum()),
            "rows_retained_if_hypothetically_one_per_exact_group": int(mask.sum() - (mask & first_seen).sum()),
        }
    assert sum(item["extra_exact_copies_after_first"] for item in cohorts.values()) == int(first_seen.sum())

    # Exact as-written case study: the two reported smudged-printing -9600 lines.
    case_mask = (
        (df["stock_code"].astype("string").str.strip() == "23005").fillna(False)
        & (qty == -9600).fillna(False)
        & df["description"].astype("string").str.contains("printing smudges/thrown away", case=False, regex=False, na=False)
    )
    case = df.loc[case_mask].copy()
    rows = []
    for idx, r in case.iterrows():
        rows.append({
            "invoice_id": str(r["invoice_no"]),
            "stock_code": str(r["stock_code"]),
            "description": str(r["description"]),
            "quantity": int(r["quantity"]),
            "unit_price": float(r["unit_price"]),
            "timestamp": pd.Timestamp(r["invoice_date"]).isoformat(),
            "customer_id": None if pd.isna(r["customer_id"]) else str(r["customer_id"]),
            "country": str(r["country"]),
            "sheet": str(r["_source_sheet"]),
            "excel_row": int(r["_excel_row"]),
            "belongs_to_exact_duplicate_group": bool(repeated.loc[idx]),
        })
    # Repetition within case (not necessarily source error). Uses exact eight columns.
    case_extra = int(case.duplicated(subset=keys).sum())
    hypothetical_case_quantity_difference = int((-case.loc[case.duplicated(subset=keys), "quantity"]).sum()) if len(case) else 0
    # Positive difference is an absolute magnitude, not a loss estimate.

    top_groups = (
        groups.loc[(pd.to_numeric(groups["quantity"], errors="coerce") < 0)
                   & (~groups["invoice_no"].astype("string").str.strip().str.upper().str.startswith("C").fillna(False))]
        .sort_values(["rows_in_group"], ascending=[False]).head(10)
    )
    return {
        "status": "observed_from_source_workbook",
        "row_unit": "invoice line, not independent stock adjustment",
        "raw_rows": int(len(df)),
        "exact_key": keys,
        "exact_duplicate_extra_rows_all": int(first_seen.sum()),
        "rows_belonging_to_exact_duplicate_groups_all": int(repeated.sum()),
        "number_of_exact_duplicate_groups_all": int(len(groups)),
        "max_rows_in_one_exact_duplicate_group_all": int(groups["rows_in_group"].max()) if len(groups) else 0,
        "cohort_duplicate_counts": cohorts,
        "target_9600_printing_smudges": {
            "candidate_rows": int(len(case)),
            "extra_exact_copies_after_first": case_extra,
            "hypothetical_absolute_units_counted_twice_if_one_duplicate": hypothetical_case_quantity_difference,
            "rows": rows,
        },
        "top_unmarked_negative_repeated_groups": [
            {
                "invoice_id": str(r["invoice_no"]),
                "stock_code": str(r["stock_code"]),
                "description": None if pd.isna(r["description"]) else str(r["description"]),
                "quantity": int(r["quantity"]),
                "unit_price": float(r["unit_price"]),
                "date_time": pd.Timestamp(r["invoice_date"]).isoformat(),
                "group_size": int(r["rows_in_group"]),
            }
            for _, r in top_groups.iterrows()
        ],
        "interpretation_limits": [
            "Exact matching fields are not proof of accidental duplication: legitimate same-item lines may repeat.",
            "The hypothetical removed-unit count is NOT actual stock loss or a cleaning recommendation.",
            "The workbook has no unique line-event ID to distinguish independent identical entries.",
            "Stock quantities across different products are not monetary values.",
            "This procedure removed or changed no rows.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/duplicate_investigation.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    result = diagnose_duplicates(sheets)
    result["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
