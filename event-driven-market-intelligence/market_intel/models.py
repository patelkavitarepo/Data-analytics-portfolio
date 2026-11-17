"""Version-one schema, validation, and point-in-time timestamps (stdlib only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamps must be ISO-8601 strings with explicit offsets")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Timezone/offset required: {value}")
    return parsed.astimezone(timezone.utc)


def stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def coordinate(lat: float | None, lon: float | None) -> None:
    if (lat is None) != (lon is None):
        raise ValueError("Latitude and longitude must be supplied together")
    if lat is not None and (not -90 <= lat <= 90 or not -180 <= lon <= 180):
        raise ValueError("Invalid geographic coordinates")


@dataclass(frozen=True)
class Facility:
    facility_id: str
    company_id: str
    label: str
    latitude: float | None
    longitude: float | None
    location_quality: str
    first_observed_at: datetime
    synthetic: bool

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "Facility":
        value = cls(
            item["facility_id"], item["company_id"], item["label"],
            item.get("latitude"), item.get("longitude"),
            item["location_quality"], utc(item["first_observed_at"]),
            item["synthetic"],
        )
        coordinate(value.latitude, value.longitude)
        if value.location_quality not in {"synthetic", "verified_geocode", "address_only"}:
            raise ValueError("Unknown facility location quality")
        if value.location_quality == "address_only" and value.latitude is not None:
            raise ValueError("Address-only site must have unknown coordinates")
        return value


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    latitude: float
    longitude: float
    screening_radius_km: float
    occurred_at: datetime | None
    source_published_at: datetime
    ingested_at: datetime
    source_id: str
    source_revision: str
    source_url: str
    synthetic: bool

    @property
    def known_at(self) -> datetime:
        return max(self.source_published_at, self.ingested_at)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "Event":
        value = cls(
            item["event_id"], item["event_type"], item["latitude"],
            item["longitude"], item["screening_radius_km"],
            utc(item["occurred_at"]) if item.get("occurred_at") else None,
            utc(item["source_published_at"]), utc(item["ingested_at"]),
            item["source_id"], item["source_revision"],
            item["source_url"], item["synthetic"],
        )
        coordinate(value.latitude, value.longitude)
        if value.screening_radius_km < 0 or value.screening_radius_km > 500:
            raise ValueError("Screening radius must be between 0 and 500 km")
        if not value.source_revision:
            raise ValueError("Event source revision is required")
        return value


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    event_id: str
    facility_id: str
    claim: str
    source_role: str
    verification: str
    source_id: str
    source_revision: str
    independence_group: str
    source_url: str
    source_published_at: datetime
    ingested_at: datetime
    synthetic: bool
    retracts: str | None = None

    @property
    def known_at(self) -> datetime:
        return max(self.source_published_at, self.ingested_at)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "Evidence":
        value = cls(
            item["evidence_id"], item["event_id"], item["facility_id"],
            item["claim"], item["source_role"], item["verification"],
            item["source_id"], item["source_revision"],
            item["independence_group"], item["source_url"],
            utc(item["source_published_at"]), utc(item["ingested_at"]),
            item["synthetic"], item.get("retracts"),
        )
        if value.claim not in {"facility_disrupted", "facility_recovered", "facility_unaffected", "retraction"}:
            raise ValueError(f"Unknown evidence claim: {value.claim}")
        if value.source_role not in {"company_primary", "official_hazard", "unverified_news"}:
            raise ValueError("Unknown evidence source role")
        if value.verification not in {"verified", "unverified"}:
            raise ValueError("Unknown verification value")
        if bool(value.retracts) != (value.claim == "retraction"):
            raise ValueError("Retraction requires retracts and no other claim may have it")
        if not value.source_revision or not value.independence_group:
            raise ValueError("Source revision and independence group required")
        return value


def _dedupe(items: list[Any], key: str) -> tuple[Any, ...]:
    seen: dict[str, Any] = {}
    for item in items:
        identity = getattr(item, key)
        if identity in seen and seen[identity] != item:
            raise ValueError(f"Conflicting revisions using the same {key}: {identity}")
        seen[identity] = item
    return tuple(seen.values())


@dataclass(frozen=True)
class Case:
    company_id: str
    ticker: str
    mode: str
    facilities: tuple[Facility, ...]
    events: tuple[Event, ...]
    evidence: tuple[Evidence, ...]

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "Case":
        if item.get("mode") != "synthetic":
            raise ValueError("Proof of concept intentionally runs synthetic mode only")
        facilities = _dedupe([Facility.from_dict(x) for x in item["facilities"]], "facility_id")
        events = _dedupe([Event.from_dict(x) for x in item["events"]], "event_id")
        evidence = _dedupe([Evidence.from_dict(x) for x in item["evidence"]], "evidence_id")
        if not all(v.synthetic for v in (*facilities, *events, *evidence)):
            raise ValueError("Synthetic scenario cannot include real-world records")
        if not all(f.location_quality == "synthetic" for f in facilities):
            raise ValueError("All simulation facilities must declare synthetic coordinates")
        if not all(x.source_url.startswith("synthetic://") for x in (*events, *evidence)):
            raise ValueError("Simulation sources must use synthetic:// URLs")
        ids = {f.facility_id for f in facilities}
        event_ids = {e.event_id for e in events}
        if any(f.company_id != item["company_id"] for f in facilities):
            raise ValueError("Facility-company relationship mismatch")
        if any(x.facility_id not in ids or x.event_id not in event_ids for x in evidence):
            raise ValueError("Evidence must refer to known facility and event")
        evidence_by_id = {x.evidence_id: x for x in evidence}
        for x in evidence:
            if x.claim == "retraction":
                target = evidence_by_id.get(x.retracts)
                if (target is None or target.event_id != x.event_id
                    or target.facility_id != x.facility_id or target.evidence_id == x.evidence_id
                    or target.known_at >= x.known_at):
                    raise ValueError("Retraction must target an earlier claim for same event/facility")
        return cls(item["company_id"], item["ticker"], "synthetic", facilities, events, evidence)


def load_case(path: str | Path) -> Case:
    with open(path, encoding="utf-8") as handle:
        return Case.from_dict(json.load(handle))
