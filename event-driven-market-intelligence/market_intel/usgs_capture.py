"""USGS raw-snapshot capture: no operational/company alerts and no automatic polling.

A feed's generated and updated values are source metadata, NOT verified first-publication
times. This adapter records raw bytes, actual observed-at times, and immutable receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import stamp

USGS_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
MAX_BYTES = 3_000_000
TAIWAN_SCREEN = {"min_lat": 21.0, "max_lat": 26.5, "min_lon": 119.0, "max_lon": 123.5}


@dataclass(frozen=True)
class Response:
    body: bytes
    status: int
    url: str
    headers: dict[str, str]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("USGS redirect refused; review endpoint manually")


def download_usgs() -> Response:
    """One explicit request only; no retries, daemon, scheduler or pagination."""
    request = Request(
        USGS_FEED,
        headers={"Accept": "application/geo+json, application/json",
                 "User-Agent": "project008-event-research/0.2 (+https://github.com/patelkavitarepo/Data-analytics-portfolio)"},
        method="GET",
    )
    with build_opener(_NoRedirect).open(request, timeout=15) as handle:
        raw = handle.read(MAX_BYTES + 1)
        return Response(
            body=raw, status=handle.status, url=handle.geturl(),
            headers={k.lower(): v for k, v in handle.headers.items()},
        )


def _moment(milliseconds: object, label: str) -> datetime:
    if type(milliseconds) is not int or milliseconds < 0:
        raise ValueError(f"{label} must be a nonnegative integer epoch-millisecond timestamp")
    try:
        return datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError(f"{label} is outside supported timestamp range") from exc


def _utc_now(clock: Callable[[], datetime]) -> datetime:
    instant = clock()
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("A timezone-aware capture clock is required")
    return instant.astimezone(timezone.utc)


def parse_feed(body: bytes) -> dict:
    """Validate the entire *worldwide* feed before filtering or persisting."""
    if not body or len(body) > MAX_BYTES:
        raise ValueError("Invalid feed size")
    try:
        data = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON body") from exc
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("Expected USGS GeoJSON FeatureCollection")
    metadata, features = data.get("metadata"), data.get("features")
    if not isinstance(metadata, dict) or not isinstance(features, list):
        raise ValueError("Missing metadata or features")
    _moment(metadata.get("generated"), "metadata.generated")
    if type(metadata.get("count")) is not int or metadata["count"] != len(features):
        raise ValueError("USGS count does not match feature array")
    if metadata.get("url") != USGS_FEED:
        raise ValueError("Unexpected source URL in feed metadata")
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Unexpected feature type")
        identifier = feature.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Missing or duplicate feature ID")
        seen.add(identifier)
        prop, geo = feature.get("properties"), feature.get("geometry")
        if not isinstance(prop, dict) or not isinstance(geo, dict):
            raise ValueError("Missing properties or geometry")
        if prop.get("type") != "earthquake" or geo.get("type") != "Point":
            raise ValueError("USGS feed contains a non-earthquake point event")
        coords = geo.get("coordinates")
        if not isinstance(coords, list) or len(coords) < 2 or len(coords) > 3:
            raise ValueError("Invalid earthquake coordinate tuple")
        lon, lat = coords[:2]
        if (type(lon) not in (float, int) or type(lat) not in (float, int)
                or not math.isfinite(lat) or not math.isfinite(lon)
                or not -90 <= lat <= 90 or not -180 <= lon <= 180):
            raise ValueError("Invalid earthquake location")
        if len(coords) == 3 and (coords[2] is not None and
                (type(coords[2]) not in (float, int) or not math.isfinite(coords[2]))):
            raise ValueError("Invalid earthquake depth")
        _moment(prop.get("time"), "properties.time")
        _moment(prop.get("updated"), "properties.updated")
        mag = prop.get("mag")
        if mag is not None and (type(mag) not in (int, float) or not math.isfinite(mag)):
            raise ValueError("Invalid earthquake magnitude")
    return data


def capture_feed(
    root: Path,
    *,
    fetcher: Callable[[], Response],
    clock: Callable[[], datetime],
    origin: str = "synthetic_fixture",
) -> dict:
    """Capture a single feed response. Tests inject bytes and a deterministic clock.

    origin='live_usgs' is only used by the explicit CLI. Neither mode enters the
    pre-existing, synthetic-only company-risk engine.
    """
    if origin not in {"synthetic_fixture", "live_usgs"}:
        raise ValueError("Unrecognized capture provenance")
    requested = _utc_now(clock)
    response = fetcher()
    received = _utc_now(clock)
    if received < requested:
        raise ValueError("Capture clock went backwards")
    if response.status != 200 or response.url != USGS_FEED:
        raise ValueError("Unexpected HTTP status or final URL")
    headers = {key.lower(): value for key, value in response.headers.items()}
    if headers.get("content-type", "").split(";")[0].strip().lower() not in (
        "application/json", "application/geo+json"):
        raise ValueError("Unexpected response content type")
    feed = parse_feed(response.body)  # fail closed, before writing any bytes
    digest = hashlib.sha256(response.body).hexdigest()
    root = Path(root)
    object_file = root / "objects" / digest[:2] / (digest + ".json")
    object_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with object_file.open("xb") as out:
            out.write(response.body)
    except FileExistsError:
        if object_file.read_bytes() != response.body:
            raise ValueError("SHA256 path collision or corrupted existing archive")
    receipt = {
        "schema_version": 1,
        "capture_id": uuid.uuid4().hex,
        "origin": origin,
        "source": "USGS_EARTHQUAKES_4_5_DAY",
        "credit": "U.S. Geological Survey",
        "request_url": USGS_FEED,
        "response_url": response.url,
        "requested_at": stamp(requested),
        "first_observed_at": stamp(received),
        "source_first_published_at": None,
        "feed_generated_at": stamp(_moment(feed["metadata"]["generated"], "metadata.generated")),
        "raw_sha256": digest,
        "raw_size_bytes": len(response.body),
        "event_count": len(feed["features"]),
        "source_api_version": feed["metadata"].get("api"),
        "response_headers": {key: headers[key] for key in
                             ("date", "etag", "last-modified", "content-type") if key in headers},
        "warning": "USGS times do not prove first publication; no facility impact is inferred",
    }
    receipts = root / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    receipt_path = receipts / (receipt["capture_id"] + ".json")
    with receipt_path.open("x", encoding="utf-8") as out:
        json.dump(receipt, out, sort_keys=True, indent=2)
        out.write("\n")
    return receipt


def load_capture(root: Path, capture_id: str) -> tuple[dict, dict]:
    """Independently check stored raw bytes; never silently accept altered snapshots."""
    if len(capture_id) != 32 or any(c not in "0123456789abcdef" for c in capture_id):
        raise ValueError("Invalid receipt ID")
    root = Path(root)
    receipt = json.loads((root / "receipts" / (capture_id + ".json")).read_text(encoding="utf-8"))
    if receipt.get("schema_version") != 1 or receipt.get("capture_id") != capture_id:
        raise ValueError("Unexpected receipt format")
    digest = receipt["raw_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid SHA256 in receipt")
    body = (root / "objects" / digest[:2] / (digest + ".json")).read_bytes()
    if hashlib.sha256(body).hexdigest() != digest or len(body) != receipt["raw_size_bytes"]:
        raise ValueError("Archived payload failed SHA256/length verification")
    return receipt, parse_feed(body)


def taiwan_screen_events(feed: dict, receipt: dict) -> list[dict]:
    """Broad bounding-box screen of earthquake epicenters, NOT a site-impact assessment."""
    result: list[dict] = []
    for feature in feed["features"]:
        lon, lat = feature["geometry"]["coordinates"][:2]
        if not (TAIWAN_SCREEN["min_lon"] <= lon <= TAIWAN_SCREEN["max_lon"]
                and TAIWAN_SCREEN["min_lat"] <= lat <= TAIWAN_SCREEN["max_lat"]):
            continue
        prop = feature["properties"]
        result.append({
            "usgs_event_id": feature["id"],
            "magnitude": prop.get("mag"),
            "latitude": lat,
            "longitude": lon,
            "depth_km": feature["geometry"]["coordinates"][2]
                if len(feature["geometry"]["coordinates"]) > 2 else None,
            "occurred_at": stamp(_moment(prop["time"], "properties.time")),
            "source_updated_at": stamp(_moment(prop["updated"], "properties.updated")),
            "source_first_published_at": None,
            "first_observed_at": receipt["first_observed_at"],
            "raw_sha256": receipt["raw_sha256"],
            "alert_permitted": False,
            "assessment": "GEOGRAPHIC_SCREEN_ONLY — no TSMC facility match",
        })
    return sorted(result, key=lambda x: (x["occurred_at"], x["usgs_event_id"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit, one-shot USGS evidence capture (NO alerts)")
    parser.add_argument("--live-usgs", action="store_true", help="I authorize ONE real USGS request")
    parser.add_argument("--output", type=Path, help="Local observation directory (ignored by Git)")
    args = parser.parse_args()
    if not args.live_usgs or args.output is None:
        parser.error("Network disabled by default. Supply --live-usgs AND --output for one capture.")
    receipt = capture_feed(args.output, fetcher=download_usgs,
                           clock=lambda: datetime.now(timezone.utc), origin="live_usgs")
    saved_receipt, feed = load_capture(args.output, receipt["capture_id"])
    print(json.dumps({"receipt": saved_receipt,
                      "taiwan_screen_events": taiwan_screen_events(feed, saved_receipt),
                      "research_notice": "No company matching, validated source latency, or live alert"},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
