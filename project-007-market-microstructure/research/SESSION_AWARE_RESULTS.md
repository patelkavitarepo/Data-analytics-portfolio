# Project 007 — D008 session-aware label construction: real-source audit

**Date:** November 11, 2026. **Result: PASSED — same-stock/date/session segmentation prevents all tested lunch-crossing targets, independently verified.** Human direction was "On to the next Holmes" following D007's lunchtime boundary investigation; all code, method choices and conclusions are AI-assisted, not attributed as human-authored scientific findings.

## Why this additional safeguard was needed

In D007, fifteen source gaps were each exactly **11:30:00–13:00:00 Asia/Shanghai (5,400 seconds)**, corresponding to the SZSE midday recess. Removing the maximum adjacent-quote gap had introduced **74** retrospective target labels that illegitimately mixed pre- and post-recess quotes even with valid quote-quality flags. A numeric 30-second rule prevented them, but a **separate explicit market-session invariant** was necessary before any predictive design. The new [SESSION_AWARE_PROTOCOL.md](SESSION_AWARE_PROTOCOL.md) was committed before this real-source check.

## Source, rights, unchanged sample

- Source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) (Quant Arena / LaPlace's Eye / Einsia AI), publicly hosted by `Ashitemaru` under **CC BY-NC 4.0, noncommercial research and attribution**. This is Shenzhen 2022, **NOT** the FI-2010 Helsinki 2010 benchmark.
- Same immutable publisher source revision: `fa85d7b95e56e81317ac349f52e916ca482f0f68`; publisher `SHA256SUMS` hashes and selected member checksums were reverified:
  - `000012.SZ.parquet`: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`.
  - `000025.SZ.parquet`: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`.
  - `000031.SZ.parquet`: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`.
- Same five observed dates per stock: **January 4, 5, 6, 7, 10, 2022**, **15,233** source quote observations in total; no later-date price columns accessed.
- Bounded byte-range data transfer: **70,447,590 bytes** to an ephemeral GitHub Actions runner; the complete ~6.23 GB TAR was not downloaded or hash-verified. Temporary per-stock source files were deleted; **no vendor prices or original quote rows committed or uploaded**.
- Source evidence: [real-data validation job](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43138003201). **121 synthetic tests passed** on Python 3.11 and 3.12; **30,466** real-source decisions were verified independently, with **zero mismatches**.

## Explicit session policy (fixed before the audit)

The separate `microstructure/session_labels.py` defines exchange-local operational session windows using timezone-aware **UTC+08:00** timestamps:
- **Morning:** 09:30:00 through 11:30:00 inclusive.
- **Afternoon:** 13:00:00 through 15:00:00 inclusive.
- **Outside these two windows:** no class label; origin recorded as `outside_session`.

The **14:57–15:00 closing call auction** occurs inside the operational *afternoon* group but has a different exchange execution mechanism, so this is a **source-label segmentation** policy, not a claim that all afternoon liquidity is homogeneous or continuously executable. The inclusive 11:30 and 13:00 endpoints accommodate the observed source rows and must not be mistaken for universal exchange event-processing rules.

All prediction *targets* still use the arithmetic **mean of the next five valid bid/ask midpoints** versus the origin midpoint, ±0.002 class threshold, strict source stale/missing-depth validity, positive uncrossed best quotes, and no crossing **stock, date, explicit session, invalid quote, or 30-second gap**. The old `microstructure/stockday_labels.py` was not modified, preserving every prior result.

## Source-verified results

| Stock | Source rows | Out-of-session source rows | Strict eligible | Stationary labels | Stationary / eligible | Changes to prior eligible classes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 5,078 | 303 | 4,686 | 4,438 | 94.7076% | **0** |
| 000025.SZ | 5,077 | 303 | 4,364 | 4,267 | 97.7773% | **0** |
| 000031.SZ | 5,078 | 303 | 4,686 | 4,107 | 87.6440% | **0** |
| **Total** | **15,233** | **909** | **13,736** | **12,812** | **93.2732%** | **0** |

At each source stock, the outside-session counts were **61, 61, 60, 61 and 60** across the five selected dates. They describe observations **outside the adopted regular-session windows**; exact original auction state was not separately authenticated. **All 909 were already excluded by the previous strict target algorithm**, so zero previously eligible labels became excluded or changed class, and zero previously excluded origins became eligible. Their exclusion **reason** changed from `invalid_or_stale_quote` to explicit `outside_session`. It would be incorrect to call these 909 extra rows newly discarded.

### Independent legacy and no-gap comparison

| Source-label policy | Eligible | Stationary | Unlabelled | Retrospective targets crossing lunch |
| --- | ---: | ---: | ---: | ---: |
| Previous source strict G30/F0 | 13,736 | 12,812 | 1,497 | 0 |
| **New explicit-session strict G30/F0** | **13,736** | **12,812** | **1,497** | **0** |
| **New explicit-session with unlimited gap (UNSAFE diagnostic)** | **13,736** | **12,812** | **1,497** | **0** |
| Previous non-session-aware unlimited-gap diagnostic (D007) | 13,810 | 12,873 | 1,423 | **74** |

**The crucial test:** With the new explicit session rule, even `max_gap_seconds=None` produced **zero** cross-lunch labels. The prior unlimited-gap implementation had made 74 false across-recess targets. The 30-second max-gap guard remains the registered *primary* policy, and unlimited-gap mode is **not** endorsed for future source data or execution.

The new source-aware optimized algorithm and a separate slower `session_oracle.py` agreed at **every row**, both under strict 30-second and unlimited-gap diagnostic policies: **15,233 × 2 = 30,466 decisions, zero discrepancies**. The independent check compares label category, exact future source-row indices, and exclusion reason. This shows code-path agreement conditional on the supplied quote data and declared schedule semantics; it does not prove that the source vendor's quotes are perfect or establish any return predictability.

## Conclusion and next gate

**Supported:** An explicit stock/date/session feature-label boundary is a robust independent safeguard against invented cross-lunch targets, even when a gap rule is inadvertently disabled. The source-verified implementation preserved all valid baseline classes and recognized 909 previously excluded off-window source observations more transparently.

**Not established:** That every out-of-window source quote is erroneous (some could be auction observations); that afternoon closing call auction observations behave like continuous trading; that the original Finnish FI-2010 labels were correctly session-partitioned; or that these historical data contain a profitable signal.

**Next design (NOT executed):** [CHRONOLOGICAL_PREDICTION_PROTOCOL.md](CHRONOLOGICAL_PREDICTION_PROTOCOL.md) proposes a new later-date 20 training / 5 validation / 10 sealed holdout structure and the simplest training-only baselines, with session-local, past-only features. Dates after January 10, 2022 are **not opened as price/label training or evaluation data**, no model was fit or scored, and no PR was merged. Source rights remain noncommercial CC BY-NC 4.0.
