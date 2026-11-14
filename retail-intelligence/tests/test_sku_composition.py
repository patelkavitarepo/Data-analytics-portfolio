"""Case 021 arithmetic identity, SKU cohort coverage and source safeguards."""
from copy import deepcopy

import pandas as pd
import pytest

from scripts.analyze_sku_composition import analyze_sku_composition


def line(invoice, sku, qty, price, date):
    return {"invoice_no": invoice, "stock_code": sku, "quantity": qty,
            "unit_price": price, "invoice_date": date}


def source():
    return pd.DataFrame([
        line("100", "A", 10, 2, "2010-01-04"),
        line("100", "BB", 5, 3, "2010-01-04"),
        line("101", "ZA", 4, 5, "2010-01-05"),
        line("102", "A", 5, 4, "2011-01-04"),
        line("103", "BB", 10, 2, "2011-01-04"),
        line("104", "CC", 3, 6, "2011-01-05"),
        line("105", "POST", 2, 6, "2011-01-05"),  # shipping candidate excluded from S2
        line("106", "M", 1, 30, "2010-01-06"),  # manual ambiguous excluded
        line("107", "A", 20, 0, "2011-01-06"),  # zero priced excluded
        line("C108", "A", -2, 3, "2010-01-06"),  # cancellation excluded
    ])


def verified():
    def m(label, gross, qty, lines):
        return {
            "recorded_month": label,
            "s2_gross_positive_line_amount_gbp_not_accounting_revenue": gross,
            "s2_recorded_positive_units_not_verified_shipments": qty,
            "s2_positive_priced_lines": lines,
        }
    return {
        "agrees_with_case_009_counts_invoice_ids_and_amounts": True,
        "monthly_s2_recorded_activity": [
            m("2010-01", 55, 19, 3),
            m("2011-01", 58, 18, 3),
        ],
    }


def test_exact_bridge_for_common_new_and_disappeared_stock_codes():
    x = analyze_sku_composition(source(), verified(), months=(1,))
    assert x["decomposition_gross_change_gbp"] == 3
    assert x["matched_period_s2_lines"] == 6
    assert x["stock_code_groups_present_in_both_years"] == 2
    assert x["stock_code_groups_only_in_later_year"] == 1
    assert x["stock_code_groups_only_in_earlier_year"] == 1
    assert x["identity_components_gbp"] == {
        "common_skus_recorded_quantity_component": 5,
        "common_skus_effective_gross_per_unit_component": 0,
        "new_only_later_year_sku_gross_contribution": 18,
        "disappeared_only_earlier_year_sku_gross_contribution": -20,
    }
    assert x["periods_reconciled_independently_to_case_018_sql"][0][
        "gross_positive_line_amount_gbp_not_revenue"
    ] == 55
    assert x["periods_reconciled_independently_to_case_018_sql"][1][
        "gross_positive_line_amount_gbp_not_revenue"
    ] == 58


def test_source_sql_gross_units_and_line_count_must_reconcile():
    for field, value, match in [
        ("s2_gross_positive_line_amount_gbp_not_accounting_revenue", 999, "gross"),
        ("s2_recorded_positive_units_not_verified_shipments", 99, "units"),
        ("s2_positive_priced_lines", 9, "line counts"),
    ]:
        d = verified()
        d["monthly_s2_recorded_activity"][0][field] = value
        with pytest.raises(AssertionError, match=match):
            analyze_sku_composition(source(), d, months=(1,))


def test_no_revenue_inference_and_null_stock_codes_remain_a_cohort():
    s = source()
    s = pd.concat([s, pd.DataFrame([
        line("109", None, 2, 10, "2010-01-06"),
        line("110", None, 1, 10, "2011-01-06"),
    ])], ignore_index=True)
    d = verified()
    d["monthly_s2_recorded_activity"][0][
        "s2_gross_positive_line_amount_gbp_not_accounting_revenue"] += 20
    d["monthly_s2_recorded_activity"][0][
        "s2_recorded_positive_units_not_verified_shipments"] += 2
    d["monthly_s2_recorded_activity"][0]["s2_positive_priced_lines"] += 1
    d["monthly_s2_recorded_activity"][1][
        "s2_gross_positive_line_amount_gbp_not_accounting_revenue"] += 10
    d["monthly_s2_recorded_activity"][1][
        "s2_recorded_positive_units_not_verified_shipments"] += 1
    d["monthly_s2_recorded_activity"][1]["s2_positive_priced_lines"] += 1
    out = analyze_sku_composition(s, d, months=(1,))
    assert out["matched_period_s2_lines"] == 8
    assert out["stock_code_groups_present_in_both_years"] == 3
    assert any("<missing_stock_code>" == x["stock_code"] for x in out[
        "top_15_skus_by_absolute_gross_change_aggregate_only"
    ])
    assert "not_causal" in out["status"]
    assert all("customer" not in str(item).lower() and "invoice" not in str(item).lower()
               for item in out["top_15_skus_by_absolute_gross_change_aggregate_only"])


def test_unverified_invalid_source_month_coverage_and_schema_fail():
    d = verified()
    d["agrees_with_case_009_counts_invoice_ids_and_amounts"] = False
    with pytest.raises(ValueError, match="Source-reconciled"):
        analyze_sku_composition(source(), d, months=(1,))
    with pytest.raises(ValueError, match="Missing matched month"):
        analyze_sku_composition(source(), verified(), months=(1, 2))
    with pytest.raises(ValueError, match="Invalid comparable month"):
        analyze_sku_composition(source(), verified(), months=(1, 1))
    with pytest.raises(ValueError, match="distinct comparison years"):
        analyze_sku_composition(source(), verified(), months=(1,), years=(2010,2010))
    with pytest.raises(ValueError, match="Missing candidate fields"):
        analyze_sku_composition(pd.DataFrame(), verified(), months=(1,))


def test_source_rows_and_reversal_intact():
    s = source()
    original = s.copy(deep=True)
    out = analyze_sku_composition(s, verified(), months=(1,))
    pd.testing.assert_frame_equal(s, original)
    assert out["candidate_rows_in_input"] == len(original)
    assert out["matched_period_s2_lines"] < len(original)
    # A source period cannot gain a phantom SKU from C-prefix or £0 data.
    assert out["stock_code_groups_present_in_both_years"] == 2
