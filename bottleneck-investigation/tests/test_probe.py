"""Source diagnostics must never emit sample identifiers or arbitrary error fields."""

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import requests
import pytest
from src.probe import probe
from src.ingest import get


def response(status, payload):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(payload).encode()
    r.headers["Content-Type"] = "application/json"
    r.url = "https://data.sfgov.org/TEST-ONLY"
    r.raw = SimpleNamespace(retries=SimpleNamespace(history=[]))
    return r


def test_probe_records_fields_not_rows(tmp_path, capsys):
    meta = {
        "id": "vw6y-z8j6",
        "name": "311 Cases",
        "rowsUpdatedAt": 1,
        "columns": [
            {
                "fieldName": "service_request_id",
                "dataTypeName": "number",
                "cachedContents": {"top": "DO NOT SAVE"},
            }
        ],
    }
    with patch(
        "src.probe.requests.get",
        side_effect=[
            response(200, meta),
            response(
                200,
                [
                    {
                        "service_request_id": "TEST-PRIVATE-IDENTIFIER",
                        "requested_datetime": "TEST",
                    }
                ],
            ),
        ],
    ):
        assert probe(tmp_path)
    assert "TEST-PRIVATE-IDENTIFIER" not in capsys.readouterr().out
    saved = (tmp_path / "source_metadata.json").read_text()
    assert "cachedContents" not in saved and "DO NOT SAVE" not in saved
    assert (
        json.loads((tmp_path / "probe.json").read_text())["checks"][1]["returned_rows"]
        == 1
    )


def test_safe_http_diagnostic(capsys):
    s = Mock()
    s.get.return_value = response(
        428, {"code": "rate_limited", "message": "try later", "token": "DO-NOT-LOG"}
    )
    with pytest.raises(requests.HTTPError):
        get(s, "https://data.sfgov.org/TEST-ONLY")
    output = capsys.readouterr().out
    assert "428" in output and "rate_limited" in output and "DO-NOT-LOG" not in output
