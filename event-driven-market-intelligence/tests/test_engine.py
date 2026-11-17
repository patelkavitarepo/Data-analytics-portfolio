"""Predeclared synthetic invariants: tests verify code logic, NOT market intelligence."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from market_intel.engine import distance_km, replay
from market_intel.models import Case, load_case, utc

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "synthetic_scenario.json"


def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def evidence(eid, claim, published="2026-01-10T00:30:00Z", ingested="2026-01-10T00:31:00Z",
             source_role="company_primary", verification="verified", retracts=None):
    item = {
        "evidence_id": eid, "event_id": "SIM-EQ-001", "facility_id": "SIM-NORTH-FAB",
        "claim": claim, "source_role": source_role, "verification": verification,
        "source_id": "SIM-COMPANY-RELEASES", "source_revision": "test-r1",
        "independence_group": "sim-company", "source_url": "synthetic://tests/" + eid,
        "source_published_at": published, "ingested_at": ingested, "synthetic": True,
    }
    if retracts:
        item["retracts"] = retracts
    return item


class TimeAndGeographyTests(unittest.TestCase):
    def test_explicit_timezone_required(self):
        with self.assertRaises(ValueError):
            utc("2026-01-10T00:03:00")

    def test_offset_converted_to_utc(self):
        self.assertEqual(utc("2026-01-10T08:00:00+08:00"), utc("2026-01-10T00:00:00Z"))

    def test_haversine_zero_and_long_distance(self):
        self.assertAlmostEqual(distance_km(24.75, 121.03, 24.75, 121.03), 0)
        self.assertGreater(distance_km(24.75, 121.03, 23.10, 120.27), 100)

    def test_bad_coordinates_rejected(self):
        data = raw()
        data["facilities"][0]["latitude"] = 101
        with self.assertRaises(ValueError):
            Case.from_dict(data)


class EventScreeningTests(unittest.TestCase):
    def test_initial_alert_is_exposure_only(self):
        history = replay(load_case(FIXTURE), "2026-01-10T00:04:00Z")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "Potential Exposure")
        self.assertEqual(history[0]["publication_to_alert_seconds"], 60)
        self.assertEqual(history[0]["ingestion_to_alert_seconds"], 0)

    def test_before_ingestion_no_alert_even_if_published(self):
        self.assertEqual(replay(load_case(FIXTURE), "2026-01-10T00:03:59Z"), [])

    def test_far_facility_is_not_alerted(self):
        records = replay(load_case(FIXTURE))
        self.assertEqual({r["facility_id"] for r in records}, {"SIM-NORTH-FAB"})

    def test_later_verified_disruption_never_leaks_backward(self):
        history = replay(load_case(FIXTURE), "2026-01-10T00:21:00Z")
        self.assertEqual([x["status"] for x in history], ["Potential Exposure", "Potential Exposure"])

    def test_unverified_rumor_cannot_confirm_disruption(self):
        history = replay(load_case(FIXTURE), "2026-01-10T00:07:00Z")
        self.assertEqual(history[-1]["status"], "Potential Exposure")
        self.assertIn("SIM-RUMOR-001", history[-1]["visible_evidence_ids"])
        self.assertNotIn("SIM-RUMOR-001", history[-1]["decisive_evidence_ids"])

    def test_verified_disruption_and_recovery(self):
        history = replay(load_case(FIXTURE))
        self.assertEqual([x["status"] for x in history],
                         ["Potential Exposure", "Potential Exposure", "Confirmed Disruption", "Resolved"])
        self.assertEqual([x["revision"] for x in history], [0, 1, 2, 3])

    def test_unknown_site_coordinates_not_assumed(self):
        # An address without validated coordinates cannot be used in radial matching.
        data = raw()
        data["facilities"][0]["latitude"] = None
        data["facilities"][0]["longitude"] = None
        data["facilities"][0]["location_quality"] = "address_only"
        with self.assertRaises(ValueError):
            Case.from_dict(data)  # synthetic-only data contracts reject mixed simulation modes

    def test_site_observed_after_event_not_available_at_detection(self):
        data = raw()
        data["facilities"][0]["first_observed_at"] = "2026-01-10T00:15:00Z"
        records = replay(Case.from_dict(data), "2026-01-10T00:14:00Z")
        self.assertEqual(records, [])
        records = replay(Case.from_dict(data), "2026-01-10T00:15:00Z")
        self.assertEqual(records[0]["alert_generated_at"], "2026-01-10T00:15:00Z")

    def test_idempotent_event_and_evidence_duplicates(self):
        data = raw()
        data["events"].append(copy.deepcopy(data["events"][0]))
        data["evidence"].append(copy.deepcopy(data["evidence"][0]))
        self.assertEqual(replay(Case.from_dict(data)), replay(load_case(FIXTURE)))

    def test_conflicting_event_revision_id_rejected(self):
        data = raw()
        conflicting = copy.deepcopy(data["events"][0])
        conflicting["latitude"] += 0.1
        data["events"].append(conflicting)
        with self.assertRaises(ValueError):
            Case.from_dict(data)

    def test_explicit_company_no_impact_dismisses(self):
        data = raw()
        data["evidence"] = [evidence("SIM-NO-IMPACT", "facility_unaffected")]
        last = replay(Case.from_dict(data))[-1]
        self.assertEqual(last["status"], "Dismissed")

    def test_no_impact_inference_from_silence_is_forbidden(self):
        data = raw()
        data["evidence"] = []
        self.assertEqual(replay(Case.from_dict(data))[-1]["status"], "Potential Exposure")

    def test_recovery_without_verified_disruption_not_resolved(self):
        data = raw()
        data["evidence"] = [evidence("SIM-RECOVERY-ALONE", "facility_recovered")]
        self.assertEqual(replay(Case.from_dict(data))[-1]["status"], "Potential Exposure")

    def test_explicit_retraction_restores_exposure_without_deleting_history(self):
        data = raw()
        data["evidence"] = [
            evidence("SIM-RETRACTED-DISRUPTION", "facility_disrupted"),
            evidence("SIM-RETRACTION", "retraction", "2026-01-10T00:35:00Z",
                     "2026-01-10T00:36:00Z", retracts="SIM-RETRACTED-DISRUPTION"),
        ]
        records = replay(Case.from_dict(data))
        self.assertEqual([r["status"] for r in records],
                         ["Potential Exposure", "Confirmed Disruption", "Potential Exposure"])
        self.assertIn("SIM-RETRACTED-DISRUPTION", records[-1]["retracted_evidence_ids"])
        self.assertEqual(records[1]["status"], "Confirmed Disruption")

    def test_unverified_retraction_cannot_erase_confirmed_evidence(self):
        data = raw()
        data["evidence"] = [
            evidence("SIM-VALID-DISRUPTION", "facility_disrupted"),
            evidence("SIM-UNVERIFIED-RETRACTION", "retraction", "2026-01-10T00:35:00Z",
                     "2026-01-10T00:36:00Z", verification="unverified", retracts="SIM-VALID-DISRUPTION"),
        ]
        self.assertEqual(replay(Case.from_dict(data))[-1]["status"], "Confirmed Disruption")

    def test_deterministic_replay(self):
        self.assertEqual(replay(load_case(FIXTURE)), replay(load_case(FIXTURE)))

    def test_real_records_rejected_by_synthetic_runner(self):
        data = raw()
        data["events"][0]["synthetic"] = False
        with self.assertRaises(ValueError):
            Case.from_dict(data)


if __name__ == "__main__":
    unittest.main()
