"""Synthetic checks for full-invoice context of ambiguous M-coded transactions."""
import pandas as pd
import pytest
from scripts.investigate_manual_code import investigate_manual_code, profile_manual_lines
from scripts.investigate_sheet_overlap import _prepare


def line(inv, stock, qty=1, price=1, cust=None, desc="Manual", when="2010-12-01 10:00"):
    return {
        "Invoice": inv, "StockCode": stock, "Description": desc,
        "Quantity": qty, "InvoiceDate": pd.Timestamp(when), "Price": price,
        "Customer ID": cust, "Country": "United Kingdom",
    }


def fixture():
    a = pd.DataFrame([
        line("100", "M", 2, 10, 123),
        line("100", "VASE", 1, 4, 123, "Vase"),
        line("101", "M", 1, 20),
        line("C102", "M", -1, 5),
        line("103", "M", -2, 0),
        line("104", "MANUAL", 1, 50, 123, "Different code"),
    ])
    b = pd.DataFrame([
        line("100", "M", 2, 10, 123),
        line("105", "M", 3, 10, 123),
        line("106", "POST", 1, 2, 123, "Postage"),
    ])
    return {"year1": a, "year2": b}


def test_reconciles_exact_cross_sheet_M_and_context():
    report = investigate_manual_code(fixture())
    c = report["reversible_candidate"]
    assert report["cross_sheet_M_positive_priced_line_difference"] == 1
    assert report["cross_sheet_M_positive_priced_amount_difference_gbp"] == 20.0
    assert c["M_positive_quantity_positive_price_non_C_lines"] == 3
    assert c["M_positive_priced_amount_gbp_not_verified_revenue"] == 70.0
    assert c["M_negative_quantity_positive_price_C_lines"] == 1
    assert c["M_all_remaining_line_types"] == 1
    assert c["M_positive_distinct_invoice_ids"] == 3
    assert c["M_positive_invoice_composition"]["invoice_ids_with_only_M_lines"] == 2
    assert c["M_positive_invoice_composition"]["invoice_ids_with_at_least_one_non_M_line"] == 1
    assert c["M_positive_invoice_composition"]["invoice_ids_with_non_M_positive_priced_line"] == 1
    assert c["M_positive_invoice_composition"]["M_lines_on_invoices_with_non_M_positive_priced_line"] == 1


def test_missing_customer_and_magnitudes_are_not_purged():
    c = investigate_manual_code(fixture())["reversible_candidate"]
    assert c["M_positive_lines_missing_customer_id"] == 1
    assert c["M_positive_line_amount_distribution_gbp"]["max"] == 30.0
    assert c["M_positive_line_amount_distribution_gbp"]["top_10_lines_share_of_M_amount_percent"] == 100.0
    assert c["M_c_prefixed_negative_priced_magnitude_not_cash_refunds_gbp"] == 5.0
    assert c["M_description_frequency_top_10"][0]["description"] == "Manual"


def test_non_M_stock_code_not_misidentified():
    raw = _prepare(pd.DataFrame([line("1","MANUAL",1,8,7), line("2","POST",1,6,7)]))
    s = profile_manual_lines(raw)
    assert s["M_positive_quantity_positive_price_non_C_lines"] == 0
    assert s["M_positive_invoice_composition"]["invoice_ids_with_only_M_lines"] == 0
    assert s["M_positive_line_amount_distribution_gbp"]["median"] is None


def test_M_never_automatically_subtracted_from_S0():
    c = investigate_manual_code(fixture())["reversible_candidate"]
    assert c["M_positive_priced_percent_of_S0_gross_line_amount"] is not None
    assert c["M_positive_priced_amount_gbp_not_verified_revenue"] == 70.0
    assert c["positive_non_M_lines_for_comparison"] == 3


def test_missing_sheet_refused():
    with pytest.raises(ValueError, match="exactly two"):
        investigate_manual_code({})
