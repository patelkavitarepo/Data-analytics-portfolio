# H001 follow-up — Inventory-adjustment hypothesis

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Original-workbook descriptive evidence gathered; cause classification remains unverified.

## Question

Do the 3,457 negative-quantity, non-C-prefixed lines appear to be sales/returns or operational movements such as damaged inventory, stock checks, and administrative corrections?

## Reproducible evidence

- **Dataset:** UCI Online Retail II, original workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Successful job:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42855486728
- **Script:** `scripts/investigate_negative_quantities.py`; output `outputs/negative_quantity_investigation.json` in the run artifact.
- This is a *descriptive audit*, not a causal study. All records remain in source form.

## Observed results

| Indicator in 3,457 non-C negative lines | Count / statistic |
| --- | ---: |
| All zero-priced, all missing customer IDs, all UK | 3,457 each |
| No description recorded | 2,689 (77.8%) |
| Description present | 768 (22.2%) |
| Distinct described rows matching at least one predefined damage/missing/check/theft keyword | 432 |
| Described rows with no match to those specific keywords | 336 |
| Damage-related keyword matches | 245 |
| Missing/loss-related keyword matches | 51 |
| Checking/stocktake-related keyword matches | 139 |
| Explicit stolen/theft/shoplifting keyword matches | 0 |
| Median absolute line quantity | 26 |
| 90th percentile absolute line quantity | 240 |
| 99th percentile absolute line quantity | 3,117.6 |
| Maximum absolute line quantity | 9,600 |
| Invoice IDs consisting of one line within the unmarked-negative subset | 3,329 |
| Invoice IDs containing multiple unmarked-negative lines | 64 |
| Unmarked-negative invoice IDs also found on positive-quantity lines | 0 |

**Important:** The keyword columns overlap and depend on literal phrasing; their counts should not be added to estimate causes. The absence of an explicit 'theft' word does *not* rule out theft. An invoice with one line *within this subset* might have additional lines in another category; the separate positive-line check found none. No inference about employee identities or motives is possible.

### Qualitative source descriptions near large negative quantities

These *observed strings* occur in some of the eight largest-magnitude non-C negative rows:

- `printing smudges/thrown away` on a -9,600 line for stock code `23005`, and another line with the same code, description, day, and quantity.
- `Printing smudges/thrown away` on a -9,058 line for stock code `23003`.
- `Zebra invcing error` on a -9,000 line for stock code `10120`.
- `Given away` on a -8,800 line for stock code `20852`.
- Other very large lines have blank or ambiguous descriptions.

**Update from Investigation 003:** The two -9,600 lines are **not exact duplicates**: their invoice numbers are `556690` and `556691`. The rows are adjacent with the same timestamp, stock, quantity, and description. Whether they describe one actual event or two remains unknown. See [exact-duplicate investigation](DUPLICATE_INVESTIGATION.md).

## Interpretation

**Strengthened:** H001's broad *operational, non-sale adjustment* explanation. Zero prices, absent customer IDs, explicit words suggesting quality defects/disposal, and the lack of positive lines sharing these invoice IDs support it more than an ordinary customer-refund interpretation.

**Not proven:** What share of 3,457 rows represents loss, giveaway, invoice correction, stock check, theft, or other reasons. The phrase `Zebra invcing error` is consistent with recording errors, not necessarily physical inventory loss. No evidence quantifies theft. Even `printing smudges/thrown away` is a recorded description, not an independently verified disposal event.

**Do not do yet:** Assign causes row by row, drop rows, publish inventory-loss totals, or estimate monetary shrinkage. The raw quantity magnitudes add units from different stock codes and do not equal currency or even commensurate merchandise.

## Decisions and next investigations

- **D004:** Keep a neutral `negative_non_c_zero_price_no_customer` observed-data cohort rather than labelling it 'theft' or definitive 'shrinkage'.
- **D005:** Preserve all original rows and their invoice/stock-code links; no modifications to revenue logic.
- **R001a:** Initial exact-duplicate audit completed. The high-magnitude pair differs by invoice ID; further near-duplicate analysis may still be valuable. See [Investigation 003](DUPLICATE_INVESTIGATION.md).
- **R001b:** Refine descriptions into provisional *lexical* groups (damage/disposal, giveaway, invoicing error, stock check, other), and quantify the percentage of blanks/unclear descriptions.
- **R001c:** Compare the sensitivity of future sales and margin definitions to the treatment of zero-priced operational lines, but only after agreeing on sales definitions.

The evidence supports further investigation of operational bookkeeping, not a claim that 3,457 products were damaged or stolen.
