"""Export independently verified aggregate-only Power BI CSV tables.

Source: Case 018 SQL + Cases 019–021 source-reconciled aggregate JSON.
No workbook, source invoice-line records or customer/invoice IDs are exported.
Tables have distinct grains; they must not be joined as transaction data.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SCENARIOS = (
    "S0_all_positive_priced_non_C",
    "S1_exclude_named_shipping_and_billing_code_candidates",
    "S2_also_exclude_manual_and_discount_code_candidates",
)
SOURCE_HASH = "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"


def _check(sql: dict, monthly: dict, concentration: dict, sku: dict) -> None:
    """Fail closed before creating CSV outputs if any input is unreconciled."""
    if sql.get("agrees_with_case_009_counts_invoice_ids_and_amounts") is not True:
        raise ValueError("Case 018 SQL reconciliation is missing")
    if monthly.get("all_25_months_reconcile_to_case_018_s2_amount_within_5p") is not True:
        raise ValueError("Case 019 monthly reconciliation is missing")
    if sku.get("status") != "sku_quantity_and_effective_value_decomposition_not_causal_pricing":
        raise ValueError("Case 021 source-verified decomposition required")
    if sku.get("years") != [2010, 2011] or sku.get("calendar_months_compared") != list(range(1, 12)):
        raise ValueError("Case 021 comparable month window changed")
    if sql.get("source_workbook_sha256_from_case_009") != SOURCE_HASH:
        raise ValueError("Unexpected original workbook SHA-256")
    if concentration.get("source_workbook_sha256_from_case_018") != SOURCE_HASH:
        raise ValueError("Case 020 source workbook mismatch")
    if sku.get("source_workbook_sha256_from_case_018") != SOURCE_HASH:
        raise ValueError("Case 021 source workbook mismatch")
    if len(sql["monthly_s2_recorded_activity"]) != 25:
        raise ValueError("Expected 25 source months")
    if len(monthly["monthly_yoy"]) != 11:
        raise ValueError("Expected 11 Jan-Nov matched-month comparisons")
    if len(concentration["monthly_id_concentration"]) != 25 or len(concentration["comparable_jan_nov_period_concentration"]) != 2:
        raise ValueError("Concentration cohort grain/coverage changed")
    if len(sku["top_15_skus_by_absolute_gross_change_aggregate_only"]) > 15:
        raise ValueError("Unbounded SKU export is not permitted")

    differences = (
        float(monthly["s2_gross_positive_line_amount_change_gbp"]),
        float(sku["decomposition_gross_change_gbp"]),
        float(monthly["later"]["s2_gross_positive_line_amount_gbp_not_revenue"]) -
        float(monthly["earlier"]["s2_gross_positive_line_amount_gbp_not_revenue"]),
    )
    if max(differences) - min(differences) > .02:
        raise AssertionError("Case 019 and Case 021 gross period changes disagree")
    if abs(sum(map(float, sku["identity_components_gbp"].values())) - differences[1]) > .02:
        raise AssertionError("Four SKU identity components do not balance")
    s2 = sql["scenario_reconciliation"][SCENARIOS[-1]]
    if int(s2["lines"]) != sum(int(x["s2_positive_priced_lines"]) for x in sql["monthly_s2_recorded_activity"]):
        raise AssertionError("Monthly S2 line count does not match SQL baseline")
    if abs(sum(float(x["s2_gross_positive_line_amount_gbp_not_accounting_revenue"]) for x in sql["monthly_s2_recorded_activity"]) - float(s2["hypothetical_gross_line_amount_gbp"])) > .05:
        raise AssertionError("Monthly S2 gross sums do not match SQL baseline")
    for i, year in enumerate((2010, 2011)):
        aggregate = monthly["earlier" if i == 0 else "later"]
        c = concentration["comparable_jan_nov_period_concentration"][i]
        s = sku["periods_reconciled_independently_to_case_018_sql"][i]
        if int(c["year"]) != year or int(s["year"]) != year:
            raise ValueError("Source periods are not in matching calendar order")
        expected = float(aggregate["s2_gross_positive_line_amount_gbp_not_revenue"])
        if any(abs(float(x) - expected) > .02 for x in (
            c["s2_gross_line_amount_gbp_not_revenue"],
            s["gross_positive_line_amount_gbp_not_revenue"],
        )):
            raise AssertionError("Yearly concentration/SKU gross sums diverged")
        if int(aggregate["s2_lines"]) != int(s["s2_source_lines"]):
            raise AssertionError("Case 021 line count does not reconcile to Case 019")


def _curate(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    """Explicit column whitelist prevents row-level identifiers escaping."""
    if not rows:
        raise ValueError("Cannot export a table with no rows")
    if any("invoice_no" in col or col in {"customer_id", "source_excel_row"} for col in fields):
        raise ValueError("Row-level identifiers must never be exported")
    return [{col: row[col] for col in fields} for row in rows]


def assemble_tables(sql: dict, monthly: dict, concentration: dict, sku: dict) -> dict[str, list[dict]]:
    _check(sql, monthly, concentration, sku)
    scenario = sql["scenario_reconciliation"]
    tables = {
        "monthly_activity.csv": _curate(sql["monthly_s2_recorded_activity"], (
            "recorded_month", "candidate_source_lines", "s2_positive_priced_lines",
            "s2_gross_positive_line_amount_gbp_not_accounting_revenue",
            "s2_distinct_qualifying_invoice_ids_not_orders",
            "s2_recorded_positive_units_not_verified_shipments", "s2_known_customer_id_lines",
            "source_cancellation_coded_lines_not_refunds", "source_zero_price_positive_lines_not_gifts",
        )),
        "matched_month_yoy.csv": _curate(monthly["monthly_yoy"], (
            "calendar_month_number", "earlier_recorded_month", "later_recorded_month",
            "earlier_s2_gross_positive_line_amount_gbp", "later_s2_gross_positive_line_amount_gbp",
            "change_pct_not_demand_growth",
        )),
        "monthly_invoice_concentration.csv": _curate(concentration["monthly_id_concentration"], (
            "recorded_month", "invoice_id_month_groups_not_confirmed_orders",
            "s2_gross_line_amount_gbp_not_revenue", "upper_one_percent_id_month_groups_count",
            "upper_one_percent_gross_line_amount_gbp_not_revenue",
            "upper_one_percent_share_of_gross_line_amount_not_verified_market_share",
            "gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only",
            "median_id_month_gross_line_amount_gbp", "ninety_fifth_percentile_id_month_gross_line_amount_gbp",
            "maximum_single_id_month_gross_line_amount_gbp", "maximum_single_id_month_share_of_total",
        )),
        "period_invoice_concentration.csv": _curate(concentration["comparable_jan_nov_period_concentration"], (
            "year", "invoice_id_month_groups_not_confirmed_orders",
            "s2_gross_line_amount_gbp_not_revenue", "upper_one_percent_id_month_groups_count",
            "upper_one_percent_gross_line_amount_gbp_not_revenue",
            "upper_one_percent_share_of_gross_line_amount_not_verified_market_share",
            "gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only",
            "median_id_month_gross_line_amount_gbp", "ninety_fifth_percentile_id_month_gross_line_amount_gbp",
            "maximum_single_id_month_gross_line_amount_gbp", "maximum_single_id_month_share_of_total",
        )),
        "scenario_sensitivity.csv": _curate([
            {"scenario_code": name, **scenario[name]} for name in SCENARIOS
        ], ("scenario_code", "lines", "invoice_ids", "hypothetical_gross_line_amount_gbp")),
        "sku_change_components.csv": _curate([
            {"component": name, "signed_gross_line_amount_gbp": amount}
            for name, amount in sku["identity_components_gbp"].items()
        ], ("component", "signed_gross_line_amount_gbp")),
        "sku_presence_cohorts.csv": _curate([
            {"cohort": "present_both_years", "stock_code_count": sku["stock_code_groups_present_in_both_years"]},
            {"cohort": "only_later_year", "stock_code_count": sku["stock_code_groups_only_in_later_year"]},
            {"cohort": "only_earlier_year", "stock_code_count": sku["stock_code_groups_only_in_earlier_year"]},
        ], ("cohort", "stock_code_count")),
        "top_sku_aggregate_examples.csv": _curate(sku["top_15_skus_by_absolute_gross_change_aggregate_only"], (
            "stock_code", "source_observed_group", "earlier_s2_amount_gbp", "later_s2_amount_gbp",
            "signed_change_gbp", "earlier_recorded_positive_units", "later_recorded_positive_units",
        )),
    }
    assert [len(x) for x in tables.values()] == [25, 11, 25, 2, 3, 4, 3, len(sku["top_15_skus_by_absolute_gross_change_aggregate_only"])]
    return tables


def export_tables(tables: dict[str, list[dict]], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in tables.items():
        if "/" in filename or "\\" in filename or not filename.endswith(".csv"):
            raise ValueError("Unexpected output filename")
        path = out_dir / filename
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]), extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
    return {name: len(rows) for name, rows in tables.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql", type=Path, default=Path("outputs/sql_kpi_workbench.json"))
    parser.add_argument("--monthly", type=Path, default=Path("outputs/monthly_business_activity.json"))
    parser.add_argument("--concentration", type=Path, default=Path("outputs/invoice_concentration.json"))
    parser.add_argument("--sku", type=Path, default=Path("outputs/sku_composition.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/powerbi_tables"))
    args = parser.parse_args()
    tables = assemble_tables(*[json.loads(p.read_text(encoding="utf-8")) for p in (
        args.sql, args.monthly, args.concentration, args.sku
    )])
    counts = export_tables(tables, args.out_dir)
    print(json.dumps({"status": "verified_aggregate_only_powerbi_import", "files": counts}, indent=2))


if __name__ == "__main__":
    main()
