# Project 008 — Event-Driven Market Intelligence (research foundation + USGS capture)

> **NO REAL-WORLD COMPANY RISK ALERTS, TRADING SIGNALS, OR DEPLOYED MONITOR.** Synthetic risk assessment remains isolated; optional USGS capture stores earthquake observations only.

**Question:** Can time-stamped event reports be connected to verified company exposures and updated as evidence arrives, without inventing impact or accidentally using future information?

Version 0.2 adds a **separate opt-in, one-shot USGS capture adapter** to the narrow, auditable offline synthetic case. The alert replay makes no network requests and refuses real-world inputs. The capture adapter cannot produce company alerts and is never executed by CI. No brokerage data or uncontrolled scraping. No other portfolio project is edited.

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
- `tests/test_engine.py` — negative/positive synthetic replay tests.
- `market_intel/usgs_capture.py` — independent single-request USGS snapshot adapter; **no company alert logic**.
- `tests/test_usgs_capture.py` — offline USGS-shaped synthetic feed tests, archive and corruption rejection.

## Not built, intentionally

No automatic data collection, scheduled polling, production source monitoring, real-time notifications, verified facility geometry, seismic shaking maps, flood footprints, suppliers, source authentication, incident adjudication, financial labels, model, dashboard, backtest, or deployment. A **manual USGS one-shot download interface** is built but **no real snapshot has been captured or validated here**.

**Next checkpoint:** perform a single authorized source capture in an approved network-enabled environment, inspect the stored receipt, test repeated revisions, and independently verify defensible facility-site geometry before attempting real company/event matching. Human-adjudicated evaluation remains separate from synthetic tests.

## Checkpoint 2 — one-shot USGS earthquake snapshot prototype (v0.2)

The USGS real-time **M4.5+ past-day** GeoJSON feed is the first candidate: a documented developer-facing interface updated approximately once per minute. We preserve the **entire worldwide source response** first; a broad Taiwan-epicenter bounding box is applied **only afterward**, in memory. The box is neither an earthquake shaking footprint nor an impact prediction. The M4.5 minimum and 24-hour rolling horizon omit smaller and older events; this is **not a complete Taiwan earthquake detection system**.

**Offline unit tests (safe, no network):**

```bash
python -m unittest discover -s tests -v
```

**Optional, explicitly authorized manual one-shot capture (requires network access):**

```bash
python -m market_intel.usgs_capture --live-usgs --output outputs/usgs-observations
```

Without **both** flags, the command fails closed. No unattended polling, scheduled requests, credentials, retries, dashboard, trading, or automated alerting are included. `outputs/` is Git-ignored. A local USGS request could not be completed in the restricted working environment, so **no genuine source response is represented as captured evidence in this branch**.

A successful capture produces:

- `objects/<sha256-prefix>/<sha256>.json`: exact raw feed bytes, created once, verified on repeat.
- `receipts/<capture_id>.json`: a unique logical append-only receipt for every retrieval, including request/receipt UTC times, source feed-generated time, response headers, response size, payload SHA-256, USGS credit, and **null** original-publication time.
- A Taiwan-screen summary containing only geographic candidate earthquakes with `alert_permitted=false`. Real company facilities are **not matched**.

The raw-byte hash guards accidental corruption, but **a local filesystem is not cryptographically tamper-proof**. Receipt metadata is unsigned. Strong adversarial immutability requires a future trusted append-only store. HTTP completion time is a conservative observed-at time, not proof of first publication. `properties.updated` and `metadata.generated` do not establish initial availability.

The API design is vetted against [USGS GeoJSON documentation](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php), [USGS catalog API advice](https://earthquake.usgs.gov/fdsnws/event/1/), and [USGS public-domain attribution guidance](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted). USGS-produced data are generally public domain with requested attribution; the adapter limits itself to the documented feed, bounded HTTP size, timeout, no redirects and no automatic retries.

**Validation distinction:** Synthetic capture tests show archive/parser correctness on controlled inputs. They do *not* prove real USGS availability, geographic coverage, detection recall, latency, or any TSMC exposure.
