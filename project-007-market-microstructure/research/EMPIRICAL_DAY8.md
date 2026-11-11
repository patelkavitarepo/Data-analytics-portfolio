# Project 007 — D008: first historical FI-2010 day-eight baseline

**Status:** Empirical *baseline-only* observation; held-out days 9–10 not read or scored. The code and computation are AI-assisted; this interpretation is a preliminary assistant-generated observation, not attributed to the human lead. **No market-making or profitable trading claim.**

## Dataset, permission, and reproducibility

Original publication: Ntakaris, Magris, Kanniainen, Gabbouj & Iosifidis (2018), *Benchmark Dataset for Mid-Price Forecasting of Limit Order Book Data with Machine Learning Methods*, *Journal of Forecasting*, DOI [10.1002/for.2543](https://doi.org/10.1002/for.2543).

Publisher's [Fairdata catalog record](https://etsin.fairdata.fi/dataset/73eb48d7-4dbc-4a10-a52a-da745b47a649) and [official Metax API](https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649) explicitly report **Open** access and **CC BY 4.0** (checked November 11, 2026). Attribution and identification of transformations remain required.

Accessible source: [the DeepLOB research authors' GitHub archive](https://github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/tree/master/data), also documented in their accompanying notebook. The dataset is attributed to the original FI-2010 authors above. **Binary identity with the original Fairdata distribution has not been independently established**; retain this provenance distinction. No third-party data are included in this repository.

- Source archive bytes: **56,278,154**, SHA256 `7a5564290a504bdc104dccaf44aa6c0b3857bf1db6b0517b9b88577c2def3e5f`
- Source files: `Train_Dst_NoAuction_DecPre_CF_7.txt`, SHA256 `11af4bbcf26f08a43a436c43619bdf772f552870d54a3b06de7b5344957279fc`; `Test_Dst_NoAuction_DecPre_CF_7.txt`, SHA256 `1acd92e13df8f499aa9475729e1d54455db1ab37894616d0c582cdd012351273`.
- Train 607,324,298 bytes, day-eight test 132,259,850 bytes. The archive also contains `Test_..._CF_8.txt` and `Test_..._CF_9.txt` (days 9/10) but those members were **not extracted, opened, or evaluated**.
- Source audit: all **149 rows** per matrix, consistent column width, finite 144 feature rows and valid {1,2,3} publisher labels for each of five predefined horizons.
- Pinned retrieval/extraction and run: `research/run_fi2010_once.py`. Public [GitHub CI source probe](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43092037095) and [day-eight actual-data run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43092339989). Dataset held only in ephemeral runner temporary storage, removed after execution; no raw data uploaded or committed.

## Predeclared basic baseline: horizon 5 sampled observations

Selected publisher target row corresponding to **five sampled observations** ahead (NOT elapsed seconds or five raw exchange messages). Train constant predictor on the most prevalent **days 1–7** publisher label (tie policy prefixed stationary 2, then 1, then 3). Predict that same class for all day-eight observations, without using any day-eight information to select the class. Evaluate accuracy and macro-averaged F1 of a three-class constant predictor.

| Population | Class 1 (up) | Class 2 (stationary) | Class 3 (down) | Total |
| --- | ---: | ---: | ---: | ---: |
| Training, days 1–7 | 87,605 (34.39%) | 80,674 (31.67%) | 86,471 (33.94%) | **254,750** |
| Evaluation, day 8 | 14,534 (26.20%) | 28,429 (51.24%) | 12,515 (22.56%) | **55,478** |

**Training decision:** always predict publisher class **1**.  
**Day-eight accuracy:** 14,534 / 55,478 = **0.26197772** (26.20%).  
**Day-eight macro-F1:** (2 × 14,534 / (55,478 + 14,534)) / 3 = **0.13839532**.

Independent numerical recomputation from the source class-count receipts agrees with the program's displayed accuracy and F1. This arithmetic cross-check is **not** a second independent parsing of the raw data.

## Preliminary finding and alternative interpretations

The train/test **publisher-label composition** changed: stationary increased from 31.67% to 51.24% (+19.57 percentage points), while up and down became less prevalent. The training-majority classifier therefore lost to the hindsight day-eight majority-class rate of 51.24% (which is **not** a legitimate predeclared baseline because it uses test labels). This is evidence of a changed **benchmark label distribution**, not necessarily a change in market microstructure. Possible explanations—including real conditions, stock mixture, label conventions/thresholds or preprocessing—have NOT been discriminated.

Do **not** infer statistical independence from 55,478 sampled observations: overlapping forward labels and clustered order-book data violate IID assumptions. No p-value, causality or confidence interval is claimed. No fitted feature-based model was scored; no model-family selection occurred.

## Critical open checks

1. Confirm whether precomputed publisher labels in the last observations of day 7 incorporate outcomes from day 8; trim/purge affected origins if needed before any model fitting/evaluation claim.
2. Confirm original Fairdata binary hashes, archive/file equivalence and sample-to-stock mapping where the catalog permits.
3. Conduct a separate *training-only* class-frequency stability analysis by day or by stock where original data allow. Do not use day-eight labels to choose features/hyperparameters.
4. Human lead interprets this descriptive result before any predictive model implementation is promoted.
5. Keep days nine and ten reserved. Current results cannot establish present-day execution costs, queue priority or live market-making profits.

## Research separation

This benchmark is separate from the original LOBSTER event/snapshot audit. It provides publisher-normalized features and labels, NOT raw order messages, original timestamps, spread dollars, or executable fills. Treating it as an order-book reconstruction source would be invalid.
