"""Mocked API responses: no authentic records are asserted by these tests."""

from unittest.mock import patch
import pandas as pd
import pytest
from src.ingest import extract, MAPPING, EXPECTED_TYPES
from src.bundle import load_bundle


def source():
    return {
        "id": "vw6y-z8j6",
        "name": "311 Cases",
        "columns": [
            {"fieldName": x, "dataTypeName": EXPECTED_TYPES[x]}
            for x in MAPPING.values()
        ],
        "rowsUpdatedAt": 1,
    }


def row(identifier="100"):
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


def test_live_field_contract():
    from src.ingest import verify_metadata

    assert MAPPING["agency"] == "agency_responsible"
    bad = source()
    bad["columns"][0]["dataTypeName"] = "text"
    with pytest.raises(ValueError, match="schema"):
        verify_metadata(bad)
    bad = source()
    bad["id"] = "wrong"
    with pytest.raises(ValueError, match="identity"):
        verify_metadata(bad)


def test_keyset_pages_and_cross_page_duplicate(tmp_path):
    responses = [
        source(),
        [{"n": "2"}],
        [row("100")],
        [row("101")],
        source(),
        [{"n": "2"}],
    ]
    with patch("src.ingest.get", side_effect=responses) as get:
        meta = extract(tmp_path, page_size=1)
    assert meta["unique_request_ids"] == 2 and meta["sql_python_parity_pages"] == 2
    assert "service_request_id > 100" in get.call_args_list[3].args[2]["$where"]
    responses = [source(), [{"n": "2"}], [row("100")], [row("100")]]
    with patch("src.ingest.get", side_effect=responses):
        with pytest.raises(ValueError, match="pagination"):
            extract(tmp_path / "bad", page_size=1)


def test_report_for_fixture_bundle(tmp_path):
    from src.review import report

    with patch(
        "src.ingest.get",
        side_effect=[source(), [{"n": "1"}], [row()], source(), [{"n": "1"}]],
    ):
        extract(tmp_path)
    observations = report(tmp_path)
    assert observations["metrics"]["requests"] == 1
    assert (tmp_path / "DATA_QUALITY_REPORT.md").exists()
