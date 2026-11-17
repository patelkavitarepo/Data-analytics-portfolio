"""Case 023: Power BI aggregate export schema, privacy and reconciliation."""
import csv
from pathlib import Path
import json
import pytest
from scripts.export_powerbi_aggregates import (
    SOURCE_HASH, assemble_tables, export_tables,
)


def fixture():
    source_months = [f"{year}-{month:02d}" for year in (2010, 2011)
                     for month in range(1, 13)]
    source_months.insert(0, "2009-12")
    sql_rows, conc_rows = [], []
    for mon in source_months:
        amt = 10 if mon == "2009-12" else 100 if mon.startswith("2010") else 200
        sql_rows.append({
            "recorded_month": mon, "candidate_source_lines": 3,
            "s2_positive_priced_lines": 2,
            "s2_gross_positive_line_amount_gbp_not_accounting_revenue": amt,
            "s2_distinct_qualifying_invoice_ids_not_orders": 1,
            "s2_recorded_positive_units_not_verified_shipments": 2,
            "s2_known_customer_id_lines": 1,
            "source_cancellation_coded_lines_not_refunds": 0,
            "source_zero_price_positive_lines_not_gifts": 1,
        })
        conc_rows.append({
            "recorded_month": mon, "invoice_id_month_groups_not_confirmed_orders": 1,
            "s2_gross_line_amount_gbp_not_revenue": amt,
            "upper_one_percent_id_month_groups_count": 1,
            "upper_one_percent_gross_line_amount_gbp_not_revenue": amt,
            "upper_one_percent_share_of_gross_line_amount_not_verified_market_share": 1,
            "gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only": 0,
            "median_id_month_gross_line_amount_gbp": amt,
            "ninety_fifth_percentile_id_month_gross_line_amount_gbp": amt,
            "maximum_single_id_month_gross_line_amount_gbp": amt,
            "maximum_single_id_month_share_of_total": 1,
        })
    sql = {
        "agrees_with_case_009_counts_invoice_ids_and_amounts": True,
        "source_workbook_sha256_from_case_009": SOURCE_HASH,
        "monthly_s2_recorded_activity": sql_rows,
        "scenario_reconciliation": {
            "S0_all_positive_priced_non_C": {"lines": 56, "invoice_ids": 30, "hypothetical_gross_line_amount_gbp": 4000},
            "S1_exclude_named_shipping_and_billing_code_candidates": {"lines": 54, "invoice_ids": 27, "hypothetical_gross_line_amount_gbp": 3800},
            "S2_also_exclude_manual_and_discount_code_candidates": {"lines": 50, "invoice_ids": 25, "hypothetical_gross_line_amount_gbp": 3610},
        },
    }
    month_yoy = [{"calendar_month_number": m, "earlier_recorded_month": f"2010-{m:02d}",
                  "later_recorded_month": f"2011-{m:02d}",
                  "earlier_s2_gross_positive_line_amount_gbp": 100,
                  "later_s2_gross_positive_line_amount_gbp": 200,
                  "change_pct_not_demand_growth": 100} for m in range(1, 12)]
    monthly = {
        "all_25_months_reconcile_to_case_018_s2_amount_within_5p": True,
        "monthly_yoy": month_yoy,
        "s2_gross_positive_line_amount_change_gbp": 1100,
        "earlier": {"s2_gross_positive_line_amount_gbp_not_revenue": 1100, "s2_lines": 22},
        "later": {"s2_gross_positive_line_amount_gbp_not_revenue": 2200, "s2_lines": 22},
    }
    def period(year, amount):
        sample = dict(conc_rows[0])
        sample.pop("recorded_month")
        sample.update({"year": year, "s2_gross_line_amount_gbp_not_revenue": amount})
        return sample
    conc = {
        "source_workbook_sha256_from_case_018": SOURCE_HASH,
        "monthly_id_concentration": conc_rows,
        "comparable_jan_nov_period_concentration": [period(2010, 1100), period(2011, 2200)],
    }
    sku = {
        "source_workbook_sha256_from_case_018": SOURCE_HASH,
        "status": "sku_quantity_and_effective_value_decomposition_not_causal_pricing",
        "years": [2010, 2011], "calendar_months_compared": list(range(1, 12)),
        "decomposition_gross_change_gbp": 1100,
        "identity_components_gbp": {
            "common_skus_recorded_quantity_component": -100,
            "common_skus_effective_gross_per_unit_component": -50,
            "new_only_later_year_sku_gross_contribution": 1300,
            "disappeared_only_earlier_year_sku_gross_contribution": -50,
        },
        "stock_code_groups_present_in_both_years": 4,
        "stock_code_groups_only_in_later_year": 3,
        "stock_code_groups_only_in_earlier_year": 2,
        "periods_reconciled_independently_to_case_018_sql": [
            {"year": 2010, "gross_positive_line_amount_gbp_not_revenue": 1100, "s2_source_lines": 22},
            {"year": 2011, "gross_positive_line_amount_gbp_not_revenue": 2200, "s2_source_lines": 22},
        ],
        "top_15_skus_by_absolute_gross_change_aggregate_only": [
            {"stock_code": "A", "source_observed_group": "present_both_years",
             "earlier_s2_amount_gbp": 10, "later_s2_amount_gbp": 20,
             "signed_change_gbp": 10, "earlier_recorded_positive_units": 1,
             "later_recorded_positive_units": 2}
        ],
    }
    return sql, monthly, conc, sku


def test_eight_source_verified_tables_and_no_customer_or_invoice_identifiers(tmp_path):
    tables = assemble_tables(*fixture())
    assert len(tables) == 8
    count = export_tables(tables, tmp_path)
    assert count["matched_month_yoy.csv"] == 11
    assert count["sku_change_components.csv"] == 4
    assert count["top_sku_aggregate_examples.csv"] == 1
    for p in tmp_path.glob("*.csv"):
        with p.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert all("invoice_no" not in field and field not in {"customer_id", "source_excel_row"}
                       for field in reader.fieldnames)
            assert sum(1 for _ in reader) > 0


def test_unverified_or_mismatched_original_source_rejected():
    cases = list(fixture())
    cases[0]["agrees_with_case_009_counts_invoice_ids_and_amounts"] = False
    with pytest.raises(ValueError, match="SQL reconciliation"):
        assemble_tables(*cases)
    cases = list(fixture())
    cases[3]["source_workbook_sha256_from_case_018"] = "unknown"
    with pytest.raises(ValueError, match="workbook mismatch"):
        assemble_tables(*cases)


def test_rejects_inconsistent_source_totals():
    cases = list(fixture())
    cases[1]["s2_gross_positive_line_amount_change_gbp"] = 1400
    with pytest.raises(AssertionError, match="disagree"):
        assemble_tables(*cases)
    cases = list(fixture())
    cases[3]["identity_components_gbp"]["new_only_later_year_sku_gross_contribution"] = 1500
    with pytest.raises(AssertionError, match="do not balance"):
        assemble_tables(*cases)
    cases = list(fixture())
    cases[0]["monthly_s2_recorded_activity"].pop()
    with pytest.raises(ValueError, match="25 source months"):
        assemble_tables(*cases)


def test_rejects_unbounded_source_sku_examples():
    cases = list(fixture())
    cases[3]["top_15_skus_by_absolute_gross_change_aggregate_only"] *= 16
    with pytest.raises(ValueError, match="Unbounded SKU"):
        assemble_tables(*cases)
