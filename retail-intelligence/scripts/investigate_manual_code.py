"""Case 010: inspect ambiguous stock code M ("Manual") before KPI exclusion.

A read-only diagnostic using Case 008's reversible candidate view. The
presence of code M never proves the line is a fee, sale, adjustment or error.
No source rows are deleted; only an aggregate JSON report is published.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.build_reversible_layer import build_candidate_layer
    from scripts.investigate_sheet_overlap import _prepare
except ModuleNotFoundError:
    from audit import sha256_file
    from build_reversible_layer import build_candidate_layer
    from investigate_sheet_overlap import _prepare


def _money(frame: pd.DataFrame) -> float:
    return round(float(
        (frame["quantity"].astype("float64") * frame["unit_price"].astype("float64")).sum()
    ), 2)


def profile_manual_lines(frame: pd.DataFrame) -> dict:
    """Source-observed line and full-invoice context, without customer IDs."""
    df = frame.copy().reset_index(drop=True)
    q = pd.to_numeric(df["quantity"], errors="coerce")
    p = pd.to_numeric(df["unit_price"], errors="coerce")
    invoice = df["invoice_no"].astype("string").str.strip()
    stock = df["stock_code"].astype("string").str.strip().str.upper()
    c = invoice.str.upper().str.startswith("C").fillna(False)
    m = stock.eq("M").fillna(False)
    positive = q.gt(0).fillna(False) & p.gt(0).fillna(False) & ~c
    selected = m & positive
    neg_c = m & c & q.lt(0).fillna(False) & p.gt(0).fillna(False)
    other_m = m & ~(selected | neg_c)

    df["_m"] = m
    df["_eligible"] = positive
    df["_m_eligible"] = selected
    df["_non_m_eligible"] = ~m & positive
    df["_invoice_id"] = invoice
    df["_amount"] = q.astype("float64") * p.astype("float64")
    df["_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    m_lines = df.loc[selected].copy()
    other_positive = df.loc[~m & positive].copy()
    totals = df.groupby("_invoice_id", dropna=False, sort=False).agg(
        lines=("_invoice_id", "size"),
        m_lines=("_m", "sum"),
        eligible_m_lines=("_m_eligible", "sum"),
        non_m_positive_lines=("_non_m_eligible", "sum"),
    )
    target_invoice_ids = m_lines["_invoice_id"].dropna().unique()
    target_invoice_context = totals.loc[totals.index.isin(target_invoice_ids)]
    assert int(target_invoice_context["eligible_m_lines"].sum()) == len(m_lines)

    only_m = target_invoice_context["m_lines"].eq(target_invoice_context["lines"])
    with_non_m = ~only_m
    with_non_m_positive = target_invoice_context["non_m_positive_lines"].gt(0)
    assert int(only_m.sum() + with_non_m.sum()) == len(target_invoice_context)
    assert int((with_non_m_positive & only_m).sum()) == 0

    descriptions = m_lines["description"].astype("string").str.strip()
    desc_counts = descriptions.fillna("<missing>").replace("", "<blank>").value_counts()
    month_counts = m_lines["_date"].dt.strftime("%Y-%m").value_counts().sort_index()
    country_counts = m_lines["country"].astype("string").fillna("<missing>").value_counts()
    amount = m_lines["_amount"].astype(float)
    sorted_amount = amount.sort_values(ascending=False)
    s0_amount = _money(df.loc[positive])
    target_amount = _money(m_lines)
    pct = round(100 * target_amount / s0_amount, 3) if s0_amount else None

    return {
        "source_rows": int(len(df)),
        "stock_code_M_all_line_types": int(m.sum()),
        "M_positive_quantity_positive_price_non_C_lines": int(selected.sum()),
        "M_negative_quantity_positive_price_C_lines": int(neg_c.sum()),
        "M_all_remaining_line_types": int(other_m.sum()),
        "M_positive_priced_amount_gbp_not_verified_revenue": target_amount,
        "M_c_prefixed_negative_priced_magnitude_not_cash_refunds_gbp": round(
            float((-df.loc[neg_c, "_amount"]).sum()), 2
        ),
        "M_positive_priced_percent_of_S0_gross_line_amount": pct,
        "positive_non_M_lines_for_comparison": int(len(other_positive)),
        "M_positive_lines_missing_customer_id": int(m_lines["customer_id"].isna().sum()),
        "positive_non_M_lines_missing_customer_id": int(
            other_positive["customer_id"].isna().sum()
        ),
        "M_positive_lines_with_missing_or_blank_description": int(
            (descriptions.isna() | descriptions.fillna("").eq("")).sum()
        ),
        "M_description_frequency_top_10": [
            {"description": str(k), "lines": int(v)} for k, v in desc_counts.head(10).items()
        ],
        "M_distinct_descriptions_including_missing": int(desc_counts.size),
        "M_positive_distinct_invoice_ids": int(len(target_invoice_context)),
        "M_positive_invoice_composition": {
            "invoice_ids_with_only_M_lines": int(only_m.sum()),
            "invoice_ids_with_at_least_one_non_M_line": int(with_non_m.sum()),
            "invoice_ids_with_non_M_positive_priced_line": int(with_non_m_positive.sum()),
            "M_lines_on_invoices_with_non_M_positive_priced_line": int(
                target_invoice_context.loc[with_non_m_positive, "eligible_m_lines"].sum()
            ),
            "M_lines_on_M_only_invoices": int(
                target_invoice_context.loc[only_m, "eligible_m_lines"].sum()
            ),
            "M_lines_on_mixed_invoices": int(
                target_invoice_context.loc[with_non_m, "eligible_m_lines"].sum()
            ),
        },
        "M_positive_unit_price_distribution_gbp": {
            "min": round(float(p.loc[selected].min()), 2) if len(m_lines) else None,
            "median": round(float(p.loc[selected].median()), 2) if len(m_lines) else None,
            "p90": round(float(p.loc[selected].quantile(.90)), 2) if len(m_lines) else None,
            "max": round(float(p.loc[selected].max()), 2) if len(m_lines) else None,
        },
        "M_positive_quantity_distribution": {
            "min": int(q.loc[selected].min()) if len(m_lines) else None,
            "median": float(q.loc[selected].median()) if len(m_lines) else None,
            "max": int(q.loc[selected].max()) if len(m_lines) else None,
        },
        "M_positive_line_amount_distribution_gbp": {
            "min": round(float(amount.min()), 2) if len(m_lines) else None,
            "median": round(float(amount.median()), 2) if len(m_lines) else None,
            "p90": round(float(amount.quantile(.90)), 2) if len(m_lines) else None,
            "max": round(float(amount.max()), 2) if len(m_lines) else None,
            "top_1_line_share_of_M_amount_percent": round(
                100 * float(sorted_amount.head(1).sum()) / target_amount, 2
            ) if target_amount else None,
            "top_10_lines_share_of_M_amount_percent": round(
                100 * float(sorted_amount.head(10).sum()) / target_amount, 2
            ) if target_amount else None,
        },
        "M_positive_by_calendar_month": {
            str(month): int(value) for month, value in month_counts.items()
        },
        "M_positive_country_top_10": [
            {"country": str(k), "lines": int(v)} for k, v in country_counts.head(10).items()
        ],
        "limitations": [
            "M is a source stock code labeled Manual, not a verified accounting category.",
            "Sharing an invoice with product-coded positive lines supports association, not the economic nature of the M line.",
            "C-prefixed negative lines are cancellation-coded, not verified realized refunds.",
            "High-value manual rows could be legitimate transactions, corrections or other entries. No causal classification is made.",
            "No customer IDs or individual invoice records are included in this aggregate JSON.",
        ],
    }


def investigate_manual_code(sheets: dict[str, pd.DataFrame]) -> dict:
    if len(sheets) != 2:
        raise ValueError("Expected exactly two worksheets")
    candidate, provenance, layer = build_candidate_layer(sheets)
    raw = pd.concat([_prepare(source) for source in sheets.values()], ignore_index=True)
    raw_stats = profile_manual_lines(raw)
    candidate_stats = profile_manual_lines(candidate)
    assert raw_stats["source_rows"] == layer["raw_source_rows"]
    assert candidate_stats["source_rows"] == layer["candidate_view_rows"]
    assert len(provenance) == layer["provenance_rows_including_every_original_line"]
    assert candidate_stats["M_positive_priced_amount_gbp_not_verified_revenue"] <= raw_stats[
        "M_positive_priced_amount_gbp_not_verified_revenue"
    ]
    return {
        "status": "read_only_ambiguous_manual_code_investigation",
        "raw": raw_stats,
        "reversible_candidate": candidate_stats,
        "cross_sheet_M_positive_priced_line_difference": (
            raw_stats["M_positive_quantity_positive_price_non_C_lines"]
            - candidate_stats["M_positive_quantity_positive_price_non_C_lines"]
        ),
        "cross_sheet_M_positive_priced_amount_difference_gbp": round(
            raw_stats["M_positive_priced_amount_gbp_not_verified_revenue"]
            - candidate_stats["M_positive_priced_amount_gbp_not_verified_revenue"], 2
        ),
        "candidate_layer_canonical_links": layer["canonical_links_for_suppressed_rows"],
        "interpretation": (
            "Exploratory profile; do not automatically exclude M, call it fraudulent, "
            "or classify all manual postings as product sales."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/manual_code_investigation.json"))
    parser.add_argument("--prior-revenue-report", type=Path, default=Path("outputs/revenue_sensitivity.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    report = investigate_manual_code(sheets)
    report["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_revenue_report.is_file():
        prior = json.loads(args.prior_revenue_report.read_text(encoding="utf-8"))
        by_code = prior["cross_sheet_reconciled_candidate"]["observed_description_examples_by_exact_code"]["M"]
        cand = report["reversible_candidate"]
        assert cand["M_positive_quantity_positive_price_non_C_lines"] == by_code["lines"]
        assert cand["M_positive_priced_amount_gbp_not_verified_revenue"] == by_code["amount_gbp"]
        report["independent_match_case009"] = True
    else:
        report["independent_match_case009"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
