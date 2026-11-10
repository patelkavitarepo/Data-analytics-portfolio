# Investigation 006 — How common are operational-looking invoice runs?

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Reproducible full-workbook descriptive analysis completed; no causal conclusion or cleaning policy.

## Question

Our first case studies showed short runs of zero-priced, no-customer, negative-quantity entries. Are such runs *unusually frequent* relative to ordinary-looking positive-priced invoices, or are consecutive invoice numbers common across many transaction types?

## Source and method

- **Source:** UCI Online Retail II, original two-sheet workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Successful run:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42867178211
- **Automated tests:** 30 passed (32 deprecation warnings from prior test code; the workflow completed successfully).
- **Reproducible script:** `python scripts/investigate_population_batches.py`, saves `outputs/population_batch_prevalence.json` into the run artifact.
- **Candidate line:** numeric (non-C) invoice ID, **negative quantity, zero unit price, missing customer ID**. These are observed fields, *not a verified "inventory loss" label*.
- **Candidate-only invoice:** all lines in that invoice ID, **within the same source worksheet**, meet that candidate definition.
- **Comparison invoice:** all its lines have **positive quantity and positive unit price**; this is *not* proof of completed customer sales.
- **Run:** within the same worksheet, consecutive numeric invoice IDs (difference = 1), where each neighboring pair of invoice first timestamps is within **five minutes**. Adjacent comparison uses absolute time difference; whole-run durations can be longer than five minutes.
- **Counting unit:** invoice **within its source worksheet**, not a globally unique invoice ID. A number repeated on both worksheets contributes twice before cross-sheet reconciliation.

## Full-dataset observations

| Observation | Candidate-only invoices | Positive-priced-only invoices |
| --- | ---: | ---: |
| Invoice-within-sheet instances | **3,457** | **40,781** |
| All line-items belong to that invoice type | Yes | Yes |
| Short-gap consecutive runs including single-invoice runs | 1,761 | 22,058 |
| Standalone invoice runs (size 1) | 1,148 | 13,229 |
| Runs containing exactly two invoices | 270 | 4,470 |
| Runs containing three or four invoices | 199 | 3,093 |
| Runs containing five or more invoices | 144 | 1,266 |
| Invoice instances within runs of 2+ | **2,309 (66.8%)** | **27,552 (67.6%)** |
| Invoice instances within runs of 3+ | 1,769 (51.2%) | 18,612 (45.6%) |
| Invoice instances within runs of 5+ | 1,102 (31.9%) | 8,306 (20.4%) |
| Largest run length | 21 | 23 |

**Important:** The similar 66.8% versus 67.6% run-membership rates show that **short consecutive clustering is not specific to candidate inventory adjustments**. Higher long-run (5+) membership among candidates is a descriptive difference under an arbitrary threshold, **not causal evidence** of a particular stock adjustment process. Different group compositions and sheet overlaps limit interpretation.

### The 3,457 candidate lines and their invoice composition

- All **3,457** candidate lines belong to candidate-only invoices on their respective source worksheets.
- **Every such invoice-within-sheet has exactly one line** (3,457 one-line invoices; zero multi-line invoices).
- **Zero** candidate lines are mixed into invoices that also contain ordinary-priced lines within their worksheet.
- A previous cross-sheet-neutral audit reported **3,393 distinct invoice IDs globally** among these 3,457 lines. The 64 difference is a critical **possible cross-sheet overlap / duplication issue**: the present analysis *deliberately* treats each worksheet separately. **Do not interpret 3,457 as 3,457 unique business events.**

### Coverage across the two original worksheets

| Sheet | Candidate lines | Candidate invoice instances | Instances in runs of 2+ |
| --- | ---: | ---: | ---: |
| `Year 2009-2010` | 2,121 | 2,121 | 1,491 |
| `Year 2010-2011` | 1,336 | 1,336 | 818 |

Some of the **same invoice number ranges** occur in both worksheets, including run `537003`–`537021` on December 3, 2010. This independently motivates a **cross-sheet duplication audit** before aggregating years into any revenue or order metric. Their duplication status requires line-by-line verification before deciding whether to count once or twice.

### Selected large runs (not a comprehensive list)

- `507893`–`507913`: **21 invoices**, May 11, 2010, 17:04–17:16, 2009–2010 sheet.
- `537003`–`537021`: **19 invoices**, Dec 3, 2010, 15:33–15:43, appears as a run in *both worksheets*.
- `542550`–`542567`: **18 invoices**, Jan 28, 2011, 14:45–14:53, 2010–2011 sheet.

No descriptions or business purposes are inferred from the ID range itself.

## Interpretation

1. **Confirmed as a source recording pattern:** Unusual negative, zero-price, anonymous lines appear in single-line invoices, often grouped under consecutive IDs.
2. **Not unique to operational-looking lines:** Ordinary-looking positive-price invoices form short consecutive sequences at a very similar rate (66.8% versus 67.6%).
3. **Still plausible but unproven:** The candidate line combination and cases with descriptions `damaged`, `given away` and `printing smudges/thrown away` support internal stock/accounting entries as a working hypothesis. Sequence adjacency **alone** is not confirmatory evidence.
4. **New source-integrity question:** Annual worksheets may contain overlapping invoice lines, so a combined-data analysis could inadvertently count some source events twice.

## Decisions and next investigations

- **D015:** Keep 3,457 entries as **source invoice lines** and 3,457 as **sheet-specific invoice instances**; do not confuse with 3,393 globally distinct invoice numbers or independent business events.
- **D016:** Do **not** use consecutive-invoice clustering as a rule to identify internal adjustments or delete repeated lines.
- **D017:** Keep original workbook untouched. Do not calculate revenue, costs or shrinkage from these provisional classifications.
- **R007 (next):** Explicitly reconcile overlapping source worksheets, especially Dec 2010, measuring exact shared invoice lines, invoice IDs, date coverage and potential double counting.
- **After R007:** Sensitivity-check business KPIs under independently documented candidate transaction definitions.

This analysis is observational; neither theft nor specific employee behavior can be inferred.
