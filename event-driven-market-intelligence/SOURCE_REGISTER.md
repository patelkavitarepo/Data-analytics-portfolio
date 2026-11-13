# Source feasibility register — reviewed 2026-11-12

**Status:** Desk research only. No live source data downloaded, no credentials obtained, no source ingestion scheduled, and no historic point-in-time evidence reconstructed. Data licenses and service policies must be rechecked before production acquisition.

| Source | Events and footprint | Access and rights assessment | Timestamps, cadence, and historical risks | Decision |
|---|---|---|---|---|
| **USGS Earthquake GeoJSON summary** | Earthquake point, magnitude, depth; optional event products/ShakeMap can add evidence, not guaranteed site-level damage | USGS-produced data generally public domain with requested attribution; documented programmatic GeoJSON feeds | Feeds reportedly update each minute. `time` represents event time, `updated` a revision time, and feed `metadata.generated` the feed production time. **None is guaranteed to be the first public release**. Snapshot immediately on each poll, store ingestion and revision hashes. Near-real-time feed archives and historic first-seen provenance not established | **First candidate for approved live ingestion after snapshot and ops review** |
| **USGS FDSN event catalog** | Time-bounded historical earthquake queries; geographic radius/rectangle | Documented API; USGS recommends feeds for automated near-real-time displays | Retrospective catalog can include revised origins/magnitudes. It is NOT automatically a point-in-time archive. May be used for event enumeration, not time-accurate simulation without historic snapshots | Candidate for later historical coverage baseline |
| **Taiwan CWA significant felt earthquake reports** | Locally authoritative origin time, epicenter, depth, magnitude, intensity by area | Dataset E-A0015-001 and English E-A0015-002; CWA membership and authorization code required for API. Listed under Taiwan Open Government Data License 1.0; verify dataset-specific conditions. No credentials stored in repo | Event-triggered, irregular updates. First publication and revision history not demonstrated from the currently available dataset page; archive each observed version | Local corroboration candidate; **blocked until credentials/access review** |
| **Taiwan CWA weather warnings/typhoons** | County-level heavy-rain CAP warnings W-C0033-003; typhoon warnings W-C0034-001. These are *warnings*, not observed inundation at a fab | CWA membership/API credentials; listed free with platform usage rules, not a generic permission to scrape websites | Irregular event-driven updates; CAP timestamps include `effective` / `onset` / `expires`, not necessarily original publication. Historical point-in-time archive needs checking | Later weather pilot only |
| **GDACS** | Global earthquakes, tropical cyclones and floods; modeled humanitarian alert severity and event geospatial data | Public API/feeds, with attribution requested and disclaimer; review complete terms before collection | Feed reference lists popular feeds refreshed every 6 minutes; no guaranteed event delivery SLA. Model-based alerts can contain errors or later revision | Independent *screening* source; never proof of factory disruption |
| **Taiwan Water Resources Agency (historic floods)** | Historical survey coverage (some mapped flood areas) | Listed Taiwan Open Government Data License 1.0 | Irregular updates, selective investigation; explicitly excludes local sporadic/urban flooding. Not a complete ground truth, much less a live flood warning feed | Not suitable as sole flood benchmark |
| **GDELT 2.0** | News event mentions; text and geolocation may be indirect | GDELT datasets openly reusable with citation. **Linked publishers' full texts have separate rights**; assess individually | Events and GKG refreshed every ~15 minutes per documentation, but article date may not equal first access time. Duplicated syndication and language translations complicate independence | Later contextual/news layer, not phase-1 operational verification |
| **TSMC facility directory / 2025 annual report** | Explicitly named fabs and address text | Manually transcribed small set of public factual statements; no bulk scraping authorized. Site rights must be checked before automation | Current public directory is mutable, with no trustworthy original posting timestamp. `first_reviewed_on=2026-11-12`, not proof of availability at earlier as-of times. No trustworthy plant polygon, validated lat/lon, production share or exact supply links | Two *address-only* real facilities, not matched by prototype |

## Primary links / evidence register

- USGS GeoJSON format and refresh: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
- USGS detailed feed / product revisions: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson_detail.php
- USGS catalog API: https://earthquake.usgs.gov/fdsnws/event/1/
- USGS public-domain policy: https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted
- USGS revision caveat: https://www.usgs.gov/faqs/whywhen-does-usgs-update-magnitude-earthquake
- CWA E-A0015 and historical catalog: https://opendata.cwa.gov.tw/dataset/earthquake
- CWA licensed significant reports: https://data.gov.tw/en/datasets/6068
- CWA API login/authorization: https://opendata.cwa.gov.tw/devManual/description
- CWA API catalog W-C0033-003 and W-C0034-001: https://opendata.cwa.gov.tw/dist/opendata-swagger.html
- GDACS feed reference: https://data.gdacs.org/feed_reference.aspx
- GDACS terms/disclaimer: https://data.gdacs.org/About/termofuse.aspx
- Taiwan government open-data license: https://data.gov.tw/en/license
- Taiwan historic flood survey coverage limits: https://data.gov.tw/en/datasets/25770
- GDELT coverage and cadence: https://www.gdeltproject.org/data.html
- GDELT reuse terms: https://www.gdeltproject.org/about.html
- TSMC fabs: https://www.tsmc.com/english/aboutTSMC/TSMC_Fabs
- TSMC company/stock identifiers: https://www.tsmc.com/english/aboutTSMC/company_profile
- TSMC 2025 20-F, semiconductor facilities disclosures: https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm

**Data-use decisions:** No automated collection in version 0.1. The synthetic module cannot call the network and refuses real records. Human review of the exact service policy, registration conditions, rate limits, attribution, personal data and any downstream content rights is required before enabling any live adapter.
