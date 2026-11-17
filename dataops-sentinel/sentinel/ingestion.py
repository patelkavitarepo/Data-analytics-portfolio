"""Bounded CSV/JSON ingestion; no adapter performs network I/O by default.

Input schemas are normalized, but values remain strings until validation. The
content hash describes original bytes, including whitespace and column order.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
import re
from typing import Callable

import pandas as pd

from .schema import COLUMNS, MAX_BYTES, MAX_FIELD_CHARS, MAX_ROWS


class IngestionError(ValueError):
    """An actionable source-format or schema error, before a run is written."""


@dataclass(frozen=True)
class Batch:
    frame: pd.DataFrame
    content_hash: str
    source_name: str
    source_kind: str
    byte_count: int


def _decode(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise IngestionError("Input must be bytes; read the source in binary mode.")
    if len(raw) > MAX_BYTES:
        raise IngestionError(f"Source exceeds the {MAX_BYTES:,}-byte (2 MiB) limit.")
    if not raw:
        raise IngestionError("Source is empty; provide a header and at least one record.")
    try:
        value = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError("Use a UTF-8 encoded CSV or JSON source.") from exc
    if "\x00" in value:
        raise IngestionError("Source contains NUL bytes; provide a text CSV or JSON file.")
    return value


def _columns(names: list[str]) -> list[str]:
    if not all(isinstance(name, str) for name in names):
        raise IngestionError("All column names must be strings.")
    normalized = [re.sub(r"\s+", "_", name.strip().lower()) for name in names]
    if len(normalized) != len(set(normalized)):
        raise IngestionError("Column names collide after normalization; use one of each required column.")
    missing = sorted(set(COLUMNS) - set(normalized))
    extra = sorted(set(normalized) - set(COLUMNS))
    details = []
    if missing:
        details.append("missing columns: " + ", ".join(missing))
    if extra:
        details.append("unexpected columns: " + ", ".join(extra))
    if details:
        raise IngestionError("Schema error (" + "; ".join(details) + "). Expected: " + ", ".join(COLUMNS))
    return normalized


def _batch(raw: bytes, rows: list[dict[str, str]], source_name: str, source_kind: str) -> Batch:
    if not rows:
        raise IngestionError("Source has no records; include at least one data row.")
    return Batch(
        frame=pd.DataFrame(rows, columns=COLUMNS, dtype=str),
        content_hash=hashlib.sha256(raw).hexdigest(),
        source_name=str(source_name),
        source_kind=source_kind,
        byte_count=len(raw),
    )


def _check_field_size(value: str, context: str) -> None:
    if len(value) > MAX_FIELD_CHARS:
        raise IngestionError(
            f"{context}: field exceeds the {MAX_FIELD_CHARS:,}-character limit. Shorten the field."
        )


def _check_csv_quotes(value: str) -> None:
    """Reject stray quotes that ``csv.reader(strict=True)`` treats as literals."""
    state = "start"
    for position, char in enumerate(value, start=1):
        if state == "quoted":
            if char == '"':
                state = "after_quote"
        elif state == "after_quote":
            if char == '"':
                state = "quoted"  # Escaped quote inside a quoted field.
            elif char in ",\r\n":
                state = "start"
            else:
                raise IngestionError(
                    f"Malformed CSV near character {position}: unexpected text after a closing quote."
                )
        elif char == '"':
            if state != "start":
                raise IngestionError(
                    f"Malformed CSV near character {position}: quote inside an unquoted field. "
                    "Quote the entire field and double embedded quotes."
                )
            state = "quoted"
        elif char in ",\r\n":
            state = "start"
        else:
            state = "unquoted"


def read_csv_bytes(raw: bytes, source_name: str = "upload.csv") -> Batch:
    """Read strict UTF-8 CSV with exactly the required columns and bounded rows."""
    value = _decode(raw)
    _check_csv_quotes(value)
    reader = csv.reader(io.StringIO(value, newline=""), strict=True)
    try:
        header = next(reader, None)
        if header is None:
            raise IngestionError("CSV is empty; include the required header.")
        for column_number, name in enumerate(header, start=1):
            _check_field_size(name, f"CSV column name {column_number}")
        columns = _columns(header)
        rows = []
        for row_number, row in enumerate(reader, start=1):
            if row_number > MAX_ROWS:
                raise IngestionError(f"CSV exceeds the {MAX_ROWS:,}-record limit.")
            if len(row) != len(columns):
                raise IngestionError(
                    f"CSV data row {row_number} has {len(row)} fields; expected {len(columns)}. "
                    "Quote values containing commas and supply every field."
                )
            for name, field in zip(columns, row):
                _check_field_size(field, f"CSV data row {row_number}, {name}")
            rows.append(dict(zip(columns, row)))
    except csv.Error as exc:
        if "field larger than field limit" in str(exc):
            raise IngestionError(
                f"CSV field near physical line {reader.line_num} exceeds the current "
                f"{csv.field_size_limit():,}-character CSV parser limit. "
                f"Fields must contain at most {MAX_FIELD_CHARS:,} characters; shorten the field."
            ) from exc
        raise IngestionError(f"Malformed CSV near physical line {reader.line_num}: {exc}.") from exc
    return _batch(raw, rows, source_name, "csv")


def _json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _check_field_size(key, "JSON column name")
            raise IngestionError(f"JSON object repeats key {key!r}; use unique keys.")
        result[key] = value
    return result


def _invalid_json_constant(value: str) -> None:
    raise IngestionError(f"JSON constant {value} is invalid; use a finite number or null.")


def _check_json_text(value: str, context: str) -> None:
    """Check characters after JSON escapes have been decoded, including keys."""
    _check_field_size(value, context)
    if "\x00" in value:
        raise IngestionError(f"{context}: remove NUL characters; provide text fields.")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise IngestionError(f"{context}: remove invalid Unicode surrogate characters.") from exc


def read_json_bytes(raw: bytes, source_name: str = "api.json") -> Batch:
    """Read a bounded JSON array of flat records using the same CSV schema."""
    text = _decode(raw)
    try:
        # Preserve number lexemes: binary floats can round invalid fractional or
        # out-of-range quantities into valid integers, or merge distinct IDs.
        records = json.loads(
            text,
            object_pairs_hook=_json_object,
            parse_constant=_invalid_json_constant,
            parse_int=str,
            parse_float=str,
        )
    except IngestionError:
        raise
    except (ValueError, RecursionError) as exc:
        raise IngestionError("Malformed JSON; supply a JSON array of flat record objects.") from exc
    if not isinstance(records, list):
        raise IngestionError("JSON must be an array of record objects.")
    if len(records) > MAX_ROWS:
        raise IngestionError(f"JSON exceeds the {MAX_ROWS:,}-record limit.")
    rows = []
    for row_number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise IngestionError(f"JSON record {row_number} must be an object.")
        for column_number, name in enumerate(record, start=1):
            _check_json_text(name, f"JSON record {row_number}, column name {column_number}")
        columns = _columns(list(record))
        row = {}
        for name, value in zip(columns, record.values()):
            if isinstance(value, (dict, list, bool)):
                raise IngestionError(f"JSON record {row_number}, {name}: use a string, number, or null.")
            normalized_value = "" if value is None else str(value)
            _check_json_text(normalized_value, f"JSON record {row_number}, {name}")
            row[name] = normalized_value
        rows.append(row)
    return _batch(raw, rows, source_name, "json")


def fetch_json(fetcher: Callable, source_name: str = "mock-api.json") -> Batch:
    """Adapt one injected HTTP-like response; never create a network client.

    The caller supplies a zero-argument callable with a bounded timeout and body
    if it chooses to implement a real transport. This MVP uses mocked responses
    only. A response must expose integer ``status_code`` and bytes ``content``.
    """
    if not callable(fetcher):
        raise IngestionError("Provide a callable JSON transport; no live fetch is configured.")
    try:
        response = fetcher()
    except Exception as exc:
        raise IngestionError("JSON transport failed; check the source or use the offline demo.") from exc
    status = getattr(response, "status_code", None)
    if not isinstance(status, int) or status < 200 or status >= 300:
        raise IngestionError(f"JSON source returned HTTP {status}; expected a 2xx response.")
    content = getattr(response, "content", None)
    if not isinstance(content, bytes):
        raise IngestionError("JSON response must expose a bytes content body.")
    return read_json_bytes(content, source_name)
