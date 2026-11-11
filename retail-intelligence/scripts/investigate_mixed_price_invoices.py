"""Case 014: invoice context for positive-quantity zero-priced lines.

Read-only profiling of mixed zero/positive-price invoices in the Case 008
reversible candidate view. Every count is descriptive, not a promotional,
stocktake, revenue, refund, or customer-identity classification.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.build_reversible_layer import build_candidate_layer
except ModuleNotFoundError:
    from audit import sha256_file
    from build_reversible_layer import build_candidate_layer


# Word patterns are deliberately probes, not mutually exclusive categories.
KEYWORD_PROBES = {
    "possible_promotion_words": r"\b(?:free|gift|sample|promotion|promo|complimentary)\b",
    "possible_operations_words": r"\b(?:found|check|adjustment|stocktake|stock|damaged|lost)\b",
}


def _summary(series: pd.Series, limit: int = 10) -> list[dict]:
    clean = series.astype("string").str.strip().fillna("<missing>").replace("", "<blank>")
    return [{"value": str(k), "lines": int(v)} for k, v in clean.value_counts().head(limit).items()]


def _describe_lines(lines: pd.DataFrame) -> dict:
    desc = lines["description"].astype("string")
    desc_missing = desc.isna() | desc.str.strip().eq("").fillna(False)
    present = lines["customer_id"].notna()
    return {
        "lines": int(len(lines)),
        "missing_customer_id_lines": int((~present).sum()),
        "known_customer_id_lines": int(present.sum()),
        "missing_or_blank_description_lines": int(desc_missing.sum()),
        "top_stock_codes": _summary(lines["stock_code"]),
        "top_descriptions": _summary(lines["description"]),
        "keyword_probe_line_counts_not_classifications": {
            k: int(desc.str.contains(pattern, flags=re.IGNORECASE, regex=True, na=False).sum())
            for k, pattern in KEYWORD_PROBES.items()
        },
    }


def examine_mixed_price_invoices(frame: pd.DataFrame) -> dict:
    required = {"invoice_no", "quantity", "unit_price", "stock_code", "description",
                "customer_id", "invoice_date", "country", "source_sheet", "source_excel_row"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    data = frame.copy().reset_index(drop=True)
    data["invoice_no"] = data["invoice_no"].astype("string").str.strip()
    if data["invoice_no"].isna().any() or data["invoice_no"].eq("").any():
        raise ValueError("Missing invoice IDs require a separate explicit handling policy")
    data["stock_code"] = data["stock_code"].astype("string").str.strip()
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")
    c = data["invoice_no"].str.upper().str.startswith("C").fillna(False)
    zero = ~c & data["quantity"].gt(0).fillna(False) & data["unit_price"].eq(0).fillna(False)
    paid = ~c & data["quantity"].gt(0).fillna(False) & data["unit_price"].gt(0).fillna(False)
    counts = pd.DataFrame({
        "invoice_no": data["invoice_no"], "zero": zero, "paid": paid,
    }).groupby("invoice_no", sort=False).agg(total_lines=("zero", "size"),
                                               zero_lines=("zero", "sum"),
                                               paid_lines=("paid", "sum"))
    mixed = counts.loc[counts["zero_lines"].gt(0) & counts["paid_lines"].gt(0)]
    only_zero = counts.loc[counts["zero_lines"].gt(0) & counts["zero_lines"].eq(counts["total_lines"])]
    other_no_paid = counts.loc[counts["zero_lines"].gt(0) & counts["paid_lines"].eq(0)
                               & counts["zero_lines"].lt(counts["total_lines"])]
    mixed_z = data.loc[zero & data["invoice_no"].isin(mixed.index)]
    mixed_p = data.loc[paid & data["invoice_no"].isin(mixed.index)]
    other_z = data.loc[zero & ~data["invoice_no"].isin(mixed.index)]

    # Identical stock code elsewhere on the SAME invoice is descriptive only.
    paid_pairs = set(zip(mixed_p["invoice_no"].astype(str), mixed_p["stock_code"].astype(str)))
    same_code = pd.Series([
        pd.notna(code) and (str(inv), str(code)) in paid_pairs
        for inv, code in zip(mixed_z["invoice_no"], mixed_z["stock_code"])
    ], dtype="bool")
    assert len(mixed_z) == int(mixed["zero_lines"].sum())
    assert int(zero.sum()) == len(mixed_z) + len(other_z)
    assert len(only_zero) + len(other_no_paid) + len(mixed) == int(counts["zero_lines"].gt(0).sum())

    return {
        "status": "descriptive_mixed_invoice_zero_price_context_not_verified_promotions",
        "candidate_view_rows": int(len(data)),
        "non_C_positive_zero_price_lines": int(zero.sum()),
        "non_C_positive_positive_price_lines": int(paid.sum()),
        "invoice_composition": {
            "invoice_ids_with_positive_zero_price_lines": int(counts["zero_lines"].gt(0).sum()),
            "invoice_ids_with_both_zero_and_positive_price_positive_quantity_lines": int(len(mixed)),
            "invoice_ids_only_positive_zero_price_lines": int(len(only_zero)),
            "invoice_ids_with_zero_lines_and_other_types_but_no_paid_lines": int(len(other_no_paid)),
            "zero_price_lines_in_mixed_invoices": int(len(mixed_z)),
            "positive_priced_lines_in_mixed_invoices": int(len(mixed_p)),
            "zero_price_lines_not_in_mixed_invoices": int(len(other_z)),
        },
        "mixed_invoice_per_invoice_distribution": {
            "zero_lines_median": float(mixed["zero_lines"].median()) if len(mixed) else None,
            "zero_lines_max": int(mixed["zero_lines"].max()) if len(mixed) else None,
            "positive_priced_lines_median": float(mixed["paid_lines"].median()) if len(mixed) else None,
            "positive_priced_lines_max": int(mixed["paid_lines"].max()) if len(mixed) else None,
            "invoice_ids_where_any_zero_line_has_same_stock_code_as_paid_line": int(
                mixed_z.loc[same_code.to_numpy(), "invoice_no"].nunique()
            ),
            "zero_lines_with_same_code_as_paid_line_on_same_invoice": int(same_code.sum()),
        },
        "zero_lines_on_mixed_invoices": _describe_lines(mixed_z),
        "zero_lines_not_on_mixed_invoices": _describe_lines(other_z),
        "paid_lines_on_mixed_invoices": _describe_lines(mixed_p),
        "guardrails": [
            "Mixed paid-looking invoice composition is NOT evidence of promotion, giveaway or bundled purchase.",
            "Keyword probes can overlap and are not commercial or accounting classifications.",
            "Shared stock code within an invoice cannot establish why one line has unit price zero.",
            "Customer ID presence is aggregated only; actual customer identifiers are never exported.",
            "No rows, Case 008 canonical links, Case 009 scenarios or business KPI rules are modified.",
        ],
    }


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = examine_mixed_price_invoices(candidate)
    assert result["candidate_view_rows"] == layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"] = int(len(provenance))
    result["cross_sheet_canonical_links"] = int(layer["canonical_links_for_suppressed_rows"])
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    p.add_argument("--output", type=Path, default=Path("outputs/mixed_price_invoices.json"))
    p.add_argument("--prior-price-paradox", type=Path, default=Path("outputs/price_paradox.json"))
    args = p.parse_args()
    result = investigate_original_workbook(pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl"))
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_price_paradox.is_file():
        prior = json.loads(args.prior_price_paradox.read_text(encoding="utf-8"))
        pzero = prior["zero_price_positive_lines"]
        context = pzero["invoice_context"]
        current = result["invoice_composition"]
        assert result["non_C_positive_zero_price_lines"] == pzero["lines"]
        assert current["invoice_ids_with_both_zero_and_positive_price_positive_quantity_lines"] == context["invoice_ids_also_containing_positive_price_positive_lines"]
        assert current["invoice_ids_only_positive_zero_price_lines"] == context["invoice_ids_containing_only_zero_price_positive_lines"]
        assert current["zero_price_lines_in_mixed_invoices"] == context["zero_price_lines_on_invoices_with_positive_priced_lines"]
        result["agrees_with_case_013_cohort_counts"] = True
    else:
        result["agrees_with_case_013_cohort_counts"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
