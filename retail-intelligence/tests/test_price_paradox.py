"""Case 013: synthetic zero/negative unit price cohorts and invoice checks."""
import pandas as pd
import pytest
from scripts.investigate_price_paradox import examine_price_paradox, investigate_original_workbook
from scripts.investigate_sheet_overlap import _prepare


def line(invoice, stock, qty, price, customer=None, desc="Test", date="2010-12-02 10:00"):
    return {"Invoice":invoice, "StockCode":stock, "Description":desc,
            "Quantity":qty, "InvoiceDate":pd.Timestamp(date), "Price":price,
            "Customer ID":customer, "Country":"United Kingdom"}


def prep(data):
    frame = _prepare(pd.DataFrame(data))
    frame["source_sheet"] = "Year A"
    frame["source_excel_row"] = range(2, len(frame)+2)
    return frame


def fixture():
    return [
        line("100","A",2,0,11,"Found"), # zero priced mixed invoice
        line("100","B",1,5,11,"Sold"),
        line("101","A",3,0,None,"Found"),
        line("102","A",4,1,22,"Normal same SKU elsewhere"),
        line("103","ERR",1,-7,33,"Adjustment"),
        line("104","C",1,0,None,"Gift?"),
        line("C105","A",-1,0,11,"C-coded excluded"),
        line("106","X",-1,0,None,"Negative quantity excluded"),
        line("107","R",2,4,33,"Ordinary goods paid"),
        line("107","Q",3,-3,None,"Negative price"),
    ]


def test_zero_and_negative_price_are_distinct_cohorts():
    r = examine_price_paradox(prep(fixture()))
    assert r["source_observed_cohorts"] == {
        "non_C_positive_quantity_zero_price": 3,
        "non_C_positive_quantity_negative_price": 2,
        "non_C_positive_quantity_positive_price": 3,
    }
    z = r["zero_price_positive_lines"]
    assert z["customer_id_missing_lines"] == 2
    assert z["lines_with_code_also_positive_priced_elsewhere"] == 2
    assert z["distinct_invoice_ids"] == 3
    assert z["invoice_context"]["invoice_ids_containing_only_zero_price_positive_lines"] == 2
    assert z["invoice_context"]["invoice_ids_also_containing_positive_price_positive_lines"] == 1
    assert z["invoice_context"]["zero_price_lines_on_invoices_with_positive_priced_lines"] == 1
    assert r["negative_unit_price_positive_lines"]["signed_line_amount_sum_gbp_not_validated_adjustment"] == -16.0


def test_negative_price_examples_have_context_not_identities():
    r = examine_price_paradox(prep(fixture()))
    n = r["negative_unit_price_positive_lines"]
    assert n["lines"] == 2 and n["distinct_invoice_ids"] == 2
    assert n["invoice_ids_also_containing_positive_priced_lines"] == 1
    assert sorted(x["signed_line_amount_gbp_not_validated_adjustment"] for x in n["top_5_source_line_examples"]) == [-9.0,-7.0]
    assert all("customer_id" not in x for x in n["top_5_source_line_examples"])
    assert all(isinstance(x["customer_id_present"], bool) for x in n["top_5_source_line_examples"])


def test_duplicate_publication_preserves_only_one_candidate_copy():
    a = pd.DataFrame([line("1","A",1,0), line("2","Z",2,-3)])
    b = pd.DataFrame([line("1","A",1,0), line("2","Z",2,-3),
                      line("3","Q",1,0)])
    r = investigate_original_workbook({"year1":a,"year2":b})
    assert r["cross_sheet_canonical_links"] == 2
    assert r["source_rows_accounted_for_in_provenance"] == 5
    assert r["candidate_view_rows"] == 3
    assert r["source_observed_cohorts"]["non_C_positive_quantity_zero_price"] == 2
    assert r["source_observed_cohorts"]["non_C_positive_quantity_negative_price"] == 1


def test_one_invoice_only_zero_price_and_other_mixed_types():
    r = examine_price_paradox(prep([
        line("9","A",1,0),
        line("9","B",-1,0),
        line("10","C",1,0),
        line("10","D",1,0),
    ]))
    z = r["zero_price_positive_lines"]["invoice_context"]
    assert z["invoice_ids_containing_only_zero_price_positive_lines"] == 1
    assert z["invoice_ids_with_other_nonpriced_types_but_no_positive_priced_lines"] == 1
    assert z["invoice_ids_also_containing_positive_price_positive_lines"] == 0


def test_no_anomalies_and_missing_required_fields():
    r = examine_price_paradox(prep([line("1","A",2,5,1)]))
    assert r["zero_price_positive_lines"]["lines"] == 0
    assert r["zero_price_positive_lines"]["quantity_distribution"]["median"] is None
    assert r["negative_unit_price_positive_lines"]["top_5_source_line_examples"] == []
    with pytest.raises(ValueError, match="Missing required source fields"):
        examine_price_paradox(pd.DataFrame())
