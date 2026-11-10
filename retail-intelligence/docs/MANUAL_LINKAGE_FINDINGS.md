# Investigation 011 — High-value Manual postings and possible cancellation links

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Verified original-workbook descriptive investigation. **No link is established as a confirmed refund, reversal, sales event or accounting correction.**

## The question

Does exact stock code `M` ("Manual") contain large atypical positive postings, and can some of its cancellation-coded negative postings be linked *provisionally* to earlier, otherwise matching positive lines?

## Reproducibility, audit controls and privacy

- **Original workbook:** UCI Online Retail II (dataset 502), SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Successful full-workbook workflow:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42890694308 — **59 synthetic tests passed** (47 warnings; no failing tests).
- **Source code:** `scripts/investigate_m_linkages.py` and tests `tests/test_m_linkages.py`; machine-readable report `outputs/manual_linkage_cases.json` in JSON-only `retail-initial-audit` workflow artifact.
- **Source integrity:** Case 008's reversible candidate view has **1,044,848 lines**; complete original-row provenance includes **1,067,371** rows and **22,523** source-duplicate links. The Case 011 totals **independently matched Case 010** (`agrees_with_case_010: true`).
- **Privacy:** no customer IDs, matched customer-specific pair table, private customer records, or raw workbook are exported in this report. Some invoice identifiers and source row locations are used for small audit case examples.
- **Original dataset is untouched.** Case 009 revenue scenario definitions and Case 008 candidate-view rules are **unchanged and unapproved**.

## Population

| Reconciled source-observed cohort | Count/amount |
| --- | ---: |
| Positive-priced, positive-quantity non-C `M` lines | **861** |
| Gross positive `M` line amount (not certified revenue) | **£339,629.94** |
| These positive `M` lines with a customer ID | **691** |
| Negative-quantity, positive-price C-prefixed `M` lines | **534** |
| C-prefixed `M` negative signed-amount magnitude (not verified refunds) | **£422,939.08** |
| C-prefixed negative `M` lines with a customer ID | **398** |
| Top 12 positive `M` lines, fraction of total positive `M` amount | **35.36%** |

The positive and cancellation-coded negative totals should **not** be netted together mechanically: they may represent different underlying reasons, different periods or incomplete source information.

## Strict candidate linkage — not a verified refund

A pairing is permitted **only** if both source lines have exact stock code `M`, nonmissing **identical** customer ID, country, absolute quantity and original numeric unit price; the positive line must have non-C invoice ID and positive quantity/price; the negative line must be C-prefixed with negative quantity and positive price; the negative entry's timestamp must be **on or after** the positive entry's timestamp and within the chosen window.

| Observed linkage statistic | Within 90 days | Within 365 days |
| --- | ---: | ---: |
| Matching positive / C-negative line-pair comparisons | **80** | **80** |
| Distinct positive `M` lines with one or more candidates | **71** | **71** |
| Distinct negative C-prefixed `M` lines with one or more candidates | **66** | **66** |
| Positive lines with exactly one possible negative match | 65 | 65 |
| Negative C lines with exactly one possible positive match | 55 | 55 |
| **Reciprocal one-to-one candidate pairs** (neither end has competing candidate) | **51** | **51** |
| C-negative lines lacking a qualifying earlier positive candidate | **468** | **468** |
| Positive lines lacking a qualifying later C-negative candidate | **790** | **790** |

**Interpretation:** Some lines have credible *candidate* partners by recorded attributes, but even **51 reciprocal one-to-one pairs are not independently confirmed reversals or refunded transactions**. Eighty pairs are not eighty independently established events; some lines have multiple possible partners. The remaining lines are "unmatched under these strict rules," **not** proven unrelated. Extending the lookback from 90 to 365 days did not create additional matches under the chosen criteria.

## Case evidence: the largest positive M lines

All of the following examples are **standalone single-line invoices** on the original source rows indicated; every listed line has quantity +1 and stock code `M`. This table intentionally omits customer identifiers.

| Positive invoice | Time | Positive M line amount | Customer ID recorded? | Qualifying *later* C-negative candidate in 90 days? |
| --- | --- | ---: | --- | --- |
| `512771` | Jun 17, 2010 16:53 | **£25,111.09** | No | No |
| `502263` | Mar 23, 2010 15:22 | £10,953.50 | Yes | Yes (one) |
| `502265` | Mar 23, 2010 15:28 | £10,953.50 | No | No |
| `522796` | Sep 16, 2010 15:12 | £10,468.80 | No | No |
| `524159` | Sep 27, 2010 16:12 | £10,468.80 | Yes | Yes (one) |
| `525399` | Oct 5, 2010 11:49 | £10,468.80 | No | No |

These are the six largest *positive* M line amounts in the report, **not evidence that these were merchandise sales**.

### A striking time-ordering counterexample

- **`C512770`** at **June 17, 2010 16:52** records quantity -1, unit price **£25,111.09**, stock code M, and **customer ID present**.
- **`512771`** at **16:53**, just **one minute later**, records quantity +1, unit price **£25,111.09**, stock code M, and **customer ID missing**.
- Each is a complete one-line invoice. The negative entry **precedes** the positive entry and their customer-ID availability differs. They therefore **do not** satisfy our strict matching criteria.
- Their temporal/amount proximity is **consistent with**, but does **not prove**, re-posting/correction or another operational process. Neither entry is verified as a real refund or confirmed completed sale.

### Another interesting local sequence

On **March 23, 2010**, source examples include these separate one-line M invoices:

| Timestamp | Invoice | Signed quantity | Unit price |
| --- | --- | ---: | ---: |
| 15:20 | `C502262` | -1 | £10,953.50 |
| 15:22 | `502263` | +1 | £10,953.50 |
| 15:24 | `C502264` | -1 | £10,953.50 |
| 15:28 | `502265` | +1 | £10,953.50 |

The customer-ID presence differs across entries, and the strict matcher counts only pairs meeting its *actual source attributes and time order*. This apparent negative-positive-negative-positive pattern is a **clue for manual source-order review**, **not** proof of two transactions, two reversals, or repeated duplicate posting.

### Large negative-coded example

- C-prefixed invoice `C556445` on **June 10, 2011 at 15:31** records a negative `M` line with amount magnitude **£38,970**. No earlier positive `M` line meets all the strict matching fields within the 90/365-day windows. This is not proof that its original event is absent from the retailer's complete financial records.

## Findings and guardrails

1. Manual `M` is heterogeneous: small and large positive entries, cancellation-coded negatives, anonymous lines, and entries embedded in otherwise standard invoices. **No blanket rule to remove M is justified.**
2. **51 reciprocal one-to-one candidate matches** exist under stringent field and time rules, but the dataset cannot certify actual refunds or event identities.
3. A substantial share of large, operational-looking entries has **no qualifying strict match**, sometimes because the cancellation appears **before** a nearby positive entry or the customer ID is missing.
4. Nearby equal amounts, invoice adjacency and shared timestamps are **not sufficient** on their own to infer links, financial effect or wrongdoing.
5. The UCI dataset lacks accounting ledgers, event-reversal IDs, staff context, settlement records and original business rules; matching is necessarily provisional.

## Decisions and next tests

- **D034:** Keep `M` as an **ambiguous manual-coded cohort**; do not adopt S2's blanket exclusion as finalized merchandise revenue, and do not automatically accept S0's inclusion as certified revenue.
- **D035:** Keep "candidate C-negative linkage" explicitly distinct from verified reversal/refund; preserve unmatched and ambiguous counts in analysis.
- **D036:** Keep all row-level evidence and source worksheet/Excel-row provenance private and unchanged; publish only this case summary and bounded contextual examples.
- **R011a (next):** Test **bidirectional close-time M sequences** as a separate descriptive category, especially C-negative **before** positive M entries with matching price and quantity. Report counts as timing patterns, without inferring a reversal.
- **R011b:** Examine whether high-value `M` lines with missing customer IDs represent operational corrections, anonymous charges or other processes. The current dataset alone may never conclusively resolve this.
- **R011c:** Continue auditing zero-priced positive lines and negative unit prices before defining final merchandise KPIs and visual dashboards.
