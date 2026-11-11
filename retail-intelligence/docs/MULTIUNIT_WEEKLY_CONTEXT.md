# Investigation 017 — The Multi-Unit Mystery: paid / £0 quantities and same-week comparison

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Script and six synthetic tests committed; **full original-source results pending GitHub Actions verification**. No business/financial rule has changed.

## Question

Does an equal-quantity multi-unit pattern (e.g. **8 units positively priced plus 8 units at £0**, or **12 + 12**) recur across invoices for the same SKU within narrow time periods? Compared with *all paid invoice-SKU occurrences of that product in the same week*, are zero/paid combinations conspicuous? Could this be consistent with a BOGO-like campaign, or might it reflect operational recording conventions?

## Previously verified facts

- Case 015: 43 zero-priced line comparisons have a paid same-SKU counterpart on the same invoice; 10 comparisons have equal **line quantities**, while others have very unequal quantities.
- Case 016: 43 invoice-SKU groups across 33 invoice IDs and 32 SKUs; five groups have exactly one paid unit + one £0 unit, **none recurring on distinct invoices of the same SKU**.
- Five SKUs have any paid/£0 pattern on more than one invoice; two recur in rolling seven-day windows. The source **does not** identify promotions, shipments or reasons.

## New analysis and safeguards

- **Code:** `scripts/investigate_multiunit_weekly_context.py`; tests `tests/test_multiunit_weekly_context.py` (six new synthetic-data test cases).
- **Reproduction:** after Case 016, run `python scripts/investigate_multiunit_weekly_context.py` from `retail-intelligence/`. Output: ignored `outputs/multiunit_weekly_context.json` and JSON-only GitHub Actions artifact.
- Use the unchanged Case 008 reversible candidate view built from the original UCI workbook; preserve all original-row provenance.
- Group **non-C positive-quantity lines** by exact invoice ID and stock code. Separate £0 lines from positive-priced lines; do not infer returns or customer identity.
- Define `equal_total_quantity`: the **sum** of all positive £0 quantities equals the sum of positively priced quantities within an invoice+SKU group. This can hold across multiple lines and does **not** prove a gift or 1:1 unit linkage.
- Define `multiunit_equal`: equal total quantities, each strictly greater than **one unit**.
- Keep `strict_one_plus_one` separate: one £0 line with one unit and one paid line with one unit.
- For each SKU, report how many invoice-SKU groups exhibit multiunit equality and whether **multiple distinct invoices** with that shape occur within *rolling* 7- or 30-day intervals.
- For products with any paired group, compare qualifying invoice-SKU groups against **paid-only** invoice-SKU groups in the **same fixed Monday–Sunday calendar week**, using the recorded paid-side invoice time. A fixed calendar week is not a rolling seven-day window.
- Emit at most 15 SKU summaries and 15 calendar-week summaries. Ratios use paid invoice-SKU **groups**, not customers, individual unit counts, shipments, revenue, or experimental randomized controls.
- Assert consistency with Case 016: zero lines with same-invoice paid counterpart, total paired invoice-SKU groups, strict 1+1 group count and SKU count. If counts disagree, fail rather than silently changing the definition.
- Preserve no-source-row-export / no-customer-ID-export safeguards; no full invoice tables or derived row-level files are published.

## How to interpret (before seeing source results)

**Potential support for a campaign hypothesis:** the same product repeatedly shows equal multi-unit £0/paid quantities across *distinct invoices* in a short window; the ratio of paired groups to all paid invoice-SKU groups is larger inside that window than outside it, with sufficient denominator and ideally external promotion evidence.

**Counterexamples or alternatives:** zero-to-paid quantities vary greatly, pairs are dominated by one unusual invoice, the SKU also has many routine paid-only transactions, or similar patterns persist over a long time. Even repeated equal units could be bundles, stock corrections, repricing, invoice conventions or another promotion format.

**Important limitations:** observational clustering is **not** a randomized causal control or verified promotion; week selection after observing peaks introduces selection bias. No rule can assign free-unit monetary value from the source alone. Sparse counts cannot support a confident general conclusion.

## Pending steps

1. Verify that GitHub Actions passes all tests and the original-source analysis, including Case 016 reconciliation.
2. Interpret the actual SKU/week cohorts, noting denominator sizes and concentration in the same invoice.
3. Only if compelling, pursue an independent promotion/price-list record to confirm business meaning; otherwise leave the category **uncertain**.
4. Continue toward provisional KPI definitions and decision-focused SQL analysis without endlessly expanding anomalies.

**Decision D054 (investigation stage):** test the multi-unit BOGO hypothesis while holding operational correction as a competing explanation; preserve the unchanged original workbook, reversible candidate view, every source-to-canonical link, and financial scenario definitions.
