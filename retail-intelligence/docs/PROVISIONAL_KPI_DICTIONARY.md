# Provisional KPI Semantic Dictionary — Project 003

**Status:** Proposed analytical *descriptions*, not accepted revenue/accounting policy. Read-only exploratory definitions. No original row edits, Case 008 provenance policy change, or financial-statement claim.

**Evidence:** [Case 008 reversible source layer](REVERSIBLE_ANALYSIS_LAYER.md), [Case 009 scenario sensitivity](REVENUE_SCENARIOS.md), [Cases 010–016 investigations](RESEARCH_QUESTIONS.md). The source is the UCI Online Retail II workbook (SHA-256 \`bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980\`). Case 017's multi-unit promotion hypothesis is **separate** from this proposed dictionary; no promotion classification is assumed.

## Unit of observation and grain

- **Raw source grain:** an original worksheet line; invoice number is **not** unique on every row.
- **Reversible candidate grain:** a source-observed line represented once after 22,523 *exact cross-sheet publication copies* are linked to retained counterparts. Within-sheet duplicates are **not deleted**.
- **Invoice ID:** distinct invoice-number string in the candidate view, *not* a verified order, customer, shipment, payment, sale, or commercial event.
- **Customer ID:** an optional identifier; NULL is **unknown**, not a new customer and not evidence that several rows share one customer.
- **Amounts:** GBP-valued source \`quantity × unit_price\`, under strictly stated filters; **not** tax-adjusted, settled, recognized revenue, gross margin, or a verified refund.
- **Date:** recorded invoice date; coverage and seasonality must be examined before interpreting month-over-month change.

## Exhaustive mutually exclusive provisional row cohorts (Case 009 verified)

Apply the following precedence **in order** to the Case 008 candidate view. The names are *labels for source shapes*, not causal classifications.

| Priority | Provisional line label | Rule | Verified candidate lines | Allowed meaning |
| ---: | --- | --- | ---: | --- |
| 1 | \`cancellation_coded\` | Invoice number begins with \`C\` (case-insensitive) | **19,165** | UCI cancellation-code indicator, not a confirmed cash refund |
| 2 | \`negative_quantity_zero_price_unknown_customer\` | Non-C, quantity < 0, price = 0, customer ID missing | **3,393** | Unexplained negative quantity and £0 |
| 3 | \`non_c_negative_quantity_other\` | Other non-C quantity < 0 | **0** | Retain as separate unresolved bucket if new data appear |
| 4 | \`positive_quantity_negative_price\` | Non-C, quantity > 0, price < 0 | **5** | Source-labelled bad-debt-looking entries investigated separately; no ledger meaning guaranteed |
| 5 | \`positive_quantity_zero_price\` | Non-C, quantity > 0, price = 0 | **2,631** | Zero price, not necessarily a gift or promotional unit |
| 6 | \`named_shipping_billing_code_candidate\` | Non-C, qty > 0, price > 0, exact trimmed upper stock code in \`POST\`, \`DOT\`, \`C2\`, \`BANK CHARGES\`, \`AMAZONFEE\` | **3,570** | Named postage/carriage/fee candidate, not necessarily invalid revenue |
| 7 | \`manual_discount_code_candidate\` | Non-C, qty > 0, price > 0, exact code \`M\` or \`D\` | **866** | Uncertain accounting/billing role |
| 8 | \`other_positive_priced\` | Other non-C, qty > 0, price > 0 | **1,015,218** | Merchandise-**like** positive-priced line, no proof of fulfillment |
| 9 | \`unresolved_other\` | Everything else, including missing values | **0** | Never silently drop unexpected source types |
| | **All candidate-view lines** | | **1,044,848** | All lines accounted for |

The source-specific five negative-price rows are labelled \`A\`-prefixed invoice / \`B\` stock code / \`Adjust bad debt\`, but this observation does **not** authorize netting their signed total into any gross scenario. Likewise, neither BOGO-like nor operational adjustments can be confidently assigned from zero price alone.

## Scenario dictionary (experiment only)

All three scenarios require **non-C**, **positive quantity**, **positive unit price**. Neither cancellation-coded amounts nor zero/negative-price amounts are mechanically added or netted.

| Name | Included line labels | Candidate lines | Source-verified value | Interpretation limits |
| --- | --- | ---: | ---: | --- |
| **S0 — broad positive-priced gross amount** | \`other_positive_priced\` + \`named_shipping_billing_code_candidate\` + \`manual_discount_code_candidate\` | 1,019,654 | **£20,533,741.92** | Does not certify customer payments or recognized revenue |
| **S1 — without named postage/billing codes** | \`other_positive_priced\` + \`manual_discount_code_candidate\` | 1,016,084 | **£20,063,792.35** | Shipping fees may legitimately form part of business turnover |
| **S2 — merchandise-like restrictive scenario** | \`other_positive_priced\` | 1,015,218 | **£19,723,764.52** | Excluding \`M\` and \`D\` may omit legitimate items, not a correctness ranking |

Do **not** label S2 "actual net sales" or "verified retail revenue". Choosing S2 as a *workbench visualization default* must be disclosed with S0/S1 alternatives.

## Candidate business-analysis metrics and exact permitted names

| Output | Proposed formula | Use | Explicitly not |
| --- | --- | --- | --- |
| \`gross_merchandise_like_line_amount_s2_gbp\` | Sum of \`quantity × unit_price\` for \`other_positive_priced\` | Historical activity by recorded invoice month/country | Recognized revenue, cash collected, net sales or profit |
| \`gross_positive_line_amount_s0_gbp\` / \`s1_gbp\` | Analogous sums under S0/S1 above | Sensitivity display | Competing official accounting statements |
| \`s2_invoice_ids_with_any_qualifying_line\` | Count distinct invoice IDs containing ≥1 S2 line | Descriptive invoice-ID activity | Verified completed orders |
| \`s2_positive_units_recorded\` | Sum positive quantities on S2 lines | Descriptive recorded unit-volume | Units actually shipped |
| \`s2_gross_amount_per_qualifying_invoice_id\` | S2 gross line amount ÷ distinct invoice IDs with ≥1 S2 line | Descriptive amount per qualifying invoice identifier | Certified average order value or average customer spend |
| \`s2_known_customer_id_line_share\` | Share of S2 lines having non-null customer ID | Coverage and segment reliability | Unique customer conversion or loyalty |
| \`source_cancellation_coded_lines\` | Count cohort 1, separately | Data-quality/context panel | Number/value of paid refunds |
| \`source_zero_price_lines\` | Count cohort 5, separately, optionally mixed vs isolated invoice | Exception monitoring | Product giveaways or lost sales |
| \`unresolved_other_line_count\` | Count cohort 9 | Quality gate | Automatic cleanup target |

## Analysis gating and milestones

1. Use SQL to **reproduce the full cohort counts and S0/S1/S2 aggregates** before building any month/country chart. A new implementation that disagrees with Case 009 must fail validation; do not conceal discrepancies with rounding or filtering.
2. Compare recorded months/years with source coverage; no marketing/customer growth conclusions without controlling for observation windows.
3. Profile high-value wholesale-like invoices and missing customer IDs before using averages or interpreting geography.
4. Keep both invoice count **and** line count visible and disclose selection bias. S2 still has heterogeneous descriptions and unknown settlement state.
5. Build Power BI only after the exploratory SQL outputs reconcile, with scenario sensitivity and cautions shown directly.

**Decision (proposed, not adopted):** Segment rows descriptively and build a reversible, documented **SQL workbench**. The report remains an exploratory portfolio investigation; no bookkeeper-approved revenue or customer-order policy is implied.
