"""Case 017: equal multi-unit quantities vs weekly paid-only baselines."""
import pandas as pd
import pytest

from scripts.investigate_multiunit_weekly_context import (
    analyze_multiunit_weekly_context, investigate_original_workbook,
)
from scripts.investigate_sheet_overlap import _prepare


def line(inv, sku, qty, price, when="2010-01-04 10:00", cid=None):
    return {
        "Invoice": inv, "StockCode": sku, "Quantity": qty, "Price": price,
        "Description": "Synthetic", "InvoiceDate": pd.Timestamp(when),
        "Customer ID": cid, "Country": "United Kingdom",
    }


def prepared(rows):
    df = _prepare(pd.DataFrame(rows))
    df["source_sheet"] = "year1"
    df["source_excel_row"] = range(2, len(df) + 2)
    return df


def rows():
    return [
        line("100", "A", 8, 0), line("100", "A", 8, 3),
        line("101", "A", 12, 0, "2010-01-06"), line("101", "A", 12, 3, "2010-01-06"),
        line("102", "A", 1, 0, "2010-01-07"), line("102", "A", 1, 5, "2010-01-07"),
        line("103", "A", 1, 0, "2010-01-08"), line("103", "A", 5, 5, "2010-01-08"),
        line("104", "A", 1, 7, "2010-01-08"),  # same-week paid-only denominator
        line("105", "A", 12, 0, "2010-01-12"), line("105", "A", 12, 3, "2010-01-12"),
        line("106", "B", 2, 0), line("106", "B", 2, 8),
        line("C107", "A", 5, 0), line("C107", "A", 5, 8),
        line("108", "A", -3, 0),
    ]


def test_multiunit_and_one_plus_one_are_distinct():
    out = analyze_multiunit_weekly_context(prepared(rows()))
    assert out["paired_invoice_sku_groups"] == 6
    assert out["distinct_invoice_ids_with_paired_skus"] == 6
    assert out["equal_total_quantity_invoice_sku_groups"] == 5
    assert out["multiunit_equal_total_quantity_invoice_sku_groups"] == 4
    assert out["strict_one_plus_one_invoice_sku_groups"] == 1
    assert out["different_total_quantity_invoice_sku_groups"] == 1
    assert out["skus_with_multiunit_equal_pairs_on_two_or_more_distinct_invoices"] == 1
    assert out["skus_with_multiunit_equal_pairs_within_7days"] == 1
    assert out["zero_price_lines_with_same_invoice_paid_same_sku"] == 6


def test_fixed_week_denominator_uses_paid_only_invoice_sku_groups():
    out = analyze_multiunit_weekly_context(prepared(rows()))
    top = out["top_observed_calendar_weeks_with_paid_only_denominators_max_15"]
    a_week = next(x for x in top if x["stock_code"] == "A" and x["week_start_monday"] == "2010-01-04")
    assert a_week["all_paid_invoice_sku_groups_same_week"] == 5
    assert a_week["paid_and_zero_invoice_sku_groups"] == 4
    assert a_week["paid_only_invoice_sku_groups_same_week"] == 1
    assert a_week["multiunit_equal_invoice_sku_groups"] == 2
    assert a_week["strict_one_plus_one_invoice_sku_groups"] == 1
    assert a_week["observed_pairing_fraction_not_promotion_rate"] == 0.8
    b_week = next(x for x in top if x["stock_code"] == "B")
    assert b_week["all_paid_invoice_sku_groups_same_week"] == 1
    assert b_week["paid_only_invoice_sku_groups_same_week"] == 0


def test_same_invoice_different_skus_not_two_invoice_ids():
    data = prepared([
        line("100", "A", 2, 0), line("100", "A", 2, 3),
        line("100", "B", 2, 0), line("100", "B", 2, 3),
    ])
    out = analyze_multiunit_weekly_context(data)
    assert out["paired_invoice_sku_groups"] == 2
    assert out["distinct_invoice_ids_with_paired_skus"] == 1
    assert out["equal_total_quantity_invoice_sku_groups"] == 2


def test_equal_summed_quantity_not_same_as_literal_one_unit():
    data = prepared([
        line("100", "A", 2, 0), line("100", "A", 3, 0),
        line("100", "A", 4, 4), line("100", "A", 1, 4),
    ])
    out = analyze_multiunit_weekly_context(data)
    assert out["equal_total_quantity_invoice_sku_groups"] == 1
    assert out["multiunit_equal_total_quantity_invoice_sku_groups"] == 1
    assert out["strict_one_plus_one_invoice_sku_groups"] == 0
    assert out["zero_price_lines_with_same_invoice_paid_same_sku"] == 2


def test_reject_invalid_schema_missing_invoice_and_missing_stock_code():
    with pytest.raises(ValueError, match="Missing required fields"):
        analyze_multiunit_weekly_context(pd.DataFrame())
    with pytest.raises(ValueError, match="Missing invoice IDs"):
        analyze_multiunit_weekly_context(prepared([line(None, "A", 1, 0)]))
    out = analyze_multiunit_weekly_context(prepared([
        line("100", None, 1, 0), line("100", None, 1, 5),
        line("101", "A", 1, 0), line("102", "A", 1, 2),
    ]))
    assert out["paired_invoice_sku_groups"] == 0
    assert out["top_observed_calendar_weeks_with_paid_only_denominators_max_15"] == []


def test_cross_sheet_exact_publication_copies_not_inflated():
    a = pd.DataFrame([line("100", "A", 8, 0), line("100", "A", 8, 5)])
    b = a.copy()
    out = investigate_original_workbook({"first": a, "second": b})
    assert out["source_rows_accounted_for_in_provenance"] == 4
    assert out["candidate_view_rows"] == 2
    assert out["cross_sheet_canonical_links"] == 2
    assert out["paired_invoice_sku_groups"] == 1
    assert out["multiunit_equal_total_quantity_invoice_sku_groups"] == 1
