# Project 007 — D006: source quote gap / quality-flag sensitivity audit

**Date:** November 11, 2026. **Status:** preregistered, real-data diagnostic completed and independently verified; not a predictive experiment or a trading backtest. This report is AI-assisted analysis responding to the human lead's instruction: "Next challenge it is holmes." No causal interpretation was supplied by the human lead.

## Predeclared question and source

Does the previously observed three-stock stationary-heavy label distribution meaningfully change if we vary the maximum allowed adjacent quote-time gap, or deliberately relax quote-quality flags? The eight configurations, frozen study stock/days, target and criteria were recorded in [GAP_FLAG_SENSITIVITY_PROTOCOL.md](GAP_FLAG_SENSITIVITY_PROTOCOL.md) **before** the new live-data run.

- Source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), published by Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0**, strictly noncommercial research with attribution.
- Exchange/period: Shenzhen, January **4, 5, 6, 7, 10, 2022**; **15** stock-days in the same three previously accepted files: **000012.SZ**, **000025.SZ**, **000031.SZ**. This is NOT FI-2010's Helsinki/Nasdaq 2010 data, and no claim is made about its original publisher labels.
- Source immutable Git revision: `fa85d7b95e56e81317ac349f52e916ca482f0f68`. Per-stock Parquet SHA256 verified against pinned archive `SHA256SUMS`:
  - 000012.SZ: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`
  - 000025.SZ: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`
  - 000031.SZ: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`
- Approximately **70,447,590 HTTP range bytes** downloaded; **no full 6.23GB archive download or whole-archive hash verification**. Three member hashes were independently checked. Ephemeral source files destroyed after the run; no raw vendor quotes committed or uploaded.
- [Successful GitHub Actions empirical run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43110070553), and **105 synthetic tests passed** on Python 3.11 and 3.12. One-time data download job was removed after the successful run.
- Primary: **k=5** sampled quote midpoints; compare mean of next five with origin, thresholds at **±0.2%**; strict same-stock/date/quote validity. Missing, stale, locked/crossed/nonpositive quotes never imputed. Every analysis is retrospective label construction, **not prediction**.

## Baseline reproduced EXACTLY before comparing scenarios

| Stock | Source rows | Up | Stationary | Down | Unlabelled | Eligible | Stationary / eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 5,078 | 122 | 4,438 | 126 | 392 | 4,686 | 94.7076% |
| 000025.SZ | 5,077 | 58 | 4,267 | 39 | 713 | 4,364 | 97.7773% |
| 000031.SZ | 5,078 | 308 | 4,107 | 271 | 392 | 4,686 | 87.6440% |
| **Pooled / source-row-weighted** | **15,233** | **488** | **12,812** | **436** | **1,497** | **13,736** | **93.2732%** |

Frozen stock-level count tuples from the previous study were asserted exactly before any stress result was accepted. In the reference model, excluded origins split into **931 invalid/stale quote origins** and **566 origins without enough contiguous valid future quotes**. The original source sample and label values were not adjusted after observing new results.

## Result A — gap policy sensitivity, source flags respected

| Scenario | Adjacent gap tolerance | Eligible | Stationary | Stationary / eligible | Newly eligible | Newly excluded | Still eligible class changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| G15 | 15 seconds | 13,736 | 12,812 | 93.2732% | 0 | 0 | 0 |
| **G30** | **30 seconds, reference** | **13,736** | **12,812** | **93.2732%** | **0** | **0** | **0** |
| G60 | 60 seconds | 13,736 | 12,812 | 93.2732% | 0 | 0 | 0 |
| G120 | 120 seconds | 13,736 | 12,812 | 93.2732% | 0 | 0 | 0 |

Across **all three stocks**, every scenario had identical eligible origin indices, classes, forward-target indices and exclusion reasons compared with G30. The source showed **five consecutive within-stock/date timestamp gaps per stock longer than 120 seconds**, and the number of gaps greater than 15, 30, 60, and 120 seconds was identical for this sample. Changing tolerances therefore created **no label-level difference** in this specific sample/validation configuration. It does not prove gap handling is irrelevant in other datasets or sessions, and does not imply we can safely bridge missing trading time. These gaps do not explain the previously observed 10.13 percentage-point cross-stock stationary spread through a change in our tested gap cutoff.

## Result B — source quality-flag counterfactual, 30-second gap policy fixed

| Scenario | Source flag handling | Eligible | Stationary | Stationary / eligible | Newly eligible | Already eligible changed class |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **F0** | **Honor stale and missing-depth (reference)** | **13,736** | **12,812** | **93.2732%** | **0** | **0** |
| FD | Ignore missing-depth flag only | 13,736 | 12,812 | 93.2732% | 0 | 0 |
| FS | Ignore stale flag only | 14,357 | 13,410 | 93.4039% | **621** | 0 |
| FSD | Ignore stale and missing-depth flags | 14,357 | 13,410 | 93.4039% | **621** | 0 |

**Under the hypothetical FS/FSD only**, the 621 newly eligible targets are 598 stationary, 10 up, and 13 down, with **no previously eligible class altered**. The strict reference's 1,497 excluded observations become 876 under the counterfactual. This reflects a **4.52% increase in eligible-label count** (621/13,736), but only a **+0.1307 percentage-point** change in stationary percentage. These newly admitted labels are not necessarily valid market quotes or executable states.

By security, newly eligible labels from ignoring stale flags:

| Stock | Reference eligible | Counterfactual eligible | Additional targets | Reference stationary % | Counterfactual stationary % |
| --- | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 4,686 | 4,786 | +100 | 94.7076 | 94.6302 |
| 000025.SZ | 4,364 | 4,785 | +421 | 97.7773 | 97.8474 |
| 000031.SZ | 4,686 | 4,786 | +100 | 87.6440 | 87.7351 |

**Stock rank remained unchanged** in all eight scenarios: 000025.SZ (highest stationary share) > 000012.SZ > 000031.SZ. The much larger response in 000025.SZ underscores its distinct missing/stale-source pattern. This is a *diagnostic stress test*, **NOT** justification to ignore stale quotes in a real predictive model or execution simulation.

## Source quality overlap and selection effects

Among 15,233 source quotes the original source parser identified:
- **458** stale or missing-event-time flags (101 + 213 + 144).
- **66** missing-depth flags (4 + 55 + 7).
- **651** invalid/absent/locked/crossed/nonpositive top-of-book price observations (235 + 184 + 232).
- **15** source consecutive within-stock/day gaps greater than 120 seconds (5 per stock).

These source conditions **overlap** and must not be summed as unique missing rows. The mutually exclusive eight-way quality cross-tab separately confirmed every row accounted for. In this sample, all 66 source missing-depth flags co-occurred with invalid/absent best quotes, explaining why ignoring *only* that flag did not admit a valid price. There were **214 stale-flagged rows with otherwise valid top-of-book prices**, yet ignoring them yielded **621 additional classifiable origins** because one newly admitted quote may also restore several nearby *future-label windows*. This illustrates that missingness can have a **nonlocal effect** on rolling target eligibility, even when the best prices of previously eligible origins remain untouched.

The 15 observed gaps do not cause label changes when the tolerance is varied among the four preregistered values. The present aggregate audit does **not** identify the exact exchange event associated with each gap; it would be inappropriate to assert a specific cause (auction, lunch break, halt, feed error) from these counts alone.

## Independent verification

Every source row across eight scenarios was independently checked against a second, deliberately slower midpoint-label oracle: **15,233 × 8 = 121,864 full origin/target/exclusion comparisons**, **zero disagreements**. All comparisons hold the original source record identities fixed. The variation in eligible labels was separately counted as **newly eligible**, **newly excluded**, **class change among already eligible**, **future-index change among already eligible**, and **exclusion-reason change among still excluded**. All of the latter four categories remained **zero** for this panel and these scenarios.

This validation certifies agreement of the two implementations *conditional on the selected data and flag semantics*. It does not independently prove the publisher source quotes are current, complete or error-free, nor establish p-values from overlapping price labels.

## What we learned, and the next gate

- **Supported:** Our original stationary-heavy result and between-stock ranking are stable to the tested gap thresholds; ignoring stale flags increases label coverage but has little effect on the pooled stationary percentage. The original strict policy remains intact.
- **Not supported:** That gaps are inherently unimportant; that stale source observations are safe to use; that quality-flag changes are a cause of market behavior; that these results reveal tradable alpha, liquidity provision profit or live execution fill patterns.
- **Still unresolved:** FI-2010's original Helsinki per-stock/day source and publisher label boundaries. This independent Shenzhen 2022 experiment cannot resolve that different dataset's provenance question.

**Next research design, not yet run:** (i) an exploratory, *source-only* examination of gap-edge quality and stock/date clustering, or (ii) a **new preregistered chronological predictive-baseline study** with training-only feature construction and genuinely untouched future dates. A predictive score would still be separate from execution profitability. The source dates after January 10, 2022 remain reserved and untouched.
