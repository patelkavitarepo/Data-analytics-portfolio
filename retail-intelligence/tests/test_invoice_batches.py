"""Fixture-only tests: validate full-invoice and local neighborhood accounting."""
import pandas as pd
import pytest

from scripts.investigate_invoice_batches import examine_batches


def fixture():
    return pd.DataFrame({
        "Invoice": ["556689", "556690", "556690", "556691", "556692",
                    "556700", "515459", "515460", "515461", "556693"],
        "StockCode": ["A", "23005", "EXTRA", "23005", "23003",
                      "A", "20852", "20852", "20852", "23005"],
        "Description": ["Other", "printing smudges/thrown away", "damaged",
                        "printing smudges/thrown away", "Different", "Later",
                        "given away", "given away", "given away", "Earlier"],
        "Quantity": [2, -9600, -5, -9600, -3, 1, -1000, -1000, -1000, -1],
        "InvoiceDate": pd.to_datetime(["2011-06-14 10:35",
                                      "2011-06-14 10:37", "2011-06-14 10:37",
                                      "2011-06-14 10:37", "2011-06-14 10:38",
                                      "2011-06-14 11:00", "2010-07-12 15:46",
                                      "2010-07-12 15:46", "2010-07-12 15:46",
                                      "2011-06-14 10:37"]),
        "Price": [2, 0, 0, 0, 0, 2, 0, 0, 0, 0],
        "Customer ID": [1, None, None, None, None, 1, None, None, None, None],
        "Country": ["United Kingdom"] * 10,
    })


CASES = (
    {"name": "smudge", "invoice_ids": ("556690", "556691"), "stock_code": "23005", "quantity": -9600},
    {"name": "gift", "invoice_ids": ("515459", "515460", "515461"), "stock_code": "20852", "quantity": -1000},
)


def test_includes_all_lines_of_target_invoice_not_just_matching_product():
    r = examine_batches({"year": fixture()}, cases=CASES)
    a = r["cases"][0]
    assert a["status"] == "observed"
    by_id = {x["invoice_id"]: x for x in a["target_invoice_full_contents"]}
    assert by_id["556690"]["line_count"] == 2
    assert by_id["556690"]["negative_quantity_lines"] == 2
    assert by_id["556691"]["line_count"] == 1
    assert a["matching_target_line_counts_by_invoice"] == {"556690": 1, "556691": 1}


def test_numeric_neighbors_and_time_context_separate():
    r = examine_batches({"year": fixture()}, cases=CASES, neighbor_radius=3)
    a = r["cases"][0]
    assert [x["invoice_id"] for x in a["neighbor_invoice_summary"]] == [
        "556689", "556690", "556691", "556692", "556693"
    ]
    assert a["same_timestamp_summary"]["distinct_other_invoice_ids"] == 1
    assert a["within_five_minutes_summary"]["other_invoice_ids"] == 3
    assert a["same_timestamp_summary"]["operational_shape_lines"] == 4
    assert r["no_cleaning"] is True


def test_three_invoice_chain_is_complete():
    r = examine_batches({"year": fixture()}, cases=CASES)
    b = r["cases"][1]
    assert b["matching_target_line_counts_by_invoice"] == {
        "515459": 1, "515460": 1, "515461": 1
    }
    assert b["same_timestamp_summary"]["distinct_invoice_ids"] == 3
    assert all(x["line_count"] == 1 for x in b["target_invoice_full_contents"])


def test_source_sheet_and_missing_target_reported_explicitly():
    r = examine_batches(
        {"Year 1": fixture(), "Year 2": fixture().iloc[[0]].copy()},
        cases=CASES + ({"name":"missing", "invoice_ids":("123",), "stock_code":"X", "quantity":-1},)
    )
    assert r["cases"][0]["source_sheet"] == "Year 1"
    assert r["cases"][2]["status"] == "target_not_found"


def test_bad_inputs_fail_clearly():
    with pytest.raises(ValueError, match="No workbook sheets"):
        examine_batches({})
    with pytest.raises(ValueError, match="nonnegative"):
        examine_batches({"year": fixture()}, neighbor_radius=-1)
