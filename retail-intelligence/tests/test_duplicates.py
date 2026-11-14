"""Synthetic-only unit tests for the duplicate audit."""
import pandas as pd
from scripts.investigate_duplicates import diagnose_duplicates


def fixture():
    return pd.DataFrame({
        "Invoice": ["101", "101", "101", "C201", "C201", "301", "302"],
        "StockCode": ["23005", "23005", "23005", "X", "X", "P", "P"],
        "Description": ["printing smudges/thrown away"] * 3 + ["Returned", "Returned", "Sale", "Sale"],
        "Quantity": [-9600, -9600, -9600, -2, -2, 1, 1],
        "InvoiceDate": pd.to_datetime(["2011-06-14"] * 7),
        "Price": [0, 0, 0, 2.5, 2.5, 5, 5],
        "Customer ID": [None, None, None, 4, 4, 3, 3],
        "Country": ["United Kingdom"] * 7,
    })


def test_repeats_are_extra_rows_not_all_members():
    result = diagnose_duplicates({"Year 2010-2011": fixture()})
    assert result["raw_rows"] == 7
    assert result["exact_duplicate_extra_rows_all"] == 3
    assert result["rows_belonging_to_exact_duplicate_groups_all"] == 5
    assert result["number_of_exact_duplicate_groups_all"] == 2
    assert result["max_rows_in_one_exact_duplicate_group_all"] == 3
    assert result["cohort_duplicate_counts"]["negative_non_c"]["extra_exact_copies_after_first"] == 2
    assert result["cohort_duplicate_counts"]["negative_c"]["extra_exact_copies_after_first"] == 1


def test_target_case_is_labeled_hypothetical_not_a_cleaning_action():
    result = diagnose_duplicates({"Year 2010-2011": fixture()})
    target = result["target_9600_printing_smudges"]
    assert target["candidate_rows"] == 3
    assert target["extra_exact_copies_after_first"] == 2
    assert target["hypothetical_absolute_units_counted_twice_if_one_duplicate"] == 19200
    assert [r["excel_row"] for r in target["rows"]] == [2, 3, 4]
    assert all(r["belongs_to_exact_duplicate_group"] for r in target["rows"])
    assert "NOT actual stock loss" in result["interpretation_limits"][1]


def test_no_duplicate_and_na_description():
    rows = fixture().iloc[[0, 3, 5]].copy()
    rows["Description"] = [None, "Returned", "Sale"]
    out = diagnose_duplicates({"One": rows})
    assert out["exact_duplicate_extra_rows_all"] == 0
    assert out["number_of_exact_duplicate_groups_all"] == 0
    assert out["target_9600_printing_smudges"]["candidate_rows"] == 0


def test_same_values_from_different_sheets_count_as_extra():
    row = fixture().iloc[[0]].copy()
    out = diagnose_duplicates({"a": row, "b": row})
    assert out["raw_rows"] == 2
    assert out["exact_duplicate_extra_rows_all"] == 1
