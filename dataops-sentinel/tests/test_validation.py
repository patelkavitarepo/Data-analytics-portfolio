import pandas as pd
import pytest

from sentinel.schema import COLUMNS
from sentinel.validation import validate


def codes(result):
    return {finding.code for finding in result.findings}


@pytest.mark.parametrize("column", COLUMNS)
def test_each_required_value_is_checked(column, make_row):
    result = validate(pd.DataFrame([make_row(**{column: " "})]))
    assert not result.accepted
    assert len(result.rejected) == 1
    assert "missing_value" in codes(result)


@pytest.mark.parametrize(
    "value",
    ["not-a-date", "2026-02-30T12:00:00Z", "1700000000", "2026-01-01", "2026-01-01T25:00:00Z"],
)
def test_bad_dates_are_hard_failures(value, make_row):
    result = validate(pd.DataFrame([make_row(event_timestamp_utc=value)]))
    assert len(result.rejected) == 1
    assert "invalid_timestamp" in codes(result)


def test_timezone_offsets_dst_and_naive_utc(make_row):
    rows = [
        make_row("early", event_timestamp_utc="2026-11-01T01:30:00-04:00"),
        make_row("late", event_timestamp_utc="2026-11-01T01:30:00-05:00"),
        make_row("naive", event_timestamp_utc="2026-11-01T05:30:00"),
    ]
    result = validate(pd.DataFrame(rows))
    assert not result.rejected
    times = [pd.Timestamp(row["event_timestamp_utc"]) for row in result.accepted]
    assert all(stamp.utcoffset().total_seconds() == 0 for stamp in times)
    assert times[0] == times[2]
    assert times[1].timestamp() - times[0].timestamp() == 3600


@pytest.mark.parametrize("quantity", ["-1", "10001", "1.5", "NaN", "inf", "-inf", "many"])
def test_invalid_quantities_rejected(quantity, make_row):
    result = validate(pd.DataFrame([make_row(quantity=quantity)]))
    assert len(result.rejected) == 1
    assert "invalid_quantity" in codes(result)


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"category": "unknown"}, "invalid_category"),
        ({"status": "unknown"}, "invalid_status"),
        ({"status": "cancelled", "quantity": "5"}, "inconsistent_status"),
        ({"status": "completed", "quantity": "0"}, "inconsistent_status"),
        ({"status": "pending", "quantity": "0"}, "inconsistent_status"),
    ],
)
def test_business_rules(changes, code, make_row):
    result = validate(pd.DataFrame([make_row(**changes)]))
    assert len(result.rejected) == 1
    assert code in codes(result)


def test_cancelled_zero_is_valid(make_row):
    result = validate(pd.DataFrame([make_row(status="cancelled", quantity="0")]))
    assert len(result.accepted) == 1
    assert not result.rejected


def test_all_duplicate_members_and_prior_ids_rejected(make_row):
    result = validate(
        pd.DataFrame([make_row("same"), make_row("same"), make_row("old"), make_row("fresh")]),
        existing_ids={"old"},
    )
    assert [row["record_id"] for row in result.accepted] == ["fresh"]
    assert [row["row_number"] for row in result.rejected] == [1, 2, 3]
    assert {"duplicate_id", "duplicate_existing"} <= codes(result)


def test_mixed_rows_preserve_reconciliation_and_raw_failure(make_row):
    result = validate(pd.DataFrame([make_row("good"), make_row("bad", quantity="-2")]))
    assert len(result.accepted) + len(result.rejected) == 2
    assert result.accepted[0]["quantity"] == 10
    assert result.rejected[0]["quantity"] == "-2"
    assert result.findings[0].row_number == 2


def test_outlier_is_advisory_and_stays_in_accepted_cohort(make_row):
    rows = [make_row(str(i)) for i in range(9)] + [make_row("spike", quantity="500")]
    result = validate(pd.DataFrame(rows))
    assert len(result.accepted) == 10
    assert not result.rejected
    advisories = [f for f in result.findings if f.severity == "advisory"]
    assert [(f.row_number, f.code) for f in advisories] == [(10, "quantity_outlier")]
    assert not [f for f in result.findings if f.severity == "error"]


def test_small_sample_does_not_make_an_outlier_claim(make_row):
    result = validate(pd.DataFrame([make_row("a"), make_row("b", quantity="500")]))
    assert len(result.accepted) == 2
    assert not result.findings
