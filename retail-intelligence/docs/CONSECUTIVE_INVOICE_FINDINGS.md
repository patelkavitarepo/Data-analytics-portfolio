# Investigation 004 — Consecutive invoice near-matches

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Original-workbook descriptive findings verified; no transaction cause or deduplication rule approved.

## Question

Are the two -9,600-unit lines on invoice IDs `556690` and `556691` an isolated anomaly, or part of a broader pattern in which distinct but consecutive invoice IDs contain otherwise-identical rows?

## Evidence and method

- UCI Online Retail II source workbook, **SHA-256** `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- [Successful GitHub Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42862675200), **19 synthetic-data tests passed** and original workbook was processed.
- Reproduction: `python scripts/investigate_consecutive_invoices.py` after obtaining original workbook. Result: `outputs/consecutive_invoice_investigation.json`, contained in the `retail-initial-audit` workflow artifact.
- This analysis uses **numeric-only invoice IDs**, excluding cancellation IDs with a `C` prefix.
- A **seven-field signature** consists of stock code, description, quantity, timestamp, unit price, customer ID, and country. Invoice ID is excluded **only for this comparison**.
- Multiple exact line repetitions inside the **same invoice ID** are collapsed solely for this pair-counting analysis, not removed from the original workbook.
- Only invoice ID numbers differing by **exactly 1** and the *same seven-field signature* are considered a matching consecutive pair.
- Pair counts refer to **different invoice IDs**, not verified distinct business events.

## Observed comparison

| Measure | Numeric invoice records, all | Negative quantity, non-C invoice records |
| --- | ---: | ---: |
| Raw line count | 1,047,871 | 3,457 |
| Distinct numeric invoice IDs | 45,330 | 3,393 |
| Distinct consecutive invoice ID pairs available within population | 36,182 | 1,721 |
| Consecutive pairs of matching seven-field *line signatures* | 559 | 4 |
| **Distinct consecutive invoice ID pairs with any seven-field match** | **166** | **4** |
| Seven-field matched pairs appearing on adjacent Excel rows | 5 | 2 |

**Denominators matter:** A single pair of invoice IDs may have many distinct matching line signatures, hence 559 matching lines across only 166 distinct ID pairs in the full numeric-invoice population. The 166/36,182 proportion is roughly **0.46%**. Within the negative non-C subset, 4/1,721 is roughly **0.23%**. These are descriptive proportions, **not probabilities** of data errors or a statistical significance test.

An additional comparison found **818** seven-field matching cross-invoice line pairs at *any* numeric-ID separation dataset-wide, versus **5** negative non-C matching pairs at any separation. The closest 4 of those 5 negative matches have consecutive IDs.

## All four negative non-C consecutive-invoice matches

| Invoice IDs | Stock code | Quantity each | Source description | Timestamp | Adjacent workbook rows? |
| --- | --- | ---: | --- | --- | --- |
| `556690` → `556691` | `23005` | -9,600 | `printing smudges/thrown away` | 2011-06-14 10:37 | Yes |
| `515459` → `515460` | `20852` | -1,000 | `given away` | 2010-07-12 15:46 | No |
| `515460` → `515461` | `20852` | -1,000 | `given away` | 2010-07-12 15:46 | No |
| `540678` → `540679` | `21667` | -1 | Description missing | 2011-01-10 16:21 | Yes |

The two `given away` pairs refer to a **three-invoice chain** (`515459`, `515460`, `515461`), rather than four independent examples.

### The -9,600 case

The two observations share the same source timestamp, product, negative quantity, £0 unit price, missing customer ID, UK country and description. They are different invoice IDs and occur in adjacent Excel rows (225531 and 225532 of the 2010–2011 sheet). This is a seven-field **near-match** but **not** an eight-field exact duplicate.

### Interpretive consequences

- **Observed:** The same consecutive-ID near-match pattern appears in several negative-quantity operational-looking rows, including a three-invoice chain for goods labeled `given away`.
- **Plausible, unverified:** An invoicing or batch-entry process may create separate IDs for related or identical operational adjustments.
- **Still possible:** Some entries may be accidental repeated postings; some may reflect distinct events. Both explanations fit the available attributes.
- **Not established:** That the -9,600 pair represents one disposal, two disposals, a duplicate posting, or a particular inventory loss amount.

## Decisions / safeguards

- **D009:** Preserve each source record, invoice ID, and line, including consecutive near-matches. Do **not** collapse records using the seven-field signature.
- **D010:** Treat the observed pattern as descriptive support for further study of system-generated or operational invoice sequences, not as evidence of employee misconduct or confirmed accounting errors.
- **D011:** Do **not** sum line quantities from different products into an inventory-loss monetary estimate; £0 unit prices and absence of purchase cost prevent that.
- **Next question:** Examine *full invoice composition* and whether these near-matches form consistent operational batches, then assess sales-KPI sensitivity under explicitly defined alternative filters. Without transaction log metadata, the ultimate reason for a repeated posting may remain unknowable.

This investigation changes **no data-cleaning policy, financial model, or output interpretation** established in earlier cases.
