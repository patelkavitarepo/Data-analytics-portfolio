"""Shared tiny synthetic inputs; tests never require a network service."""

import csv
import io
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from sentinel.schema import COLUMNS  # noqa: E402


@pytest.fixture
def make_row():
    def factory(record_id="SYN-001", **changes):
        row = {
            "record_id": record_id,
            "event_timestamp_utc": "2026-01-15T12:00:00Z",
            "location": "Fictional North Depot",
            "category": "delivery",
            "quantity": "10",
            "status": "completed",
        }
        row.update(changes)
        return row

    return factory


@pytest.fixture
def csv_bytes():
    def factory(rows, columns=COLUMNS):
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue().encode("utf-8")

    return factory


@pytest.fixture
def example_path():
    return PROJECT / "data" / "synthetic_operations.csv"


@pytest.fixture
def manifest_path():
    return PROJECT / "data" / "truth_manifest.json"
