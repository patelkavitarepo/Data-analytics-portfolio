# Case 020 — Invoice concentration: full-source verified results

**Project:** 003 Retail Intelligence  
**Status:** **Verified against the original UCI workbook, 110 synthetic tests passed.** The results are descriptive gross-positive line amount sensitivity, **not** recognized revenue, a causal growth estimate, or evidence of invalid invoices.

## Original-source evidence

- [Successful GitHub Actions run #42945421106](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106), original-source audit success; **110 tests passed**.
- Aggregate evidence: `outputs/invoice_concentration.json` from GitHub Actions `retail-initial-audit` artifact; source workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- Code: `scripts/analyze_invoice_concentration.py`; tests: `tests/test_invoice_concentration.py`.
- Every source row remains accounted for: **1,067,371 raw lines**, **22,523** exact cross-year source-copy links, **1,044,848 candidate lines**; **1,015,218 S2 positive-priced merchandise-like candidate lines** reconciled with independently verified Case 018 SQL.
- Invoice-ID-month group sums, monthly gross amounts, line count and full S2 amount reconcile with Case 018. No source data, provenance or KPI filters were changed.

## Comparable Jan–Nov period findings

| Metric | Jan–Nov 2010 | Jan–Nov 2011 |
| --- | ---: | ---: |
| S2 gross positive-priced line amount (**not revenue**) | **£8,639,086.69** | **£8,889,734.02** |
| Qualifying invoice-ID-month groups (not confirmed orders) | **18,122** | **17,410** |
| Highest 1% of invoice-ID-month groups, rounded up | **182** | **175** |
| S2 gross line amount attributable to that upper 1% | **£1,387,672.65** | **£1,582,417.16** |
| Share attributable to upper 1% | **16.06%** | **17.80%** |
| S2 gross amount from remaining groups, **sensitivity only** | **£7,251,414.04** | **£7,307,316.86** |
| Median S2 gross line amount per invoice-ID-month | **£300.58** | **£304.24** |
| 95th-percentile invoice-ID-month gross amount | **£1,384.68** | **£1,493.66** |
| Largest single invoice-ID-month gross amount | **£49,844.99** | **£77,183.60** |

The full period S2 gross change is **+£250,647.33 (+2.90%)**. With the largest one percent of invoice-ID-month groups **omitted independently within each year for a sensitivity exercise**, the remaining amount changes by **+£55,902.82 (+0.77%)**.

The *difference between the upper-one-percent groups' amounts across years* is **£194,744.51**, equivalent arithmetically to **77.7% of the untrimmed £250,647.33 cross-period difference**. But the two sets include **different invoices and different counts (182 vs 175)**. This is **not a causal attribution of business growth to those invoices**, and the top groups were selected after seeing the outcomes.

## One-month concentration examples (observed, not an experimental design)

- **January 2011:** 11 largest qualifying invoice-ID-month groups account for **26.12%** of that month's S2 amount (11 of 1,081 qualifying invoice-ID-month groups). The single largest group is **£77,183.60**, about **11.49%** of the month's S2 total.
- **January 2010:** 11 of 1,089 qualifying groups account for **21.36%**; the month's maximum is **£44,051.60**, about **7.07%** of the monthly S2 amount.
- **November 2010:** the highest 28 groups account for **20.90%**; **November 2011:** the highest 28 account for **18.54%**. Concentration is **not uniformly higher in 2011 in every month**.
- **December 2011**, incomplete (source stops December 9), has exceptional concentration, but should **not** enter like-for-like full-month comparisons. It remains a cautionary boundary example, not evidence of seasonal shifts.

## Interpretation and business recommendation

1. **Observed:** The upper 1% of invoice-ID-month groups contribute a **larger** share of the illustrative S2 gross amount in the comparable 2011 period than in 2010 (**17.80% vs 16.06%**).
2. **Observed:** Omitting extreme invoice-ID-month groups reduces the headline descriptive gross change from **2.90% to 0.77%**. This substantially weakens an unsupported claim that the business broadly increased across routine purchases.
3. **Observed:** The median per invoice-ID-month increases **£300.58 → £304.24** (about **1.22%**), far less dramatically than the top outliers' magnitudes. The 95th percentile increases as well, so more than one feature of the distribution changed.
4. **Not established:** Customer demand growth, true retail revenue, profitability, operational errors, wholesale share, fraud, shipping, price inflation or completed order count.
5. **Limitations:** The source includes wholesale-like quantities, ambiguous accounting/fee lines, unknown payments/fulfilment, missing customer IDs and incomplete final-period coverage. Candidate S2 is explicitly **not accounting-approved**.

**Decision D058:** Present the 2.90% S2 change together with the **+0.77% upper-one-percent-omitted sensitivity** and disclose that the largest invoice-ID-month groups explain much of the arithmetic difference *between independently selected tails*, without inferring a cause. Keep all original observations. Do not remove outliers from any default view.

## Next: Case 021 — composition before causation

Test the relative contribution of **recorded quantity and effective gross amount per unit** and the distribution of SKU activity in 2010 versus 2011 comparable periods. An identity-based gross-value decomposition is permissible, but it must **not** be described as price inflation, product profitability, successful marketing, or verified customer spending. Separately retain the Case 020 concentration sensitivity. After that, focus on a concise decision-oriented report and dashboard design.

**No data deletion, source mutation, provenance change or approved financial KPI definition resulted from this investigation.**
