"""Explicit, replayable screening logic; never estimates physical hazard or market impact."""

from __future__ import annotations

from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from .models import Case, Event, Evidence, Facility, stamp, utc


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate spherical great-circle distance; not a measured hazard footprint."""
    a1, a2 = radians(lat1), radians(lat2)
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    h = sin(dlat / 2) ** 2 + cos(a1) * cos(a2) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(h)))


def _status(records: list[Evidence]) -> tuple[str, list[str], list[str]]:
    """Only verified primary statements may assert actual facility operating status."""
    retracted = {
        e.retracts for e in records
        if e.claim == "retraction" and e.source_role == "company_primary"
        and e.verification == "verified"
    }
    active = [
        e for e in records
        if e.evidence_id not in retracted and e.claim != "retraction"
        and e.verification == "verified" and e.source_role == "company_primary"
    ]
    state = "Potential Exposure"
    decisive: list[str] = []
    for e in sorted(active, key=lambda v: (v.known_at, v.evidence_id)):
        if e.claim == "facility_disrupted":
            state = "Confirmed Disruption"
            decisive.append(e.evidence_id)
        elif e.claim == "facility_unaffected":
            state = "Dismissed"
            decisive.append(e.evidence_id)
        elif e.claim == "facility_recovered" and state == "Confirmed Disruption":
            state = "Resolved"
            decisive.append(e.evidence_id)
    return state, decisive, sorted(retracted)


def _snapshot(case: Case, event: Event, facility: Facility,
              at: datetime, visible: list[Evidence], revision: int, km: float) -> dict:
    status, decisive, retracted = _status(visible)
    warnings = ["Circular distance is a screening heuristic, NOT a hazard intensity/impact map."]
    if status == "Potential Exposure":
        warnings.append("No verified operational impact; potential exposure only.")
    if any(e.source_role != "company_primary" or e.verification != "verified" for e in visible):
        warnings.append("One or more reports remain unverified for operational claims.")
    return {
        "mode": "SYNTHETIC_RESEARCH_ONLY",
        "company_id": case.company_id,
        "ticker": case.ticker,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "facility_id": facility.facility_id,
        "distance_km": round(km, 3),
        "screening_radius_km": event.screening_radius_km,
        "revision": revision,
        "status": status,
        "event_occurred_at": stamp(event.occurred_at) if event.occurred_at else None,
        "event_source_published_at": stamp(event.source_published_at),
        "event_ingested_at": stamp(event.ingested_at),
        "alert_generated_at": stamp(at),
        "publication_to_alert_seconds": int((at - event.source_published_at).total_seconds()),
        "ingestion_to_alert_seconds": int((at - event.ingested_at).total_seconds()),
        "event_source_id": event.source_id,
        "event_source_revision": event.source_revision,
        "visible_evidence_ids": [e.evidence_id for e in visible],
        "decisive_evidence_ids": decisive,
        "retracted_evidence_ids": retracted,
        "source_independence_groups": sorted(set(e.independence_group for e in visible)),
        "warnings": warnings,
    }


def replay(case: Case, as_of: str | datetime | None = None) -> list[dict]:
    """Immutable derived alert revisions, using ONLY information available at as_of.

    Alert time is an idealized simulation step, not actual pipeline processing latency.
    """
    if case.mode != "synthetic":
        raise ValueError("Real-world alert execution disabled")
    cutoff = (utc(as_of) if isinstance(as_of, str) else as_of)
    records: list[dict] = []
    for event in sorted(case.events, key=lambda x: (x.known_at, x.event_id)):
        if cutoff is not None and event.known_at > cutoff:
            continue
        for site in sorted(case.facilities, key=lambda x: x.facility_id):
            if site.first_observed_at > event.known_at:
                # If location evidence arrives later, do not pretend matching was possible at detection.
                availability = site.first_observed_at
            else:
                availability = event.known_at
            if site.latitude is None or site.longitude is None:
                continue
            km = distance_km(site.latitude, site.longitude, event.latitude, event.longitude)
            if km > event.screening_radius_km:
                continue
            if cutoff is not None and availability > cutoff:
                continue
            visible: list[Evidence] = []
            updates = sorted(
                (e for e in case.evidence if e.event_id == event.event_id
                 and e.facility_id == site.facility_id),
                key=lambda x: (x.known_at, x.evidence_id),
            )
            timeline = sorted({availability} | {max(availability, e.known_at) for e in updates})
            for at in timeline:
                if cutoff is not None and at > cutoff:
                    break
                # A report can be included only after both source publication and ingestion.
                visible = [e for e in updates if e.known_at <= at]
                records.append(_snapshot(case, event, site, at, visible,
                                         len([r for r in records if r["event_id"] == event.event_id
                                              and r["facility_id"] == site.facility_id]), km))
    return sorted(records, key=lambda x: (x["alert_generated_at"], x["event_id"], x["facility_id"], x["revision"]))
