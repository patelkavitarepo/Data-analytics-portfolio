"""Synthetic examples test interpretation guards for H001; not source findings."""
import pandas as pd
from scripts.investigate_negative_quantities import investigate


def fixture():
    return pd.DataFrame({
        "Invoice": ["100", "100", "101", "102", "C103", "104"],
        "StockCode": ["A", "A", "B", "C", "D", "E"],
        "Description": ["Damaged stock", "sale", "MISSING", "check damaged", "return", None],
        "Quantity": [-5, 1, -2, -3, -1, 2],
        "InvoiceDate": pd.to_datetime(["2010-01-02"] * 6),
        "Price": [0, 10, 0, 0, 5, 7],
        "Customer ID": [None, 55, None, None, 10, 12],
        "Country": ["United Kingdom"] * 6,
    })


def test_profile_counts_keywords_without_assigning_causes():
    report = investigate({"Year 2009-2010": fixture()})
    h = report["h001_diagnostic_profile"]
    assert h["rows"] == 3
    assert h["keyword_hits_by_literal_text_pattern"]["damage_terms"] == 2
    assert h["keyword_hits_by_literal_text_pattern"]["missing_or_loss_terms"] == 1
    assert h["keyword_hits_by_literal_text_pattern"]["checking_or_stocktake_terms"] == 1
    assert h["keyword_hits_by_literal_text_pattern"]["theft_explicit_terms"] == 0
    assert h["rows_with_any_listed_keyword"] == 3
    assert h["quantity_absolute_sum_units_not_financial_value"] == 10
    assert h["quantity_absolute_max"] == 5


def test_shared_invoice_does_not_infer_why():
    h = investigate({"Year 2009-2010": fixture()})["h001_diagnostic_profile"]
    assert h["single_line_invoice_ids_within_group"] == 3
    assert h["multi_line_invoice_ids_within_group"] == 0
    assert h["invoice_ids_also_having_positive_quantity_lines"] == 1
    assert h["positive_quantity_lines_sharing_invoice_ids"] == 1


def test_profile_handles_no_unmarked_negative_rows():
    rows = fixture().copy()
    rows.loc[rows["Quantity"] < 0, "Invoice"] = "C201"
    h = investigate({"Year 2009-2010": rows})["h001_diagnostic_profile"]
    assert h["rows"] == 0
    assert h["quantity_absolute_max"] is None
    assert h["rows_with_any_listed_keyword"] == 0
