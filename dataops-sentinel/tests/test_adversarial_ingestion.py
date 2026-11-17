"""Independent boundary cases for untrusted JSON numbers and escaped text."""

from concurrent.futures import ThreadPoolExecutor
import csv
import json

import pytest

from sentinel.ingestion import IngestionError, read_csv_bytes, read_json_bytes
from sentinel.repository import Repository
from sentinel.schema import COLUMNS, MAX_BYTES, MAX_FIELD_CHARS


def json_number(row, field, token):
    """Put an exact, unquoted JSON number token into a tiny synthetic record."""
    placeholder = "EXACT_NUMBER_TOKEN"
    text = json.dumps([{**row, field: placeholder}])
    return text.replace(json.dumps(placeholder), token).encode("utf-8")


@pytest.mark.parametrize(
    "token,status",
    [
        ("1.0000000000000001", "completed"),
        ("10000.0000000000001", "completed"),
        ("-1e-10000", "cancelled"),
    ],
)
def test_json_numeric_boundary_failures_remain_exact_in_saved_audit(
    tmp_path, make_row, token, status
):
    batch = read_json_bytes(json_number(make_row(status=status), "quantity", token))
    assert batch.frame.iloc[0]["quantity"] == token
    repo = Repository(tmp_path / "numeric-boundary.sqlite")
    run = repo.ingest(batch)
    assert (run["input_count"], run["accepted_count"], run["rejected_count"]) == (1, 0, 1)
    assert run["advisory_count"] == 0
    assert run["rejected"][0]["quantity"] == token
    assert {finding["code"] for finding in run["findings"]} == {"invalid_quantity"}
    assert repo.get_run(run["run_id"])["rejected"][0]["quantity"] == token


@pytest.mark.parametrize("token", ["1e999999999999999999999999", "1e-999999999999999999999999"])
def test_json_extreme_exponents_are_rejected_without_float_overflow_or_crash(
    tmp_path, make_row, token
):
    run = Repository(tmp_path / "extreme-exponent.sqlite").ingest(
        read_json_bytes(json_number(make_row(), "quantity", token))
    )
    assert run["accepted_count"] == 0
    assert run["rejected_count"] == 1
    assert run["rejected"][0]["quantity"] == token
    assert {finding["code"] for finding in run["findings"]} == {"invalid_quantity"}


def test_json_distinct_numeric_business_ids_do_not_round_to_duplicates(tmp_path, make_row):
    left = "9007199254740992.0"
    right = "9007199254740993.0"
    first = json_number(make_row(), "record_id", left)
    second = json_number(make_row(), "record_id", right)
    raw = first[:-1] + b"," + second[1:]
    repo = Repository(tmp_path / "numeric-ids.sqlite")
    run = repo.ingest(read_json_bytes(raw))
    assert run["accepted_count"] == 2
    assert run["rejected_count"] == 0
    assert [row["record_id"] for row in run["accepted"]] == [left, right]
    assert repo.get_run(run["run_id"])["accepted"] == run["accepted"]


def test_json_large_integer_token_is_preserved_without_interpreter_digit_limit(tmp_path, make_row):
    token = "9" * 5000
    run = Repository(tmp_path / "large-number.sqlite").ingest(
        read_json_bytes(json_number(make_row(), "quantity", token))
    )
    assert run["rejected_count"] == 1
    assert run["rejected"][0]["quantity"] == token
    assert {finding["code"] for finding in run["findings"]} == {"invalid_quantity"}


@pytest.mark.parametrize("column", COLUMNS)
def test_json_escaped_nul_in_each_value_fails_before_audit(make_row, column):
    raw = json.dumps([make_row(**{column: "prefix\x00suffix"})]).encode("utf-8")
    assert b"\x00" not in raw
    with pytest.raises(IngestionError) as error:
        read_json_bytes(raw)
    assert f"JSON record 1, {column}:" in str(error.value)
    assert "NUL" in str(error.value)


@pytest.mark.parametrize("column", COLUMNS)
@pytest.mark.parametrize("invalid_text,description", [("\x00", "NUL"), ("\ud800", "surrogate")])
def test_json_invalid_escaped_column_names_have_renderable_errors(
    make_row, column, invalid_text, description
):
    row = make_row()
    row[column + invalid_text] = row.pop(column)
    raw = json.dumps([row]).encode("utf-8")
    with pytest.raises(IngestionError) as error:
        read_json_bytes(raw)
    message = str(error.value)
    assert "JSON record 1, column name" in message
    assert description in message
    assert invalid_text not in message
    message.encode("utf-8")


@pytest.mark.parametrize("column", COLUMNS)
def test_json_escaped_surrogate_in_each_value_has_actionable_error(make_row, column):
    raw = json.dumps([make_row(**{column: "\ud800"})]).encode("utf-8")
    with pytest.raises(IngestionError) as error:
        read_json_bytes(raw)
    assert f"JSON record 1, {column}:" in str(error.value)
    assert "surrogate" in str(error.value)


@pytest.mark.parametrize("column", COLUMNS)
@pytest.mark.parametrize("character", ["x", "é"])
@pytest.mark.parametrize("format_name", ["csv", "json"])
def test_each_field_accepts_exact_character_limit(make_row, csv_bytes, column, character, format_name):
    value = character * MAX_FIELD_CHARS
    row = make_row(**{column: value})
    if format_name == "csv":
        raw, reader = csv_bytes([row]), read_csv_bytes
    else:
        raw, reader = json.dumps([row], ensure_ascii=False).encode("utf-8"), read_json_bytes
    assert len(raw) < MAX_BYTES
    assert reader(raw).frame.iloc[0][column] == value


@pytest.mark.parametrize("column", COLUMNS)
@pytest.mark.parametrize("format_name", ["csv", "json"])
def test_each_field_above_character_limit_has_size_feedback(
    make_row, csv_bytes, column, format_name
):
    row = make_row(**{column: "x" * (MAX_FIELD_CHARS + 1)})
    if format_name == "csv":
        raw, reader = csv_bytes([row]), read_csv_bytes
    else:
        raw, reader = json.dumps([row]).encode("utf-8"), read_json_bytes
    assert len(raw) < MAX_BYTES
    before = csv.field_size_limit()
    with pytest.raises(IngestionError) as error:
        reader(raw)
    assert f"{MAX_FIELD_CHARS:,}" in str(error.value)
    assert "character" in str(error.value)
    assert "shorten the field" in str(error.value).lower()
    assert csv.field_size_limit() == before


@pytest.mark.parametrize("extra_characters", [0, 1])
@pytest.mark.parametrize("format_name", ["csv", "json"])
def test_column_name_character_limit_is_checked_before_schema_error(
    make_row, csv_bytes, extra_characters, format_name
):
    column = " " * (MAX_FIELD_CHARS - len("record_id") + extra_characters) + "record_id"
    row = make_row()
    row[column] = row.pop("record_id")
    if format_name == "csv":
        raw, reader = csv_bytes([row], columns=tuple(row)), read_csv_bytes
    else:
        raw, reader = json.dumps([row]).encode("utf-8"), read_json_bytes
    assert len(raw) < MAX_BYTES
    if extra_characters:
        with pytest.raises(IngestionError) as error:
            reader(raw)
        assert f"{MAX_FIELD_CHARS:,}" in str(error.value)
        assert "Schema error" not in str(error.value)
        assert column not in str(error.value)
    else:
        assert reader(raw).frame.iloc[0]["record_id"] == row[column]


def test_json_escaped_text_limit_counts_decoded_characters(make_row):
    row = make_row(location="é" * MAX_FIELD_CHARS)
    raw = json.dumps([row], ensure_ascii=True).encode("utf-8")
    assert len(raw) > MAX_FIELD_CHARS
    assert len(raw) < MAX_BYTES
    assert read_json_bytes(raw).frame.iloc[0]["location"] == row["location"]
    row["location"] += "é"
    with pytest.raises(IngestionError, match="131,072-character limit"):
        read_json_bytes(json.dumps([row], ensure_ascii=True).encode("utf-8"))


def test_oversized_duplicate_json_key_is_not_echoed_in_error():
    key = "x" * (MAX_FIELD_CHARS + 1)
    quoted_key = json.dumps(key)
    raw = f"[{{{quoted_key}: 1, {quoted_key}: 2}}]".encode("utf-8")
    with pytest.raises(IngestionError) as error:
        read_json_bytes(raw)
    assert f"{MAX_FIELD_CHARS:,}" in str(error.value)
    assert key not in str(error.value)


def test_parallel_parses_never_change_process_csv_field_limit(make_row, csv_bytes, monkeypatch):
    original_limit = csv.field_size_limit
    before = original_limit()

    def read_only_limit(*args):
        assert not args, "Ingestion must never mutate the process CSV field limit."
        return original_limit()

    monkeypatch.setattr(csv, "field_size_limit", read_only_limit)
    good = make_row(location="x" * MAX_FIELD_CHARS)
    bad = make_row(location="x" * (MAX_FIELD_CHARS + 1))
    jobs = [
        (read_csv_bytes, csv_bytes([good]), False),
        (read_csv_bytes, csv_bytes([bad]), True),
        (read_json_bytes, json.dumps([good]).encode("utf-8"), False),
        (read_json_bytes, json.dumps([bad]).encode("utf-8"), True),
    ] * 2

    def parse(job):
        reader, raw, should_fail = job
        if should_fail:
            with pytest.raises(IngestionError):
                reader(raw)
        else:
            assert len(reader(raw).frame) == 1
        assert original_limit() == before

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(parse, jobs))
    assert original_limit() == before
