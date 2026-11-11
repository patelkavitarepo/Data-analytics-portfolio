# Data rights and source provenance — gate OPEN for code, BLOCKED for empirical publication

Reviewed November 11, 2026. This is a source-selection record, not a legal opinion or license grant.

- Official samples: https://php.lobsterdata.com/info/DataSamples.php — provides AMZN level 1 (0.7 MB) and level 5 (2 MB) sample downloads and a paired message/snapshot README.
- Official format: https://php.lobsterdata.com/info/DataStructure.php — message file is 6 columns; book file is 4 × depth levels; event types include cross trade (6) and halt (7). The corresponding book row is the POST-event state. Dummy zero-volume levels appear when depth is missing.
- LOBSTER website use notice: https://data.lobsterdata.com/imprint.php — restricts systematic website downloading and other uses; access/download visibility is not evidence of redistribution, caching or publication rights.
- Current-provider terms page: https://php.lobsterdata.com/termsAndConditions.php — additional contractual provisions may apply. The license applicable to individual sample analysis and public aggregate screenshots/metrics has NOT been established.
- Separate alternative for future full raw event reconstruction: Nasdaq ITCH sample info at https://www.nasdaqtrader.com/Content/TechnicalSupport/FAQs/ITCH_FAQ.pdf; different format/rights require independent review.

| Action | Current status |
| --- | --- |
| Write and publish original code and synthetic unit tests | Allowed for this research workflow |
| Read the published data format and plan a local importer | Supported |
| Automated acquisition or rehosting provider CSVs | NOT authorized here |
| Analyze locally supplied samples | Do only if the user's applicable access and research-use terms permit |
| Publish actual-data aggregates or screenshots | NOT established; review separately |
| Publish raw samples or machine-readable derived observations | NOT established; do not upload |

No remote fetch, GitHub Action acquisition, provider account, credential or payment is part of this project. Local data, audit outputs and caches must remain ignored. Full-depth reconstruction is NOT supported by price-range-filtered LOBSTER message files alone. Do not confuse samples with full-sequence ITCH data.
