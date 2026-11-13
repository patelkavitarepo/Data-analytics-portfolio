# Project 008 — Event-Driven Market Intelligence (research foundation)

> **SYNTHETIC ONLY — NOT A REAL-WORLD RISK ALERT, TRADING SIGNAL, OR DEPLOYED MONITOR.**

**Question:** Can time-stamped event reports be connected to verified company exposures and updated as evidence arrives, without inventing impact or accidentally using future information?

Version 0.1 is a narrow, auditable **offline code experiment**, not a validated event monitor. It makes no network requests, uses no brokerage data, and does not scrape third-party sites. No other portfolio project is edited.

## Scope

- Real information: manually researched **TSMC Fab 12A** and **Fab 18A** addresses in `data/verified_facilities.json` from official TSMC directory. Coordinates, polygons, suppliers, utilities and historical first-publication times explicitly remain `null` / unknown. These records **never enter the demo matcher**.
- Simulation: `data/synthetic_scenario.json` contains a completely fictional semiconductor company, fictional fabs, fabricated coordinates and fake event/press evidence. No simulated report corresponds to an actual company event.
- Simulated event radius: arbitrary **30 km screening rule** for software tests, **not** an earthquake damage radius or site-level shaking estimate.

## How to run

From this folder with Python 3.11–3.13, using only the standard library:

```bash
python -m unittest discover -s tests -v
python -m market_intel.demo
python -m market_intel.demo --as-of 2026-01-10T00:07:00Z
```

The demo prints a JSON collection of **immutable derived alert revisions** and SHA-256 of the serialized response; no output is modified in place. The final hash is deterministic for identical code and fixture. The code has **zero third-party dependencies**; `.python-version` suggests Python 3.11 and `pyproject.toml` specifies supported versions.

## Expected synthetic path

| Simulated UTC | Newly available information | Allowed status |
|---|---|---|
| 00:04 | Simulated hazard published 00:03, ingested 00:04; fictional site within 30-km filter | **Potential Exposure** |
| 00:07 | Fictional unverified news rumor | **Potential Exposure** (rumor visible, not decisive) |
| 00:22 | Fictional verified primary company statement | **Confirmed Disruption** |
| 01:36 | Fictional verified primary recovery statement | **Resolved** |

The fictional south facility is outside the radius and produces no alert. This is not a measured detection SLA: `alert_generated_at` equals a simulation transition time, and zero ingestion-to-alert latency is **assumed** rather than observed. Source-to-alert synthetic latency for first alert is 60 seconds.

## Integrity checks

- As-of cutoff uses the later of publication and ingestion, with explicit timezone-aware UTC conversion. Historic evidence can arrive late; later statements do not bleed into earlier snapshots.
- Distance is computed with a great-circle formula, while operational impact is **not** inferred from proximity or arbitrary event severity.
- Duplicate identical primary IDs are idempotent; contradictory same-ID reports raise an error. Cross-provider event reconciliation is not yet implemented.
- Only a **pre-labeled synthetic verified company-primary** claim can advance facility status. Verification here is a test fixture assumption, **not** authentication of an actual press release or its content.
- Every new piece of evidence, including an unverified rumor, generates an append-only alert revision; a later retraction can change current assessment without deleting its predecessors.
- No evidence of impact is **unknown**, not no impact. No firm-size, revenue, supply-chain or stock-price inference is attempted.

## Files

- `SOURCE_REGISTER.md` — authoritative source review, access/permissions, timing/coverage restrictions and URLs.
- `RESEARCH_PROTOCOL.md` — predeclared research questions, point-in-time schema, validation gates, known failures.
- `data/verified_facilities.json` — verified street-address facts, deliberately no numeric geocodes.
- `data/synthetic_scenario.json` — transparent fictional case.
- `market_intel/models.py` — type-checked record contracts, source identity and time validation.
- `market_intel/engine.py` — deterministic event-to-site screening and evidence-state replay.
- `market_intel/demo.py` — offline repeatable output.
- `tests/test_engine.py` — negative/positive regression tests.

## Not built, intentionally

No CWA/USGS download, HTTP poller, real-time notifications, verified facility geometry, seismic shaking maps, flood footprints, suppliers, source authentication, incident adjudication, financial labels, model, dashboard, backtest, deployment, or production data-rights approval.

**Next checkpoint:** establish an explicitly permitted USGS snapshot adapter *in a new draft PR/review step*, capture raw feed versions and their first-seen times, and verify defensible facility-site geometry before trying real company/event matching. Keep any human-adjudicated evaluation separate from synthetic developer tests.
