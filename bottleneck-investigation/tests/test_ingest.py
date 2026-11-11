"""Mocked API responses: no authentic records are asserted by these tests."""

from unittest.mock import patch
import pandas as pd
import pytest
from src.ingest import extract, MAPPING
from src.bundle import load_bundle


def source():
    return {
        "name": "311 TEST ONLY",
        "columns": [{"fieldName": x} for x in MAPPING.values()],
        "rowsUpdatedAt": 1,
    }


def row(identifier="TEST-ONLY"):
    r = {x: None for x in MAPPING.values()}
    r.update(
        service_request_id=identifier,
        requested_datetime="2025-01-01T12:00:00",
        closed_date="2025-01-03T12:00:00",
        status_description="Closed",
    )
    return r


def test_mock_extraction_reconciles(tmp_path):
    responses = [source(), [{"n": "1"}], [row()], source(), [{"n": "1"}]]
    with patch("src.ingest.get", side_effect=responses):
        meta = extract(tmp_path)
    assert (
        meta["rows"] == 1 and meta["source_count_before"] == meta["source_count_after"]
    )
    assert load_bundle(tmp_path)[1].requests.sum() == 1


@pytest.mark.parametrize("mode", ["changed", "short", "schema", "duplicate", "count"])
def test_reject_bad_extract(tmp_path, mode):
    meta = source()
    if mode == "schema":
        meta["columns"] = []
        responses = [meta]
    elif mode == "short":
        responses = [meta, [{"n": "1"}], []]
    elif mode == "duplicate":
        responses = [meta, [{"n": "2"}], [row(), row()], meta, [{"n": "2"}]]
    elif mode == "count":
        responses = [meta, [{"n": "1"}], [row()], meta, [{"n": "2"}]]
    else:
        responses = [
            meta,
            [{"n": "1"}],
            [row()],
            dict(meta, rowsUpdatedAt=2),
            [{"n": "1"}],
        ]
    with patch("src.ingest.get", side_effect=responses):
        with pytest.raises(ValueError):
            extract(tmp_path)
    assert not (tmp_path / "provenance.json").exists()
