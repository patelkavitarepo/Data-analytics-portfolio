"""Case 020: invoice-ID/month concentration, outlier trimming and SQL baselines."""
from copy import deepcopy

import pandas as pd
import pytest

from scripts.analyze_invoice_concentration import inspect_invoice_concentration


def line(invoice, sku, qty, price, when):
    return {
        "invoice_no": invoice,
        "stock_code": sku,
        "quantity": qty,
        "unit_price": price,
        "invoice_date": when,
    }


def source():
    return pd.DataFrame([
        line("100", "A", 2, 5, "2010-01-04"),
        line("100", "B", 1, 2, "2010-01-04"),
        line("101", "A", 1, 8, "2010-01-05"),
        line("102", "A", 1, 0, "2010-01-05"),  # not paid
        line("103", "A", 1, 5, "2010-02-04"),
        line("200", "A", 1, 6, "2011-01-04"),
        line("201", "M", 1, 100, "2011-01-04"),  # excluded code
        line("202", "POST", 1, 10, "2011-01-04"),  # excluded code
        line("203", "A", 1, 4, "2011-01-05"),
        line("204", "A", 3, 2, "2011-02-04"),
        line("205", "A", 1, 3, "2011-02-05"),
        line("C206", "A", -1, 5, "2011-02-05"),  # cancellation
    ])


def verified_sql_reference():
    data = [
        ("2010-01", 3, 2, 20),
        ("2010-02", 1, 1, 5),
        ("2011-01", 2, 2, 10),
        ("2011-02", 2, 2, 9),
    ]
    return {
        "agrees_with_case_009_counts_invoice_ids_and_amounts": True,
        "monthly_s2_recorded_activity": [
            {"recorded_month": m, "s2_positive_priced_lines": n,
             "s2_distinct_qualifying_invoice_ids_not_orders": inv,
             "s2_gross_positive_line_amount_gbp_not_accounting_revenue": gross}
            for m, n, inv, gross in data
        ],
        "scenario_reconciliation": {
            "S2_also_exclude_manual_and_discount_code_candidates": {
                "lines": 8,
                "hypothetical_gross_line_amount_gbp": 44,
            }
        },
    }


def test_top_one_percent_concentration_and_monthly_sql_reconciliation():
    out = inspect_invoice_concentration(
        source(), verified_sql_reference(), period_month_numbers=(1, 2)
    )
    assert out["source_candidate_view_rows"] == 12
    assert out["reconciled_s2_lines"] == 8
    assert len(out["monthly_id_concentration"]) == 4
    jan = next(x for x in out["monthly_id_concentration"] if x["recorded_month"] == "2010-01")
    assert jan["invoice_id_month_groups_not_confirmed_orders"] == 2
    assert jan["upper_one_percent_id_month_groups_count"] == 1
    assert jan["maximum_single_id_month_gross_line_amount_gbp"] == 12
    assert jan["upper_one_percent_share_of_gross_line_amount_not_verified_market_share"] == 0.6
    assert jan["gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only"] == 8
    assert out["yoy_change_after_omitting_each_period_upper_one_percent_id_month_groups_pct_sensitivity"] == 0


def test_invoice_id_aggregation_is_distinct_from_line_count():
    out = inspect_invoice_concentration(
        source(), verified_sql_reference(), period_month_numbers=(1, 2)
    )
    a = out["comparable_jan_nov_period_concentration"]
    assert a[0]["invoice_id_month_groups_not_confirmed_orders"] == 3
    assert a[1]["invoice_id_month_groups_not_confirmed_orders"] == 4
    assert a[0]["s2_gross_line_amount_gbp_not_revenue"] == 25
    assert a[1]["s2_gross_line_amount_gbp_not_revenue"] == 19


def test_source_reconciliation_fails_on_invoice_count_or_gross_mismatch():
    d = verified_sql_reference()
    d["monthly_s2_recorded_activity"][0][
        "s2_distinct_qualifying_invoice_ids_not_orders"] = 3
    with pytest.raises(AssertionError, match="Invoice counts mismatch"):
        inspect_invoice_concentration(source(), d, period_month_numbers=(1, 2))
    d = verified_sql_reference()
    d["monthly_s2_recorded_activity"][0][
        "s2_gross_positive_line_amount_gbp_not_accounting_revenue"] = 60
    with pytest.raises(AssertionError, match="Gross S2 amount mismatch"):
        inspect_invoice_concentration(source(), d, period_month_numbers=(1, 2))


def test_missing_or_invalid_dates_and_unverified_reference_rejected():
    with pytest.raises(ValueError, match="Independently source-reconciled"):
        inspect_invoice_concentration(source(), {"agrees_with_case_009_counts_invoice_ids_and_amounts": False}, (1, 2))
    d = source()
    d.loc[0, "invoice_date"] = None
    with pytest.raises(ValueError, match="Date coverage incomplete"):
        inspect_invoice_concentration(d, verified_sql_reference(), period_month_numbers=(1, 2))
    d = source()
    d.loc[0, "invoice_no"] = None
    with pytest.raises(ValueError, match="Missing invoice IDs"):
        inspect_invoice_concentration(d, verified_sql_reference(), period_month_numbers=(1, 2))


def test_missing_requested_reporting_month_is_not_silently_ignored():
    with pytest.raises(ValueError, match="requested comparable period"):
        inspect_invoice_concentration(
            source(), verified_sql_reference(), period_month_numbers=(1, 2, 3)
        )
