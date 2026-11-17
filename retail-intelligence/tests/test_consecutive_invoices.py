"""Synthetic examples for detecting near-duplicates with different invoice IDs."""
import pandas as pd
import pytest
from scripts.investigate_consecutive_invoices import analyze_consecutive_invoices


def fixture():
    return pd.DataFrame({
        "Invoice": [
            "556690", "556691", "556692", "556692",
            "600000", "600001", "C600002", "700000",
        ],
        "StockCode": ["23005", "23005", "B", "B", "M", "M", "M", "Z"],
        "Description": [
            "printing smudges/thrown away", "printing smudges/thrown away",
            "other", "other", "ordinary sale", "ordinary sale",
            "ordinary sale", None,
        ],
        "Quantity": [-9600, -9600, -3, -3, 1, 1, 1, -1],
        "InvoiceDate": pd.to_datetime(["2011-06-14 10:37"] * 8),
        "Price": [0, 0, 0, 0, 2, 2, 2, 0],
        "Customer ID": [None, None, None, None, 123, 123, 123, None],
        "Country": ["United Kingdom"] * 8,
    })


def test_target_9600_pair_with_different_invoices():
    report = analyze_consecutive_invoices({"year": fixture()})
    target = report["target_556690_556691"]
    assert target["matching_seven_fields_and_consecutive_ids"]
    assert target["number_of_matching_pair_records"] == 1
    assert target["pairs"][0]["source_excel_row_a"] == 2
    assert target["pairs"][0]["source_excel_row_b"] == 3
    assert target["pairs"][0]["adjacent_source_rows"]


def test_same_invoice_duplicate_is_not_cross_invoice_pair():
    report = analyze_consecutive_invoices({"year": fixture()})
    assert report["distinct_numeric_invoice_ids"] == 6
    assert report["same_signature_unique_invoice_pairs_consecutive"] == 2
    assert report["negative_non_c"]["seven_field_matching_pairs_consecutive_ids"] == 1
    assert report["negative_non_c"]["consecutive_numeric_invoice_id_pairs_within_cohort"] == 2


def test_matching_not_only_quantity_stock():
    rows = fixture().iloc[[0, 1]].copy()
    rows.iloc[1, rows.columns.get_loc("Price")] = 1
    report = analyze_consecutive_invoices({"year": rows})
    assert report["same_signature_unique_invoice_pairs_consecutive"] == 0
    assert not report["target_556690_556691"]["matching_seven_fields_and_consecutive_ids"]


def test_not_confusing_cancelled_invoice_with_numeric():
    rows = fixture().iloc[[4, 5, 6]].copy()
    report = analyze_consecutive_invoices({"year": rows})
    assert report["raw_rows_with_numeric_invoice_id"] == 2
    assert report["same_signature_unique_invoice_pairs_consecutive"] == 1
    assert report["negative_non_c"]["raw_rows"] == 0


def test_no_matches():
    row = fixture().iloc[[7]].copy()
    report = analyze_consecutive_invoices({"year": row})
    assert report["same_signature_unique_invoice_pairs_consecutive"] == 0
    assert report["negative_non_c"]["seven_field_matching_pairs_consecutive_ids"] == 0


def test_missing_worksheets_refused():
    with pytest.raises(ValueError, match="no worksheets"):
        analyze_consecutive_invoices({})
