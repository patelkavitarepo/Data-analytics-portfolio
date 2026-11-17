"""Case 016: source-independent temporal repetition, denominators and limits."""
import pandas as pd
import pytest

from scripts.investigate_temporal_zero_paid_sku import (
    _pair_counts_within, inspect_repeated_zero_paid_sku, investigate_original_workbook,
)
from scripts.investigate_sheet_overlap import _prepare


def line(invoice, sku, q, price, time="2010-01-01 12:00", cid=None):
    return {"Invoice": invoice, "StockCode": sku, "Quantity": q,
            "Price": price, "InvoiceDate": pd.Timestamp(time),
            "Description": "Synthetic test", "Customer ID": cid,
            "Country": "United Kingdom"}


def prep(rows):
    x = _prepare(pd.DataFrame(rows))
    x["source_sheet"] = "year1"
    x["source_excel_row"] = range(2, len(x) + 2)
    return x


def sample():
    return [
        line("100", "A", 1, 0, "2010-01-01"),
        line("100", "A", 1, 3, "2010-01-01"),
        line("101", "A", 1, 0, "2010-01-03"),
        line("101", "A", 1, 3, "2010-01-03"),
        line("102", "A", 1, 4, "2010-01-04"),  # paid-only denominator
        line("103", "B", 1, 0, "2010-01-08"),
        line("103", "B", 1, 9, "2010-01-08"),
        line("104", "A", 1, 0, "2010-02-20"),
        line("104", "A", 1, 3, "2010-02-20"),
        line("105", "A", 1, 0, "2010-02-22"),
        line("105", "A", 2, 3, "2010-02-22"),
        line("C106", "A", 1, 0, "2010-02-23"),  # cancellation ignored
        line("C106", "A", 1, 3, "2010-02-23"),
    ]


def test_repeated_sku_in_separate_invoices_close_in_time():
    r = inspect_repeated_zero_paid_sku(prep(sample()))
    assert r["zero_price_lines_with_paid_same_sku_on_same_invoice"] == 5
    assert r["distinct_invoice_ids_with_same_sku_zero_paid"] == 5
    assert r["invoice_sku_groups_with_zero_and_paid"] == 5
    assert r["invoice_sku_groups_exactly_one_zero_unit_and_one_paid_unit"] == 4
    assert r["distinct_skus_with_any_paired_invoice"] == 2
    assert r["distinct_skus_with_two_or_more_paired_invoices"] == 1
    assert r["distinct_skus_with_paired_invoices_within_7days"] == 1
    assert r["distinct_skus_with_paired_invoices_within_30days"] == 1
    a = next(x for x in r["top_sku_recurrence_context_max_15"] if x["stock_code"] == "A")
    assert a["distinct_invoice_ids_with_zero_and_paid_same_sku"] == 4
    assert a["paid_invoice_sku_groups_any_date_for_this_sku"] == 5
    assert a["distinct_invoice_pair_comparisons_within_7days"] == 2
    assert a["max_paired_invoice_sku_groups_in_any_7day_window"] == 2


def test_window_boundaries_and_cluster_count():
    stamps = [pd.Timestamp("2010-01-01"), pd.Timestamp("2010-01-08"),
              pd.Timestamp("2010-01-09"), pd.Timestamp("2010-04-01")]
    pairs, peak = _pair_counts_within(stamps, 7)
    assert (pairs, peak) == (2, 2)  # Jan 1/8 and Jan 8/9


def test_line_counts_differ_from_invoice_sku_groups():
    r = inspect_repeated_zero_paid_sku(prep([
        line("100", "A", 1, 0), line("100", "A", 1, 0),
        line("100", "A", 2, 5), line("100", "B", 1, 0),
        line("100", "B", 1, 7),
    ]))
    assert r["zero_price_lines_with_paid_same_sku_on_same_invoice"] == 3
    assert r["invoice_sku_groups_with_zero_and_paid"] == 2
    assert r["distinct_invoice_ids_with_same_sku_zero_paid"] == 1
    assert r["invoice_sku_groups_exactly_one_zero_unit_and_one_paid_unit"] == 1


def test_blank_stock_and_nonmatching_invoice_never_link():
    r = inspect_repeated_zero_paid_sku(prep([
        line("100", None, 1, 0), line("100", None, 1, 10),
        line("101", "A", 1, 0), line("102", "A", 1, 5),
    ]))
    assert r["zero_price_lines_with_paid_same_sku_on_same_invoice"] == 0
    assert r["top_sku_recurrence_context_max_15"] == []


def test_empty_case_and_missing_source_fields_or_invoice_ids():
    r = inspect_repeated_zero_paid_sku(prep([line("100", "A", 1, 5)]))
    assert r["distinct_skus_with_any_paired_invoice"] == 0
    assert r["distinct_skus_with_paired_invoices_within_7days"] == 0
    with pytest.raises(ValueError, match="Missing required fields"):
        inspect_repeated_zero_paid_sku(pd.DataFrame())
    with pytest.raises(ValueError, match="Missing invoice IDs"):
        inspect_repeated_zero_paid_sku(prep([line(None, "A", 1, 0)]))


def test_cross_sheet_overlap_does_not_double_count_recurrence():
    a = pd.DataFrame([line("100", "A", 1, 0), line("100", "A", 1, 5)])
    b = a.copy()
    r = investigate_original_workbook({"first": a, "second": b})
    assert r["source_rows_accounted_for_in_provenance"] == 4
    assert r["candidate_view_rows"] == 2
    assert r["cross_sheet_canonical_links"] == 2
    assert r["zero_price_lines_with_paid_same_sku_on_same_invoice"] == 1
    assert r["distinct_skus_with_two_or_more_paired_invoices"] == 0
