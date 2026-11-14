# Investigation 017 — The Multi-Unit Mystery: source-verified paid/£0 comparisons

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** **Verified on the original UCI Online Retail II workbook.** No BOGO promotion, correction, refund, delivery or revenue classification is established.

## Question and analyst hypothesis

A classic buy-one-get-one campaign might appear as equal quantities of the same SKU positively priced and £0 on one invoice, with **the same pairing recurring across different invoice IDs during a short period**. Case 016 found no repeated *strict 1+1-unit* pairing for the same SKU. Does a broader multi-unit equal-quantity pattern (e.g., 8 paid + 8 £0) repeat, particularly during weeks when that SKU had other ordinary paid-only invoicing activity?

## Verification and source integrity

- **Official source:** UCI Online Retail II, original workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **GitHub Actions:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42940297437 — **completed success; 95 synthetic tests passed**, and original-source Case 017 analysis completed.
- **Source code:** `scripts/investigate_multiunit_weekly_context.py`; tests `tests/test_multiunit_weekly_context.py`.
- **Result:** `outputs/multiunit_weekly_context.json` in GitHub Actions `retail-initial-audit` summary artifact; only aggregates and bounded SKU/week context, no original row-level records or customer IDs.
- **Reference view:** 1,044,848 candidate lines after the 22,523 reversible cross-sheet copy links; all 1,067,371 source records remain accounted for in provenance.
- **Prior-case check:** `agrees_with_case_016_cohorts = true`. No source data, canonical links, scenario rules, or financial classifications were modified.

## Core findings

| Measure | Original-source verified value |
| --- | ---: |
| Non-C positive-quantity zero-price lines | **2,631** |
| Non-C positive-quantity positive-price lines | **1,019,654** |
| £0 lines with positively priced same-SKU neighbors on same invoice | **43** |
| Invoice+SKU groups with qualifying paid and zero-price lines | **43** |
| Distinct invoice IDs containing these groups | **33** |
| Distinct stock codes with any qualifying group | **32** |
| Strict one-paid-unit + one-zero-unit invoice+SKU groups | **5** |
| **Equal total paid and zero quantity**, any positive size | **10** |
| **Equal multi-unit quantities** (both sides > 1 unit) | **5** |
| Unequal total quantities | **33** |
| SKUs with multi-unit equal-quantity patterns on ≥2 distinct invoices | **0** |
| SKUs with multi-unit equal-quantity patterns within rolling seven days | **0** |

All **five** equal multi-unit groups occur on **different stock codes**, and none recurs for the same product on another invoice. The exact 1+1 structure and the multi-unit equality structures are disjoint in the observed source view. Thus **neither strict 1+1 nor multi-unit equal quantities show repeated same-SKU invoice evidence** consistent with a documented recurring BOGO mechanism, within these narrowly observed candidate groups.

**Caution:** This does not disprove promotions that use discount codes, sale prices rather than explicit £0 lines, other bundle ratios, or different recording conventions.

## Same-week denominator examples

Same-week comparison uses fixed calendar **Monday–Sunday** weeks of *paid invoice+SKU groups* (not physical deliveries, customers, verified orders, or campaign eligible populations). Ratios are descriptive and **not promotional redemption rates**. These observations were selected after viewing results.

| SKU | Week starting | Paid+£0 invoice+SKU groups | Paid-only groups same week | Total paid invoice+SKU groups | Equal multi-unit groups |
| --- | --- | ---: | ---: | ---: | ---: |
| `20724` | Jan 3, 2011 | **2** | **13** | **15** | 0 |
| `84016` | Apr 26, 2010 | **2** | **2** | **4** | 0 |
| `85042` | Dec 14, 2009 | **1** | **13** | **14** | **1** |
| `21143` | Dec 14, 2009 | **1** | **5** | **6** | **1** |
| `22043` | Nov 1, 2010 | **1** | **0** | **1** | **1** |
| `22044` | Nov 1, 2010 | **1** | **5** | **6** | **1** |
| `23407` | Nov 14, 2011 | **1** | **8** | **9** | **1** |

Note that a 100% observed pairing fraction for `22043` that week is **only 1 out of 1 qualifying paid invoice+SKU group**. One observation cannot prove a promotion. Conversely, `20724` and `84016` recur in a week, **but neither has equal total paid/£0 quantities**. Different grouping and denominator choices change impressions considerably.

## Interpretation

1. **Not verified:** BOGO, free goods, pricing corrections, stock adjustment, customer uptake, official campaign dates, product shipment, actual payments, realized refunds or accounting revenue.
2. **Weakening of narrow BOGO hypothesis:** The paid-plus-£0 same-SKU pattern exists, but repeated exact quantity parity for the **same** SKU across **different** invoice IDs is **not observed**. That is the strong differentiator between an isolated pattern and an apparent repeating deal.
3. **Separate hypothesis:** Stock code `84016` appears in six paid+£0 invoice groups yet never with equal recorded total quantities; some have extreme quantity imbalance. This warrants a separately preserved operational/billing-convention lead, not an automatic diagnosis.
4. **Methodological warning:** Small weekly denominators, selection of high-frequency weeks after seeing them, lack of promotion metadata, and wholesale-like orders prohibit attributing causation.

## Decisions and next milestone

- **D055:** Retain paid/£0 same-SKU pairs as **descriptive anomalies**. No automatic promotion, giveaway, adjustment, duplicate, return or cash-refund classification.
- **D056:** Record that repeated *strict* and *multi-unit* equal-quantity BOGO-like forms were not observed for the same SKU on multiple invoices. The evidence weakens that specific hypothesis only; do not convert an absence-of-evidence result into proof of no promotions.
- **D057:** Keep original workbook, reversible candidate view, complete provenance and S0/S1/S2 scenario definitions untouched.
- **R017a:** Optional independent merchant promotion calendar/price-list verification if available; not essential before analysis.
- **R017b:** Keep `84016` as a possible operational convention for later review, without holding the full project hostage to one unresolved SKU.
- **Next:** Begin Case 018 SQL cohort/scenario validation and monthly business performance work, with source-grain checks and transparent provisional definitions.

**Milestone conclusion:** The £0/paid pricing branch can be documented as **unresolved business semantics, descriptively investigated**. We have enough to begin exploratory business analytics without claiming every posting type has been explained.
