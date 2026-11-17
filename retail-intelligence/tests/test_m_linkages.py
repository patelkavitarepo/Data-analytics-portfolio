"""Case 011 synthetics: distinguish candidate links from verified refunds."""
import pandas as pd
import pytest

from scripts.investigate_m_linkages import investigate_m_reversals, investigate_original_workbook
from scripts.investigate_sheet_overlap import _prepare


def line(invoice, code, qty, price, customer=None, date="2010-02-01 10:00",
         country="United Kingdom"):
    return dict(
        Invoice=invoice, StockCode=code, Description="Manual" if code=="M" else "Mug",
        Quantity=qty, InvoiceDate=pd.Timestamp(date), Price=price,
        **{"Customer ID": customer}, Country=country,
    )


def fixture():
    a = pd.DataFrame([
        line("100", "M", 2, 10, 1, "2010-02-01"),
        line("100", "VASE", 1, 4, 1, "2010-02-01"),
        line("C101", "M", -2, 10, 1, "2010-02-02"),
        line("200", "M", 1, 5000, 2, "2010-01-01"),
        line("C201", "M", -1, 5000, 2, "2010-02-01"),
        line("300", "M", 1, 7, 3, "2010-01-01"),
        line("C301", "M", -1, 7, 3, "2010-05-01"),
        line("400", "M", 1, 9, 4, "2010-05-01"),
        line("C401", "M", -1, 9, 4, "2010-04-30"),
        line("500", "M", 1, 5, None, "2010-05-01"),
        line("C501", "M", -1, 5, None, "2010-05-02"),
    ])
    b = pd.DataFrame([
        line("100", "M", 2, 10, 1, "2010-02-01"),  # duplicate publication
        line("700", "M", 1, 100, 9, "2010-04-01"),
    ])
    return {"yearA": a, "yearB": b}


def test_strict_90_vs_365_day_matches_and_no_anon_matching():
    result = investigate_original_workbook(fixture())
    assert result["positive_non_C_M_lines"] == 6
    assert result["negative_C_M_lines"] == 5
    assert result["canonical_cross_sheet_links"] == 1
    assert result["matching_90_days"]["pair_comparisons_meeting_all_fields_and_window"] == 2
    assert result["matching_365_days"]["pair_comparisons_meeting_all_fields_and_window"] == 3
    assert result["matching_90_days"]["reciprocal_one_to_one_candidate_pairs_not_verified_reversals"] == 2
    assert result["matching_365_days"]["reciprocal_one_to_one_candidate_pairs_not_verified_reversals"] == 3
    assert result["matching_365_days"]["negative_C_lines_without_candidate_in_window"] == 2


def test_high_value_top_case_reports_context_but_not_identities():
    result = investigate_original_workbook(fixture())
    assert result["top_positive_M_line_cases"][0]["invoice_id"] == "200"
    assert result["top_positive_M_line_cases"][0]["absolute_line_amount_gbp_not_certified"] == 5000.0
    assert result["top_positive_M_line_cases"][0]["same_customer_exact_quantity_price_country_candidate_90d"] == 1
    multi = next(x for x in result["top_positive_M_line_cases"] if x["invoice_id"] == "100")
    assert multi["invoice_positive_non_M_lines"] == 1
    assert multi["invoice_total_lines"] == 2
    assert multi["invoice_other_stock_codes"] == ["VASE"]
    assert all("customer_id" not in x for x in result["top_positive_M_line_cases"])
    assert all(isinstance(x["customer_id_present"], bool) for x in result["top_positive_M_line_cases"])
    assert result["positive_M_gross_line_amount_not_verified_revenue_gbp"] == 5141.0


def test_many_to_one_ambiguity_is_not_called_unique():
    df = _prepare(pd.DataFrame([
        line("101", "M", 1, 10, 8, "2010-01-01"),
        line("102", "M", 1, 10, 8, "2010-01-02"),
        line("C103", "M", -1, 10, 8, "2010-01-03"),
    ]))
    df["source_sheet"] = "one"
    df["source_excel_row"] = range(2, len(df)+2)
    r = investigate_m_reversals(df)
    assert r["matching_90_days"]["pair_comparisons_meeting_all_fields_and_window"] == 2
    assert r["matching_90_days"]["negative_C_lines_with_exactly_one_candidate_positive_line"] == 0
    assert r["matching_90_days"]["reciprocal_one_to_one_candidate_pairs_not_verified_reversals"] == 0


def test_different_price_country_or_customer_cannot_match():
    df = _prepare(pd.DataFrame([
        line("100", "M", 1, 10, 1),
        line("C101", "M", -1, 11, 1),
        line("C102", "M", -1, 10, 2),
        line("C103", "M", -1, 10, 1, country="France"),
        line("C104", "M", -2, 10, 1),
    ]))
    df["source_sheet"] = "one"
    df["source_excel_row"] = range(2, len(df)+2)
    r = investigate_m_reversals(df)
    assert r["matching_365_days"]["pair_comparisons_meeting_all_fields_and_window"] == 0


def test_no_M_does_not_break():
    df = _prepare(pd.DataFrame([line("1", "OTHER", 1, 3, 1)]))
    df["source_sheet"]="one"
    df["source_excel_row"]=[2]
    r=investigate_m_reversals(df)
    assert r["positive_non_C_M_lines"] == 0
    assert r["matching_90_days"]["pair_comparisons_meeting_all_fields_and_window"] == 0
    assert r["top_positive_M_line_cases"] == []


def test_invalid_sheet_count_rejected():
    with pytest.raises(ValueError, match="exactly two"):
        investigate_original_workbook({})
