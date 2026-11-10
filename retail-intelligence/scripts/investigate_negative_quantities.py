"""Evidence-only diagnostics of negative quantities in UCI Online Retail II.

Count the overlap of invoice cancellation markers and quantity signs. No rows
are excluded or reclassified, no financial measure is calculated, and the
cause of non-C negative quantities is treated as unknown.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

try:
    from scripts.audit import normalize_columns, sha256_file
except ModuleNotFoundError:
    from audit import normalize_columns, sha256_file


def _counts(series: pd.Series, limit: int = 12) -> list[dict]:
    cleaned = series.astype("string").str.strip().replace("", pd.NA).dropna()
    counts = cleaned.value_counts().head(limit)
    return [{"value": str(v), "rows": int(n)} for v, n in counts.items()]


def investigate(sheets: dict[str, pd.DataFrame]) -> dict:
    if not sheets:
        raise ValueError("No sheets supplied")
    normalized = {str(name): normalize_columns(raw) for name, raw in sheets.items()}
    df = pd.concat(normalized.values(), keys=normalized.keys(), names=["sheet", "source_index"])
    df = df.reset_index(level="source_index", drop=True).reset_index(names="sheet")
    invoice = df["invoice_no"].astype("string").str.strip()
    has_c = invoice.str.upper().str.startswith("C").fillna(False)
    qty = pd.to_numeric(df["quantity"], errors="coerce")
    negative = qty.lt(0).fillna(False)
    nonnegative = qty.ge(0).fillna(False)
    price = pd.to_numeric(df["unit_price"], errors="coerce")
    nonc_negative = negative & ~has_c
    c_negative = negative & has_c
    c_nonnegative = nonnegative & has_c
    matrix = {
        "negative_quantity_and_c_prefixed_invoice": int(c_negative.sum()),
        "negative_quantity_and_not_c_prefixed_invoice": int(nonc_negative.sum()),
        "nonnegative_quantity_and_c_prefixed_invoice": int(c_nonnegative.sum()),
        "nonnegative_quantity_and_not_c_prefixed_invoice": int((nonnegative & ~has_c).sum()),
        "quantity_not_numeric_or_missing": int(qty.isna().sum()),
    }
    assert sum(matrix.values()) == len(df)
    assert matrix["negative_quantity_and_c_prefixed_invoice"] + matrix[
        "negative_quantity_and_not_c_prefixed_invoice"
    ] == int(negative.sum())
    mask_groups = {
        "c_prefixed_negative": c_negative,
        "not_c_prefixed_negative": nonc_negative,
        "c_prefixed_nonnegative": c_nonnegative,
    }
    groups = {}
    for label, mask in mask_groups.items():
        subset = df.loc[mask]
        q_subset, p_subset = qty.loc[mask], price.loc[mask]
        groups[label] = {
            "rows": int(mask.sum()),
            "distinct_invoice_ids": int(invoice.loc[mask].replace("", pd.NA).nunique()),
            "distinct_stock_codes": int(subset["stock_code"].nunique(dropna=True)),
            "missing_customer_id_rows": int(subset["customer_id"].isna().sum()),
            "missing_description_rows": int(subset["description"].isna().sum()),
            "zero_unit_price_rows": int((p_subset == 0).sum()),
            "negative_unit_price_rows": int((p_subset < 0).sum()),
            "quantity_min": float(q_subset.min()) if len(q_subset) else None,
            "quantity_max": float(q_subset.max()) if len(q_subset) else None,
            "rows_by_source_sheet": {str(k): int(v) for k, v in subset["sheet"].value_counts().items()},
            "top_stock_codes": _counts(subset["stock_code"]),
            "top_descriptions": _counts(subset["description"], limit=8),
            "top_countries": _counts(subset["country"], limit=8),
        }
    nonc = df.loc[nonc_negative].copy()
    nonc["invoice_date"] = pd.to_datetime(nonc["invoice_date"], errors="coerce")
    nonc["year_month"] = nonc["invoice_date"].dt.strftime("%Y-%m")
    return {
        "status": "observed_from_source_workbook",
        "unit_of_observation": "invoice line; not a unique order",
        "source": "UCI Online Retail II, dataset 502",
        "row_count": int(len(df)),
        "negative_quantity_rows": int(negative.sum()),
        "c_prefixed_invoice_rows": int(has_c.sum()),
        "invoice_prefix_vs_quantity_sign": matrix,
        "groups": groups,
        "non_c_negative_rows_by_month": {
            str(k): int(v) for k, v in nonc["year_month"].value_counts().sort_index().items()
        },
        "interpretation_limits": [
            "UCI documents C-prefixed invoices as cancellations; sign and C prefix are separate observed attributes.",
            "Negative quantities without a C prefix are not automatically returns; causes are unverified.",
            "Rows are invoice lines, not unique invoices or customers.",
            "Zero-price and missing-customer-ID groups can overlap; do not add them.",
            "No rows dropped or reclassified and no revenue calculated.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/negative_quantity_investigation.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    result = investigate(sheets)
    result["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
