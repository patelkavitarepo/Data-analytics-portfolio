# Investigation 009 — Retail gross line-amount scenario sensitivity

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Source-verified experimental KPI scenarios; **none approved as accounting revenue**.

## What we asked

After removing exact December 2010 cross-sheet publication copies **only in a reversible candidate view**, how do common stock-code exclusions change a proposed gross positive-priced merchandise-like amount? How many invoice lines sit in cancellation, zero-price and ambiguous categories?

## Reproduction

- **Original workbook:** UCI Online Retail II (dataset 502), SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **GitHub Actions:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42883445158 — **success**, 48 synthetic tests passed (36 warnings, no failures).
- **Code:** `scripts/investigate_revenue_scenarios.py`; tests `tests/test_revenue_scenarios.py`.
- **Source-data analysis:** load the workbook, build the Case 008 candidate view in memory, compare with the concatenated raw worksheets, then export only aggregate `outputs/revenue_sensitivity.json`.
- **Reconciled independently** with `outputs/reversible_layer_audit.json`: 22,523 canonical cross-sheet links and 1,044,848 candidate lines.
- **No source rows changed**; candidate and provenance row-level data remain in ignored local `data/`, not in published workflow artifacts.

## Three explicitly experimental scenarios

All scenarios require a **non-C-prefixed invoice, positive quantity and positive unit price**, and calculate `quantity × unit_price`, summed across qualifying *invoice lines*. They are **gross positive-priced line amounts**, *not* net or recognized company revenue.

- **S0 — Broad positive-priced:** all qualifying lines.
- **S1 — Narrow named shipping/billing exclusions:** S0 minus exact uppercase stock codes `POST`, `DOT`, `C2`, `BANK CHARGES`, `AMAZONFEE`. Case-insensitive exact-code match after trimming, **not** descriptions containing these substrings.
- **S2 — Further manual/discount exclusions:** S1 minus `M` and `D`, two additional uncertain codes. S2 is **not** automatically more accurate; some manual entries might be legitimate revenue.

### Impact of cross-sheet overlap and scenario changes

| Metric | Raw workbook (both sheets, uncorrected overlap) | Candidate view (matched cross-sheet lines once) | Cross-sheet difference |
| --- | ---: | ---: | ---: |
| Original/candidate invoice lines, all types | 1,067,371 | 1,044,848 | 22,523 |
| S0 qualifying lines | 1,041,670 | 1,019,654 | 22,016 |
| **S0 gross positive line amount** | **£20,972,594.57** | **£20,533,741.92** | **£438,852.65** |
| S1 qualifying lines | 1,038,037 | 1,016,084 | 21,953 |
| **S1 gross positive line amount** | **£20,474,120.30** | **£20,063,792.35** | **£410,327.95** |
| S2 qualifying lines | 1,037,151 | 1,015,218 | 21,933 |
| **S2 gross positive line amount** | **£20,132,991.08** | **£19,723,764.52** | **£409,226.56** |

Differences **within the candidate view**:

| Candidate-view exclusion | Rows affected | Gross line amount excluded |
| --- | ---: | ---: |
| S0 → S1: exact named shipping/billing codes | **3,570** | **£469,949.57** |
| S1 → S2: additional M and D codes | **866** | **£340,027.83** |

These figures are not amounts of refund, stock loss, profit, or financial error. They describe sensitivity to provisional line-level inclusion decisions.

## Observed stock-code labels and amounts — candidate view

| Exact stock code | Descriptions seen in source | Positive-priced qualifying lines | Hypothetical gross line amount |
| --- | --- | ---: | ---: |
| `POST` | POSTAGE | 1,851 | £125,682.42 |
| `DOT` | DOTCOM POSTAGE | 1,415 | £309,854.11 |
| `C2` | CARRIAGE | 267 | £13,426.00 |
| `BANK CHARGES` | Bank Charges | 34 | £519.24 |
| `AMAZONFEE` | AMAZON FEE | 3 | £20,467.80 |
| `M` | Manual | 861 | £339,629.94 |
| `D` | Discount | 5 | £397.89 |

These descriptions are **observed source labels**, not independently verified accounting treatments. In particular, the large `M` impact must not be erased without investigating its underlying invoices.

## Exhaustive, mutually exclusive candidate-view line cohorts

| Source-observed cohort | Candidate lines |
| --- | ---: |
| C-prefixed invoice lines, any quantity | **19,165** |
| Non-C negative quantity, zero price, customer ID missing | **3,393** |
| Other negative non-C lines | **0** |
| Non-C positive quantity, positive price | **1,019,654** |
| Non-C positive quantity, zero price | **2,631** |
| Non-C positive quantity, negative price | **5** |
| Non-C zero quantity | **0** |
| Remaining unresolved non-C types | **0** |
| **Total candidate lines** | **1,044,848** |

C-prefixed invoice codes signify cancellation according to UCI documentation. Of the candidate view's 19,165 C-prefixed lines, 19,164 have negative quantity and positive unit price. Their *unsigned magnitude of negative signed line amounts* is **£1,465,677.23**; **do not interpret it as realized refunds**, net it mechanically against S0/S1/S2, or imply cash actually changed hands.

All 3,393 non-C negative, zero-price, no-customer candidate lines remain *possible operational inventory adjustments*, **not confirmed shrinkage or theft**.

## Interpretation

1. **Cross-sheet overlap matters:** a naive S0 total over both unadjusted worksheets differs from the reversible view by £438,852.65.
2. **The business definition matters too:** named carriage/shipping/billing code exclusions change the candidate S0 by £469,949.57; excluding manual and discount codes would change it by another £340,027.83.
3. **Code labels are evidence but not policy:** `POST` / `DOT` / `C2` have postage/carriage-oriented descriptions, but finance/retail reporting could intentionally include shipping revenue in total receipts. `M` may include valid manual postings. `D` is not automatically equivalent to a ledger discount adjustment.
4. **Cancellation is not verified refund:** cancellation-coded entries cannot safely serve as realized cash refunds or be subtracted without transaction-level matching and financial confirmation.
5. **Unresolved zero/negative prices remain:** 2,631 zero-priced positive lines and 5 negative-unit-price positive lines in candidate need review before publishing final KPIs.
6. **Customer IDs are not used to filter qualifying lines:** missing IDs limit repeat-customer analysis, but do not on their own disqualify positive-priced lines.
7. **Invoice counts shown per scenario are distinct IDs among qualifying lines, not necessarily completed purchases.**

## Safeguards and next investigations

- **D027:** Retain S0, S1 and S2 as *comparative sensitivity scenarios*; no final company-revenue definition has been approved.
- **D028:** Do not subtract C-prefixed signed amounts as refunds or call them recognized refunds.
- **D029:** Do not silently drop postage, carriage, manual, discount or zero-priced records. Document exclusions by exact code and their line and value effects.
- **D030:** Continue to use Case 008's reversible cross-sheet candidate view; keep source and full provenance intact.
- **R009a:** Explore the composition of `M` invoices (customer ID availability, descriptions, dates, price distribution and nearby stock-coded items) before deciding to exclude them.
- **R009b:** Audit zero-priced positive and negative-price entries and review code-meaning uncertainty.
- **R009c:** Decide whether to report separate merchandise gross line amount, shipping/billing line amount, cancellation-coded signed amount, and *provisional* order counts rather than a single unsupported "net revenue" KPI.

**No sales dashboard, finalized net revenue, profit, loss or cashflow interpretation is approved yet.**
