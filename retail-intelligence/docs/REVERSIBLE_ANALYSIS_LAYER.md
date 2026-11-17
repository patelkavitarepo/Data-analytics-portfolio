# Investigation 008 — Reversible cross-sheet analysis layer

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Implementation and tests complete. **Candidate/proposed analysis view, NOT an approved production cleaning rule.**

## Question

Can we construct a usable analysis dataset that avoids counting the same invoice line twice when the original UCI Online Retail II workbook repeats December 2010 transactions in both annual sheets, **without deleting source evidence or blindly deduplicating within a worksheet**?

## Verified run and code

- **Original source:** UCI Online Retail II (dataset 502); SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- **Successful GitHub Actions source run:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42879978426
- **42 synthetic-data tests passed** across the project (34 warnings, no failures). The full original source workbook was processed successfully.
- **Implementation:** `scripts/build_reversible_layer.py` and `tests/test_reversible_layer.py`.
- **Independent check:** the new layer's row counts and positive-line-amount difference match the separately computed [Investigation 007 cross-sheet audit](ANNUAL_SHEET_OVERLAP.md).
- **Summary output:** `outputs/reversible_layer_audit.json`, included in the workflow's uploaded **JSON-only** `retail-initial-audit` artifact.
- **Row-level outputs:** `data/derived/candidate_analysis_lines.csv.gz` and `data/derived/source_line_provenance.csv.gz`. They contain source data and must **remain local**, ignored by Git; they are **not uploaded** by the GitHub workflow.

## Deterministic candidate-view rule

1. Normalize the eight documented source fields (`invoice_no`, `stock_code`, `description`, `quantity`, `invoice_date`, `unit_price`, `customer_id`, `country`).
2. Assign each source line a **sheet name** and its **original Excel row number** (first data row = 2). Assign an *occurrence rank* within its exact eight-field key, independently for each sheet.
3. **Retain every line from the first worksheet** (`Year 2009-2010`).
4. From the second worksheet (`Year 2010-2011`), **retain each unmatched key-and-occurrence**. When an eight-field key and occurrence rank exactly match one in the first sheet, mark the second-sheet copy **excluded from the candidate view**. This exclusion is *view-level only*.
5. Record every original row in a provenance ledger with `source_sheet`, `source_excel_row`, `included_in_candidate_view`, `overlap_type`, `candidate_canonical_sheet` and `candidate_canonical_excel_row`. Excluded rows point to their actual corresponding retained first-sheet row.
6. **Do not remove within-sheet exact duplicate lines** or collapse two invoice IDs because their quantities or timestamps are similar. Different invoice contents remain separate.

This is a **multiplicity-aware** method. Example: If a line appears twice in the first sheet and three times in the second, the candidate view keeps two first-sheet occurrences **plus one unmatched second-sheet occurrence**; the other two second-sheet copies point to their corresponding first-sheet rows.

## Reconciliation against original workbook

| Source category | Raw lines | Candidate-view excluded exact cross-sheet copies | Candidate-view lines |
| --- | ---: | ---: | ---: |
| Non-C negative, £0 price, customer ID missing | 3,457 | 64 | **3,393** |
| C-prefixed cancellation-coded lines | 19,494 | 329 | **19,165** |
| Non-C, positive quantity and positive unit price | 1,041,670 | 22,016 | **1,019,654** |
| All other line types | 2,750 | 114 | **2,636** |
| **Total** | **1,067,371** | **22,523** | **1,044,848** |

Additional cross-checks:

- **First worksheet lines retained:** 525,461.
- **Second worksheet lines retained:** 519,387.
- **Candidate-view lines:** 1,044,848.
- **Full provenance rows (one for every original source line):** **1,067,371**.
- **Canonical links for suppressed second-sheet copies:** **22,523**.
- **Independent reconciliation with Investigation 007:** **passed**.
- Original workbook remains unmodified.

## Value sensitivity — not certified revenue

For *non-C* lines with **positive quantity and positive unit price only**, the illustrative gross positive line amount is computed as `quantity × unit_price`:

| Scenario | Hypothetical amount |
| --- | ---: |
| Sum both unadjusted source sheets | **£20,972,594.57** |
| Sum candidate view with cross-sheet exact copies counted once | **£20,533,741.92** |
| Difference attributable to matched cross-sheet copies | **£438,852.65** |

This is **not** a finalized revenue calculation: cancellations, tax, postage, discounts, refunds, fees, product definitions, and other accounting details are not yet fully resolved. The change is *not* money lost by the retailer; it reflects a duplicated data-publication window in the source workbook.

## How to reproduce

From `retail-intelligence/` after installing requirements:

```bash
python scripts/audit.py --download
python scripts/investigate_sheet_overlap.py
python scripts/build_reversible_layer.py
python -m pytest -q
```

The final script verifies its count/value reconciliation against `outputs/annual_sheet_overlap.json` when present. Keep `data/raw/` and `data/derived/` private (both fall under ignored `data/`). Only aggregate JSON reports are included in the GitHub Actions artifact, not the row-level files.

## Decisions and next work

- **D023:** Keep the source workbook unchanged. The exclusion flag exists **only in a candidate analysis view**.
- **D024:** Retain every source row reference and a direct retained-canonical-row link for every second-sheet exact copy.
- **D025:** Do not treat within-sheet repetitions as accidental errors or delete them at this stage.
- **D026:** Keep all revenue interpretations explicitly hypothetical until business transaction types are defined.
- **Next (Case 009):** Define and sensitivity-test exploratory retail KPI cohorts (positive-priced non-C lines; cancellation-coded lines; postage/service codes; operational-looking zero-price negative lines; ambiguous rows). Compare raw versus candidate view and document *each* row-impact decision before publishing a dashboard.

## Limitations

The candidate view is **not** a unique real-world-event ledger. The original workbook has no immutable source event ID, so exact line matching cannot conclusively determine whether two identical-looking records are separate legitimate business events. The occurrence-ranked method transparently handles matching counts; it does not infer true customer behavior, revenue, theft, or stock loss.
