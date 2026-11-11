# Investigation 015 — Same-SKU mixed-price invoice patterns

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Diagnostic script and six synthetic guardrail tests prepared. **Original-source Case 015 results and GitHub Actions verification are pending.**

## Question

Of the 43 positive-quantity, zero-price lines sharing the same stock code with at least one positively priced line on the **same invoice ID**, what can recorded quantities, prices, timestamps, and other context tell us? Does an equal quantity, same-minute timestamp or another matching field establish that two lines refer to the same physical item or business event? **No—those are patterns only.**

## Verified starting point (Case 014)

The previous [source-verified Case 014 investigation](MIXED_PRICE_INVOICE_FINDINGS.md) established that **43** zero-priced lines across **33** invoice IDs share their stock code with a paid line on the same invoice. This is a narrow subset of the **709** zero-priced lines on **125** mixed-price invoices. The source is UCI Online Retail II, workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.

Do **not** interpret the 43/33 baseline as confirmed promotional bundles, billing corrections, matched transactions, duplicate records, or losses.

## New method (pending full-source run)

- Script: `scripts/investigate_same_sku_price_pairs.py`; synthetic tests: `tests/test_same_sku_price_pairs.py`.
- Run from `retail-intelligence/`: `python scripts/investigate_same_sku_price_pairs.py` after the Case 014 script, with the original UCI workbook available locally.
- Reports only aggregate counts and at most ten bounded, descriptive invoice/SKU examples in `outputs/same_sku_mixed_prices.json` (ignored by Git; GitHub Actions uploads the JSON summary artifact).
- Uses Case 008's unchanged **reversible candidate view** and accounts for all original source records in provenance.
- Matches only **non-C invoice, positive-quantity, exactly zero-price lines** with **non-C invoice, positive-quantity, strictly positive-price lines** sharing a non-missing exact stock code and invoice ID.
- Separates the number of **unique zero lines**, **unique paid lines**, **unique invoice IDs** and **many-to-many pair comparisons**.
- Counts same-quantity comparisons, within-minute recorded timestamp equality and whether customer information is known-same, known-different, one-missing or both-missing. Missing values never imply identity.
- Exposes known cross-country disagreement rather than hiding it.
- Records how many invoice-SKU groups have multiple distinct positive prices.
- Checks the exact source-derived zero line and invoice counts against the Case 014 JSON; the original workbook analysis should fail if those disagree.
- Tests null stock codes, negative/C-coded lines, no-match cohorts, many-to-many pairs, customer-ID conflicts and cross-sheet exact source-copy suppression.

## Unresolved interpretation and safeguards

- Same SKU on the same invoice does **not** establish the same unit was charged and gifted, that a posting was duplicated, or that an item was shipped.
- An invoice's minute-level timestamp often applies to all of its lines; same timestamp has limited power to establish independent actions.
- A known different customer or country is explicitly recorded as a conflict, not silently treated as one event.
- Source rows, candidate row rules, financial S0/S1/S2 scenarios, and existing labels remain untouched.
- No individual customer ID or unbounded row-level pairing table is published.

## Next decisions (once original-source evidence is available)

1. Verify the GitHub Actions run and source count reconciliation.
2. Inspect quantities and partner multiplicity; interpret any apparent regularities as **hypotheses**, not conclusions.
3. Only then consider broader invoice-composition contrasts or the separate `A`-invoice / `B`-stock-code accounting-looking cohort.
4. Do not finalize sale, return or accounting definitions without supporting business semantics.

**No transaction pair is a verified gift, promotion, correction, refund or merchandise sale.**
