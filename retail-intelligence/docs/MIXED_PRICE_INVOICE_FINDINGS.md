# Investigation 014 — Zero-priced lines on mixed-price invoices

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Method and synthetic tests implemented; original-workbook Case 014 results **pending successful GitHub Actions run**. This document must not be interpreted as a verified source finding beyond the Case 013 baseline.

## Question

Of the zero-priced positive-quantity non-C invoice lines, do those appearing beside positively priced products have different descriptions, customer-ID coverage or stock-code relationships from zero-priced lines on other invoices?

The contextual hypotheses include promotions, bundled items, operational adjustments, inventory records and data entry conventions. **None is established by proximity to a paid-looking line.**

## Independently verified baseline from Case 013

The preceding, already source-verified Case 013 recorded:

- **2,631** positive-quantity, zero-price, non-C lines on **1,986** invoice IDs.
- **125** invoice IDs include both positive-quantity zero-price and positive-quantity positive-price lines; **709** zero-priced lines are on these mixed invoices.
- **1,861** invoice IDs contain only positive-quantity zero-price lines. This is a different context, not a proven cause.
- **2,561** of all zero-priced lines have missing customer IDs; **1,642** lack a description.
- Case 013 already ruled out the remaining zero-price-with-other-types-but-no-positive-price invoice cohort in the original source, but Case 014 explicitly tests for it.

See [Case 013 source report](PRICE_PARADOX_FINDINGS.md). All Case 014 finer-grained figures **remain unverified** until its original-workbook report is produced.

## New reproducible method

- Script: `scripts/investigate_mixed_price_invoices.py`.
- Tests: `tests/test_mixed_price_invoices.py` (five synthetic checks passed in an isolated local test harness; repo-wide original-source workflow still pending).
- Run: `python scripts/investigate_mixed_price_invoices.py` after `scripts/investigate_price_paradox.py`.
- Local output: `outputs/mixed_price_invoices.json`; published through GitHub Actions as JSON summary only. No workbook, source-level rows or customer identifiers are uploaded.
- Uses Case 008's cross-sheet reversible candidate view with original provenance. No change to raw or candidate rows or S0/S1/S2 financial scenarios.
- Restricts invoice comparison to positive-quantity non-C zero-price vs positive-quantity non-C positive-price lines. Does not assign a business meaning to cancellations or other signs.
- Separates zero-priced lines **on mixed invoices** from **all other** zero-priced lines.
- Describes known/missing customer-ID counts, missing descriptions, top stock codes/descriptions, and keyword hits for promotion-like versus operations-like words. Keyword probes can overlap; they are **not classifications**.
- Tests whether an exact stock code is also positively priced **on the same invoice**. Even a positive finding does not establish that an item was a gift, promotion or bundle.
- Tests invoice group reconciliation, C-prefix exclusion, no-zero cases, missing-ID failures, and exact cross-sheet copy handling.
- When the Case 013 result file is available, the new original-workbook run asserts agreement on four previously verified Case 013 counts.

## Safeguards and decisions

**D044 (pending source check):** Continue to separate observed invoice structure from speculative causes. Do not call any zero-priced line a promotion, free sample, inventory discovery, or financial loss on this evidence alone.

**D045 (pending source check):** Preserve every raw record and full source provenance. Keep zero-priced lines outside positive-priced gross amount scenarios unless an explicit later business/KPI rule is adopted.

## Next steps

1. Confirm all repository tests and original-workbook Case 014 output pass on GitHub Actions.
2. Examine whether the mixed-invoice cohort has informative description and stock-code differences from the comparison cohort; report actual source counts only after verification.
3. Examine the broader `A`-invoice / `B`-stock-code pattern separately, as proposed by Case 013.
4. Draft a **provisional KPI semantic dictionary** of merchandise-like, fees, manual, cancellations, zero-price and bad-debt-labelled entries, without accepting it as finalized accounting revenue.

**Limits:** There are no staff IDs, settlements, refund references, promotion rules or verified ledger classifications in the source. Invoice juxtaposition alone cannot establish business intent or wrongdoing.
