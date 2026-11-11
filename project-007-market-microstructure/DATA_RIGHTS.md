# Data rights and source provenance — Project 007

Reviewed November 11, 2026. This is evidence of public metadata and a research source, not legal advice or a universal permission grant.

## FI-2010 (newly verified source)

- **Official catalog:** https://etsin.fairdata.fi/dataset/73eb48d7-4dbc-4a10-a52a-da745b47a649
- **Public official metadata endpoint:** https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649
- The official record returned HTTP 200 and states **access type Open; license Creative Commons Attribution 4.0 International (CC BY 4.0)**. Secondary old metadata API independently agreed.
- **Attribution:** Ntakaris, Magris, Kanniainen, Gabbouj & Iosifidis (2018), *Benchmark Dataset for Mid-Price Forecasting of Limit Order Book Data with Machine Learning Methods*, *Journal of Forecasting*, DOI https://doi.org/10.1002/for.2543.
- **Researcher-hosted copy:** https://github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/tree/master/data. Their public research notebook explicitly directs users to the original dataset and its alternative research reproduction.
- Reproducible archive SHA256: `7a5564290a504bdc104dccaf44aa6c0b3857bf1db6b0517b9b88577c2def3e5f` (56,278,154 bytes). This research archive's **byte identity with Fairdata's originally deposited file remains unverified**.
- The project has downloaded and analyzed training CF7 and day-eight test CF7 only, on ephemeral CI runners. Reserved day-nine/day-ten ZIP members were listed but **never extracted, opened or scored**.
- Attribution, original source, host, any transformations, input hashes and limitations must accompany published derived results. No user credentials, purchases, new provider account or full raw dataset upload were needed.

## LOBSTER (separate rights gate, still unresolved)

- Official samples: https://php.lobsterdata.com/info/DataSamples.php
- Format: https://php.lobsterdata.com/info/DataStructure.php
- Website and subscription conditions: https://php.lobsterdata.com/imprint.php and https://php.lobsterdata.com/termsAndConditions.php
- Applicable research and public-output rights **have not been established** for this different provider.
- No LOBSTER provider downloads, automated acquisition or public derived reports are authorized by the FI-2010 license. Our synthetic LOBSTER-format code can still be published.

## Rules and separation

| Activity | Status |
| --- | --- |
| Publish original project code, synthetic tests and research protocol | Supported |
| Run cited FI-2010 researcher-hosted source on ephemeral CI | Completed with official dataset metadata supporting open access and CC BY 4.0; provenance distinctions disclosed |
| Publish attribution-bearing FI-2010 aggregate baseline scores | Supported by CC BY 4.0, conditional on proper attribution, disclosure of source and changes |
| Claim mirror byte identity with original deposited archive | **Not verified** |
| Commit or upload full FI-2010 files to this repository | Not done or needed; keep vendor data outside Git |
| Acquire/use LOBSTER samples and publish its output | **Not cleared separately** |
| Treat FI-2010 normalized data as raw exchange event messages or execution records | **Invalid** |

See `research/EMPIRICAL_DAY8.md` and `research/FI2010_SOURCE_REVIEW.md` for details. 
