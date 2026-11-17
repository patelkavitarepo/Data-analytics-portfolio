"""Synthetic USGS-shaped feed fixtures. Never require network access."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from market_intel.usgs_capture import (
    USGS_FEED, MAX_BYTES, Response, capture_feed, load_capture,
    parse_feed, taiwan_screen_events,
)


def fixture() -> dict:
    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": 1794528000000,
            "url": USGS_FEED, "title": "SIMULATED USGS-SHAPED FEED", "count": 2, "api": "1.0",
        },
        "features": [
            {"type": "Feature", "id": "SIM-NO-REAL-QUAKE-1",
             "properties": {"type": "earthquake", "mag": 5.0,
                            "time": 1794527900000, "updated": 1794527950000},
             "geometry": {"type": "Point", "coordinates": [121.0, 23.8, 10.0]}},
            {"type": "Feature", "id": "SIM-NO-REAL-QUAKE-2",
             "properties": {"type": "earthquake", "mag": 5.0,
                            "time": 1794527800000, "updated": 1794527990000},
             "geometry": {"type": "Point", "coordinates": [141.0, 36.0, 8.0]}},
        ],
    }


def body(data=None):
    return json.dumps(fixture() if data is None else data, sort_keys=True).encode("utf-8")


def transport(raw=None, status=200, content_type="application/json", url=USGS_FEED):
    return Response(raw if raw is not None else body(), status, url, {
        "content-type": content_type, "etag": '"synthetic-revision"', "date": "Fri, 13 Nov 2026 02:39:00 GMT"})


class CapturedFeedTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.clock_times = iter([
            datetime(2026, 11, 13, 2, 40, tzinfo=timezone.utc),
            datetime(2026, 11, 13, 2, 40, 2, tzinfo=timezone.utc),
        ])

    def capture(self, response=None, origin="synthetic_fixture"):
        return capture_feed(self.root, fetcher=lambda: response or transport(),
                            clock=lambda: next(self.clock_times), origin=origin)

    def test_persists_exact_raw_bytes_and_verifiable_receipt(self):
        raw = body()
        receipt = self.capture(transport(raw))
        self.assertEqual(receipt["raw_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["first_observed_at"], "2026-11-13T02:40:02Z")
        self.assertEqual(receipt["requested_at"], "2026-11-13T02:40:00Z")
        self.assertIsNone(receipt["source_first_published_at"])
        self.assertEqual(receipt["origin"], "synthetic_fixture")
        self.assertEqual(receipt["source"], "USGS_EARTHQUAKES_4_5_DAY")
        self.assertEqual(receipt["event_count"], 2)
        saved, parsed = load_capture(self.root, receipt["capture_id"])
        self.assertEqual(saved, receipt)
        self.assertEqual(parsed, fixture())
        self.assertEqual(list(self.root.rglob("*.json")).__len__(), 2)

    def test_two_captures_same_bytes_share_object_but_not_receipt(self):
        a = self.capture()
        self.clock_times = iter([
            datetime(2026, 11, 13, 2, 41, tzinfo=timezone.utc),
            datetime(2026, 11, 13, 2, 41, 2, tzinfo=timezone.utc),
        ])
        b = self.capture()
        self.assertEqual(a["raw_sha256"], b["raw_sha256"])
        self.assertNotEqual(a["capture_id"], b["capture_id"])
        self.assertNotEqual(a["first_observed_at"], b["first_observed_at"])
        self.assertEqual(len(list((self.root / "objects").rglob("*.json"))), 1)
        self.assertEqual(len(list((self.root / "receipts").rglob("*.json"))), 2)

    def test_tampering_rejected(self):
        r = self.capture()
        target = self.root / "objects" / r["raw_sha256"][:2] / (r["raw_sha256"] + ".json")
        target.write_bytes(b"{}")
        with self.assertRaises(ValueError):
            load_capture(self.root, r["capture_id"])

    def test_taiwan_screen_does_not_issue_alert(self):
        receipt = self.capture()
        _, feed = load_capture(self.root, receipt["capture_id"])
        records = taiwan_screen_events(feed, receipt)
        self.assertEqual([r["usgs_event_id"] for r in records], ["SIM-NO-REAL-QUAKE-1"])
        self.assertFalse(records[0]["alert_permitted"])
        self.assertIsNone(records[0]["source_first_published_at"])
        self.assertEqual(records[0]["first_observed_at"], receipt["first_observed_at"])
        self.assertNotIn("company_id", records[0])

    def test_bytes_new_version_keeps_prior_record(self):
        a = self.capture()
        changed = fixture()
        changed["features"][0]["properties"]["mag"] = 5.1
        self.clock_times = iter([
            datetime(2026, 11, 13, 2, 42, tzinfo=timezone.utc),
            datetime(2026, 11, 13, 2, 42, 2, tzinfo=timezone.utc),
        ])
        b = self.capture(transport(body(changed)))
        self.assertNotEqual(a["raw_sha256"], b["raw_sha256"])
        self.assertEqual(load_capture(self.root, a["capture_id"])[1], fixture())
        self.assertEqual(load_capture(self.root, b["capture_id"])[1], changed)

    def test_http_errors_and_wrong_url_fail_without_writing(self):
        for response in (transport(status=503), transport(url="https://example.com/x"),
                         transport(content_type="text/html")):
            with self.subTest(response=response):
                self.clock_times = iter([datetime.now(timezone.utc)] * 2)
                with self.assertRaises(ValueError):
                    self.capture(response)
        self.assertFalse((self.root / "objects").exists())

    def test_invalid_json_does_not_create_archive(self):
        with self.assertRaises(ValueError):
            self.capture(transport(b"{oops"))
        self.assertFalse((self.root / "objects").exists())

    def test_aware_clock_required(self):
        with self.assertRaises(ValueError):
            capture_feed(self.root, fetcher=transport, clock=lambda: datetime(2026, 11, 13))

    def test_backwards_clock_rejected(self):
        instants = iter([datetime(2026, 11, 13, 2, 40, 1, tzinfo=timezone.utc),
                         datetime(2026, 11, 13, 2, 40, tzinfo=timezone.utc)])
        with self.assertRaises(ValueError):
            capture_feed(self.root, fetcher=transport, clock=lambda: next(instants))

    def test_disallows_unrecognized_provenance(self):
        with self.assertRaises(ValueError):
            self.capture(origin="real_company_alert")


class GeoJSONValidationTests(unittest.TestCase):
    def test_accept_empty_feed(self):
        data = fixture()
        data["features"] = []
        data["metadata"]["count"] = 0
        self.assertEqual(parse_feed(body(data))["features"], [])

    def test_reject_oversize_body(self):
        with self.assertRaises(ValueError):
            parse_feed(b" " * (MAX_BYTES + 1))

    def test_reject_incorrect_count(self):
        data = fixture()
        data["metadata"]["count"] = 99
        with self.assertRaises(ValueError):
            parse_feed(body(data))

    def test_reject_duplicate_event_id(self):
        data = fixture()
        data["features"][1]["id"] = data["features"][0]["id"]
        with self.assertRaises(ValueError):
            parse_feed(body(data))

    def test_reject_non_numeric_or_out_of_bounds_coordinate(self):
        for value in (None, "25", 99, float("inf"), True):
            with self.subTest(value=value):
                data = fixture()
                data["features"][0]["geometry"]["coordinates"][1] = value
                with self.assertRaises(ValueError):
                    parse_feed(body(data))

    def test_reject_false_epoch_milliseconds(self):
        for value in (None, "1794528000000", True, -2):
            with self.subTest(value=value):
                data = fixture()
                data["features"][0]["properties"]["time"] = value
                with self.assertRaises(ValueError):
                    parse_feed(body(data))

    def test_reject_unexpected_source_url(self):
        data = fixture()
        data["metadata"]["url"] = "https://other.example"
        with self.assertRaises(ValueError):
            parse_feed(body(data))

    def test_reject_non_earthquake_type(self):
        data = fixture()
        data["features"][0]["properties"]["type"] = "quarry blast"
        with self.assertRaises(ValueError):
            parse_feed(body(data))

    def test_reject_invalid_magnitude(self):
        data = fixture()
        data["features"][0]["properties"]["mag"] = float("nan")
        with self.assertRaises(ValueError):
            parse_feed(body(data))

    def test_reject_unknown_geometry(self):
        data = fixture()
        data["features"][0]["geometry"]["type"] = "Polygon"
        with self.assertRaises(ValueError):
            parse_feed(body(data))


if __name__ == "__main__":
    unittest.main()
