# Case 021 — Quantity vs. merchandise mix / observed amount per unit

**Project:** 003 Retail Intelligence  
**Status:** New read-only SKU composition diagnostic and five synthetic tests committed; original-UCI source verification **pending**. No causal or accounting conclusions are authorized.

## Why this follows Case 020

The verified Jan–Nov S2 amount increased **2.90%** from 2010 to 2011, but recorded units declined **6.00%**. Independent invoice concentration analysis found that the top one percent of invoice-ID-month groups increased from **16.06% to 17.80%** of S2 gross, and a sensitivity removing those groups lowers the illustrative gross difference to **+0.77%**.

Those facts require investigation of **composition and unit quantities**, not an unsupported inference that price increases or new demand caused a business improvement.

## Reproducibility

- **Read-only script:** `scripts/analyze_sku_composition.py`.
- **Synthetic guardrail tests:** `tests/test_sku_composition.py` (five test cases).
- Run after Case 008 has written its **ignored local** `data/derived/candidate_analysis_lines.csv.gz` and Case 018 has produced **source-verified** `outputs/sql_kpi_workbench.json`:

```bash
python scripts/analyze_sku_composition.py
python -m pytest -q
```

- Output: aggregate-only `outputs/sku_composition.json`, uploaded in the GitHub Actions `retail-initial-audit` artifact. **No customer ID, original invoice ID or row-level source table** is emitted.
- Same S2 definition as Case 009 and Case 018: exclude C-prefix invoices, nonpositive quantity, nonpositive price, and exact trimmed upper codes `POST`, `DOT`, `C2`, `BANK CHARGES`, `AMAZONFEE`, `M`, `D`.
- Select identical January–November calendar months in each of 2010 and 2011. Source date incompleteness outside the comparison remains a known limitation.
- Group by exact (trimmed uppercase) stock code, preserving missing codes as explicit `<missing_stock_code>` rather than silently excluding them.
- **Before interpreting**, reconcile both period's S2 gross line amount, summed recorded positive quantities and line count with independently source-reconciled Case 018 monthly SQL results.

## Four-component arithmetic identity

For each stock code present in *both* periods, let `u0` and `u1` denote recorded S2 positive unit quantities; `v0` and `v1` denote gross S2 positive line amounts; and `p0 = v0/u0` be the first year's **observed gross value per recorded unit**.

Then:

`v1 − v0 = (u1 − u0) × p0 + (v1 − u1 × p0)`

The first term is labelled **recorded-quantity component**. The second term is labelled **observed effective gross value per unit component**—a **residual accounting identity**, which can reflect within-SKU price dispersion, invoicing practices or code reuse rather than a formal price change.

Separately, stock codes observed **only in 2011** contribute their recorded gross S2 amount; codes observed **only in 2010** contribute the negative of their recorded gross S2 amount. The sum of all four terms must reproduce the Jan–Nov S2 gross line amount difference to 5p tolerance.

This is **not** a causal decomposition, consumer price index, hedonic price model, new-product adoption metric, margin report or wholesale sales classification. Stock code presence in one period is not a verified product launch or discontinuation.

## Interpretation guardrails

- Product mix can change across and within SKUs. Recorded units may refer to heterogeneous physical products or quantities.
- All amounts are **not recognized revenue**, payments, net sales or fulfilled orders.
- C-coded cancellations are not verified refunds and are not subtracted.
- This decomposition does not identify why the top one percent of invoice-ID-month groups changed; it complements Case 020's **separate** sensitivity.
- Unrecognized source semantics, incomplete customer IDs, coverage and unusually high wholesale-like quantities prevent strong causal labels.

## Next milestone

After **full original-source GitHub Actions verification**, use the observed component magnitudes and source-supplied stock-code examples to draft a concise executive summary and dashboard specification, with scenario sensitivity and invoice concentration presented alongside any SKU-bridge story.

**Decision (proposed):** Move from anomaly discovery to a transparent, qualified activity-and-composition explanation. **Do not change raw data, the Case 008 provenance map, or S0/S1/S2 rules.**
