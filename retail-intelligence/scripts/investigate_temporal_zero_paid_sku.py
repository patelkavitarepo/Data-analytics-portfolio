"""Case 016 — test for repeated same-SKU £0-plus-paid patterns across invoices.

This observes *repetition* over 7/30-day periods, NOT whether the retailer
advertised a BOGO or other promotion. The source lacks promotion flags.
No rows or revenue rules are changed, and no customer IDs are exported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.build_reversible_layer import build_candidate_layer
except ModuleNotFoundError:
    from audit import sha256_file
    from build_reversible_layer import build_candidate_layer


def _pair_counts_within(dates: list[pd.Timestamp], days: int) -> tuple[int, int]:
    """Count inter-invoice comparisons in a window and largest observed cluster.

    Dates belong to *distinct invoice+SKU* groups, one timestamp per group.
    A sliding window avoids quadratic enumeration as populations grow.
    """
    valid = sorted(x for x in dates if pd.notna(x))
    left = 0
    total = 0
    peak = 0
    period = pd.Timedelta(days=days)
    for right, stamp in enumerate(valid):
        while stamp - valid[left] > period:
            left += 1
        total += right - left
        peak = max(peak, right - left + 1)
    return total, peak


def inspect_repeated_zero_paid_sku(frame: pd.DataFrame) -> dict:
    required = {"invoice_no", "stock_code", "description", "quantity", "unit_price",
                "invoice_date", "customer_id", "country", "source_sheet", "source_excel_row"}
    if missing := sorted(required.difference(frame.columns)):
        raise ValueError(f"Missing required fields: {missing}")
    df = frame.copy()
    df["invoice_no"] = df["invoice_no"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    if df["invoice_no"].isna().any() or df["invoice_no"].eq("").any():
        raise ValueError("Missing invoice IDs need explicit reconciliation")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    c = df["invoice_no"].str.upper().str.startswith("C").fillna(False)
    positive_quantity = df["quantity"].gt(0).fillna(False) & ~c
    valid_sku = df["stock_code"].notna() & df["stock_code"].ne("")
    zero = df.loc[positive_quantity & valid_sku & df["unit_price"].eq(0).fillna(False)]
    paid = df.loc[positive_quantity & valid_sku & df["unit_price"].gt(0).fillna(False)]
    keys = ["invoice_no", "stock_code"]

    z = zero.groupby(keys, sort=False).agg(
        zero_lines=("quantity", "size"),
        zero_quantity=("quantity", "sum"),
        first_zero_time=("invoice_date", "min"),
    ).reset_index()
    p = paid.groupby(keys, sort=False).agg(
        paid_lines=("quantity", "size"),
        paid_quantity=("quantity", "sum"),
        first_paid_time=("invoice_date", "min"),
    ).reset_index()
    # Every row of p represents one invoice+SKU with at least one paid line.
    all_paid_groups = p.merge(
        z, on=keys, how="left", validate="one_to_one",
    )
    paired = all_paid_groups.loc[all_paid_groups["zero_lines"].notna()].copy()
    paired["exact_one_plus_one_unit_lines"] = (
        paired["zero_lines"].eq(1) & paired["paid_lines"].eq(1)
        & paired["zero_quantity"].eq(1) & paired["paid_quantity"].eq(1)
    )
    paired["first_observed_time"] = paired[["first_zero_time", "first_paid_time"]].min(axis=1)

    stats = []
    for sku, group in paired.groupby("stock_code", sort=False):
        all_for_sku = all_paid_groups.loc[all_paid_groups["stock_code"].eq(sku)]
        times = group["first_observed_time"].tolist()
        seven_pairs, seven_peak = _pair_counts_within(times, 7)
        thirty_pairs, thirty_peak = _pair_counts_within(times, 30)
        known = group["first_observed_time"].dropna()
        stats.append({
            "stock_code": str(sku),
            "distinct_invoice_ids_with_zero_and_paid_same_sku": int(group["invoice_no"].nunique()),
            "paid_invoice_sku_groups_any_date_for_this_sku": int(len(all_for_sku)),
            "exact_one_zero_unit_plus_one_paid_unit_invoice_sku_groups": int(
                group["exact_one_plus_one_unit_lines"].sum()
            ),
            "distinct_invoice_pair_comparisons_within_7days": int(seven_pairs),
            "distinct_invoice_pair_comparisons_within_30days": int(thirty_pairs),
            "max_paired_invoice_sku_groups_in_any_7day_window": int(seven_peak),
            "max_paired_invoice_sku_groups_in_any_30day_window": int(thirty_peak),
            "first_paired_invoice_date": known.min().isoformat() if len(known) else None,
            "last_paired_invoice_date": known.max().isoformat() if len(known) else None,
        })
    # Multiple invoice+SKU groups can share an invoice ID; do not add them as separate orders.
    stats.sort(key=lambda d: (
        -d["max_paired_invoice_sku_groups_in_any_7day_window"],
        -d["distinct_invoice_ids_with_zero_and_paid_same_sku"],
        d["stock_code"],
    ))
    total_zero_lines_with_partner = int(
        zero.merge(p[keys], on=keys, how="inner", validate="many_to_one").shape[0]
    )
    result = {
        "status": "temporal_same_sku_zero_paid_invoice_recurrence_no_promotion_proven",
        "candidate_view_rows": int(len(df)),
        "zero_price_positive_quantity_non_C_lines_with_valid_sku": int(len(zero)),
        "paid_price_positive_quantity_non_C_lines_with_valid_sku": int(len(paid)),
        "zero_price_lines_with_paid_same_sku_on_same_invoice": total_zero_lines_with_partner,
        "distinct_invoice_ids_with_same_sku_zero_paid": int(paired["invoice_no"].nunique()),
        "invoice_sku_groups_with_zero_and_paid": int(len(paired)),
        "invoice_sku_groups_exactly_one_zero_unit_and_one_paid_unit": int(
            paired["exact_one_plus_one_unit_lines"].sum()
        ) if len(paired) else 0,
        "distinct_skus_with_any_paired_invoice": int(paired["stock_code"].nunique()),
        "distinct_skus_with_two_or_more_paired_invoices": int(sum(
            v["distinct_invoice_ids_with_zero_and_paid_same_sku"] >= 2 for v in stats
        )),
        "distinct_skus_with_paired_invoices_within_7days": int(sum(
            v["distinct_invoice_pair_comparisons_within_7days"] > 0 for v in stats
        )),
        "distinct_skus_with_paired_invoices_within_30days": int(sum(
            v["distinct_invoice_pair_comparisons_within_30days"] > 0 for v in stats
        )),
        "top_sku_recurrence_context_max_15": stats[:15],
        "guardrails": [
            "Repeated zero-plus-paid invoices on the same SKU do not prove an actual BOGO campaign.",
            "Stock-specific repetition should be interpreted against all paid invoice-SKU occurrences; this descriptive analysis is not a causal or statistical test.",
            "No promotion calendar, discounts policy, fulfillment evidence or independent price ledger is available.",
            "The first recorded timestamp per invoice-SKU group is approximate; no individual event order is assumed.",
            "A 7-day or 30-day cluster can also arise from stock changes, billing conventions or recording errors.",
            "One invoice can contribute multiple SKU groups. Invoice-SKU counts are not sales, transactions, units gifted or customers.",
            "Zero-price entries are not assigned implied retail prices. No KPI, source, candidate-view, or provenance change.",
            "No customer identifiers or row-level outputs are exported.",
        ],
    }
    assert result["distinct_skus_with_paired_invoices_within_7days"] <= result["distinct_skus_with_paired_invoices_within_30days"]
    return result


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = inspect_repeated_zero_paid_sku(candidate)
    assert result["candidate_view_rows"] == layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"] = int(len(provenance))
    result["cross_sheet_canonical_links"] = int(layer["canonical_links_for_suppressed_rows"])
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    p.add_argument("--output", type=Path, default=Path("outputs/temporal_zero_paid_sku.json"))
    p.add_argument("--prior-case-015", type=Path, default=Path("outputs/same_sku_mixed_prices.json"))
    a = p.parse_args()
    result = investigate_original_workbook(pd.read_excel(a.workbook, sheet_name=None, engine="openpyxl"))
    result["source_workbook_sha256"] = sha256_file(a.workbook)
    if a.prior_case_015.is_file():
        prior = json.loads(a.prior_case_015.read_text(encoding="utf-8"))
        assert result["zero_price_lines_with_paid_same_sku_on_same_invoice"] == prior["zero_price_lines_with_paid_line_same_sku_same_invoice"]
        assert result["distinct_invoice_ids_with_same_sku_zero_paid"] == prior["invoice_ids_with_any_zero_price_same_sku_paid_partner"]
        result["agrees_with_case_015_counts"] = True
    else:
        result["agrees_with_case_015_counts"] = False
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
