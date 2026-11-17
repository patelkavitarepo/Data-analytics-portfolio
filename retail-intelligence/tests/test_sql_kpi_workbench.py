"""Case 018: SQLite semantic coverage, order-grain limits and source checks."""
from pathlib import Path

import pytest

from scripts.run_sql_kpi_workbench import (
    add_frame_rows, analyze_sql, check_against_case_009, create_db,
)

VIEW = (Path(__file__).resolve().parents[1]
        / "sql/001_provisional_retail_kpis.sql").read_text(encoding="utf-8")


def row(invoice, sku, qty, price, month="2010-01", customer="7"):
    return {
        "invoice_no": invoice, "stock_code": sku, "quantity": qty,
        "unit_price": price, "invoice_date": f"{month}-03 10:00:00",
        "customer_id": customer, "country": "United Kingdom",
    }


def source_rows():
    return [
        row("100", "A", 2, 5),           # S2: £10
        row("100", "post", 1, 2),        # named fees
        row("100", " M ", 1, 9),        # ambiguous
        row("101", "A", 1, 0),          # zero-price
        row("A1", "B", 1, -3, customer=None),
        row("A2", "A", -2, 0, customer=None),
        row("C50", "A", -1, 5),         # source cancellation
        row("200", "D", 1, 4),          # manual/discount
        row("300", "A", 1, 3, month="2010-02"),
        row("301", "A", 0, 4),          # unresolved (not silently discarded)
    ]


def run(rows):
    with create_db() as con:
        add_frame_rows(con, rows)
        return analyze_sql(con, VIEW)


def fake_baseline():
    return {
        "cross_sheet_reconciled_candidate": {
            "source_lines": 10,
            "mutually_exclusive_line_cohorts": {
                "c_prefixed_any_quantity": 1,
                "negative_non_c_zero_price_missing_customer": 1,
                "other_negative_non_c": 0,
                "positive_non_c_negative_price": 1,
                "positive_non_c_zero_price": 1,
                "positive_non_c_positive_price": 5,
                "zero_quantity_non_c": 1,
                "unresolved_non_c_other": 0,
            },
            "scenarios_experimental_not_accounting_revenue": {
                "S0_all_positive_priced_non_C": {
                    "lines": 5, "invoice_ids": 3,
                    "hypothetical_gross_line_amount_gbp": 28,
                },
                "S1_exclude_named_shipping_and_billing_code_candidates": {
                    "lines": 4, "invoice_ids": 3,
                    "hypothetical_gross_line_amount_gbp": 26,
                },
                "S2_also_exclude_manual_and_discount_code_candidates": {
                    "lines": 2, "invoice_ids": 2,
                    "hypothetical_gross_line_amount_gbp": 13,
                },
            },
        },
    }


def test_full_cohort_partition_and_experimental_scenarios():
    out = run(source_rows())
    c = out["mutually_exclusive_provisional_line_cohorts"]
    assert out["candidate_view_lines"] == 10
    assert sum(c.values()) == 10
    assert c["other_positive_priced"] == 2
    assert c["named_shipping_billing_code_candidate"] == 1
    assert c["manual_discount_code_candidate"] == 2
    assert c["cancellation_coded"] == 1
    assert c["negative_quantity_zero_price_unknown_customer"] == 1
    assert c["positive_quantity_negative_price"] == 1
    assert c["positive_quantity_zero_price"] == 1
    assert c["unresolved_other"] == 1
    s = out["scenario_reconciliation"]
    assert s["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"] == 28
    assert s["S1_exclude_named_shipping_and_billing_code_candidates"]["hypothetical_gross_line_amount_gbp"] == 26
    assert s["S2_also_exclude_manual_and_discount_code_candidates"]["hypothetical_gross_line_amount_gbp"] == 13


def test_monthly_s2_metrics_keep_invoice_grain_and_missingness():
    out = run(source_rows())
    months = out["monthly_s2_recorded_activity"]
    jan = next(m for m in months if m["recorded_month"] == "2010-01")
    feb = next(m for m in months if m["recorded_month"] == "2010-02")
    assert jan["s2_distinct_qualifying_invoice_ids_not_orders"] == 1
    assert jan["s2_positive_priced_lines"] == 1
    assert jan["s2_gross_positive_line_amount_gbp_not_accounting_revenue"] == 10
    assert jan["source_cancellation_coded_lines_not_refunds"] == 1
    assert jan["source_zero_price_positive_lines_not_gifts"] == 1
    assert feb["s2_gross_positive_line_amount_gbp_not_accounting_revenue"] == 3


def test_verification_against_case_009_and_mismatch_rejection():
    out = run(source_rows())
    check_against_case_009(out, fake_baseline())
    assert out["agrees_with_case_009_counts_invoice_ids_and_amounts"] is True
    corrupted = fake_baseline()
    corrupted["cross_sheet_reconciled_candidate"][
        "scenarios_experimental_not_accounting_revenue"
    ]["S2_also_exclude_manual_and_discount_code_candidates"]["hypothetical_gross_line_amount_gbp"] = 15
    with pytest.raises(AssertionError):
        check_against_case_009(run(source_rows()), corrupted)


def test_case_sensitive_C_classification_and_missing_customer():
    out = run([
        row(" c100 ", "A", -1, 4),
        row("200", "A", -5, 0, customer=None),
        row("201", "A", -2, 0, customer="5"),
        row("202", "A", 1, 0, customer=None),
    ])
    c = out["mutually_exclusive_provisional_line_cohorts"]
    assert c["cancellation_coded"] == 1
    assert c["negative_quantity_zero_price_unknown_customer"] == 1
    assert c["non_c_negative_quantity_other"] == 1
    assert c["positive_quantity_zero_price"] == 1
    assert out["scenario_reconciliation"]["S0_all_positive_priced_non_C"]["lines"] == 0


def test_cannot_silently_convert_nulls_to_s2():
    out = run([
        row("100", "A", None, 5), row("100", "A", 1, None),
        row("100", "A", 0, None),
    ])
    assert out["mutually_exclusive_provisional_line_cohorts"]["unresolved_other"] == 3
    assert out["scenario_reconciliation"]["S2_also_exclude_manual_and_discount_code_candidates"]["lines"] == 0
