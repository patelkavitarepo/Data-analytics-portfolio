"""Case 015: zero-priced and paid same-stock-code lines on one invoice.

Read-only within-invoice candidate comparisons on Case 008's reversible view.
A matching invoice ID and SKU is NOT proof that lines refer to one physical
unit, gift, promotion, correction, billing event, or duplicate.
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


CUSTOMER_STATES = ("known_same", "known_different", "one_missing", "both_missing")


def analyze_same_sku_price_pairs(frame: pd.DataFrame) -> dict:
    required = {"invoice_no", "stock_code", "description", "quantity",
                "unit_price", "invoice_date", "customer_id", "country",
                "source_sheet", "source_excel_row"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    data = frame.copy().reset_index(drop=True)
    data["invoice_no"] = data["invoice_no"].astype("string").str.strip()
    data["stock_code"] = data["stock_code"].astype("string").str.strip()
    if data["invoice_no"].isna().any() or data["invoice_no"].eq("").any():
        raise ValueError("Missing invoice IDs require explicit reconciliation")
    for field in ("quantity", "unit_price", "customer_id"):
        data[field] = pd.to_numeric(data[field], errors="coerce")
    data["invoice_date"] = pd.to_datetime(data["invoice_date"], errors="coerce")
    data["_line_id"] = data.index.astype("int64")
    non_c = ~data["invoice_no"].str.upper().str.startswith("C").fillna(False)
    q = data["quantity"].gt(0).fillna(False)
    zero = data.loc[non_c & q & data["unit_price"].eq(0).fillna(False)].copy()
    paid = data.loc[non_c & q & data["unit_price"].gt(0).fillna(False)].copy()

    # Null stock codes are not legitimate same-code evidence.
    zero_joinable = zero.loc[zero["stock_code"].notna() & zero["stock_code"].ne("")]
    paid_joinable = paid.loc[paid["stock_code"].notna() & paid["stock_code"].ne("")]
    keep = ["invoice_no", "stock_code", "quantity", "unit_price", "invoice_date",
            "customer_id", "country", "_line_id"]
    joined = zero_joinable[keep].merge(
        paid_joinable[keep],
        on=["invoice_no", "stock_code"],
        how="inner", suffixes=("_zero", "_paid"),
        validate="many_to_many",
    )

    if len(joined):
        joined["same_quantity"] = joined["quantity_zero"].eq(joined["quantity_paid"]).fillna(False)
        joined["time_gap_minutes"] = (
            joined["invoice_date_paid"] - joined["invoice_date_zero"]
        ).dt.total_seconds().abs().div(60)
        joined["same_country"] = (
            joined["country_zero"].notna() & joined["country_paid"].notna()
            & joined["country_zero"].eq(joined["country_paid"]).fillna(False)
        )
        zc, pc = joined["customer_id_zero"], joined["customer_id_paid"]
        both_known = zc.notna() & pc.notna()
        joined["customer_state"] = "one_missing"
        joined.loc[zc.isna() & pc.isna(), "customer_state"] = "both_missing"
        joined.loc[both_known & zc.eq(pc).fillna(False), "customer_state"] = "known_same"
        joined.loc[both_known & zc.ne(pc).fillna(False), "customer_state"] = "known_different"

        multiple_prices = joined.groupby(["invoice_no", "stock_code"])["unit_price_paid"].nunique()
        # The example list is bounded, and no customer IDs are emitted.
        examples = []
        selected = joined.sort_values(
            ["invoice_no", "_line_id_zero", "unit_price_paid", "_line_id_paid"]
        ).drop_duplicates("_line_id_zero").head(10)
        for _, v in selected.iterrows():
            examples.append({
                "invoice_id": str(v["invoice_no"]),
                "stock_code": str(v["stock_code"]),
                "zero_line_quantity": float(v["quantity_zero"]),
                "paid_partner_quantity_example": float(v["quantity_paid"]),
                "paid_partner_unit_price_gbp_example": round(float(v["unit_price_paid"]), 2),
                "same_quantity_in_this_comparison": bool(v["same_quantity"]),
                "recorded_time_gap_minutes_in_this_comparison": (
                    float(v["time_gap_minutes"]) if pd.notna(v["time_gap_minutes"]) else None
                ),
                "customer_information_relation_not_identity": str(v["customer_state"]),
            })
        any_equal_qty = int(joined.loc[joined["same_quantity"], "_line_id_zero"].nunique())
        same_minute = int(joined["time_gap_minutes"].eq(0).sum())
        known_time = int(joined["time_gap_minutes"].notna().sum())
        distinct_paid = int(joined["_line_id_paid"].nunique())
        distinct_zero = int(joined["_line_id_zero"].nunique())
        conflict_country = int(
            (joined["country_zero"].notna() & joined["country_paid"].notna()
             & ~joined["same_country"]).sum()
        )
        state_counts = {
            key: int(joined["customer_state"].eq(key).sum())
            for key in CUSTOMER_STATES
        }
        assert sum(state_counts.values()) == len(joined)
        assert same_minute <= known_time
        mult = int(multiple_prices.gt(1).sum())
    else:
        examples = []
        any_equal_qty = same_minute = known_time = distinct_paid = distinct_zero = 0
        conflict_country = mult = 0
        state_counts = {key: 0 for key in CUSTOMER_STATES}

    zero_invoice_ids = set(zero["invoice_no"].dropna().tolist())
    paid_invoice_ids = set(paid["invoice_no"].dropna().tolist())
    shared_invoice_ids = zero_invoice_ids & paid_invoice_ids
    matched_ids = int(joined["invoice_no"].nunique())
    assert matched_ids <= len(shared_invoice_ids)
    assert distinct_zero <= len(zero) and distinct_paid <= len(paid)

    return {
        "status": "source_observed_same_invoice_same_sku_price_context_not_verified_transaction_links",
        "candidate_view_rows": int(len(data)),
        "positive_quantity_zero_price_non_C_lines": int(len(zero)),
        "positive_quantity_positive_price_non_C_lines": int(len(paid)),
        "invoice_ids_with_both_zero_and_paid_lines": int(len(shared_invoice_ids)),
        "zero_price_lines_with_paid_line_same_sku_same_invoice": distinct_zero,
        "invoice_ids_with_any_zero_price_same_sku_paid_partner": matched_ids,
        "unique_positive_priced_lines_participating": distinct_paid,
        "zero_positive_pair_comparisons_not_transaction_count": int(len(joined)),
        "zero_lines_with_any_same_quantity_paid_partner": any_equal_qty,
        "same_quantity_pair_comparisons": int(joined["same_quantity"].sum()) if len(joined) else 0,
        "recorded_same_minute_pair_comparisons": same_minute,
        "pair_comparisons_with_known_time_gap": known_time,
        "pair_comparisons_with_both_known_but_different_country": conflict_country,
        "invoice_and_sku_groups_with_multiple_distinct_positive_prices": mult,
        "customer_relation_pair_comparisons": state_counts,
        "bounded_descriptive_example_comparisons": examples,
        "guardrails": [
            "Same invoice ID and stock code do not demonstrate free gifts, repricing, duplicate posting, return, fraud or one physical unit.",
            "One zero-priced line can have multiple positive-priced candidates; candidate pair comparisons cannot be added as distinct transactions.",
            "Even same quantities and timestamps are descriptive only; recorded times may have minute-level resolution.",
            "Known different customer IDs or countries are preserved as conflicting evidence, not silently interpreted as a same-event link.",
            "Missing customer information never implies customer identity or matching.",
            "No raw/candidate rows, provenance links, financial assumptions or revenue KPI rules are changed.",
            "No actual customer identifiers or full row-level pairing tables are published.",
        ],
    }


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = analyze_same_sku_price_pairs(candidate)
    assert result["candidate_view_rows"] == layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"] = int(len(provenance))
    result["cross_sheet_canonical_links"] = int(layer["canonical_links_for_suppressed_rows"])
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    p.add_argument("--output", type=Path, default=Path("outputs/same_sku_mixed_prices.json"))
    p.add_argument("--prior-mixed", type=Path, default=Path("outputs/mixed_price_invoices.json"))
    args = p.parse_args()
    result = investigate_original_workbook(
        pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    )
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_mixed.is_file():
        prior = json.loads(args.prior_mixed.read_text(encoding="utf-8"))
        mix = prior["mixed_invoice_per_invoice_distribution"]
        assert result["positive_quantity_zero_price_non_C_lines"] == prior["non_C_positive_zero_price_lines"]
        assert result["positive_quantity_positive_price_non_C_lines"] == prior["non_C_positive_positive_price_lines"]
        assert result["invoice_ids_with_both_zero_and_paid_lines"] == prior["invoice_composition"]["invoice_ids_with_both_zero_and_positive_price_positive_quantity_lines"]
        assert result["zero_price_lines_with_paid_line_same_sku_same_invoice"] == mix["zero_lines_with_same_code_as_paid_line_on_same_invoice"]
        assert result["invoice_ids_with_any_zero_price_same_sku_paid_partner"] == mix["invoice_ids_where_any_zero_line_has_same_stock_code_as_paid_line"]
        result["agrees_with_case_014_counts"] = True
    else:
        result["agrees_with_case_014_counts"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
