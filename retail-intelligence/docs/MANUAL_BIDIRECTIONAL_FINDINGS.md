# Investigation 012 — Bidirectional short-time Manual sign-flip patterns

**Project:** 003 Retail Intelligence  
**Date:** November 10, 2026  
**Status:** Full-source descriptive analysis complete. **No pair is proven to represent a refund, correction or reversal.**

## Question

Are the close-time C-prefixed negative / non-C positive `M` ("Manual") patterns from Case 011 isolated cases, or do they recur across the entire overlap-reconciled dataset? Does the *recorded direction* of the negative/positive entries, invoice-number proximity and missing customer information help characterize the pattern?

## Source, code and reproducibility

- **Source:** UCI Online Retail II, original two-sheet workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Verified workflow:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42898160193 — **success**, 67 synthetic tests passed (48 warnings; none failed).
- **Script:** `scripts/investigate_m_bidirectional.py`; tests `tests/test_m_bidirectional.py`; reproducible invocation `python scripts/investigate_m_bidirectional.py` from `retail-intelligence/` after obtaining the UCI workbook.
- **Summary:** `outputs/manual_bidirectional_patterns.json` included in the GitHub Actions JSON-only `retail-initial-audit` artifact. **No raw workbook, customer IDs or row-level pairing table is published.**
- **Reference view:** Case 008 reversible candidate view with 1,044,848 source lines and 22,523 cross-sheet exact-copy links; provenance accounts for 1,067,371 original source rows. **Independent agreement with Case 011 passed.**
- **No changes** to original records, candidate-view filters, source overlap handling, gross line amount scenarios or refund assumptions.

## Pairing method and limitations

1. Positive-side eligible lines: exact stock code `M`, **non-C-prefixed** invoice, positive quantity, positive unit price (861 lines).
2. Negative-side eligible lines: exact stock code `M`, **C-prefixed** invoice, negative quantity, positive unit price (534 lines).
3. Pair comparison requires **same absolute quantity, original numeric unit price and country**; invoice IDs must differ. **Customer IDs are not required**, so we can characterize anonymous transactions rather than silently dropping them.
4. Compare recorded timestamps in *both directions*: **negative before positive**, **positive before negative**, and **same recorded minute**. Absolute time gap thresholds are 1, 5, 15 and 60 minutes.
5. Classify customer information: **known same**, **known different**, **one missing**, **both missing**. Known-different customer IDs are reported as lookalike pairs but **excluded from candidate-link counts**. Missing never implies equality.
6. Candidate pairs with **no known customer conflict** remain *hypotheses*. The `reciprocal_one_to_one` statistic means each line has only one available partner under the rule; it **does not** mean the underlying event is proven or uniquely identified in a financial ledger.
7. Negative and positive events can have many-to-many candidate pair comparisons. Pair counts **must not** be summed as independent physical transactions or money movements.

## Population-level results

| Window | All similar positive/C-negative pair comparisons | Known-different customer pairs excluded | No-known-conflict candidate comparisons | Reciprocal one-to-one candidates | Negative-first candidates | Positive-first candidates | Same-minute candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **1 minute** | 45 | 1 | **44** | 44 | 25 | 18 | 1 |
| **5 minutes** | 171 | 3 | **168** | 140 | **104** | **63** | 1 |
| **15 minutes** | 209 | 3 | **206** | 149 | **127** | **78** | 1 |
| **60 minutes** | 227 | 3 | **224** | 155 | **138** | **85** | 1 |

For the **5-minute window**:

- **78** pairs have **known matching** customer IDs.
- **78** pairs have customer information missing on one side.
- **12** pairs have both customer IDs missing.
- **3** pairs have different *known* customer IDs and are **not treated as candidate links**.
- Among 168 candidates without known conflict, **162 distinct positive lines** and **157 distinct negative lines** have at least one plausible partner. These are *distinct line counts*, not transaction or customer counts.
- **87 candidate comparisons** have adjacent invoice-number portions (`Cxxxxx` versus `xxxxx` differing by one); adjacency is contextual evidence only.
- **140 candidate comparisons are reciprocally unique under this 5-minute search**, but many include unknown customer information and remain unverified.

## An exploratory repeated-amount comparator, not a causal control

Among the 861 eligible positive `M` lines, **15** pairs of *positive-positive* lines from different invoice IDs have matching quantity, price and country within five minutes; **26** positive-positive pairs meet those criteria within fifteen minutes (44 distinct positive source lines participate).

The **171 sign-flip lookalike comparisons** in the five-minute window therefore outnumber the 15 positive-positive comparisons under this specific matching rule. However, the comparison mixes **861 positive versus 534 negative opportunities** and **positive-versus-positive opportunities** with different populations and business mechanisms; **it is not a causal test or error-rate estimate**. Do not infer that every sign-flip is a reversal or that staff intentionally reposted a transaction.

## Source examples (illustrative, not confirmed linkage)

| Negative M invoice | Positive M invoice | Negative timestamp | Positive timestamp | Magnitude of each line | Customer relationship |
| --- | --- | --- | --- | ---: | --- |
| `C512770` | `512771` | Jun 17, 2010 16:52 | Jun 17, 2010 16:53 | **£25,111.09** | One customer ID missing |
| `C502262` | `502263` | Mar 23, 2010 15:20 | Mar 23, 2010 15:22 | **£10,953.50** | Known same |
| `C502264` | `502265` | Mar 23, 2010 15:24 | Mar 23, 2010 15:28 | **£10,953.50** | One customer ID missing |
| `C525398` | `525399` | Oct 5, 2010 11:47 | Oct 5, 2010 11:49 | **£10,468.80** | One customer ID missing |
| `C496116` | `496115` | Jan 29, 2010 11:05 | Jan 29, 2010 11:04 | **£8,985.60** | Known same; positive first |
| `C520749` | `520750` | Aug 31, 2010 11:04 | Aug 31, 2010 11:04 | **£1,868.56** | Known same; same minute |

In the first example, the C-negative row **comes before** the positive row and the positive customer ID is missing. It was *correctly excluded* by Case 011's strict positive-first matcher. Its newly observed inclusion as a **weak timing-pattern candidate** is not a reversal determination or financial netting instruction.

## Interpretation / decisions

- **Observed:** Short-time bidirectional sign-flip patterns recur, often with negative C-prefixed entries preceding positive entries. This is a source recording pattern and a useful clue about workflow/data semantics.
- **Not established:** Why any two rows were recorded, whether either is a mistake, whether money moved, whether one reversed the other, or who entered them.
- **D037:** Preserve Case 011's **strict known-customer, positive-first** candidate matches separately from Case 012's broader **bidirectional temporal lookalikes**. They answer *different* questions and are not interchangeable.
- **D038:** Preserve uncertainty states, especially `one_missing` and `both_missing`. Do not impute customer identity or accept anonymous same-amount matches as uniquely linked events.
- **D039:** Do not modify source or cleaned-view policies or calculate financial net amounts from potential matches. The workbook and its provenance mapping stay unchanged.
- **Next:** investigate **positive zero-priced entries** (2,631 candidate lines) and **positive quantity with negative unit price** (5 candidate lines), then revisit final KPI definitions with explicit ambiguous categories.

## Limits

Recorded timestamps have only minute precision; same-minute pairs have unknown true order. Customer and event identifiers are missing for some lines, and no business ledger, settlement history or reversal reference is included. Nearby equal price and quantity are compatible with legitimate operations as well as clerical corrections. The analysis should never infer employee wrongdoing, theft, fraudulent refunds or actual business losses.
