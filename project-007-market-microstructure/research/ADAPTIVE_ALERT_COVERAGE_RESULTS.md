# Project 007 — D014 adaptive-alert attempt: FAIL-CLOSED coverage result

**Source-authenticated November 12, 2026. D014's preregistered full-panel model/policy comparison was NOT completed.** This is a negative source-feasibility finding, not evidence that adaptive thresholds help or fail at predicting direction. The attached [postmortem protocol](ADAPTIVE_ALERT_COVERAGE_POSTMORTEM_PROTOCOL.md) explicitly followed the first failed attempt; it must not be presented as pre-price registration for the original D014 evaluation.

## Executive outcome

The [first D014 model-run attempt](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43275799910) failed closed before fitting, scoring or comparing the two original D012 models. A complete observed trading date for stock **000025.SZ** had no decision-ready current/past quote snapshots under the unchanged five-level-book and five-prior-contiguous-quote requirements.

A separate one-time, publisher-hash-authenticated, **NO FUTURE LABELS** source audit [run 43277130722](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43277130722) isolated the issue: **two** of 000025.SZ's **20 newly frozen warmup dates** had **zero decision-ready observations** despite 1,022–1,023 source rows:

| Date (2022) | Source rows | Valid complete five-level book | Past-five valid quotes | Joint decision-ready | Source missing-depth flag not healthy | Source stale flag not healthy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| May 30 | 1,022 | 0 | 0 | **0** | 971 | 15 |
| June 2 | 1,023 | 3 | 0 | **0** | 948 | 15 |

Flags can overlap and do not explain every rejected record; no trading suspension or market-level cause has been independently established. The counts describe the pinned vendor source, not independently reconstructed exchange event flow.

The rolling policy's frozen rule requires each of the immediately prior ten **complete observed common trading days** to supply at least one eligible score. There is **no legitimate ten-day score window** crossing these two missing 000025.SZ dates. No after-the-fact stock/date removal, source-gap imputation, window shortening, baseline substitution, threshold change or model retuning was permitted.

## Source-coverage unevenness extends beyond two days

| Stock | Warmup source rows | Warmup decision-ready | Confirmation source rows | Confirmation decision-ready |
| --- | ---: | ---: | ---: | ---: |
| 000012.SZ | 20,456 | 18,765 | 10,229 | 9,390 |
| **000025.SZ** | **20,458** | **10,653** | **10,229** | **8,149** |
| 000031.SZ | 20,455 | 18,733 | 10,230 | 9,390 |

Additional **000025.SZ** dates with severely sparse decision-ready coverage: May 25 **25/1,023**, May 27 **2/1,023**, May 31 **14/1,023**, June 1 **11/1,023**, June 8 **49/1,023**, and **June 15** (first confirmation date) **58/1,023**. Source missing-depth flags were high on these dates. Many other stock-days were well covered. The problem is concentrated in the source coverage of one security, not a reason to claim a universal data problem or verified exchange trading halt.

**Scientific implication:** timestamp-only source calendar membership is not equivalent to the availability of admissible contemporaneous order-book features. A statistically reasonable missing-data policy must be designed prospectively, and assessed for survivor/selection bias. We cannot simply select well-covered days after inspecting them and claim an independent validation.

## Integrity and provenance

- Original source is attributed [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) by Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0 noncommercial**. All three member SHA256s were reauthenticated against publisher SHA256SUMS at pinned revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`; complete 6.23 GB archive not downloaded.
- [D014 pre-price frozen design](ADAPTIVE_ALERT_PROTOCOL.md) and [source-authenticated timestamp-only 20/10/10 manifest](ADAPTIVE_ALERT_DATE_MANIFEST.json), SHA256 `953b173e4b0ba4b6968ce6113e8345c85e942dbe6b46b31ca722968a98f208c8`, were committed before first D014 market-price/depth experiment. Warmup **May 17–Jun 14**, confirmation **Jun 15–28**, final **Jun 29–Jul 12, 2022**.
- First source run **did read some confirmation future labels while assembling source rows** for earlier stock/date partitions, but failed before fitting either model or issuing any scores, alerts or comparative metrics. No confirmation label values were inspected or published as outcomes. The subsequent **separate coverage postmortem computed ZERO future target labels** on either warmup or confirmation; it inspected only source current/past quote validity.
- Original D009 **Feb 22–Mar 7**, D012 **Apr 28–May 16**, and new D014 **Jun 29–Jul 12** reserved final blocks all remain **unscored**. Raw vendor quote files and row-level price/prediction sequences were not committed. Arrow can physically decompress boundary-overlapping batches; final isolation is statistical, not cryptographic.
- **187 synthetic tests passed on Python 3.11 and 3.12**, covering original invariants, rolling-before-current-day cutoffs, strict session history, source date/price separation, label-free coverage reader, and sealed final protections. [Coverage audit workflow](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43277130722) succeeded and was removed after use. The failed model run is retained as part of the research record, not concealed.

## Interpretation and next research gate

**Result:** source eligibility assumptions required by the preregistered adaptive policy did not hold across the frozen panel. D014 **cannot claim** that rolling cutoffs improved alert frequency or false-direction accuracy: neither model/policy comparison was completed; no directional alert precision, recall, utility or trading P&L was estimated for these new dates.

**Next gate, not yet a new model experiment:** before any replacement study, preregister a market-data **availability-aware** signal decision protocol that specifies exactly what happens on a day with no valid scores, and how the ten-day history and abstention/coverage denominators are handled. Fail-closed alerts should remain distinguishable from market inactivity and unavailable data. Require study population and data-quality policies fixed **before** new source-price access, never use this D014 confirmation to tune them, and reserve a separately downstream final test. A scientifically defensible design may treat no-data days as enforced abstention while keeping all source-calendar days and reporting the opportunity loss, but that would be a NEW design, not a rescue of D014.

Project 007 PR #7 remains **draft/unmerged**; no model promoted, execution venue connected, live order, fills, profits or risk-adjusted returns measured.
