# Investigation 014 — The Mixed-Price Mystery: zero-priced lines in mixed invoices

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Verified against the original UCI Online Retail II workbook. **No business classification, revenue calculation or cleaning policy approved.**

## Question

Do positive-quantity, zero-unit-price lines appearing alongside positively priced lines on the *same invoice ID* have different observable properties from zero-price lines on invoices without positively priced lines? Can description completeness, customer-ID availability, same-invoice stock codes and textual clues support separate investigation paths without inventing business intent?

## Reproducibility and verification

- **Official source:** UCI Online Retail II, original workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Verified GitHub Actions:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42933178973 — completed **success**, 77 synthetic-data tests passed, original-workbook Case 014 executed and artifact uploaded.
- **Script:** `scripts/investigate_mixed_price_invoices.py`; **tests:** `tests/test_mixed_price_invoices.py`.
- **Report:** `outputs/mixed_price_invoices.json` in the GitHub Actions `retail-initial-audit` artifact (aggregates only, no actual customer identifiers, original workbook, or row-level exports).
- **Case 008 source view:** 1,044,848 candidate lines after 22,523 exact cross-sheet copy links; all 1,067,371 original rows accounted for in provenance.
- **Independent check:** `agrees_with_case_013_cohort_counts = true`; four zero-priced cohort counts cross-checked with the previously verified Case 013 report.
- **No changes:** Source records, reversible overlap provenance, S0/S1/S2 gross-positive-priced scenarios, and operational / financial classifications all remain unchanged.

## Original-source results

| Observation | Verified amount |
| --- | ---: |
| Positive-quantity, zero-price non-C lines | **2,631** |
| Invoice IDs with at least one such line | **1,986** |
| Invoice IDs with both zero-priced and positive-priced positive-quantity lines | **125** |
| Zero-price lines on these **mixed** invoices | **709** |
| Positive-priced lines on these mixed invoices | **7,660** |
| Invoice IDs containing **only** positive-quantity zero-priced lines | **1,861** |
| Zero-price lines outside mixed invoices | **1,922** |
| Zero-price invoice IDs with only other nonpaid line types, but no paid lines | **0** |
| Median zero-priced line count per mixed invoice | **1** |
| Maximum zero-priced lines in one mixed invoice | **64** |
| Median positively priced lines per mixed invoice | **16** |
| Maximum positively priced lines on one mixed invoice | **651** |
| Mixed invoices with at least one zero-price line sharing exact stock code with a positive-priced line in the **same invoice** | **33** |
| Such zero-priced lines sharing stock code with a paid line in the same invoice | **43** |

These are invoice **ID** and invoice-**line** counts, not verified distinct payments, fulfilled shipments, free gifts or customer orders.

## Two descriptively different source populations

| Feature | £0 lines **on mixed-price invoices** | £0 lines **outside mixed-price invoices** |
| --- | ---: | ---: |
| Positive-quantity zero-price lines | **709** | **1,922** |
| Customer ID **present** | 61 | 9 |
| Customer ID **missing** | 648 | 1,913 |
| Missing or blank description | **0** | **1,642** |
| Promotion-like keyword-probe matches | **1** | **0** |
| Operations-like keyword-probe matches | **0** | **108** |

- Of mixed-invoice zero-priced lines, **all 709 have descriptions**, including product-like descriptions such as `OWL DOORSTOP` (14 lines), `POLYESTER FILLER PAD 45x45cm` (9), `PICNIC BASKET WICKER LARGE` (8), `IVORY KITCHEN SCALES` (8), and colored door signs.
- In the comparison cohort, missing descriptions dominate (**1,642 of 1,922**). Among descriptions *that do exist*, recurrent values include `check` (39), `found` (28), `Found` (9), `adjustment` (14), `amazon`, and `mailout`.
- Among the **7,660 positive-priced lines** on mixed invoices, 926 have known customer IDs and 6,734 have missing customer IDs. Thus even the paid-looking context has substantial identity missingness.
- Textual word probes are limited to a small **pre-specified, incomplete** keyword list and may match incidental prose. They are not reliable operational classifiers, and absence of a matching word is not absence of the underlying process.
- The markedly different *description completeness* and *known-customer coverage* are descriptive evidence of distinct **recording contexts**. They are **not proof** of distinct underlying business causes, sales, or events.

## Interpretation and decisions

- **Observed:** The zero-price population is strongly heterogeneous by invoice composition. The 125 mixed invoices have product-like descriptions on all 709 zero-priced lines, while the 1,861 zero-price-only invoices contain many missing descriptions and operations-like wording. These differences justify **separately tracking the cohorts**.
- **Observed:** 43 zero-priced lines on 33 mixed invoices share an exact stock code with a positively priced line on the same invoice. This is a concrete testable clue about price-entry conventions, but does not establish a duplicate, same-unit event, replacement, bundle or gift.
- **Not established:** The 709 mixed-invoice zero-priced lines are promotional items, free samples, fulfilled merchandise, or legitimate sales; nor are the 1,922 other zero-price lines definitively stocktakes, internal adjustments, or errors.
- **D044:** Retain distinct, explicitly *descriptive* labels `zero_price_on_mixed_invoice` and `zero_price_only_invoice` for exploratory reporting. Do not assign a causal or accounting category.
- **D045:** Preserve every source line, every canonical cross-sheet link, and all prior KPI scenario definitions. In particular, no zero-price line is assigned a positive monetary amount or added to recognized revenue.
- **D046:** Investigate the 33 mixed invoice IDs and 43 same-stock-code zero-priced lines at **invoice-line level in-memory**, reporting only safe, bounded examples and aggregate counts; inspect sequence/quantity/price relationships before any stronger interpretation.
- **D047:** Keep customer-ID missingness explicit in both cohorts. Missing identifiers are not evidence of sameness or of absence of customers.

## Proposed next investigation — Case 015

**R014a — Same-invoice same-SKU pricing:** For each of the 43 zero-priced lines, compare quantities, timestamp differences (if any), and nearby positively priced lines of the same stock code on the same invoice. Establish whether exact same-SKU mixed pricing clusters in particular invoice types or dates. Check whether apparent duplicated invoice lines are merely distinct rows. Preserve a no-link/unknown status where business semantics cannot be determined.

**R014b — Robustness and representativeness:** Determine whether the large 64-zero-line or 651-paid-line invoices disproportionately influence population differences. Report at invoice as well as line granularity and avoid treating lines on one invoice as independent evidence.

**R013b — Separate later lead:** Source-wide `A`-prefixed and stock-code-`B` accounting-looking entries are a *different case* and should not be lumped into Case 014.

**Limits:** The source lacks original commercial rules, shipment/settlement confirmation, promotion flags, accounting mapping, and reliable staff/event identifiers. No employee misconduct, actual losses, refunded cash or valid merchandise revenue can be reconstructed from these descriptive co-occurrences alone.
