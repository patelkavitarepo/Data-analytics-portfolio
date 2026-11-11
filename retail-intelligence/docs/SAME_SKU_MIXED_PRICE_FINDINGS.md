# Investigation 015 — Same-SKU £0 and positive-priced lines on the same invoice

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** **Verified against the original UCI workbook**. No promotional, correction, refund, duplicate, or revenue classification approved.

## Question

When a non-C invoice contains a positive-quantity, £0 line and a positive-quantity, positively priced line of the exact same stock code, do the recorded quantities and customer information support a conventional one-paid, one-free pattern, a rebooking/correction mechanism, or neither?

## Reproducibility and source integrity

- **Source:** UCI Online Retail II original two-sheet workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Verified GitHub Actions:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42935952251 — **successful**, **83 synthetic tests passed**, all full-source analysis steps completed.
- **Code:** `scripts/investigate_same_sku_price_pairs.py`; tests `tests/test_same_sku_price_pairs.py`.
- **Machine-readable result:** `outputs/same_sku_mixed_prices.json` in the `retail-initial-audit` GitHub Actions artifact. This exports bounded case examples and aggregates only, **not customer ID values, raw invoice tables or original workbook**.
- **Provenance:** 1,067,371 original source lines reconciled into the Case 008 1,044,848-line reversible candidate view; 22,523 cross-sheet source-copy links, unchanged.
- **Independent agreement:** Case 015 counts reconcile to Case 014 (`agrees_with_case_014_counts = true`).
- **No changes:** All source records, overlap handling, Case 009 S0/S1/S2 scenario definitions and financial/semantic rules remain untouched.

## Verified results

| Measure | Original-source result |
| --- | ---: |
| Non-C positive-quantity £0 candidate lines, all SKUs | **2,631** |
| Non-C positive-quantity, positive-price candidate lines | **1,019,654** |
| Invoice IDs containing both kinds of positive-quantity lines | **125** |
| £0 lines with a positive-priced **same-stock-code** line on the same invoice | **43** |
| Distinct invoice IDs containing such same-SKU pairs | **33** |
| Distinct positive-priced lines participating | **43** |
| Same-SKU £0-positive **pair comparisons** (not confirmed business events) | **43** |
| Comparisons with equal recorded quantities | **10** |
| Unique £0 lines with at least one equal-quantity positive partner | **10** |
| Comparisons with matching recorded minute | **43** |
| Comparisons with known conflicting countries | **0** |
| Invoice+SKU groups with multiple distinct positive partner prices | **0** |

### Customer-ID relation among the 43 comparisons

| Customer relationship | Pair comparisons |
| --- | ---: |
| Both IDs known and matching | **10** |
| Both IDs known and different | 0 |
| One ID missing | 0 |
| Both IDs missing | **33** |

**Missing IDs are not confirmation of a matching customer**, and same invoice ID or same timestamp is not independent evidence of the same physical event.

### Selected source examples (not confirmed gifts or corrections)

| Invoice | Stock code | £0 quantity | Paid quantity | Recorded paid unit price | IDs |
| --- | --- | ---: | ---: | ---: | --- |
| `492079` | `85042` | 8 | 8 | £4.95 | Known same |
| `492760` | `21143` | 12 | 12 | £1.95 | Known same |
| `500870` | `84033` | 99 | 1 | £85.10 | Both missing |
| `502469` | `84016` | 899 | 1 | £93.61 | Both missing |
| `506393` | `84016` | 299 | 1 | £25.53 | Both missing |
| `506571` | `84016` | 3,600 | 1 | £408.40 | Both missing |
| `507637` | `84016` | 10,200 | 1 | £1,157.15 | Both missing |
| `508649` | `84016` | 598 | 2 | £25.53 | Both missing |

All examples share a recorded invoice minute. The exact **stock code 84016** appears repeatedly in the bounded examples with much larger zero quantities than paid quantities; the source does **not** specify whether the paid line represents charges, an operational valuation, units delivered, or a different convention.

## Interpretation

1. **Observed:** Some same-SKU £0/paid pairs have equal quantities (10), while at least several large-magnitude examples have very unequal quantities (e.g. 10,200 versus 1). Equal quantities alone do not establish a BOGO, because an 8/8 or 12/12 pattern differs from a literal one-unit-plus-one-unit pair and may represent something else.
2. **Observed:** The 33 pair comparisons with both IDs missing cannot be attributed to identifiable customers. This limits any claim about broad customer uptake of a promotion.
3. **Observed:** Every pair shares a recorded minute; this may reflect invoice-level timestamps rather than meaningful independent sequencing. Timing alone cannot prove a correction.
4. **Not established:** BOGO promotions, discount schemes, corrections, inventory valuation, shipment/settlement, duplicates, error, theft, customer count, or financial netting.

## Decisions and next investigation

- **D048:** Do not label same-SKU £0-plus-paid observations as promotions, BOGO, returns, free goods, operational corrections or duplicate orders.
- **D049:** Preserve distinct source-line and invoice-ID counts; never add potential pair comparisons as independent physical events or implied free-unit value.
- **D050:** Preserve missing customer-ID states, exact original quantities/prices, the Case 008 cross-sheet provenance map and every KPI scenario unchanged.
- **R015a:** Investigate temporal recurrence **of the same SKU across different invoice IDs** and whether exact *one zero-unit plus one paid-unit* shapes cluster in the same 7- and 30-day periods. Case 016 separately tests this without assuming BOGO.
- **R015b:** Investigate whether repeated high-quantity zero-price examples for code 84016 share additional distinctive conventions, before claiming a specific billing mechanism.
- **R015c:** Use an explicit denominator and examine distinct invoice counts and date windows; raw frequency alone cannot identify promotional periods.

[Case 016 experimental design](TEMPORAL_BOGO_HYPOTHESIS.md) is the next step. Its source findings must not be invented until CI completes.
