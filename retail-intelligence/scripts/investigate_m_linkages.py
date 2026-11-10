"""Case 011 — high-value 'M' postings and possible cancellation relationships.

Read-only case study on Case 008's *reversible* cross-sheet-reconciled view.
A cancellation is a candidate comparison, never proof of a refund, reversal,
or an independent business event. Only summary/case-context JSON is published.
No customer IDs, personal details, or raw line exports are published.
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


def _amount(line):
    return round(float(line), 2)


def _money_total(series):
    return _amount(series.sum())


def _top_examples(df: pd.DataFrame, records: pd.DataFrame,
                  invoice_context: pd.DataFrame,
                  sale_match_counts: dict, cancel_match_counts: dict,
                  count: int, negative: bool) -> list[dict]:
    examples = []
    sort = records.sort_values(["amount_magnitude", "source_excel_row"], ascending=[False, True])
    for _, r in sort.head(count).iterrows():
        invoice = str(r["invoice_no"])
        context = invoice_context.loc[invoice]
        line_id = int(r["line_id"])
        examples.append({
            "invoice_id": invoice,
            "source_sheet": str(r["source_sheet"]),
            "source_excel_row": int(r["source_excel_row"]),
            "timestamp": pd.Timestamp(r["invoice_date"]).isoformat(),
            "quantity": int(r["quantity"]),
            "unit_price_gbp": _amount(r["unit_price"]),
            "absolute_line_amount_gbp_not_certified": _amount(r["amount_magnitude"]),
            "customer_id_present": bool(pd.notna(r["customer_id"])),
            "invoice_total_lines": int(context["all_lines"]),
            "invoice_positive_non_M_lines": int(context["positive_non_M_lines"]),
            "invoice_other_stock_codes": context["other_stock_codes"],
            "same_customer_exact_quantity_price_country_candidate_90d": int(
                (cancel_match_counts if negative else sale_match_counts)[90].get(line_id, 0)
            ),
            "same_customer_exact_quantity_price_country_candidate_365d": int(
                (cancel_match_counts if negative else sale_match_counts)[365].get(line_id, 0)
            ),
        })
    return examples


def _match_window(pairs: pd.DataFrame, positive_ids: set[int],
                  cancel_ids: set[int], days: int) -> tuple[dict, dict, dict]:
    if pairs.empty:
        matched = pairs
    else:
        elapsed = pairs["cancel_date"] - pairs["sale_date"]
        matched = pairs.loc[elapsed.ge(pd.Timedelta(0)) & elapsed.le(pd.Timedelta(days=days))]
    by_sale = matched.groupby("sale_line_id")["cancel_line_id"].nunique().to_dict()
    by_cancel = matched.groupby("cancel_line_id")["sale_line_id"].nunique().to_dict()
    reciprocal = matched.loc[
        matched["sale_line_id"].map(by_sale).eq(1)
        & matched["cancel_line_id"].map(by_cancel).eq(1)
    ]
    result = {
        "max_days_after_original_positive_line": days,
        "pair_comparisons_meeting_all_fields_and_window": int(len(matched)),
        "positive_lines_with_one_or_more_candidate_cancellations": int(len(by_sale)),
        "negative_C_lines_with_one_or_more_candidate_positive_lines": int(len(by_cancel)),
        "positive_lines_with_exactly_one_candidate_cancellation": int(sum(v == 1 for v in by_sale.values())),
        "negative_C_lines_with_exactly_one_candidate_positive_line": int(sum(v == 1 for v in by_cancel.values())),
        "reciprocal_one_to_one_candidate_pairs_not_verified_reversals": int(len(reciprocal)),
        "negative_C_lines_without_candidate_in_window": int(len(cancel_ids) - len(by_cancel)),
        "positive_lines_without_candidate_in_window": int(len(positive_ids) - len(by_sale)),
        "note": "All candidates require known identical customer ID, country, absolute quantity, and unit price; C timestamp must follow positive timestamp within the stated window. These links are not independently verified refunds or corrections.",
    }
    assert len(by_sale) <= len(positive_ids) and len(by_cancel) <= len(cancel_ids)
    return result, by_sale, by_cancel


def investigate_m_reversals(frame: pd.DataFrame) -> dict:
    df = frame.reset_index(drop=True).copy()
    df["line_id"] = range(len(df))
    df["invoice_no"] = df["invoice_no"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip().str.upper()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    is_m = df["stock_code"].eq("M").fillna(False)
    c = df["invoice_no"].str.upper().str.startswith("C").fillna(False)
    positive_m = is_m & ~c & df["quantity"].gt(0) & df["unit_price"].gt(0)
    negative_c_m = is_m & c & df["quantity"].lt(0) & df["unit_price"].gt(0)
    other_positive = ~is_m & ~c & df["quantity"].gt(0) & df["unit_price"].gt(0)

    sale = df.loc[positive_m].copy()
    canc = df.loc[negative_c_m].copy()
    sale["amount_magnitude"] = sale["quantity"] * sale["unit_price"]
    canc["amount_magnitude"] = -canc["quantity"] * canc["unit_price"]

    # Full-invoice context. Group by invoice number after the cross-sheet
    # source overlap has been reconciled; only boolean/count summaries leave
    # this function, never customer identifiers or raw invoice contents.
    context = df.loc[df["invoice_no"].isin(
        pd.concat([sale["invoice_no"], canc["invoice_no"]]).unique()
    )].copy()
    context["positive_non_M"] = other_positive.reindex(context.index).fillna(False)
    def code_examples(group):
        return sorted(set(group.loc[group["stock_code"].ne("M"), "stock_code"].dropna().tolist()))[:6]
    invoice_context = context.groupby("invoice_no", sort=False).agg(
        all_lines=("line_id", "size"),
        positive_non_M_lines=("positive_non_M", "sum"),
    )
    if len(invoice_context):
        invoice_context["other_stock_codes"] = (
            context.groupby("invoice_no", sort=False).apply(
                code_examples, include_groups=False
            ).reindex(invoice_context.index)
        )

    # Linkage hypotheses deliberately exclude anonymous rows: NA=NA
    # matches would create misleading "exact" candidate relationships.
    sale_known = sale.dropna(subset=["customer_id", "invoice_date", "country"]).copy()
    canc_known = canc.dropna(subset=["customer_id", "invoice_date", "country"]).copy()
    sale_keys = sale_known[[
        "line_id", "customer_id", "country", "quantity", "unit_price", "invoice_date"
    ]].rename(columns={
        "line_id": "sale_line_id", "quantity": "abs_qty",
        "invoice_date": "sale_date",
    })
    cancel_keys = canc_known[[
        "line_id", "customer_id", "country", "quantity", "unit_price", "invoice_date"
    ]].rename(columns={
        "line_id": "cancel_line_id", "invoice_date": "cancel_date",
    })
    cancel_keys["abs_qty"] = -cancel_keys["quantity"]
    cancel_keys = cancel_keys.drop(columns=["quantity"])
    pairs = sale_keys.merge(
        cancel_keys, how="inner",
        on=["customer_id", "country", "abs_qty", "unit_price"],
        validate="many_to_many",
    )
    # Never export the pair table; it contains customer IDs.
    windows, sale_counts, cancel_counts = {}, {}, {}
    for days in (90, 365):
        windows[days], sale_counts[days], cancel_counts[days] = _match_window(
            pairs, set(sale["line_id"].tolist()), set(canc["line_id"].tolist()), days
        )
    assert windows[90]["pair_comparisons_meeting_all_fields_and_window"] <= windows[365][
        "pair_comparisons_meeting_all_fields_and_window"
    ]
    top_positive = _top_examples(df, sale, invoice_context, sale_counts, cancel_counts, 12, False)
    top_cancel = _top_examples(df, canc, invoice_context, sale_counts, cancel_counts, 10, True)

    return {
        "status": "read_only_case_011_manual_high_value_and_candidate_linkages",
        "source_view_rows": int(len(df)),
        "positive_non_C_M_lines": int(len(sale)),
        "negative_C_M_lines": int(len(canc)),
        "positive_M_gross_line_amount_not_verified_revenue_gbp": _money_total(sale["amount_magnitude"]),
        "negative_C_M_signed_magnitude_not_realized_refunds_gbp": _money_total(canc["amount_magnitude"]),
        "positive_M_lines_with_customer_id": int(sale["customer_id"].notna().sum()),
        "negative_C_M_lines_with_customer_id": int(canc["customer_id"].notna().sum()),
        "positive_M_top_12_share_of_positive_M_amount_percent": round(
            100 * float(sale.nlargest(12, "amount_magnitude")["amount_magnitude"].sum())
            / float(sale["amount_magnitude"].sum()), 2
        ) if len(sale) and float(sale["amount_magnitude"].sum()) != 0 else None,
        "top_positive_M_line_cases": top_positive,
        "top_negative_C_M_line_cases": top_cancel,
        "candidate_link_rules": {
            "stock_code": "M on both sides",
            "positive_side": "non-C invoice, quantity > 0, unit price > 0",
            "cancel_side": "C-prefix invoice, quantity < 0, unit price > 0",
            "exact_fields": [
                "nonmissing same customer_id", "country",
                "absolute quantity", "unit price (original numeric value)",
            ],
            "temporal_condition": "cancellation timestamp >= positive timestamp; <= 90 or 365 days later",
            "meaning": "search candidates only, NOT confirmed same-event refunds",
        },
        "matching_90_days": windows[90],
        "matching_365_days": windows[365],
        "interpretation_limits": [
            "Even a reciprocal one-to-one match does not demonstrate that money was refunded or a prior order was fully cancelled.",
            "Missing customer IDs, truncated time coverage, quantities split across lines, price changes, and event logs absent from UCI limit matching.",
            "Large positive manual postings may be genuine sales, corrections, fees, wholesale transactions, or something else; description 'Manual' gives no causal detail.",
            "Case examples are invoice IDs and item counts only; no customer IDs or customer-level matched pairs are exported.",
            "No source records or candidate-layer exclusions were modified.",
        ],
    }


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = investigate_m_reversals(candidate)
    assert result["source_view_rows"] == layer["candidate_view_rows"]
    assert len(provenance) == layer["provenance_rows_including_every_original_line"]
    result["provenance_rows_accounted_for"] = len(provenance)
    result["canonical_cross_sheet_links"] = layer["canonical_links_for_suppressed_rows"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/manual_linkage_cases.json"))
    parser.add_argument("--prior-manual-audit", type=Path, default=Path("outputs/manual_code_investigation.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    report = investigate_original_workbook(sheets)
    report["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_manual_audit.is_file():
        prior = json.loads(args.prior_manual_audit.read_text(encoding="utf-8"))
        prior_m = prior["reversible_candidate"]
        assert report["positive_non_C_M_lines"] == prior_m[
            "M_positive_quantity_positive_price_non_C_lines"
        ]
        assert report["negative_C_M_lines"] == prior_m[
            "M_negative_quantity_positive_price_C_lines"
        ]
        assert report["positive_M_gross_line_amount_not_verified_revenue_gbp"] == prior_m[
            "M_positive_priced_amount_gbp_not_verified_revenue"
        ]
        report["agrees_with_case_010"] = True
    else:
        report["agrees_with_case_010"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
