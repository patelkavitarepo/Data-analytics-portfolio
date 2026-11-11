# Investigation 016 — Could repeated £0 + paid SKU patterns indicate a timed promotion?

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** New investigation script and six synthetic-data tests committed; **original-workbook findings pending CI**. Case 015's same-invoice results are also pending original-source verification as of this commit.

## User hypothesis

If a stock code appears with a positively priced line and a £0 line **on the same invoice**, and the **same SKU pairing repeats on distinct invoices over a limited time**, the retailer *could* have been running a BOGO or similar promotion. If such patterns are rare, inconsistent, or isolated, a promotional explanation is less supported. **Repetition is necessary contextual evidence, not sufficient proof of a campaign.**

## Code and method

- Script: `scripts/investigate_temporal_zero_paid_sku.py`, test file: `tests/test_temporal_zero_paid_sku.py`.
- Read-only against Case 008's cross-sheet-reconciled candidate view, with original-sheet provenance retained.
- Identify non-C, positive-quantity lines with **zero unit price** and with **positive unit price**.
- Group by exact invoice ID **and** stock code. A qualifying group contains at least one zero-price and one positive-price line for that same SKU.
- Identify invoice-SKU groups with exactly one positive-quantity *unit* at £0 and exactly one positively priced unit — the cleanest observed 1+1 shape. Do not equate this with a fulfilled 'buy one get one' deal.
- Count **distinct invoice IDs**, **distinct SKUs**, **invoice-SKU groups**, and **zero-price lines** independently. One invoice may have more than one SKU, and a SKU may have multiple paid or zero lines.
- For each qualifying stock code, count pairs of **distinct paired invoices** within **7-day** and **30-day** windows, and calculate the largest local number of qualifying invoice-SKU groups in each window.
- Report the total number of invoice-SKU groups for that code containing a paid line over the **full observation period** as context, not a statistically matched comparison.
- Output at most 15 SKU-level recurrence summaries; **no customer IDs** or row-level pairing tables are exported. Final JSON saved to ignored `outputs/temporal_zero_paid_sku.json`.
- Cross-check the source-derived total number of zero-priced lines with paid same-SKU neighbors, and the unique associated invoice-ID count, against the Case 015 summary when available. A mismatch fails the source analysis.

## How to evaluate

**Pattern supporting further BOGO inquiry:** The *same SKU* shows the one-paid-unit + one-zero-unit shape on **multiple distinct invoices within a short period**, with other invoice/SKU examples spanning that period and a change in prevalence outside it.

**Alternative hypotheses:** Differential pricing for quantities, inventory adjustments, correction/reposting conventions, data-entry error, a different promotion mechanic, or unrelated recording contexts.

**Not established even with strong clustering:** A public promotion, exact campaign dates, customer redemption behavior, physical shipment, payment settlement, intent of personnel, or number/value of free goods.

## Source integrity and next steps

1. Verify **full-source** CI and report counts with direct evidence, not synthetic-test-only inference.
2. Compare same-SKU paired invoice frequency inside versus outside candidate windows; use paid-only invoice-SKU records as a context denominator. A rigorous time-specific baseline is a possible follow-up beyond this exploratory summary.
3. Review the original invoice quantity/price patterns on top recurring SKUs before interpreting the result as a BOGO hypothesis.
4. Keep the source workbook, Case 008 candidate view, S0/S1/S2 scenario definitions, and refund/financial assumptions unchanged.

**Decision R016:** Preserve the user's timed-BOGO hypothesis as a testable explanation alongside operational correction, without selecting either before evidence. No business categorization or KPI decision is authorized by temporal coincidence alone.
