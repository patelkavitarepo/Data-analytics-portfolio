import hashlib
import json
from types import SimpleNamespace

import pytest

from sentinel.ingestion import (
    IngestionError,
    fetch_json,
    read_csv_bytes,
    read_json_bytes,
)
from sentinel.schema import COLUMNS, MAX_BYTES, MAX_ROWS


def test_csv_provenance_and_column_normalization(make_row, csv_bytes):
    raw = csv_bytes([make_row()])
    header, body = raw.split(b"\n", 1)
    raw = header.replace(b"record_id", b" Record ID ") + b"\n" + body
    batch = read_csv_bytes(raw, source_name="fictional.csv")
    assert tuple(batch.frame.columns) == COLUMNS
    assert len(batch.frame) == 1
    assert batch.content_hash == hashlib.sha256(raw).hexdigest()
    assert batch.byte_count == len(raw)
    assert batch.source_name == "fictional.csv"


def test_missing_columns_actionable():
    with pytest.raises(IngestionError) as error:
        read_csv_bytes(b"record_id,quantity\nSYN-1,2\n")
    assert "event_timestamp_utc" in str(error.value)


@pytest.mark.parametrize(
    "raw",
    [
        b"record_id,record_id\na,b\n",
        b"record_id, Record ID \na,b\n",
        b"\xff\xfe\x00bad",
        b"",
        b'"unterminated\n',
    ],
)
def test_invalid_schema_encoding_and_format_rejected(raw):
    with pytest.raises(IngestionError):
        read_csv_bytes(raw)


@pytest.mark.parametrize("extra", [b",unexpected", b""])
def test_ragged_csv_rejected(make_row, csv_bytes, extra):
    raw = csv_bytes([make_row()])
    lines = raw.splitlines()
    if extra:
        lines[1] += extra
    else:
        lines[1] = lines[1].rsplit(b",", 1)[0]
    with pytest.raises(IngestionError):
        read_csv_bytes(b"\n".join(lines) + b"\n")


def test_header_only_rejected():
    with pytest.raises(IngestionError):
        read_csv_bytes((",".join(COLUMNS) + "\n").encode())


def test_extra_columns_rejected(make_row, csv_bytes):
    row = make_row(extra="unsupported")
    with pytest.raises(IngestionError):
        read_csv_bytes(csv_bytes([row], (*COLUMNS, "extra")))


def test_byte_and_row_limits(make_row, csv_bytes):
    with pytest.raises(IngestionError):
        read_csv_bytes(b"x" * (MAX_BYTES + 1))
    rows = [make_row(str(i)) for i in range(MAX_ROWS + 1)]
    with pytest.raises(IngestionError):
        read_csv_bytes(csv_bytes(rows))
    # Exactly the documented row limit remains usable.
    assert len(read_csv_bytes(csv_bytes(rows[:-1])).frame) == MAX_ROWS


def test_json_ingestion_and_one_shot_mocked_adapter(make_row):
    raw = json.dumps([make_row()]).encode()
    batch = read_json_bytes(raw)
    assert len(batch.frame) == 1
    assert batch.content_hash == hashlib.sha256(raw).hexdigest()
    calls = []

    def fetcher():
        calls.append(True)
        return SimpleNamespace(status_code=200, content=raw)

    result = fetch_json(fetcher)
    assert calls == [True]
    assert result.frame.to_dict("records") == batch.frame.to_dict("records")


@pytest.mark.parametrize("payload", [b"{}", b"[1]", b"[]", b"null", b"not-json"])
def test_json_errors(payload):
    with pytest.raises(IngestionError):
        read_json_bytes(payload)


def test_api_error_and_offline_path_are_actionable():
    with pytest.raises(IngestionError):
        fetch_json(lambda: SimpleNamespace(status_code=503, content=b"unavailable"))

    def offline():
        raise TimeoutError("offline fixture")

    with pytest.raises(IngestionError):
        fetch_json(offline)
    with pytest.raises(IngestionError):
        fetch_json(lambda: SimpleNamespace(status_code=200, content=b"[broken"))
    with pytest.raises(IngestionError):
        fetch_json(lambda: SimpleNamespace(status_code=200, content=b"x" * (MAX_BYTES + 1)))


def test_quotes_embedded_in_unquoted_csv_field_are_rejected(make_row, csv_bytes):
    raw = csv_bytes([make_row()]).replace(b"Fictional North Depot", b'Fictional "North" Depot')
    with pytest.raises(IngestionError):
        read_csv_bytes(raw)


def test_valid_escaped_quotes_and_multiline_csv_fields_are_preserved(make_row, csv_bytes):
    location = 'Fictional "North"\nDepot, Bay A'
    batch = read_csv_bytes(csv_bytes([make_row(location=location)]))
    assert len(batch.frame) == 1
    assert batch.frame.iloc[0]["location"] == location
