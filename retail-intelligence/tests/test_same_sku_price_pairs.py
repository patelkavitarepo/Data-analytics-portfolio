"""Case 015: many-to-many, same-SKU, and identity guardrails."""
import pandas as pd
import pytest

from scripts.investigate_same_sku_price_pairs import (
    analyze_same_sku_price_pairs, investigate_original_workbook,
)
from scripts.investigate_sheet_overlap import _prepare


def line(invoice, code, qty, price, customer=None, when="2010-12-02 10:00",
         country="United Kingdom"):
    return {
        "Invoice": invoice, "StockCode": code, "Description": "Synthetic",
        "Quantity": qty, "Price": price, "Customer ID": customer,
        "InvoiceDate": pd.Timestamp(when), "Country": country,
    }


def prep(rows):
    x = _prepare(pd.DataFrame(rows))
    x["source_sheet"] = "first"
    x["source_excel_row"] = range(2, len(x) + 2)
    return x


def example():
    return [
        line("100", "A", 1, 0, 7),
        line("100", "A", 1, 5, 7),
        line("100", "B", 1, 0),
        line("101", "A", 3, 0, when="2010-12-02 10:00"),
        line("101", "A", 2, 6, 9, when="2010-12-02 10:02"),
        line("101", "A", 3, 4, 9, when="2010-12-02 10:04"),
        line("102", "C", 2, 0, 2),
        line("102", "C", 2, 2, 3),
        line("C103", "A", 1, 0, 11),
        line("C103", "A", 1, 7, 11),
    ]


def test_distinct_line_counts_not_same_as_all_pair_comparisons():
    r = analyze_same_sku_price_pairs(prep(example()))
    assert r["positive_quantity_zero_price_non_C_lines"] == 4
    assert r["invoice_ids_with_both_zero_and_paid_lines"] == 3
    assert r["zero_price_lines_with_paid_line_same_sku_same_invoice"] == 3
    assert r["invoice_ids_with_any_zero_price_same_sku_paid_partner"] == 3
    assert r["unique_positive_priced_lines_participating"] == 4
    assert r["zero_positive_pair_comparisons_not_transaction_count"] == 4
    assert r["zero_lines_with_any_same_quantity_paid_partner"] == 3
    assert r["same_quantity_pair_comparisons"] == 3
    assert r["recorded_same_minute_pair_comparisons"] == 2
    assert r["invoice_and_sku_groups_with_multiple_distinct_positive_prices"] == 1


def test_customer_conflicts_and_missingness_not_imputed():
    r = analyze_same_sku_price_pairs(prep(example()))
    assert r["customer_relation_pair_comparisons"] == {
        "known_same": 1, "known_different": 1, "one_missing": 2, "both_missing": 0,
    }
    assert all(
        "customer_id" not in str(example)
        for example in r["bounded_descriptive_example_comparisons"]
    )


def test_invoice_sku_sign_and_country_are_conservative():
    r = analyze_same_sku_price_pairs(prep([
        line("200", "A", 1, 0, 1, country="France"),
        line("200", "A", 1, 5, 1, country="Germany"),
        line("200", "B", 1, 6),
        line("201", "A", -1, 0),
        line("C202", "A", 1, 0),
        line("C202", "A", 1, 7),
    ]))
    assert r["zero_positive_pair_comparisons_not_transaction_count"] == 1
    assert r["pair_comparisons_with_both_known_but_different_country"] == 1


def test_empty_cohort_and_bad_schema():
    r = analyze_same_sku_price_pairs(prep([
        line("1", "A", 1, 0), line("2", "A", 1, 9),
    ]))
    assert r["zero_positive_pair_comparisons_not_transaction_count"] == 0
    assert r["bounded_descriptive_example_comparisons"] == []
    assert all(v == 0 for v in r["customer_relation_pair_comparisons"].values())
    with pytest.raises(ValueError, match="Missing required fields"):
        analyze_same_sku_price_pairs(pd.DataFrame())
    with pytest.raises(ValueError, match="Missing invoice IDs"):
        analyze_same_sku_price_pairs(prep([line(None, "A", 1, 0)]))


def test_cross_sheet_copies_keep_single_candidate_occurrence():
    first = pd.DataFrame([
        line("100", "A", 1, 0, 4),
        line("100", "A", 1, 4, 4),
    ])
    second = first.copy()
    r = investigate_original_workbook({"one": first, "two": second})
    assert r["candidate_view_rows"] == 2
    assert r["source_rows_accounted_for_in_provenance"] == 4
    assert r["cross_sheet_canonical_links"] == 2
    assert r["zero_positive_pair_comparisons_not_transaction_count"] == 1


def test_unknown_stock_code_cannot_match_to_unknown_stock_code():
    r = analyze_same_sku_price_pairs(prep([
        line("300", None, 1, 0), line("300", None, 1, 5),
    ]))
    assert r["invoice_ids_with_both_zero_and_paid_lines"] == 1
    assert r["zero_positive_pair_comparisons_not_transaction_count"] == 0
