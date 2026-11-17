"""Fixture tests ensure multiplicity-safe full-row overlap, not join explosion."""
import pandas as pd
import pytest

from scripts.investigate_sheet_overlap import investigate_sheet_overlap


def row(invoice, item, quantity, price, when="2010-12-01 10:00", cust=None, desc=None):
    return dict(
        Invoice=invoice, StockCode=item, Description=desc, Quantity=quantity,
        InvoiceDate=pd.Timestamp(when), Price=price, **{"Customer ID":cust},
        Country="United Kingdom"
    )


def test_exact_cross_sheet_multiset_counts_not_cartesian():
    duplicate = row("100", "X", 2, 4, cust=12, desc="Mug")
    left = pd.DataFrame([duplicate, duplicate, row("101","Z",-2,0)])
    right = pd.DataFrame([duplicate, row("101","Z",-2,0),row("103","Q",1,9)])
    report = investigate_sheet_overlap({"Year A":left, "Year B":right})
    assert report["combined_raw_rows"] == 6
    assert report["exact_matching_source_line_copies_across_sheets"] == 2
    assert report["distinct_eight_field_keys_shared"] == 2
    assert report["hypothetical_rows_if_only_cross_sheet_exact_copies_counted_once"] == 4
    assert report["overlapping_rows_by_observed_line_type"]["negative_non_c_zero_price_missing_customer"] == 1
    assert report["hypothetical_duplicated_gross_positive_line_amount_gbp"] == 8.0
    assert report["distinct_invoice_numbers_appearing_in_both_sheets"] == 2
    assert report["shared_invoice_numbers_with_partly_matching_line_multisets"] == 1
    assert report["shared_invoice_numbers_with_fully_matching_line_multisets"] == 1


def test_same_invoice_identifier_with_changed_line_not_exact_overlap():
    left = pd.DataFrame([row("200", "X", 1, 2, desc="Item")])
    right = pd.DataFrame([row("200", "X", 2, 2, desc="Item")])
    report = investigate_sheet_overlap({"one":left, "two":right})
    assert report["exact_matching_source_line_copies_across_sheets"] == 0
    assert report["distinct_invoice_numbers_appearing_in_both_sheets"] == 1
    assert report["shared_invoice_numbers_with_no_exact_matching_line"] == 1


def test_all_fields_including_missing_and_timestamp_must_match():
    left = pd.DataFrame([row("1","A",-1,0,desc=None),row("2","B",1,5,when="2010-12-01 10:00")])
    right = pd.DataFrame([row("1","A",-1,0,desc=None),row("2","B",1,5,when="2010-12-01 10:01")])
    r = investigate_sheet_overlap({"a":left,"b":right})
    assert r["exact_matching_source_line_copies_across_sheets"] == 1
    assert r["overlapping_rows_by_observed_line_type"]["negative_non_c_zero_price_missing_customer"] == 1
    assert r["hypothetical_duplicated_gross_positive_line_amount_gbp"] == 0.0
    assert r["monthly_exact_cross_sheet_copy_counts"]["2010-12"] == 1


def test_cancelled_invoice_not_ordinary_positive_money():
    left = pd.DataFrame([row("C10","X",-1,5,desc="Cancelled")])
    right = pd.DataFrame([row("C10","X",-1,5,desc="Cancelled")])
    r = investigate_sheet_overlap({"a":left,"b":right})
    assert r["overlapping_rows_by_observed_line_type"]["c_prefixed_cancellation"] == 1
    assert r["hypothetical_duplicated_gross_positive_line_amount_gbp"] == 0.0


def test_no_overlapping_invoices():
    left = pd.DataFrame([row("1","X",1,3,when="2010-01-01")])
    right = pd.DataFrame([row("2","Y",1,4,when="2011-01-01")])
    r = investigate_sheet_overlap({"a":left,"b":right})
    assert r["exact_matching_source_line_copies_across_sheets"] == 0
    assert r["distinct_invoice_numbers_appearing_in_both_sheets"] == 0
    assert r["calendar_range_in_both_sheets"]["first"] is None


def test_only_two_sheets_supported():
    with pytest.raises(ValueError, match="exactly two"):
        investigate_sheet_overlap({})
