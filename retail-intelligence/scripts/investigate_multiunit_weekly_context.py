"""Case 017: same-SKU multi-unit equal quantities and weekly paid-only context.

This is descriptive evidence only: neither a zero-price line nor a matching
quantity implies an advertised BOGO, fulfilled goods, or an accounting event.
Source workbook / reversible analysis layer / KPI scenarios remain unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.build_reversible_layer import build_candidate_layer
    from scripts.investigate_temporal_zero_paid_sku import _pair_counts_within
except ModuleNotFoundError:
    from audit import sha256_file
    from build_reversible_layer import build_candidate_layer
    from investigate_temporal_zero_paid_sku import _pair_counts_within


REQUIRED = {
    "invoice_no", "stock_code", "description", "quantity", "unit_price",
    "invoice_date", "customer_id", "country", "source_sheet", "source_excel_row",
}


def analyze_multiunit_weekly_context(frame: pd.DataFrame) -> dict:
    missing = sorted(REQUIRED.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    d = frame.copy()
    d["invoice_no"] = d["invoice_no"].astype("string").str.strip()
    d["stock_code"] = d["stock_code"].astype("string").str.strip()
    if d["invoice_no"].isna().any() or d["invoice_no"].eq("").any():
        raise ValueError("Missing invoice IDs require explicit reconciliation")
    d["quantity"] = pd.to_numeric(d["quantity"], errors="coerce")
    d["unit_price"] = pd.to_numeric(d["unit_price"], errors="coerce")
    d["invoice_date"] = pd.to_datetime(d["invoice_date"], errors="coerce")
    is_c = d["invoice_no"].str.upper().str.startswith("C").fillna(False)
    eligible = ~is_c & d["quantity"].gt(0).fillna(False)
    valid_sku = d["stock_code"].notna() & d["stock_code"].ne("")
    zero = d.loc[eligible & valid_sku & d["unit_price"].eq(0).fillna(False)]
    paid = d.loc[eligible & valid_sku & d["unit_price"].gt(0).fillna(False)]
    keys = ["invoice_no", "stock_code"]

    # Aggregate to invoice+SKU before looking at any apparent "offer".
    z = zero.groupby(keys, sort=False).agg(
        zero_lines=("quantity", "size"),
        zero_units=("quantity", "sum"),
        zero_time=("invoice_date", "min"),
    ).reset_index()
    p = paid.groupby(keys, sort=False).agg(
        paid_lines=("quantity", "size"),
        paid_units=("quantity", "sum"),
        paid_time=("invoice_date", "min"),
    ).reset_index()
    all_paid = p.merge(z, on=keys, how="left", validate="one_to_one")
    all_paid["paired"] = all_paid["zero_lines"].notna()
    all_paid["equal_quantities"] = (
        all_paid["paired"] & all_paid["paid_units"].eq(all_paid["zero_units"]).fillna(False)
    )
    all_paid["multiunit_equal"] = (
        all_paid["equal_quantities"] & all_paid["zero_units"].gt(1).fillna(False)
    )
    all_paid["strict_one_and_one"] = (
        all_paid["equal_quantities"] & all_paid["zero_units"].eq(1).fillna(False)
        & all_paid["zero_lines"].eq(1) & all_paid["paid_lines"].eq(1)
    )
    paired = all_paid.loc[all_paid["paired"]].copy()
    paired["first_time"] = paired[["paid_time", "zero_time"]].min(axis=1)
    # Fixed calendar weeks (Mon-Sun) are NOT rolling seven-day windows.
    # Using paid-side invoice time gives the same observation point for both
    # the numerator and the paid-only comparison denominator.
    all_paid["week_start"] = all_paid["paid_time"].dt.to_period("W-SUN").dt.start_time
    all_paid["week_label"] = all_paid["week_start"].dt.strftime("%Y-%m-%d")
    focus_codes = set(paired["stock_code"].dropna().tolist())
    focused = all_paid.loc[all_paid["stock_code"].isin(focus_codes)].copy()
    week_stats = focused.dropna(subset=["week_start"]).groupby(
        ["stock_code", "week_label"], sort=False
    ).agg(
        all_paid_invoice_sku_groups=("paid_lines", "size"),
        paid_and_zero_invoice_sku_groups=("paired", "sum"),
        equal_quantity_invoice_sku_groups=("equal_quantities", "sum"),
        multiunit_equal_invoice_sku_groups=("multiunit_equal", "sum"),
        strict_one_plus_one_invoice_sku_groups=("strict_one_and_one", "sum"),
    ).reset_index()
    week_stats = week_stats.loc[week_stats["paid_and_zero_invoice_sku_groups"].gt(0)].copy()
    week_stats["paid_only_invoice_sku_groups"] = (
        week_stats["all_paid_invoice_sku_groups"] - week_stats["paid_and_zero_invoice_sku_groups"]
    )
    # Ratios are purely descriptive, not causal campaign rates.
    week_stats["observed_pairing_fraction_of_paid_invoice_sku_groups"] = (
        week_stats["paid_and_zero_invoice_sku_groups"] / week_stats["all_paid_invoice_sku_groups"]
    )
    week_stats = week_stats.sort_values(
        ["paid_and_zero_invoice_sku_groups",
         "multiunit_equal_invoice_sku_groups",
         "all_paid_invoice_sku_groups", "stock_code", "week_label"],
        ascending=[False, False, False, True, True],
    )
    top_weeks = [{
        "stock_code": str(row["stock_code"]),
        "week_start_monday": str(row["week_label"]),
        "paid_and_zero_invoice_sku_groups": int(row["paid_and_zero_invoice_sku_groups"]),
        "paid_only_invoice_sku_groups_same_week": int(row["paid_only_invoice_sku_groups"]),
        "all_paid_invoice_sku_groups_same_week": int(row["all_paid_invoice_sku_groups"]),
        "equal_quantity_invoice_sku_groups": int(row["equal_quantity_invoice_sku_groups"]),
        "multiunit_equal_invoice_sku_groups": int(row["multiunit_equal_invoice_sku_groups"]),
        "strict_one_plus_one_invoice_sku_groups": int(row["strict_one_plus_one_invoice_sku_groups"]),
        "observed_pairing_fraction_not_promotion_rate": round(
            float(row["observed_pairing_fraction_of_paid_invoice_sku_groups"]), 6
        ),
    } for _, row in week_stats.head(15).iterrows()]

    sku_summaries = []
    for sku, group in paired.groupby("stock_code", sort=False):
        full_sku = focused.loc[focused["stock_code"].eq(sku)]
        eq = group.loc[group["multiunit_equal"]]
        seven_multi, peak_seven_multi = _pair_counts_within(
            eq[["paid_time", "zero_time"]].min(axis=1).tolist(), 7
        )
        thirty_multi, _ = _pair_counts_within(
            eq[["paid_time", "zero_time"]].min(axis=1).tolist(), 30
        )
        total_paid = int(len(full_sku))
        sku_summaries.append({
            "stock_code": str(sku),
            "paid_invoice_sku_groups_all_dates": total_paid,
            "paired_invoice_sku_groups_all_dates": int(len(group)),
            "paid_only_invoice_sku_groups_all_dates": total_paid - int(len(group)),
            "equal_total_quantity_invoice_sku_groups": int(group["equal_quantities"].sum()),
            "multiunit_equal_total_quantity_invoice_sku_groups": int(len(eq)),
            "strict_one_paid_unit_plus_one_zero_unit_groups": int(group["strict_one_and_one"].sum()),
            "distinct_multiunit_equal_invoices_paired_within_7days": int(peak_seven_multi),
            "multiunit_equal_distinct_invoice_pair_comparisons_within_7days": int(seven_multi),
            "multiunit_equal_distinct_invoice_pair_comparisons_within_30days": int(thirty_multi),
        })
    sku_summaries.sort(key=lambda x: (
        -x["multiunit_equal_total_quantity_invoice_sku_groups"],
        -x["paired_invoice_sku_groups_all_dates"],
        x["stock_code"],
    ))

    shared_zero = zero.merge(p[keys], on=keys, how="inner", validate="many_to_one")
    result = {
        "status": "observed_same_sku_multiunit_and_weekly_context_no_bogo_verified",
        "candidate_view_rows": int(len(d)),
        "non_C_positive_quantity_zero_price_lines_with_stock_code": int(len(zero)),
        "non_C_positive_quantity_paid_lines_with_stock_code": int(len(paid)),
        "zero_price_lines_with_same_invoice_paid_same_sku": int(len(shared_zero)),
        "paired_invoice_sku_groups": int(len(paired)),
        "distinct_invoice_ids_with_paired_skus": int(paired["invoice_no"].nunique()),
        "strict_one_plus_one_invoice_sku_groups": int(paired["strict_one_and_one"].sum()),
        "equal_total_quantity_invoice_sku_groups": int(paired["equal_quantities"].sum()),
        "multiunit_equal_total_quantity_invoice_sku_groups": int(paired["multiunit_equal"].sum()),
        "different_total_quantity_invoice_sku_groups": int(
            len(paired) - int(paired["equal_quantities"].sum())
        ),
        "skus_with_multiunit_equal_pairs_on_two_or_more_distinct_invoices": int(sum(
            s["multiunit_equal_total_quantity_invoice_sku_groups"] >= 2
            for s in sku_summaries
        )),
        "skus_with_multiunit_equal_pairs_within_7days": int(sum(
            s["multiunit_equal_distinct_invoice_pair_comparisons_within_7days"] > 0
            for s in sku_summaries
        )),
        "distinct_stock_codes_with_any_paid_zero_pair": int(paired["stock_code"].nunique()),
        "top_skus_by_multiunit_equal_count_max_15": sku_summaries[:15],
        "top_observed_calendar_weeks_with_paid_only_denominators_max_15": top_weeks,
        "guardrails": [
            "Equal summed quantities on one invoice are not proof of paid/free unit linkage, promotion, or delivery.",
            "Fixed Monday-Sunday calendar weeks differ from the rolling 7-day windows in Case 016.",
            "Invoices and invoice-SKU groups are not interchangeable; one invoice may contain several SKUs.",
            "Weekly paid-only counts are descriptive; a paid-only group might still have a different kind of discount.",
            "The highest observed weeks are selected after inspection and cannot establish promotion dates or causal effects.",
            "An observed pairing fraction is NOT a campaign redemption, sales conversion, refund, or revenue rate.",
            "C-prefixed and negative/nonpositive-quantity lines are outside this specific comparison, not removed from source.",
            "No raw rows, reversible candidate-view policy, financial S0/S1/S2 definitions or customer IDs are changed or exported.",
        ],
    }
    assert (
        result["equal_total_quantity_invoice_sku_groups"]
        + result["different_total_quantity_invoice_sku_groups"]
        == result["paired_invoice_sku_groups"]
    )
    assert result["strict_one_plus_one_invoice_sku_groups"] <= result["equal_total_quantity_invoice_sku_groups"]
    return result


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = analyze_multiunit_weekly_context(candidate)
    assert result["candidate_view_rows"] == layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"] = int(len(provenance))
    result["cross_sheet_canonical_links"] = int(layer["canonical_links_for_suppressed_rows"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/multiunit_weekly_context.json"))
    parser.add_argument("--prior-case-016", type=Path, default=Path("outputs/temporal_zero_paid_sku.json"))
    args = parser.parse_args()
    result = investigate_original_workbook(
        pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    )
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_case_016.is_file():
        prev = json.loads(args.prior_case_016.read_text(encoding="utf-8"))
        assert result["zero_price_lines_with_same_invoice_paid_same_sku"] == prev["zero_price_lines_with_paid_same_sku_on_same_invoice"]
        assert result["paired_invoice_sku_groups"] == prev["invoice_sku_groups_with_zero_and_paid"]
        assert result["strict_one_plus_one_invoice_sku_groups"] == prev["invoice_sku_groups_exactly_one_zero_unit_and_one_paid_unit"]
        assert result["distinct_stock_codes_with_any_paid_zero_pair"] == prev["distinct_skus_with_any_paired_invoice"]
        result["agrees_with_case_016_cohorts"] = True
    else:
        result["agrees_with_case_016_cohorts"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
