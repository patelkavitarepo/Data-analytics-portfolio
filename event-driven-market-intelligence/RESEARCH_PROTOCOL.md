# Project 008 — Predeclared research protocol, v0.1

Status: predeclared 2026-11-12; **not a statistical pre-registration or blinded external test**. No market model, financial data, holdout or stock-return question is included.

## Hypotheses and predeclared questions

- **H0 / software validity:** Point-in-time rules should suppress events before ingestion, unverified impact claims, matches with unknown coordinates, and source updates not available by the cutoff.
- **Q1 / detection feasibility (not yet tested):** With a timestamped capture archive of eligible CWA and USGS feeds, what fraction of independently enumerated eligible Taiwanese earthquakes are detected in the first 5, 15, and 60 minutes of their earliest *verified public release*? Primary metric: recall at each horizon; also missing source-release-time rate. Do not use event occurrence as publication time.
- **Q2 / company matching (not yet tested):** Among facility-event pairs reviewed blindly by a human using contemporaneous location/footprint evidence, what are the precision, recall, and abstention rates of a geographic screening rule? False positives from the rule are potential-exposure mismatches, not claims about share prices. Report geographic uncertainty and rule coverage.
- **Q3 / operational claim validity (not yet tested):** Of proposed **Confirmed Disruption** labels, what fraction are supported by a contemporaneously available, directly attributable primary statement? Count absent evidence as **unknown**, not an actual no-impact label.
- **Q4 / timeliness (not yet tested):** What are empirical P50/P90/P99 source-publication-to-ingest and ingest-to-alert latencies, separating missing/unreliable publication timestamps from measured delays?

## Pilot and tests (frozen before synthetic execution)

Company: **TSMC, 2330.TW / TSM**, for documented current site inventory; pilot real sites **Fab 12A (Hsinchu)** and **Fab 18A (Tainan)**. No real coordinates are asserted. Earthquakes are the first event category. Flooding is postponed pending credible affected-area polygons and validated site geometry. No assertions about TSMC operational disruptions.

Synthetic universe is completely separate: fictional company, fictional north/south facilities, fictional event, fictional statements and fictional radius. The 30-km proximity threshold is an **arbitrary coding fixture**, not a measured felt-intensity radius, a physical earthquake impact model, or a tuned research parameter.

Predeclared pass/fail rules:
1. No alert before source publication AND ingestion AND site-location availability.
2. Only a nearby fictional site alerts; far-away site stays silent.
3. Proximity can only create **Potential Exposure**.
4. A rumor (unverified news claim) cannot create **Confirmed Disruption**.
5. A *verified synthetic company-primary* statement can confirm disruption, and an explicit later primary recovery can resolve it. A recovery without confirmed disruption cannot.
6. Silence does not equal no impact. Explicit verified company-primary **unaffected** evidence can dismiss.
7. A verified retraction of prior evidence restores the correct current assessment without rewriting the recorded earlier alert.
8. Duplicate identical event/evidence IDs do not double count; conflicting same-ID revisions fail closed.
9. Timestamp parsing requires timezone offsets and converts to UTC; points outside valid latitude/longitude fail.
10. Replaying a prior cutoff never sees future evidence; outputs are deterministic for same fixture and version.

## Point-in-time record contract

Four mandatory conceptual clocks:
1. `event.occurred_at`: observed disaster occurrence, nullable when unknown or future-looking forecast. It **does not establish public availability**.
2. `source_published_at`: original source release for a *particular revision*, when proven. If unknown in real research, mark null and do not hallucinate. Simulation requires a synthetic value.
3. `ingested_at`: the system's archived receipt time for that exact revision.
4. `alert_generated_at`: an immutable alert revision timestamp.

The synthetic engine uses `known_at = max(source_published_at, ingested_at)`; a site also requires `first_observed_at <= alert_generated_at`. One cannot reconstruct historical first-publication timestamps from a current revised USGS `updated` value alone. A real adapter will need first-seen capture, source-specific release semantics, HTTP receipt time, feed `generated`, and archived raw payload SHA-256.

Entities and relationships (all IDs required):
- Company (`company_id`, ticker), Facility (`facility_id`, company_id, coordinate-quality status, first-observed timestamp), with *unknown* dependency relationships retained as null.
- Hazard Event (`event_id`, revision, type, point coordinates, screening radius, time fields, source provenance).
- Evidence (`evidence_id`, event_id, facility_id, claim, verification status, source role, source revision, independence group, publication/ingestion timestamps, raw-link placeholder, optional `retracts`).
- Alert revision (`event_id`, facility_id, revision, status, decisive and visible evidence IDs, timestamps, distance, warnings). Revisions are append-only derived records; new replay does not overwrite prior revisions.

Production extensions **NOT implemented**: immutable raw-byte object store with sha256, as-of versioning for mutable facility geometries, cross-provider event identity reconciliation, source-identity verification/independence review, forecast validity intervals, polygons/intensity fields, provider permission registry enforcement, outage/infrastructure edges and consumer-facing audit UI.

## Evaluation controls & failure conditions

Do not choose events because TSMC stock moved. Build source eligibility rules and sampling dates before viewing outcomes. Construct positive, negative, ambiguous, delayed and corrected examples. Source overlapping event lists are not independent ground truth; compare to an adjudicated catalog with missed-event audits. For geospatial scoring use actual credible shake intensity maps or hazard footprints (when authorized), not earthquake epicenter proximity as impact evidence. Estimate confidence intervals for eventual empirical metrics; never infer achieved recall/precision from unit tests.

Known fatal gaps for a real inference claim: unverified site polygons/coordinates; unknown suppliers/utilities and output shares; first-release-time history generally absent; publication revisions, 2026-06-01 CWA earthquake schema change and feed lag; earthquakes not equal factory disruption; strong geographic false positives; incomplete official flooding surveys; primary company reporting delays; same-owner syndication errors. Missing production-verified evidence must result in **Potential Exposure** or abstention, never fabricated confirmation.

## Advancement gates

**Gate A (met for synthetic code only):** deterministic regression tests, strict no-live-data barrier, provenance fields, explicit negative controls, draft PR review.

**Gate B (not met):** written, source-specific acquisition approval, raw immutable snapshots, valid event+facility geodata and replayable first-seen times, operational source verification, predeclared evaluation sample and manual adjudication protocol. No live alerts until Gate B.

**Gate C (not met):** measured out-of-sample event completeness, geography matching errors, abstention and false-claim rates on independently reviewed samples. Only then consider financial relevance, separately predeclared.
## v0.2 predeclared acquisition validation (before first successful live USGS capture)

**New subsystem boundary:** `market_intel.usgs_capture` may retain observed USGS *hazard* records but may never produce alerts or be imported by the synthetic-only risk engine. There is no company-facility matching for real events. USGS first-publication time is treated as unknown.

**AQ1 — reproducibility:** For each accepted source snapshot, check that stored original bytes round-trip and their SHA-256 digest matches. An altered archive must fail verification. Repeated identical responses require distinct receipt IDs but share one content-addressed object. Changed feed bytes must not overwrite prior objects.

**AQ2 — malformed and provenance data:** Non-200 status, redirect, unrecognized content type, malformed JSON, surprising source URL, duplicate event IDs, invalid coordinates/time fields, count mismatch, and oversize payload must not produce a valid receipt. Poller/network actions are disabled by default and excluded from CI.

**AQ3 — first-seen observability:** Record UTC request start, response completion, and USGS feed-generation times separately. Do not call observed-at minus source-updated-at *release latency*. A USGS updated value is a revision marker, not an audited first-release timestamp; no empirical alert latency is calculated.

**AQ4 — exploratory geographic screening:** Report magnitude >=4.5, past-day, Taiwan-box events as geographical **candidates only**. This screening does not estimate facility shaking or operational damage. Do not claim geographic recall until a predeclared independently adjudicated sample and coverage eligibility criteria exist.

**Gate B remains unmet:** The one-shot adapter is a software capability, not proof that a legitimate snapshot has been acquired or an authorized continuous data operation established. Any manual test artifacts must remain outside version-controlled source folders, or in ignored `outputs/` with provenance logged.
