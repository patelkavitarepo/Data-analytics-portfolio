"""Case 014: mixed invoice counts and false-label safeguards."""
import pandas as pd
import pytest
from scripts.investigate_mixed_price_invoices import examine_mixed_price_invoices, investigate_original_workbook
from scripts.investigate_sheet_overlap import _prepare


def line(invoice, code, qty, price, desc="Item", customer=None):
    return {"Invoice": invoice, "StockCode": code, "Quantity": qty, "Price": price,
            "Description": desc, "Customer ID": customer,
            "InvoiceDate": pd.Timestamp("2010-12-02 10:00"), "Country": "United Kingdom"}


def prepared(lines):
    x = _prepare(pd.DataFrame(lines))
    x["source_sheet"] = "year1"
    x["source_excel_row"] = range(2, len(x) + 2)
    return x


def sample():
    return [
        line("100", "A", 1, 0, "FREE sample", 10),
        line("100", "A", 2, 5, "Sold", 10),
        line("100", "B", 1, 0, None, None),
        line("101", "C", 1, 0, "found", None),
        line("102", "D", 1, 0, "check", 11),
        line("102", "E", -2, 0, "note", None),
        line("103", "F", 1, 0, "gift", 12),
        line("103", "G", 1, 7, "Paid", 12),
        line("C104", "Z", -1, 3, "Cancel", 99),
        line("C104", "Z", 1, 0, "free", 99),
    ]


def test_mixed_invoice_and_other_cohorts_separate():
    x = examine_mixed_price_invoices(prepared(sample()))
    c = x["invoice_composition"]
    assert x["non_C_positive_zero_price_lines"] == 5
    assert c["invoice_ids_with_positive_zero_price_lines"] == 4
    assert c["invoice_ids_with_both_zero_and_positive_price_positive_quantity_lines"] == 2
    assert c["invoice_ids_only_positive_zero_price_lines"] == 1
    assert c["invoice_ids_with_zero_lines_and_other_types_but_no_paid_lines"] == 1
    assert c["zero_price_lines_in_mixed_invoices"] == 3
    assert c["positive_priced_lines_in_mixed_invoices"] == 2
    assert c["zero_price_lines_not_in_mixed_invoices"] == 2


def test_context_same_code_and_keyword_probes_are_descriptive():
    x = examine_mixed_price_invoices(prepared(sample()))
    c = x["mixed_invoice_per_invoice_distribution"]
    assert c["zero_lines_with_same_code_as_paid_line_on_same_invoice"] == 1
    assert c["invoice_ids_where_any_zero_line_has_same_stock_code_as_paid_line"] == 1
    m = x["zero_lines_on_mixed_invoices"]
    assert m["missing_customer_id_lines"] == 1
    assert m["missing_or_blank_description_lines"] == 1
    assert m["keyword_probe_line_counts_not_classifications"]["possible_promotion_words"] == 2
    other = x["zero_lines_not_on_mixed_invoices"]
    assert other["keyword_probe_line_counts_not_classifications"]["possible_operations_words"] == 2
    assert "customer_id" not in str(x["zero_lines_on_mixed_invoices"]["top_descriptions"])


def test_no_zero_lines_is_well_defined():
    x = examine_mixed_price_invoices(prepared([line("10", "A", 1, 5)]))
    assert x["invoice_composition"]["invoice_ids_with_positive_zero_price_lines"] == 0
    assert x["mixed_invoice_per_invoice_distribution"]["zero_lines_median"] is None
    assert x["zero_lines_on_mixed_invoices"]["lines"] == 0


def test_reject_missing_required_fields_and_invoice_id():
    with pytest.raises(ValueError, match="Missing required fields"):
        examine_mixed_price_invoices(pd.DataFrame())
    with pytest.raises(ValueError, match="Missing invoice IDs"):
        examine_mixed_price_invoices(prepared([line(None, "A", 1, 0)]))


def test_cross_sheet_exact_duplicates_are_not_two_mixed_invoices():
    a = pd.DataFrame([line("10", "X", 1, 0), line("10", "Y", 2, 9)])
    b = pd.DataFrame([line("10", "X", 1, 0), line("10", "Y", 2, 9)])
    r = investigate_original_workbook({"first": a, "second": b})
    assert r["source_rows_accounted_for_in_provenance"] == 4
    assert r["candidate_view_rows"] == 2
    assert r["cross_sheet_canonical_links"] == 2
    assert r["invoice_composition"]["zero_price_lines_in_mixed_invoices"] == 1
