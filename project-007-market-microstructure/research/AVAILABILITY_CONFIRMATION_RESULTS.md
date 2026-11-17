# D015 — One-time confirmation results (frozen)

**Source:** authenticated Quant-Arena Public L1, Quant Arena / LaPlace's Eye / Einsia AI; CC BY-NC 4.0 noncommercial with attribution. [One-time GitHub Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43285307088) succeeded. Date manifest SHA256 `0a594c1d46a4e1b415b390ada8fe8db76ce5401d8b8d1c15d87d7750bbc92a14` was committed before reading new prices.

**Chronology:** original March 8–April 6, 2022 fitting reproduced at exactly 54,290 examples; July 13–August 9 label-free warmup; August 10–23 one-time confirmation; August 24–September 6 final SEALED and unscored. Previous D009/D012/D014 final blocks also unscored. No raw vendor rows, per-origin scores or prices committed; no trading fills or returns.

Each model/policy evaluated the same 30,690 confirmation source origins, of which 27,349 had verifiable future labels. 3,376 current-source observations were unavailable. Both quality-gated policies further abstained on 14,085 observations for failing the frozen ten-prior-day 50% source-health rule; 13,229 observations remained decision-capable. These statuses are not stationary predictions. Precision uses only future-verifiable alerts, not the all-source denominator.

| Original model | Policy | All-source alerts | Matched alerts | Correct | Wrong | Matched precision | Hypothetical +1/−4 units |
|---|---|---:|---:|---:|---:|---:|---:|
| Balanced | Static baseline | 126 | 126 | 11 | 115 | 8.73% | −449 |
| Balanced | Static + health | 79 | 79 | 5 | 74 | 6.33% | −291 |
| Balanced | Rolling + health | 164 | 161 | 13 | 148 | 8.07% | −579 |
| Unweighted | Static baseline | 126 | 126 | 12 | 114 | 9.52% | −444 |
| Unweighted | Static + health | 78 | 78 | 5 | 73 | 6.41% | −287 |
| Unweighted | Rolling + health | 176 | 174 | 16 | 158 | 9.20% | −616 |

All-source alert rates: balanced 0.411% static, 0.257% static+health, 0.534% rolling+health; unweighted 0.411%, 0.254%, 0.573%. All six rates below 2% does **not** demonstrate predictive reliability. Zero-alert reference utility is 0; every tested model/policy is worse under the specified illustrative loss. Quality gating suppresses both right and wrong alerts, and precision worsened relative to the corresponding static baseline. Rolling thresholds increased alert count and did not solve the false-direction problem. No model promoted.

**Important limitations and next review:** Ten confirmation days, correlated quote origins and stock heterogeneity prevent broad generalization. Source health is a proxy, not an economic alpha signal. These are historical classifications, not measured execution profits or investment returns. The preregistered protocol additionally requests stock/day analyses, recall, coverage, uncertainty and alternative illustrative loss sensitivities; these are not yet fully aggregated in this short report, so no claim is made that every protocol analysis is complete. Do not adjust thresholds on these dates or access any reserved final test. The next research task is an independent failure analysis of directional information content and feature/label construction, using only permitted already-observed aggregates or a separately preregistered fresh period.
