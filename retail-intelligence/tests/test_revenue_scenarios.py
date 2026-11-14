"""Synthetic, reproducible tests for Case 009's provisional KPI semantics."""
import pandas as pd
import pytest
from scripts.investigate_revenue_scenarios import (
    analyze_lines, investigate_revenue_scenarios, NARROW_NONMERCH_CODES
)


def row(invoice, stock, qty=1, price=1, desc="x", customer=None):
    return {
        "Invoice": invoice, "StockCode": stock, "Description": desc,
        "Quantity": qty, "InvoiceDate": pd.Timestamp("2010-12-02 10:00"),
        "Price": price, "Customer ID": customer, "Country": "United Kingdom",
    }


def fixture():
    a = pd.DataFrame([
        row("100","PRODUCT",2,10,"Mug",123),
        row("101","POST",1,3,"Postage"),
        row("102","M",1,9,"Manual"),
        row("C103","PRODUCT",-1,10,"Cancelled",123),
        row("104","DAMAGE",-2,0,"Damaged"),
        row("105","D",1,2,"Discount"),
        row("106","FREE",2,0,"No price"),
        row("107","PRODUCT",1,-1,"Negative price"),
    ])
    b = pd.DataFrame([
        row("100","PRODUCT",2,10,"Mug",123),
        row("108","PRODUCT",1,5,"Other",123),
    ])
    return {"Year A": a, "Year B": b}


def test_cross_sheet_and_code_sensitivity():
    r = investigate_revenue_scenarios(fixture())
    raw = r["raw"]["scenarios_experimental_not_accounting_revenue"]
    can = r["cross_sheet_reconciled_candidate"]["scenarios_experimental_not_accounting_revenue"]
    assert r["reversible_layer_links"] == 1
    assert raw["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"] == 59.0
    assert can["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"] == 39.0
    assert can["S1_exclude_named_shipping_and_billing_code_candidates"]["hypothetical_gross_line_amount_gbp"] == 36.0
    assert can["S2_also_exclude_manual_and_discount_code_candidates"]["hypothetical_gross_line_amount_gbp"] == 25.0
    assert r["sensitivity_by_scenario"]["S0_all_positive_priced_non_C"]["source_overlap_difference_gbp"] == 20.0
    assert r["cross_sheet_reconciled_candidate"]["cancellation_lines_not_assumed_to_be_refunds"]["absolute_signed_amount_for_those_lines_gbp"] == 10.0


def test_cohorts_are_exclusive_and_exhaustive():
    report = investigate_revenue_scenarios(fixture())["cross_sheet_reconciled_candidate"]
    counts = report["mutually_exclusive_line_cohorts"]
    assert sum(counts.values()) == 9
    assert counts["c_prefixed_any_quantity"] == 1
    assert counts["negative_non_c_zero_price_missing_customer"] == 1
    assert counts["positive_non_c_zero_price"] == 1
    assert counts["positive_non_c_negative_price"] == 1
    assert counts["positive_non_c_positive_price"] == 5


def test_labels_are_exact_and_conservative():
    a = pd.DataFrame([row("1","POSTCARD",1,10,"Postcard"), row("2","POST",1,3,"Postage")])
    b = pd.DataFrame([row("3","OTHER",1,1,"Item")])
    report = investigate_revenue_scenarios({"A":a,"B":b})["cross_sheet_reconciled_candidate"]
    ss=report["scenarios_experimental_not_accounting_revenue"]
    assert "POST" in NARROW_NONMERCH_CODES and "POSTCARD" not in NARROW_NONMERCH_CODES
    assert ss["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"] == 14.0
    assert ss["S1_exclude_named_shipping_and_billing_code_candidates"]["hypothetical_gross_line_amount_gbp"] == 11.0


def test_cancellation_not_automatically_net_refund():
    a = pd.DataFrame([row("C100","PRODUCT",-3,7,"Cancelled")])
    b = pd.DataFrame([row("C101","PRODUCT",1,5,"Odd cancellation")])
    r = investigate_revenue_scenarios({"A":a, "B":b})
    ss=r["cross_sheet_reconciled_candidate"]["scenarios_experimental_not_accounting_revenue"]
    assert ss["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"] == 0.0
    cs=r["cross_sheet_reconciled_candidate"]["cancellation_lines_not_assumed_to_be_refunds"]
    assert cs["c_prefixed_lines_all"] == 2
    assert cs["absolute_signed_amount_for_those_lines_gbp"] == 21.0


def test_missing_customer_does_not_auto_exclude_positive_paid():
    a=pd.DataFrame([row("200","PRODUCT",3,2,customer=None)])
    b=pd.DataFrame([row("201","OTHER",1,2,customer=None)])
    r=investigate_revenue_scenarios({"A":a,"B":b})
    assert r["cross_sheet_reconciled_candidate"]["scenarios_experimental_not_accounting_revenue"]["S0_all_positive_priced_non_C"]["lines"] == 2


def test_invalid_sheet_number_rejected():
    with pytest.raises(ValueError, match="exactly two"):
        investigate_revenue_scenarios({})
