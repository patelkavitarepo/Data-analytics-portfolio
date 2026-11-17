# Investigation 013 — The Price Paradox: zero and negative unit prices

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Verified on original UCI workbook; **no cleaning, revenue or accounting policy approved**.

## Question

Among the cross-sheet-reconciled invoice lines, why are **2,631 non-C positive-quantity lines priced at zero** and **five non-C positive-quantity lines priced below zero**? Are these evidence of free promotions, inventory movements, bookkeeping adjustments or something else?

## Evidence, reproducibility and source integrity

- **Original source:** UCI Online Retail II (dataset 502), workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **GitHub Actions:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42912802097 — **success** with **72 synthetic-data tests passed** (49 non-failing warnings).
- **Code:** `scripts/investigate_price_paradox.py` and `tests/test_price_paradox.py`.
- **Aggregate report:** `outputs/price_paradox.json`, published in the JSON-only `retail-initial-audit` workflow artifact; no workbook, individual customer IDs or original row-level data exported.
- **Source view:** 1,044,848 candidate invoice lines after **22,523** reversible cross-sheet copy links, with **1,067,371** original rows accounted for in provenance.
- **Independent reconciliation:** cohort sizes agree with Case 009's source-verified `revenue_sensitivity.json` (true).
- **Definitions:** Positive quantity, non-C invoice, unit price exactly 0 versus strictly below 0. C-prefixed rows are treated separately. No assumptions about fulfilled sales or cash settlement.

## Cohort A — 2,631 positive-quantity, £0 unit-price lines

| Observation | Verified |
| --- | ---: |
| Zero-priced positive-quantity non-C lines | **2,631** |
| Customer ID present | **70** |
| Customer ID missing | **2,561** |
| Missing description | **1,642** |
| Distinct invoice numbers with at least one such line | **1,986** |
| Invoices made up entirely of positive-quantity zero-price lines | **1,861** |
| Invoices that also contain positive-quantity positive-price lines | **125** |
| Zero-price lines occurring on those mixed paid-looking invoices | **709** |
| Distinct stock codes in zero-price lines | **1,395** |
| Zero-price lines whose stock code also occurs at positive price elsewhere | **2,561** |
| Zero-price stock codes also seen at positive price elsewhere | **1,327** |
| Zero-price stock codes never observed at a positive price elsewhere | **68** |
| Quantity per zero-price line: median | **4** |
| Quantity per zero-price line: 90th percentile | **100** |
| Quantity per zero-price line: largest | **12,540** |
| UK country lines | **2,604** |

The invoice composition is mutually exhaustive: of 1,986 invoice IDs, **1,861 are zero-price-only** and **125 also contain positive-price lines**, while **none** mix zero-priced positive lines with only other nonpositive categories but no positive-priced lines.

### Source description clues

- Description absent on **1,642** of these lines (about **62.4%**).
- Examples of recurring descriptions: `check` (39), `found` (28), `Found` (9), `adjustment` (14), `amazon` (8), and product-like descriptions `OWL DOORSTOP` (14) and `POLYESTER FILLER PAD 45x45cm` (12).
- The *same stock codes* often appear with positive prices on other lines, which suggests the £0 field is not necessarily a product's normal price. It does **not** establish whether any zero-price line was a gift, sample, inventory discovery, data issue or accounting adjustment.
- Mixed invoices with paid-looking lines allow plausible promotions or bundled zero-value items, but without business rules no categorical decision is justified.

## Cohort B — Five positive-quantity, negative-unit-price lines

**All five** source lines are separate, **one-line, non-C invoices** with:
- invoice IDs prefixed `A`;
- exact stock code `B`;
- source description `Adjust bad debt`;
- quantity **+1**;
- **missing customer ID**;
- no accompanying ordinary positive-priced invoice lines.

| Invoice | Date and time | Unit price and signed line amount | Source sheet |
| --- | --- | ---: | --- |
| `A506401` | Apr 29, 2010, 13:36 | **−£53,594.36** | Year 2009–2010 |
| `A516228` | Jul 19, 2010, 11:24 | **−£44,031.79** | Year 2009–2010 |
| `A528059` | Oct 20, 2010, 12:04 | **−£38,925.87** | Year 2009–2010 |
| `A563186` | Aug 12, 2011, 14:51 | **−£11,062.06** | Year 2010–2011 |
| `A563187` | Aug 12, 2011, 14:52 | **−£11,062.06** | Year 2010–2011 |
| **Total signed line amount** | | **−£158,676.14** | |

**Interpretation:** The exact `A` prefix, `B` stock code and uniform `Adjust bad debt` description are compelling source evidence for a **bad-debt-labelled accounting-entry cohort**, *not* ordinary merchandise sold for a negative price. The dataset does **not** show an accounts receivable ledger or settlement status; we must **not** claim these amounts are actual verified write-offs, refunds, profit reductions or theft.

**Caution about apparent repetition:** `A563186` and `A563187` share date, hour, near-identical time (one minute apart), quantity, price, stock code and description, but have **different invoice IDs**. They are not exact source duplicate rows across all eight fields. Their shared amount cannot by itself establish accidental double posting.

## Business implications, decisions, and next case

- **D040:** Keep both anomalous cohorts separately labelled in exploratory reporting. Do not silently erase the zero-price entries or present them as known free merchandise.
- **D041:** Tag the five `B` / `Adjust bad debt` / `A`-prefixed lines as **source-labelled bad-debt adjustments**, *not* negative-priced product sales; do **not** automatically net −£158,676.14 against provisional gross merchandise S0/S1/S2.
- **D042:** Preserve the original workbook, the reversible candidate view, and all source-row provenance. No cleaning or accounting rule was changed.
- **D043:** Retain the 70 zero-price lines with customer IDs and 125 mixed invoices for further context testing, rather than assuming all £0 lines are stocktakes.
- **R013a:** Investigate the 125 mixed-price invoices and whether products or description labels distinguish promotions, bundles, and other plausible £0 cases.
- **R013b:** Inspect all `A`-prefixed and `B`-coded lines across *all* quantity signs and invoice types, to establish how broad the bad-debt-labelled category is. Check whether `A563186` / `A563187` are source recording lookalikes beyond this small cohort, without making a duplicate-removal decision.
- **R013c:** Build a **proposed KPI semantic dictionary**, keeping merchandise-like positive-priced, postage/billing, manual/ambiguous, C-prefixed cancellation, stock movement candidates, zero-priced positive items and bad-debt-labelled entries **separate and fully transparent**. Revenue definitions still require business meaning and will remain experimental.

**Final caveat:** This is source-record observation, not a reconstruction of financial statements. The UCI invoice-line table does not certify internal account mappings, cash receipts, refunds, stock losses, credit terms, ledger adjustments, or staff actions.
