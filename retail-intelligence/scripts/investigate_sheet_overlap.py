"""Investigation 007: reconcile overlap between UCI Online Retail II's annual sheets.

Exact cross-sheet matching uses all eight normalized fields with multiplicity:
for each distinct line, the number shared is min(count_sheet_A, count_sheet_B).
No source rows are removed or reclassified. Gross positive line value is a
sensitivity scenario, not certified revenue or a deduplication decision.
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


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    data = normalize_columns(frame).copy()
    # These are identifiers, not quantities; comparable text representation.
    for col in ("invoice_no", "stock_code"):
        data[col] = data[col].astype("string").str.strip()
    data["invoice_date"] = pd.to_datetime(data["invoice_date"], errors="coerce")
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")
    data["customer_id"] = pd.to_numeric(data["customer_id"], errors="coerce")
    return data


def _date_range(frame: pd.DataFrame) -> dict:
    dates = frame["invoice_date"]
    return {
        "rows": int(len(frame)),
        "first": dates.min().isoformat() if dates.notna().any() else None,
        "last": dates.max().isoformat() if dates.notna().any() else None,
        "distinct_invoice_ids": int(frame["invoice_no"].nunique(dropna=True)),
    }


def investigate_sheet_overlap(sheets: dict[str, pd.DataFrame]) -> dict:
    """Precisely match source rows across two worksheets, not within a sheet."""
    if len(sheets) != 2:
        raise ValueError("Expected exactly two original yearly worksheets")
    (name_a, raw_a), (name_b, raw_b) = list(sheets.items())
    a, b = _prepare(raw_a), _prepare(raw_b)
    keys = list(FIELDS)

    # Counting values keeps duplicate multiplicity without an m:n explosion.
    ca = a.value_counts(subset=keys, dropna=False, sort=False).rename("a")
    cb = b.value_counts(subset=keys, dropna=False, sort=False).rename("b")
    shared = ca.to_frame().join(cb.to_frame(), how="inner")
    shared["copies_in_both"] = shared[["a", "b"]].min(axis=1).astype("int64")
    matched = shared.reset_index()
    matched_count = int(matched["copies_in_both"].sum())
    assert matched_count <= min(len(a), len(b))
    combined = len(a) + len(b)

    inv_a = a["invoice_no"].dropna().value_counts()
    inv_b = b["invoice_no"].dropna().value_counts()
    shared_ids = inv_a.index.intersection(inv_b.index)
    exact_by_invoice = matched.groupby("invoice_no", dropna=True)["copies_in_both"].sum()
    common_matching_ids = shared_ids.intersection(exact_by_invoice.index)
    if len(shared_ids):
        exact_for_common = exact_by_invoice.reindex(shared_ids, fill_value=0)
        full_match = (
            (exact_for_common == inv_a.reindex(shared_ids))
            & (exact_for_common == inv_b.reindex(shared_ids))
        )
        full_ids = int(full_match.sum())
        none_ids = int(exact_for_common.eq(0).sum())
    else:
        full_ids = none_ids = 0

    invoice = matched["invoice_no"].astype("string").str.strip()
    q = matched["quantity"]
    price = matched["unit_price"]
    cancellation = invoice.str.upper().str.startswith("C").fillna(False)
    nonc_negative = q.lt(0).fillna(False) & ~cancellation
    candidate = nonc_negative & price.eq(0).fillna(False) & matched["customer_id"].isna()
    positive_priced = q.gt(0).fillna(False) & price.gt(0).fillna(False) & ~cancellation
    group_rows = {
        "negative_non_c_zero_price_missing_customer": int(matched.loc[candidate, "copies_in_both"].sum()),
        "c_prefixed_cancellation": int(matched.loc[cancellation, "copies_in_both"].sum()),
        "positive_quantity_positive_price_non_c": int(matched.loc[positive_priced, "copies_in_both"].sum()),
        "all_remaining_types": int(matched.loc[~(candidate | cancellation | positive_priced), "copies_in_both"].sum()),
    }
    assert sum(group_rows.values()) == matched_count

    # A gross line-amount sensitivity only: excludes C prefixes and zero/negative
    # prices or quantities, and makes no assumption about actual cash collected.
    gross_shared = (
        matched.loc[positive_priced, "quantity"].astype(float)
        * matched.loc[positive_priced, "unit_price"].astype(float)
        * matched.loc[positive_priced, "copies_in_both"].astype(float)
    ).sum()
    monthly = matched.assign(
        month=pd.to_datetime(matched["invoice_date"]).dt.strftime("%Y-%m")
    ).groupby("month", dropna=False)["copies_in_both"].sum().sort_index()
    both_dates = pd.concat([a["invoice_date"], b["invoice_date"]], ignore_index=True)
    overlap_first = max(a["invoice_date"].min(), b["invoice_date"].min())
    overlap_last = min(a["invoice_date"].max(), b["invoice_date"].max())
    distinct_matched_invoices = int(matched["invoice_no"].nunique(dropna=True))

    return {
        "status": "source_verified_cross_sheet_multiset_comparison",
        "sheet_a": str(name_a),
        "sheet_b": str(name_b),
        "sheet_a_coverage": _date_range(a),
        "sheet_b_coverage": _date_range(b),
        "calendar_range_in_both_sheets": {
            "first": overlap_first.isoformat() if pd.notna(overlap_first) and overlap_first <= overlap_last else None,
            "last": overlap_last.isoformat() if pd.notna(overlap_last) and overlap_first <= overlap_last else None,
        },
        "combined_raw_rows": int(combined),
        "exact_matching_source_line_copies_across_sheets": matched_count,
        "distinct_eight_field_keys_shared": int(len(matched)),
        "hypothetical_rows_if_only_cross_sheet_exact_copies_counted_once": int(combined - matched_count),
        "share_of_raw_rows_represented_by_cross_sheet_extra_copies_percent": round(100 * matched_count / combined, 4) if combined else 0.0,
        "distinct_invoice_numbers_appearing_in_both_sheets": int(len(shared_ids)),
        "distinct_invoice_numbers_with_one_or_more_exact_matching_lines": int(len(common_matching_ids)),
        "shared_invoice_numbers_with_no_exact_matching_line": none_ids,
        "shared_invoice_numbers_with_fully_matching_line_multisets": full_ids,
        "shared_invoice_numbers_with_partly_matching_line_multisets": int(len(shared_ids) - none_ids - full_ids),
        "distinct_invoice_ids_on_exact_cross_sheet_matching_lines": distinct_matched_invoices,
        "overlapping_rows_by_observed_line_type": group_rows,
        "hypothetical_duplicated_gross_positive_line_amount_gbp": round(float(gross_shared), 2),
        "monthly_exact_cross_sheet_copy_counts": {str(k): int(v) for k,v in monthly.items()},
        "source_workbook_sha256": None,  # populated by main; never inferred
        "interpretation_limits": [
            "An exact eight-field cross-sheet match is evidence the same source line appears in both worksheets; not proof that distinct real-world events could never match.",
            "If both sheets represent overlapping publication windows, reporting both copies can overstate row counts and gross positive line amounts.",
            "The value sensitivity is NOT accounting revenue, profit, refunded money, or validated lost sales.",
            "Within-sheet repeated rows are left untouched and are distinct from cross-sheet matching.",
            "Shared invoice numbers with different line data can reflect changed lines, separate documents, or identifier reuse; not automatically duplicates.",
            "The above is a read-only audit; no cleaned dataset or exclusion policy was created.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/annual_sheet_overlap.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    result = investigate_sheet_overlap(sheets)
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
