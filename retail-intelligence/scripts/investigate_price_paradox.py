"""Case 013 — Price Paradox: positive quantities at zero or negative unit prices.

Read-only exploration of the Case 008 reversible source view. No zero-priced
line is automatically called a gift, sample, inventory discovery or sale.
Negative unit prices are reported as anomalies, not assumed discounts/refunds.
Only aggregate statistics and five bounded invoice examples are published.
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


def _small_value(x: object) -> str | None:
    if pd.isna(x):
        return None
    return str(x).strip()[:140]


def _top_counts(series: pd.Series, n: int = 12) -> list[dict]:
    values = series.astype("string").str.strip().fillna("<missing>").replace("", "<blank>")
    return [
        {"value": str(key), "lines": int(value)}
        for key, value in values.value_counts(dropna=False).head(n).items()
    ]


def examine_price_paradox(frame: pd.DataFrame) -> dict:
    df = frame.reset_index(drop=True).copy()
    required = {
        "invoice_no", "stock_code", "description", "quantity", "unit_price",
        "country", "customer_id", "invoice_date", "source_sheet", "source_excel_row",
    }
    if required - set(df.columns):
        raise ValueError(f"Missing required source fields: {sorted(required-set(df.columns))}")
    df["invoice_no"] = df["invoice_no"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    c = df["invoice_no"].str.upper().str.startswith("C").fillna(False)
    positive = df["quantity"].gt(0).fillna(False) & ~c
    free_shape = positive & df["unit_price"].eq(0).fillna(False)
    neg_price = positive & df["unit_price"].lt(0).fillna(False)
    priced = positive & df["unit_price"].gt(0).fillna(False)
    z = df.loc[free_shape].copy()
    n = df.loc[neg_price].copy()

    # Same stock code occurs elsewhere at a positive unit price; this does
    # NOT demonstrate zero-price line was a normal sale, gift, or product.
    priced_codes = set(df.loc[priced, "stock_code"].dropna().tolist())
    z_code_also_priced = z["stock_code"].isin(priced_codes)
    z["_same_code_positive_priced_elsewhere"] = z_code_also_priced

    df["_zero"] = free_shape
    df["_negprice"] = neg_price
    df["_priced"] = priced
    all_inv = df.groupby("invoice_no", dropna=False, sort=False).agg(
        total_lines=("invoice_no", "size"),
        zero_positive_lines=("_zero", "sum"),
        negative_price_positive_lines=("_negprice", "sum"),
        positive_priced_lines=("_priced", "sum"),
    )
    zero_inv = all_inv.loc[all_inv["zero_positive_lines"].gt(0)]
    neg_inv = all_inv.loc[all_inv["negative_price_positive_lines"].gt(0)]
    assert int(zero_inv["zero_positive_lines"].sum()) == len(z)
    assert int(neg_inv["negative_price_positive_lines"].sum()) == len(n)
    z_with_paid = zero_inv["positive_priced_lines"].gt(0)
    z_only = zero_inv["zero_positive_lines"].eq(zero_inv["total_lines"])
    z_mixed_without_paid = ~z_with_paid & ~z_only

    # For each anomalous negative-price line publish bounded invoice context
    # without actual customer identifiers or other invoice-line content.
    neg_examples = []
    n_copy = n.copy()
    n_copy["_magnitude"] = (
        n_copy["quantity"].astype("float64") * n_copy["unit_price"].astype("float64")
    ).abs()
    for _, row in n_copy.sort_values("_magnitude", ascending=False).head(12).iterrows():
        inv_id = str(row["invoice_no"])
        context = neg_inv.loc[inv_id]
        neg_examples.append({
            "invoice_id": inv_id,
            "source_sheet": str(row["source_sheet"]),
            "source_excel_row": int(row["source_excel_row"]),
            "date": row["invoice_date"].isoformat() if pd.notna(row["invoice_date"]) else None,
            "stock_code": _small_value(row["stock_code"]),
            "description": _small_value(row["description"]),
            "quantity": float(row["quantity"]),
            "unit_price_gbp": float(row["unit_price"]),
            "signed_line_amount_gbp_not_validated_adjustment": round(
                float(row["quantity"] * row["unit_price"]), 2
            ),
            "customer_id_present": bool(pd.notna(row["customer_id"])),
            "invoice_total_lines": int(context["total_lines"]),
            "invoice_other_positive_priced_lines": int(context["positive_priced_lines"]),
            "invoice_zero_price_positive_lines": int(context["zero_positive_lines"]),
        })

    zero_quantity = z["quantity"].astype("float64")
    negative_signed = (
        n["quantity"].astype("float64") * n["unit_price"].astype("float64")
    ).sum()
    raw_positive_non_C_zero = int(z["quantity"].gt(0).sum())
    assert raw_positive_non_C_zero == len(z)

    return {
        "status": "exploratory_source_price_paradox_no_classifications_approved",
        "candidate_view_rows": int(len(df)),
        "source_observed_cohorts": {
            "non_C_positive_quantity_zero_price": int(len(z)),
            "non_C_positive_quantity_negative_price": int(len(n)),
            "non_C_positive_quantity_positive_price": int(priced.sum()),
        },
        "zero_price_positive_lines": {
            "lines": int(len(z)),
            "customer_id_present_lines": int(z["customer_id"].notna().sum()),
            "customer_id_missing_lines": int(z["customer_id"].isna().sum()),
            "distinct_invoice_ids": int(z["invoice_no"].nunique()),
            "distinct_stock_codes": int(z["stock_code"].nunique()),
            "lines_with_code_also_positive_priced_elsewhere": int(
                z_code_also_priced.sum()
            ),
            "distinct_codes_also_positive_priced_elsewhere": int(
                z.loc[z_code_also_priced, "stock_code"].nunique()
            ),
            "distinct_codes_never_seen_positive_priced_elsewhere": int(
                z.loc[~z_code_also_priced, "stock_code"].nunique()
            ),
            "quantity_distribution": {
                "min": float(zero_quantity.min()) if len(z) else None,
                "median": float(zero_quantity.median()) if len(z) else None,
                "p90": float(zero_quantity.quantile(.9)) if len(z) else None,
                "max": float(zero_quantity.max()) if len(z) else None,
            },
            "invoice_context": {
                "invoice_ids_with_zero_price_positive_line": int(len(zero_inv)),
                "invoice_ids_containing_only_zero_price_positive_lines": int(z_only.sum()),
                "invoice_ids_also_containing_positive_price_positive_lines": int(z_with_paid.sum()),
                "invoice_ids_with_other_nonpriced_types_but_no_positive_priced_lines": int(z_mixed_without_paid.sum()),
                "zero_price_lines_on_invoices_with_positive_priced_lines": int(
                    zero_inv.loc[z_with_paid, "zero_positive_lines"].sum()
                ),
            },
            "description_top_15": _top_counts(z["description"], 15),
            "stock_code_top_15": _top_counts(z["stock_code"], 15),
            "country_top_10": _top_counts(z["country"], 10),
            "month_counts": {
                str(k): int(v)
                for k, v in z["invoice_date"].dt.strftime("%Y-%m").value_counts().sort_index().items()
            },
        },
        "negative_unit_price_positive_lines": {
            "lines": int(len(n)),
            "signed_line_amount_sum_gbp_not_validated_adjustment": round(float(negative_signed), 2),
            "distinct_invoice_ids": int(n["invoice_no"].nunique()),
            "customer_id_present_lines": int(n["customer_id"].notna().sum()),
            "invoice_ids_also_containing_positive_priced_lines": int(
                neg_inv["positive_priced_lines"].gt(0).sum()
            ),
            "top_5_source_line_examples": neg_examples[:5],
        },
        "guardrails": [
            "Zero price is not evidence of a giveaway, completed sale, theft or stocktake without independent business context.",
            "The same stock code appearing with a positive price elsewhere is contextual evidence only; it does not establish why the zero-price posting exists.",
            "Negative unit price could be a correction, discount, error or another accounting convention. Signed amounts are not validated revenue or refunded cash.",
            "The S0, S1 and S2 gross positive-priced definitions exclude zero and negative prices and are not changed.",
            "Invoice-ID grouping is within the cross-sheet-reconciled candidate view; distinct line records inside an invoice are preserved.",
            "Only bounded public invoice examples and aggregate counts are exported; no individual customer IDs are published.",
            "All original workbook lines and provenance remain intact.",
        ],
    }


def investigate_original_workbook(sheets: dict[str, pd.DataFrame]) -> dict:
    candidate, provenance, layer = build_candidate_layer(sheets)
    result = examine_price_paradox(candidate)
    assert result["candidate_view_rows"] == layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"] = int(len(provenance))
    result["cross_sheet_canonical_links"] = layer["canonical_links_for_suppressed_rows"]
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    p.add_argument("--output", type=Path, default=Path("outputs/price_paradox.json"))
    p.add_argument("--prior-revenue-sensitivity", type=Path,
                   default=Path("outputs/revenue_sensitivity.json"))
    args = p.parse_args()
    result = investigate_original_workbook(
        pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    )
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_revenue_sensitivity.is_file():
        prev = json.loads(args.prior_revenue_sensitivity.read_text(encoding="utf-8"))
        prior = prev["cross_sheet_reconciled_candidate"]["mutually_exclusive_line_cohorts"]
        current = result["source_observed_cohorts"]
        assert current["non_C_positive_quantity_zero_price"] == prior["positive_non_c_zero_price"]
        assert current["non_C_positive_quantity_negative_price"] == prior["positive_non_c_negative_price"]
        assert current["non_C_positive_quantity_positive_price"] == prior["positive_non_c_positive_price"]
        result["agrees_with_case_009_cohort_counts"] = True
    else:
        result["agrees_with_case_009_cohort_counts"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
