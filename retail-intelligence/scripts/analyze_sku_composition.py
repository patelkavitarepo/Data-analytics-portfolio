"""Case 021 — recorded quantity vs per-SKU gross-per-unit decomposition.

Identity-based DESCRIPTIVE accounting of changes in exploratory S2 line
amounts across matched January–November 2010 / 2011 source records.

This is not an inflation index, genuine pricing analysis, demand inference,
a counterfactual, or recognized revenue. Exact source/provenance preserved.
No customer or invoice IDs are published.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


EXCLUDED = frozenset({
    "POST", "DOT", "C2", "BANK CHARGES", "AMAZONFEE", "M", "D"
})
AMOUNT = "s2_gross_positive_line_amount_gbp_not_accounting_revenue"
UNITS = "s2_recorded_positive_units_not_verified_shipments"
LINES = "s2_positive_priced_lines"
SOURCE_SKU_UNKNOWN = "<missing_stock_code>"


def _period_from_sql(sql: dict, year: int, months: tuple[int, ...]) -> tuple[float, float, int]:
    source = sql["monthly_s2_recorded_activity"]
    lookup = {str(row["recorded_month"]): row for row in source}
    if len(lookup) != len(source):
        raise ValueError("Duplicate SQL month rows")
    picked = []
    for m in months:
        key = f"{year:04d}-{m:02d}"
        if key not in lookup:
            raise ValueError("Missing matched month in SQL reference: " + key)
        picked.append(lookup[key])
    return (
        sum(float(x[AMOUNT]) for x in picked),
        sum(float(x[UNITS]) for x in picked),
        sum(int(x[LINES]) for x in picked),
    )


def analyze_sku_composition(
    source: pd.DataFrame,
    verified_sql: dict,
    months: tuple[int, ...] = tuple(range(1, 12)),
    years: tuple[int, int] = (2010, 2011),
) -> dict:
    required = {"invoice_no", "stock_code", "quantity", "unit_price", "invoice_date"}
    if missing := sorted(required.difference(source.columns)):
        raise ValueError(f"Missing candidate fields: {missing}")
    if not verified_sql.get("agrees_with_case_009_counts_invoice_ids_and_amounts"):
        raise ValueError("Source-reconciled independent SQL summary is mandatory")
    if len(years) != 2 or years[0] == years[1]:
        raise ValueError("Two distinct comparison years required")
    if not months or len(set(months)) != len(months) or any(
        not isinstance(m, int) or m < 1 or m > 12 for m in months
    ):
        raise ValueError("Invalid comparable month set")

    d = source[list(required)].copy()
    d["invoice_no"] = d["invoice_no"].astype("string").str.strip()
    if d["invoice_no"].isna().any() or d["invoice_no"].eq("").any():
        raise ValueError("Missing invoice ID requires separate reconciliation")
    d["stock_code"] = d["stock_code"].astype("string").str.strip().str.upper()
    d["quantity"] = pd.to_numeric(d["quantity"], errors="coerce")
    d["unit_price"] = pd.to_numeric(d["unit_price"], errors="coerce")
    d["invoice_date"] = pd.to_datetime(d["invoice_date"], errors="coerce")
    non_c = ~d["invoice_no"].str.upper().str.startswith("C").fillna(False)
    valid = (
        non_c
        & d["quantity"].gt(0).fillna(False)
        & d["unit_price"].gt(0).fillna(False)
        & ~d["stock_code"].isin(EXCLUDED)
    )
    s2 = d.loc[valid].copy()
    if s2["invoice_date"].isna().any():
        raise ValueError("S2 row has missing invoice date")
    s2["year"] = s2["invoice_date"].dt.year
    s2["month"] = s2["invoice_date"].dt.month
    selected = s2.loc[s2["year"].isin(years) & s2["month"].isin(months)].copy()
    selected["sku_key"] = selected["stock_code"].fillna(SOURCE_SKU_UNKNOWN)
    selected["gross_line_amount"] = selected["quantity"] * selected["unit_price"]

    # No source-record-level results are emitted. Aggregate by SKU/year first.
    by_sku = selected.groupby(
        ["year", "sku_key"], sort=False, observed=True
    ).agg(
        recorded_units=("quantity", "sum"),
        gross_positive_line_amount=("gross_line_amount", "sum"),
        qualifying_source_lines=("quantity", "size"),
    ).reset_index()
    a, b = years
    left = by_sku.loc[by_sku["year"].eq(a)].drop(columns="year").rename(columns={
        "recorded_units": "units_a",
        "gross_positive_line_amount": "gross_a",
        "qualifying_source_lines": "lines_a",
    })
    right = by_sku.loc[by_sku["year"].eq(b)].drop(columns="year").rename(columns={
        "recorded_units": "units_b",
        "gross_positive_line_amount": "gross_b",
        "qualifying_source_lines": "lines_b",
    })
    merged = left.merge(right, on="sku_key", how="outer", validate="one_to_one")
    for col in ("units_a", "gross_a", "lines_a", "units_b", "gross_b", "lines_b"):
        merged[col] = merged[col].fillna(0)
    common = merged["units_a"].gt(0) & merged["units_b"].gt(0)
    entrants = merged["units_a"].eq(0) & merged["units_b"].gt(0)
    exits = merged["units_b"].eq(0) & merged["units_a"].gt(0)
    if not (common | entrants | exits).all():
        raise AssertionError("Unexpected SKU cohort with no positive units")

    # An exact algebraic identity for a common SKU:
    # Δgross = Δunits * (grossA/unitsA)
    #         + unitsB * (grossB/unitsB - grossA/unitsA).
    # The latter is an observed effective per-unit VALUE component, not
    # evidence of a change in the seller's posted unit price.
    both = merged.loc[common].copy()
    old_effective = both["gross_a"] / both["units_a"]
    both["quantity_component"] = (both["units_b"] - both["units_a"]) * old_effective
    both["effective_value_per_unit_component"] = (
        both["gross_b"] - both["units_b"] * old_effective
    )
    both["gross_change"] = both["gross_b"] - both["gross_a"]
    if not (
        (both["quantity_component"] + both["effective_value_per_unit_component"]
         - both["gross_change"]).abs().max() if len(both) else 0
    ) < 0.01:
        raise AssertionError("SKU algebra does not reconcile")

    quantity_change = float(both["quantity_component"].sum())
    effective_change = float(both["effective_value_per_unit_component"].sum())
    entrants_value = float(merged.loc[entrants, "gross_b"].sum())
    exits_value = -float(merged.loc[exits, "gross_a"].sum())
    total_year_a = float(merged["gross_a"].sum())
    total_year_b = float(merged["gross_b"].sum())
    gross_delta = total_year_b - total_year_a
    bridge_sum = quantity_change + effective_change + entrants_value + exits_value
    if abs(gross_delta - bridge_sum) > 0.05:
        raise AssertionError("SKU decomposition sum differs from gross change")

    # Independent SQL agreement for EACH matched year before interpreting.
    yearly = []
    for year, total, unit, line in [
        (a, total_year_a, float(merged["units_a"].sum()), int(merged["lines_a"].sum())),
        (b, total_year_b, float(merged["units_b"].sum()), int(merged["lines_b"].sum())),
    ]:
        expected_total, expected_unit, expected_line = _period_from_sql(
            verified_sql, year, months
        )
        if abs(total - expected_total) > 0.05:
            raise AssertionError(f"Year {year} S2 gross amount does not match SQL")
        if abs(unit - expected_unit) > 0.001:
            raise AssertionError(f"Year {year} recorded units do not match SQL")
        if line != expected_line:
            raise AssertionError(f"Year {year} S2 line counts do not match SQL")
        yearly.append({
            "year": year,
            "gross_positive_line_amount_gbp_not_revenue": round(total, 2),
            "recorded_positive_units_not_verified_shipments": unit,
            "s2_source_lines": line,
            "stock_codes_with_qualifying_s2_lines": int(
                (merged["units_a"] if year == a else merged["units_b"]).gt(0).sum()
            ),
            "gross_positive_line_amount_per_recorded_unit_not_price_inflation":
                round(total / unit, 6) if unit else None,
        })

    merged["gross_change"] = merged["gross_b"] - merged["gross_a"]
    top = merged.reindex(
        merged["gross_change"].abs().sort_values(ascending=False).index
    ).head(15)
    examples = [{
        "stock_code": str(x["sku_key"]),
        "source_observed_group": ("present_both_years" if x["units_a"] > 0 and x["units_b"] > 0
                                  else "only_later_year" if x["units_b"] > 0
                                  else "only_earlier_year"),
        "earlier_s2_amount_gbp": round(float(x["gross_a"]), 2),
        "later_s2_amount_gbp": round(float(x["gross_b"]), 2),
        "signed_change_gbp": round(float(x["gross_change"]), 2),
        "earlier_recorded_positive_units": float(x["units_a"]),
        "later_recorded_positive_units": float(x["units_b"]),
    } for _, x in top.iterrows()]

    return {
        "status": "sku_quantity_and_effective_value_decomposition_not_causal_pricing",
        "years": [a, b],
        "calendar_months_compared": list(months),
        "candidate_rows_in_input": int(len(d)),
        "matched_period_s2_lines": int(len(selected)),
        "periods_reconciled_independently_to_case_018_sql": yearly,
        "stock_code_groups_present_in_both_years": int(common.sum()),
        "stock_code_groups_only_in_later_year": int(entrants.sum()),
        "stock_code_groups_only_in_earlier_year": int(exits.sum()),
        "decomposition_gross_change_gbp": round(gross_delta, 2),
        "identity_components_gbp": {
            "common_skus_recorded_quantity_component": round(quantity_change, 2),
            "common_skus_effective_gross_per_unit_component": round(effective_change, 2),
            "new_only_later_year_sku_gross_contribution": round(entrants_value, 2),
            "disappeared_only_earlier_year_sku_gross_contribution": round(exits_value, 2),
        },
        "top_15_skus_by_absolute_gross_change_aggregate_only": examples,
        "guardrails": [
            "This is an arithmetic identity, not a causal decomposition or statistical explanation.",
            "The effective gross-per-unit component can move with within-SKU discounting, price, product-code reuse, or mix, not only posted price.",
            "SKU groups present only in one year are not verified new/discontinued products; source coverage can change.",
            "The source includes wholesale-like invoices, missing customers, ambiguous codes, partial December 2011 and no verified settlement or shipment information.",
            "All values are exploratory S2 gross positive-priced line amounts; not net or recognized revenue, profit or true demand.",
            "SKU examples are aggregate product-code changes, not individual invoices, customer IDs or accounting-validated categories.",
            "All source records, Case 008 exact-copy provenance and S0/S1/S2 definitions remain unchanged.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, default=Path("data/derived/candidate_analysis_lines.csv.gz"))
    p.add_argument("--sql-summary", type=Path, default=Path("outputs/sql_kpi_workbench.json"))
    p.add_argument("--output", type=Path, default=Path("outputs/sku_composition.json"))
    args = p.parse_args()
    if not args.candidate.is_file() or not args.sql_summary.is_file():
        raise FileNotFoundError("Local Case 008 candidate and verified Case 018 summary required")
    candidate = pd.read_csv(
        args.candidate, compression="gzip", low_memory=False,
        usecols=["invoice_no", "stock_code", "quantity", "unit_price", "invoice_date"],
        dtype={"invoice_no": "string", "stock_code": "string"},
    )
    sql = json.loads(args.sql_summary.read_text(encoding="utf-8"))
    out = analyze_sku_composition(candidate, sql)
    out["source_workbook_sha256_from_case_018"] = sql["source_workbook_sha256_from_case_009"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": out["status"],
        "matched_period_s2_lines": out["matched_period_s2_lines"],
        "periods_reconciled_to_sql": out["periods_reconciled_independently_to_case_018_sql"],
        "gross_change_gbp": out["decomposition_gross_change_gbp"],
        "identity_components_gbp": out["identity_components_gbp"],
        "sku_cohort_counts": {
            "common": out["stock_code_groups_present_in_both_years"],
            "only_later": out["stock_code_groups_only_in_later_year"],
            "only_earlier": out["stock_code_groups_only_in_earlier_year"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
