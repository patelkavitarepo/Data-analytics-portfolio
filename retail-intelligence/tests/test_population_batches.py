"""Synthetic controls for candidate-run prevalence; not a claim about source."""
import pandas as pd
import pytest

from scripts.investigate_population_batches import investigate_population, summarize_runs


def example():
    # 101..103: same-time candidate 3-run. 104 has 15m gap; 106 follows
    # another gap. 200..202: ordinary positive-priced 3-run.
    invoice = ["101", "102", "103", "104", "106", "200", "201", "202", "203", "300", "300", "301"]
    quantities = [-2, -1, -3, -1, -4, 1, 2, 1, 1, -1, 2, -1]
    ts = [
        "2010-01-01 10:00", "2010-01-01 10:01", "2010-01-01 10:03",
        "2010-01-01 10:20", "2010-01-01 10:21",
        "2010-01-01 11:00", "2010-01-01 11:02", "2010-01-01 11:06", "2010-01-01 11:30",
        "2010-01-01 12:00", "2010-01-01 12:00", "2010-01-01 12:02"
    ]
    prices = [0,0,0,0,0,2,2,2,2,0,2,0]
    customers = [None]*5+[1]*4+[None,1,None]
    return pd.DataFrame({
        "Invoice": invoice, "StockCode": [str(i) for i in range(len(invoice))],
        "Description": ["test"]*len(invoice),
        "Quantity": quantities, "InvoiceDate": pd.to_datetime(ts),
        "Price": prices, "Customer ID": customers,
        "Country": ["United Kingdom"]*len(invoice),
    })


def test_all_candidate_rows_accounted_for():
    result = investigate_population({"first": example()})
    assert result["candidate_lines"] == 7
    assert result["candidate_only_invoice_ids_within_sheet"] == 6
    assert result["candidate_lines_in_candidate_only_invoices"] == 6
    assert result["candidate_lines_in_mixed_invoices"] == 1
    assert result["mixed_invoices_with_candidate_lines"] == 1
    assert result["positive_priced_only_invoice_ids_within_sheet"] == 4


def test_run_requires_both_consecutive_ids_and_close_timestamps():
    r = investigate_population({"first": example()})
    c = r["candidate_only_invoice_sequences"]
    assert c["invoices"] == 6
    assert c["runs"] == 4
    assert c["runs_size_3_to_4"] == 1
    assert c["invoices_in_runs_size_2_plus"] == 3
    assert c["invoices_in_runs_size_3_plus"] == 3
    assert c["largest_run_invoices"] == 3
    assert c["top_runs"][0]["first_invoice"] == "101"
    assert c["top_runs"][0]["last_invoice"] == "103"
    p = r["positive_priced_only_invoice_sequences"]
    assert p["invoices"] == 4
    assert p["runs_size_3_to_4"] == 1
    assert p["invoices_in_runs_size_2_plus"] == 3


def test_different_sheets_cannot_join():
    small = example().iloc[[0, 1]].copy()
    r = investigate_population({"sheet_a": small, "sheet_b": small})
    assert r["candidate_only_invoice_ids_within_sheet"] == 4
    assert r["candidate_only_invoice_sequences"]["runs"] == 2
    assert r["candidate_only_invoice_sequences"]["invoices_in_runs_size_2_plus"] == 4
    assert r["coverage_by_original_sheet"]["sheet_b"]["candidate_lines"] == 2


def test_negative_c_prefix_never_in_candidate_group():
    rows = example().iloc[[0,1,2]].copy()
    rows.loc[rows["Invoice"].eq("102"),"Invoice"] = "C102"
    r = investigate_population({"one": rows})
    assert r["candidate_lines"] == 2
    assert r["candidate_only_invoice_sequences"]["invoices_in_runs_size_2_plus"] == 0


def test_no_candidates_is_handled():
    rows = example().iloc[5:9]
    r = investigate_population({"one": rows})
    c = r["candidate_only_invoice_sequences"]
    assert c["invoices"] == 0
    assert c["runs"] == 0
    assert r["candidate_lines_in_mixed_invoices"] == 0


def test_rejects_missing_source():
    with pytest.raises(ValueError, match="No source sheets"):
        investigate_population({})
