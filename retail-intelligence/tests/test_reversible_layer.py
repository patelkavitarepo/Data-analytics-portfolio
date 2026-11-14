"""Synthetic checks for reversible cross-sheet deduplication proposals."""
import pandas as pd
import pytest

from scripts.build_reversible_layer import build_candidate_layer


def row(invoice, stock, quantity=2, price=3, description=None, date="2010-12-02 10:00", customer=None):
    return {
        "Invoice": invoice, "StockCode": stock, "Description": description,
        "Quantity": quantity, "InvoiceDate": pd.Timestamp(date), "Price": price,
        "Customer ID": customer, "Country": "United Kingdom",
    }


def test_multiset_overlap_preserves_within_first_sheet_repeats():
    a = pd.DataFrame([row("100", "X"), row("100", "X"), row("101", "Y", -2, 0)])
    b = pd.DataFrame([row("100", "X"), row("101", "Y", -2, 0), row("102", "Z")])
    candidate, provenance, report = build_candidate_layer({"a": a, "b": b})
    assert report["raw_source_rows"] == 6
    assert report["candidate_view_rows"] == 4
    assert report["second_sheet_matching_copies_excluded_in_candidate_view"] == 2
    assert len(provenance) == 6
    assert provenance["included_in_candidate_view"].sum() == 4
    assert report["rows_by_type_excluded_cross_sheet"]["negative_non_c_zero_price_missing_customer"] == 1
    assert report["hypothetical_positive_line_amount_difference_gbp"] == 6.0
    assert candidate.loc[candidate["invoice_no"].eq("100")].shape[0] == 2
    links = provenance.loc[provenance["overlap_type"].eq("second_sheet_exact_cross_sheet_copy")]
    assert set(links["source_sheet"]) == {"b"}
    assert links.set_index("source_excel_row")["candidate_canonical_excel_row"].to_dict() == {2: 2, 3: 4}


def test_extra_second_sheet_occurrence_is_retained():
    a = pd.DataFrame([row("100", "X")])
    b = pd.DataFrame([row("100", "X"), row("100", "X")])
    candidate, provenance, report = build_candidate_layer({"a": a, "b": b})
    assert report["second_sheet_matching_copies_excluded_in_candidate_view"] == 1
    assert len(candidate) == 2
    assert report["second_sheet_lines_retained"] == 1
    assert provenance.loc[
        provenance["source_sheet"].eq("b"), "included_in_candidate_view"
    ].tolist() == [False, True]
    assert candidate.loc[candidate["invoice_no"].eq("100")].shape[0] == 2


def test_same_invoice_different_line_retained():
    a = pd.DataFrame([row("100","X",2)])
    b = pd.DataFrame([row("100","X",3)])
    candidate, provenance, report = build_candidate_layer({"a": a, "b": b})
    assert len(candidate) == 2
    assert report["second_sheet_matching_copies_excluded_in_candidate_view"] == 0
    assert provenance["included_in_candidate_view"].all()


def test_zero_overlap_and_customer_missing():
    a = pd.DataFrame([row("100", "X", -1, 0, description=None)])
    b = pd.DataFrame([row("200", "X", -1, 0, description=None)])
    candidate, provenance, report = build_candidate_layer({"a": a, "b": b})
    assert len(candidate) == 2
    assert report["candidate_view_rows"] == 2
    assert report["canonical_links_for_suppressed_rows"] == 0


def test_all_eight_source_fields_in_match():
    a = pd.DataFrame([row("100", "X", date="2010-12-02 10:00")])
    b = pd.DataFrame([row("100", "X", date="2010-12-02 10:01")])
    candidate, _, report = build_candidate_layer({"a": a, "b": b})
    assert len(candidate) == 2
    assert report["hypothetical_positive_line_amount_difference_gbp"] == 0.0


def test_errors_if_not_exactly_two_sheets():
    with pytest.raises(ValueError, match="exactly two"):
        build_candidate_layer({})
