import pandas as pd
import pytest

from scripts.audit import audit_frames, normalize_columns


def example():
    return pd.DataFrame({
        "Invoice": ["10001", "C10002", "10003", "10003"],
        "StockCode": ["A", "A", "B", "B"],
        "Description": ["Item A", "Item A", "Item B", "Item B"],
        "Quantity": [2, -1, 1, 1],
        "InvoiceDate": pd.to_datetime(["2010-01-01", "2010-01-02", "2010-01-03", "2010-01-03"]),
        "Price": [3.5, 3.5, 0, 0],
        "Customer ID": [100, 100, None, None],
        "Country": ["UK"] * 4,
    })


def test_normalizes_uci_original_headers():
    result = normalize_columns(example())
    assert "invoice_no" in result.columns
    assert "unit_price" in result.columns
    assert "customer_id" in result.columns


def test_audit_flags_issues_without_dropping_rows():
    result = audit_frames({"Year 2009-2010": example()})
    assert result["rows"] == 4
    assert result["missing_or_blank_by_field"]["customer_id"] == 2
    assert result["invoice_codes_starting_c_rows"] == 1
    assert result["negative_quantity_rows"] == 1
    assert result["zero_unit_price_rows"] == 2
    assert result["exact_duplicate_lines_across_eight_fields"] == 1
    assert result["cleaning_decisions"].startswith("None")


def test_rejects_unexpected_schema():
    with pytest.raises(ValueError, match="Expected eight distinct fields"):
        normalize_columns(example().drop(columns=["Price"]))
