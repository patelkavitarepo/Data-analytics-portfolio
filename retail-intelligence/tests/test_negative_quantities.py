import pandas as pd
import pytest
from scripts.investigate_negative_quantities import investigate

def example():
    return pd.DataFrame({
        "Invoice": ["C101", "102", "C103", "104", "104", "105"],
        "StockCode": ["A", "POST", "B", "B", "B", "C"],
        "Description": ["Item A", "Postage", "Item B", "Item B", "Item B", None],
        "Quantity": [-2, -1, 3, -4, 1, -1],
        "InvoiceDate": pd.to_datetime(["2010-01-01"] * 6),
        "Price": [2.5, 0, 1.0, 5.0, 3.5, -2.0],
        "Customer ID": [1, None, 2, 3, 3, None],
        "Country": ["UK"] * 6,
    })

def test_cross_tab_reconciles_every_row():
    report = investigate({"year1": example()})
    assert report["row_count"] == 6
    assert report["negative_quantity_rows"] == 4
    assert report["c_prefixed_invoice_rows"] == 2
    assert report["invoice_prefix_vs_quantity_sign"] == {
        "negative_quantity_and_c_prefixed_invoice": 1,
        "negative_quantity_and_not_c_prefixed_invoice": 3,
        "nonnegative_quantity_and_c_prefixed_invoice": 1,
        "nonnegative_quantity_and_not_c_prefixed_invoice": 1,
        "quantity_not_numeric_or_missing": 0,
    }

def test_unmarked_negatives_not_assumed_cancellations():
    report = investigate({"year1": example()})
    unmarked = report["groups"]["not_c_prefixed_negative"]
    assert unmarked["rows"] == 3
    assert unmarked["distinct_invoice_ids"] == 3
    assert unmarked["zero_unit_price_rows"] == 1
    assert unmarked["negative_unit_price_rows"] == 1
    assert unmarked["missing_customer_id_rows"] == 2
    assert report["non_c_negative_rows_by_month"] == {"2010-01": 3}

def test_bad_or_missing_workbook_schema_raises():
    with pytest.raises(ValueError, match="No sheets supplied"):
        investigate({})
    with pytest.raises(ValueError, match="Expected eight distinct fields"):
        investigate({"year1": example().drop(columns="Price")})
