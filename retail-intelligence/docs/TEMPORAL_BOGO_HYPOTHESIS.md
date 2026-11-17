# Investigation 016 — Timed BOGO hypothesis: source-verified recurrence

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** **Original UCI workbook audit complete and verified**. Repeated paid-plus-£0 patterns exist, but a recurring *strict one-paid-unit + one-zero-unit* BOGO-like shape is **not observed** across multiple invoices. **No promotion, correction, or financial classification established.**

## Analyst's hypothesis

If the same stock code appears with a positively priced line and a £0 line on the *same invoice*, and the same combination occurs on **different invoice IDs during a narrow period**, the retailer **might** have had a BOGO campaign. A stronger signature would show one paid unit plus one zero-price unit for the same SKU, repeatedly and temporally concentrated.

Alternative explanations include merchandise repricing, stock movements, bookkeeping/billing conventions, invoice data issues, or other discounting arrangements.

## Original-source verification

- **Official source:** UCI Online Retail II (dataset 502), source workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **GitHub Actions source audit:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42937165126 — **completed successfully, 89 synthetic tests passed**; Case 016 analyzed the original workbook and uploaded its JSON summary.
- **Source code:** `scripts/investigate_temporal_zero_paid_sku.py`; tests `tests/test_temporal_zero_paid_sku.py`; result `outputs/temporal_zero_paid_sku.json` in GitHub Actions `retail-initial-audit` artifact (JSON aggregate summaries, no customer IDs or raw workbook).
- **Source view:** 1,044,848 candidate records after 22,523 exact cross-sheet source-copy links; complete provenance for 1,067,371 original worksheet rows.
- **Independent cross-case agreement:** `agrees_with_case_015_counts = true`.
- **No modifications:** All source records, canonical overlap links, KPI S0/S1/S2 scenarios and refund/financial assumptions remain intact.

## Verified population counts

| Measure | Value |
| --- | ---: |
| Non-C, positive-quantity zero-price lines | **2,631** |
| Non-C, positive-quantity positive-price lines | **1,019,654** |
| £0 lines paired with a positively priced **same-SKU line on same invoice** | **43** |
| Distinct invoice IDs with qualifying same-SKU paid/zero patterns | **33** |
| Invoice+SKU groups with qualifying patterns | **43** |
| Distinct stock codes exhibiting any same-invoice paid/£0 combination | **32** |
| Invoice+SKU groups with exactly **one zero-price unit and one positively priced unit**, each on its own line | **5** |
| Stock codes exhibiting qualifying combinations on **two or more distinct invoices** | **5** |
| Stock codes with qualifying invoices at most **7 days** apart | **2** |
| Stock codes with qualifying invoices at most **30 days** apart | **4** |

**Important:** All five repeating stock codes have **zero** strictly one-unit + one-unit groups. Consequently the five strictly 1+1 groups **do not recur for any single SKU on distinct invoices** under this method. This weakens the specific repeated literal BOGO signature, but is not evidence that no promotion ever occurred.

## Five SKU codes repeated across different invoices

| SKU | Qualifying invoice IDs | All paid invoice+SKU groups across complete observation | Strict 1+1 groups | Within-7-day invoice pair comparisons | Max qualifying invoices within any 7-day window | First / last qualifying invoice dates |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `20724` | **4** | 2,035 | 0 | 3 | 3 | Nov 19, 2010 / Jan 11, 2011 |
| `84016` | **6** | 62 | 0 | 1 | 2 | Mar 24, 2010 / Jun 24, 2010 |
| `22356` | **2** | 1,584 | 0 | 0 | 1 | Nov 19 / Dec 14, 2010 |
| `22423` | **2** | 3,918 | 0 | 0 | 1 | Jun 24, 2010 / Jan 11, 2011 |
| `22652` | **2** | 830 | 0 | 0 | 1 | Nov 30 / Dec 21, 2010 |

The denominators are **all paid invoice+SKU occurrences over the full date range**, not same-window rates, eligible promotions, unique customers, or validated items shipped. Do not use them to calculate a causal promotion prevalence estimate or compare the SKUs as if they were matched control populations.

Additional time-window context:
- `20724` has three pair comparisons within seven days, with at most **3** qualifying invoice+SKU groups in a seven-day window.
- `84016` has six pairs of invoice groups within 30 days (and one pair within seven days), with at most **4** qualifying invoice+SKU groups in a 30-day window.
- `22356` and `22652` each have one pair of qualifying invoices within 30 days, but none within seven days.
- `22423` has two qualifying invoices many months apart; no 30-day pair.

**Pair-comparison counts are not counts of promotions, free items, independent retail events, or invoice IDs.**

## Interpretation

1. **Observed:** A small group of stock codes exhibits repeat £0-plus-paid invoice/SKU groups. In particular, `84016` recurs with very unequal quantities in selected Case 015 source examples (e.g. 10,200 £0 units versus one positively priced line), making it a poor candidate for a *literal* one-free-unit/one-paid-unit promotion.
2. **Observed:** Exactly five invoice/SKU groups have a literal unit 1+1 shape, but none is on one of the five repeatedly qualifying SKUs. There is **no demonstrated repeat literal 1+1 BOGO pattern** for the same product on distinct invoices in this source view.
3. **Not tested sufficiently:** Equal-quantity multi-unit BOGO shapes (e.g. 8 paid and 8 £0), date-specific *paid-only* comparison frequencies, other sales discounts or promotions not expressed as £0 lines, and whether product descriptions imply a different inventory/billing convention. Lack of evidence here is not proof that no promotion happened.
4. **Not established:** Actual advertising or campaign dates, customer redemption, deliveries, refunds, bookkeeping causes, recognized revenue, theft, error or actual losses.

## Decisions and next steps

- **D051:** Preserve the analyst's BOGO hypothesis but classify it as **not supported by recurring strict 1+1 line evidence**. Do **not** mark it impossible, because this analysis excludes alternative promotion quantities/mechanics and lacks independent promotion records.
- **D052:** Treat recurrent paid/£0 products as **anomaly clusters** requiring context, not automatically promotional items or operational adjustments.
- **D053:** Preserve full source rows, reversible cross-sheet provenance, unknown-customer states and S0/S1/S2 scenario rules unchanged.
- **R016a:** Examine **equal-total-quantity** zero-price and paid same-SKU pairs, including multi-unit 8+8 and 12+12 patterns, across different invoices; no assumption that equal quantity implies BOGO.
- **R016b:** For top recurring SKUs, compare paired-invoice share versus paid-only invoice/SKU groups **within the same fixed 7-day periods**, rather than using lifetime paid counts, and record sample sizes without presenting causal tests.
- **R016c:** Investigate particularly unusual `84016` quantity/price conventions separately; its presence in the recurrence table is not evidence of promotion.
- **R016d:** Consider source-provided promotion/price-list records or independent merchant evidence if ever available, to validate business meanings before dashboard labels.

**No source records changed and no business classifications were finalized.**
