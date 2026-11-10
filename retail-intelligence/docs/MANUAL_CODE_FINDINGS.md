# Investigation 010 — What does stock code M ("Manual") represent?

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Verified descriptive source audit, business meaning still unresolved. **Do not automatically include or exclude M from recognized revenue.**

## The question

In Case 009, excluding exact stock codes `M` and `D` reduced the candidate gross positive-priced line-amount scenario by £340,027.83, of which `M` alone accounted for £339,629.94. Are `M` lines uniform fees/adjustments, ordinary product sales, or mixed transactions?

## Reproducible evidence

- **Original source:** UCI Online Retail II two-sheet workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Successful CI:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42886173182.
- **Tests:** 53 passed (39 warnings, no test failures).
- **Code:** `scripts/investigate_manual_code.py`, synthetic tests `tests/test_manual_code.py`.
- **Report:** `outputs/manual_code_investigation.json` in the GitHub Actions `retail-initial-audit` artifact. Contains aggregate findings only, **no customer IDs or raw rows**.
- Analysis uses the **Case 008 reversible candidate layer** and independently reconciles the positive-priced `M` row count and amount with Case 009. No source rows are modified.

## Line-level source observations

| Measure | Unadjusted two-sheet workbook | Cross-sheet-reconciled candidate |
| --- | ---: | ---: |
| All stock-code `M` lines | 1,426 | **1,403** |
| Positive quantity/price, non-C `M` lines | 881 | **861** |
| Negative quantity/positive price, C-prefixed `M` lines | 537 | **534** |
| All other `M` line types | 8 | **8** |
| Gross positive-priced `M` line amount (not verified revenue) | £340,731.33 | **£339,629.94** |
| Magnitude of C-prefixed negative `M` line amounts (not verified cash refunds) | £423,886.17 | **£422,939.08** |

**Cross-sheet publication overlap:** 20 positive-priced `M` line copies account for £1,101.39 of the raw/candidate amount difference.

**The `M` positive amount represents 1.654% of candidate Scenario S0** (£20,533,741.92). This is *not* proof that it is revenue or expense.

### Invoice context of 861 positive-priced candidate M lines

- **788 distinct invoice IDs** contain at least one qualifying `M` line.
- **290 invoice IDs contain only `M` stock-code lines** (even if a single invoice has multiple M lines).
- **498 invoice IDs contain both `M` and at least one non-M stock-code line**.
- **480 invoice IDs contain a non-M line that is itself positive-quantity and positive-price**.
- **534 M lines** occur on these invoices with ordinary positive-priced non-M lines; another **18 M lines** occur on mixed invoices without a qualifying positive-priced non-M line (552 M lines on any mixed invoice in total).
- **309 M lines** occur on M-only invoices.
- **170 of 861 M positive lines lack a customer ID**; this is about 19.7%. Do not infer a customer's identity from invoice adjacency.
- **All 861 positive M descriptions are exactly “Manual”** in the source; the text provides little causal detail.
- Positive-priced M entries occur across every month of the two-year window, not only around the December cross-sheet overlap.
- **763** of those 861 lines have country United Kingdom; other countries also appear.

### Distributions (positive quantity and positive price, non-C)

| Metric | Candidate view |
| --- | ---: |
| Minimum unit price | £0.06 |
| Median unit price | £2.95 |
| 90th percentile unit price | £851.60 |
| Maximum unit price | £25,111.09 |
| Minimum line amount | £0.08 |
| **Median line amount** | **£8.85** |
| 90th percentile line amount | £851.60 |
| **Largest line amount** | **£25,111.09** |
| **Top 10 lines as a share of total M positive line amount** | **31.91%** |
| Typical positive quantity (median) | 1 |
| Largest positive quantity | 1,600 |

The broad amount distribution is consistent with **heterogeneous** transactions, but does not specify their accounting or operational purpose. A large manual line could be legitimate, an adjustment, or something else.

## Interpretation

1. **We cannot justify deleting `M` wholesale.** Most `M`-containing positive invoice IDs are mixed with other stock codes. Some may be legitimate charges associated with goods; invoice association alone does not prove economic classification.
2. **Neither can we certify `M` as merchandise revenue.** Many M-only invoices, very high-value outliers, and an uninformative description invite deeper case-specific inspection.
3. **C-prefixed M lines also matter.** Their signed amount magnitude is £422,939.08 in the candidate view; this is **not confirmed refunded money**, a matching reversal, or a valid figure to automatically subtract.
4. **The top of the distribution matters.** A few entries account for a large proportion of the total. Treat high-value cases as manual-review candidates, not evidence of wrongdoing.
5. **S0/S1/S2 remain sensitivity scenarios, not financial truth.** The difference between S1 and S2 must continue to be explained explicitly; `M` is by far the largest component of the additional exclusion.

## Decisions and next tests

- **D031:** Retain exact stock code `M` as its own **ambiguous manual-coded cohort** in downstream exploratory reporting. Show it as a separate gross positive amount instead of silently deleting it or automatically counting it as confirmed merchandise.
- **D032:** Preserve all original rows and the Case 008 provenance map; no row or invoice cleaning decision.
- **D033:** Keep positive M, cancellation-coded negative M, and the eight remaining M lines separate. No automatic pairing or assumption of realized refunds.
- **R010a:** Investigate the high-value positive `M` lines and their whole invoices (other stock codes, timestamps, quantities, customer-ID presence), keeping row-level source data private.
- **R010b:** Explore possible linked M cancellation-coded lines and identify whether invoice IDs, customers, amounts or dates offer credible reversal relationships. Do not claim matching without source evidence.
- **R010c:** Before formal KPI publication, decide whether to show **merchandise-like**, **shipping/billing-like**, **manual/ambiguous**, and **cancellation-coded** amounts as separate provisional metrics, all clearly labeled.

## Limits

The dataset has no internal manual-entry reason, ledger mapping, transaction event ID, staff note, original accounting category, or verified settlement details. Its code and description alone cannot prove a sale, error, fee, refund, fraud, or stock loss. Invoices may contain both real goods and administrative lines.
