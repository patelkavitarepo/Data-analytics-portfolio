# Investigation 007 — Annual worksheet overlap and exact cross-sheet copies

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Confirmed overlap on the original UCI workbook; **read-only audit**. No cleaning rule has been applied.

## Question

Do the two yearly Excel worksheets include the same invoice lines in their overlapping December 2010 period? If so, how many lines and invoices appear in both, and what would an uncorrected line-total calculation double-count?

## Reproducibility and source integrity

- **Dataset:** UCI Online Retail II (dataset 502), original `online_retail_II.xlsx`
- **Original workbook SHA-256:** `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- **Successful GitHub workflow:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42871691979
- **Tests:** 36 passed (32 pre-existing deprecation warnings; no failing tests).
- **Script:** `scripts/investigate_sheet_overlap.py`. Run: `python scripts/investigate_sheet_overlap.py` after obtaining the official workbook.
- **Machine-readable output:** `outputs/annual_sheet_overlap.json`, uploaded in GitHub Actions artifact `retail-initial-audit`. Neither data workbook nor source records are committed.
- **Exact key:** invoice ID, stock code, description, quantity, date/time, unit price, customer ID, and country — all eight source fields.
- **Multiplicity-safe matching:** For each exact eight-field line key, overlap count equals the *minimum* of its occurrence counts across the two source sheets. This avoids cross-join multiplication and **does not** remove repeated lines already within a worksheet.

## Verified coverage

| Source sheet | Original lines | First timestamp | Last timestamp | Distinct invoice IDs |
| --- | ---: | --- | --- | ---: |
| Year 2009-2010 | 525,461 | 2009-12-01 07:45 | 2010-12-09 20:01 | 28,816 |
| Year 2010-2011 | 541,910 | 2010-12-01 08:26 | 2011-12-09 12:50 | 25,900 |
| **Combined raw lines** | **1,067,371** | | | |

The **overlapping time coverage** is December 1, 2010 08:26 through December 9, 2010 20:01 (timestamps at the original minute resolution).

## Evidence of duplicate publication across sheets

| Measure | Verified result |
| --- | ---: |
| **Exact source-line copies repeated across both worksheets** | **22,523** |
| Distinct eight-field line signatures present in both sheets | 22,202 |
| Overlap as a share of combined raw rows | 2.1101% |
| **Distinct invoice IDs present in both worksheets** | **1,088** |
| Shared invoice IDs with one or more exact matching lines | 1,088 |
| **Shared invoice IDs with fully matching line multisets** | **1,088** |
| Shared invoice IDs with partly matching line contents | 0 |
| Shared invoice IDs with no exact matching lines | 0 |
| Matched line copies outside December 2010 | **0** |
| Raw rows in hypothetical cross-sheet-exact-one-copy dataset | **1,044,848** |

**Conclusion about the file structure:** the original workbook re-publishes exactly matching invoices/lines across its two yearly worksheets in December 2010. This is a concrete source-overlap problem for any analyses that concatenate both worksheets without reconciliation. This finding is **not** a claim that distinct underlying business events can never have all eight attributes identical.

## Types of shared lines (mutually exclusive)

| Observed type | Repeated lines across sheets |
| --- | ---: |
| Negative quantity, non-C invoice, zero price, customer ID missing | 64 |
| C-prefixed invoice (cancellation-coded) | 329 |
| Positive quantity and positive price on non-C invoice | **22,016** |
| All remaining line types | 114 |
| **All repeated line copies** | **22,523** |

The **64 repeated non-C negative records** explain the difference between 3,457 sheet-specific candidate invoice-line instances and 3,393 global distinct invoice IDs previously observed. This is **cross-sheet publication overlap**, not proof of 64 erroneous postings within the retailer's own systems.

## Gross positive line amount sensitivity

Define a *hypothetical* positive line amount as `quantity × unit_price` **only for** non-C invoice lines with positive quantity and positive unit price. This is **not** a certified revenue, profit or cash collected metric; it excludes cancellations and other line types that are not yet fully classified.

- **Value of matched cross-sheet line copies under that formula:** **£438,852.65**.
- **Interpretation:** blindly summing both original worksheets could double-count that much in this *specific hypothetical gross positive-line amount*, not necessarily in a complete or accepted revenue KPI.
- The value is **not** a loss, bad debt, refund, theft estimate, or validated overstatement of official company accounts.
- No figure for overall revenue or final adjusted revenue is asserted.

## Decisions

- **D018:** Preserve the original workbook and all source worksheet/row provenance. **No original data removed.**
- **D019:** Mark December 2010 as a confirmed **cross-sheet duplicate-publication period**. Distinguish source-duplicate publication from repeated entries within one worksheet.
- **D020:** Before building the sales dashboard, create *proposed* analysis tables that retain only one cross-sheet copy of each exact eight-field line, **with a reversible provenance map and before/after row-count checks**. Do not merge or apply such a cleaning policy without a separately documented decision.
- **D021:** Do not delete lines solely because the invoice number repeats, and do not implicitly remove within-sheet exact duplicates. Consider the full invoice-line key and multiplicity.
- **D022:** All future date, invoice and sales summaries must specify whether they are raw-sheet totals or cross-sheet-reconciled figures. No dashboard/revenue metric is yet finalized.

## Next case

Design a **reversible, independently validated analysis layer** with source-sheet/Excel-row traceability, cross-sheet overlap flags, and separate definitions for ordinary positive-priced lines, cancellations, operational negative entries, and ambiguous records. Sensitivity-check any proposed KPI definition rather than silently adopting one.

## Limitations

- Historical observational data: source logs, financial ledgers, inventory counts and transaction event IDs are not included.
- String and numeric field normalization are documented in the script. The equality is across normalized original fields, not a claim about real-world event identity.
- The exact-match count is a multiset overlap. Counting only unique eight-field *keys* (22,202) would understate 22,523 overlapping line copies.
- This audit did not infer staff behavior or inspect external retailer accounting systems.
