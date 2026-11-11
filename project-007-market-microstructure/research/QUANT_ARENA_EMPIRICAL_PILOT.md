# Project 007 — Quant-Arena single-stock/day source validation (empirical)

**Status: first authentic noncommercial source pilot completed and verified, November 11, 2026.** This is a **separate market/data-source methodology experiment**, not an FI-2010 reproduction, prediction model, strategy, or trading backtest. Human lead approved "start working on the second option while we wait for the reply"; methods and interpretations below are AI-assisted, not human-generated findings.

## Attribution and source evidence

Dataset: [Ashitemaru, *Quant-Arena Public L1*](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), publisher-declared CC BY-NC 4.0, noncommercial educational research only. Citation in the publisher card currently lists *Quant-Arena: Benchmarking LLM Agents for Quantitative Trading Research* (2026, author TBD). Source source-level coverage differs from FI-2010: **Shenzhen**, not Helsinki; **2022–2023**, not 2010; regular **15-second best-quote snapshots**, not event message stream.

- **Git revision** (verified full 40-hex from publisher API): `fa85d7b95e56e81317ac349f52e916ca482f0f68`
- **Archive**: `quant-arena-public-l1-v1.tar`, publisher reported 6,230,128,640 bytes and 293 scanned members. The complete archive was **not** acquired or hashed.
- **Exactly one selected member**: `quant-arena-public-l1-v1/000012.SZ.parquet`, 25,455,922 bytes; **SHA256 `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`**, matching the published `SHA256SUMS` inside the pinned TAR. Source `manifest.json` was also read and confirmed parseable; its internal schema was not used to infer the checksum.
- **Total network download (byte-ranged)**: 25,730,912 bytes, not 6.23 GB. HTTP 206/Content-Range and standard TAR checksum checks validated the selective acquisition.
- **Stock preselection**: 000012.SZ, the example named by the publisher, chosen without class or price outcomes.
- **Date selection**: earliest two distinct genuine sessions in that stock's chronological Parquet: **2022-01-04 and 2022-01-05**, 1,023 15-second snapshot rows per day (2,046 selected). The source stock Parquet has 494,832 rows across its full stated coverage. No other stock's data were opened.
- **Source numeric/timing checks**: true Parquet has **45 columns**: `symbol`, `available_at`, `source_event_time`, 10 bid prices and 10 bid volumes, 10 ask prices and 10 ask volumes, `missing_depth`, `stale`. The dataset card's 45-column description is confirmed; a separate benchmark doc had referred to 44 fields. Prices are publisher-described decimal128(28,4) in CNY and timestamps Asia/Shanghai (+08:00). Source row chronology and integrity were validated, no reordering or interpolation.
- **Reproducibility**: [successful one-stock live CI run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43100987354) on PR #7; local file was ephemeral in runner, raw quotes and Parquet bytes **not committed or redistributed**.
- **Software tests**: **92 synthetic unit tests passed on both Python 3.11 and 3.12** in that CI run. These check engineering correctness separately from the empirical summary.

## Real descriptive results: midpoint-average labels at ±0.2%

For each origin, compute best midpoint `m_0=(bid1+ask1)/2` and average the next `k` valid, contiguous midpoints within the **same stock and trading date**; classify the fractional difference as **up (≥+0.002), stationary (between −0.002 and +0.002), or down (≤−0.002)**. No forward interpolation, threshold optimization, or training is performed.

| Horizon (15s sampled snapshots) | Up | Stationary | Down | Unlabelled | Eligible | Stationary among eligible |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 39 | 1,827 | 38 | 142 | 1,904 | 95.96% |
| 2 | 33 | 1,819 | 38 | 156 | 1,890 | 96.24% |
| 3 | 41 | 1,799 | 46 | 160 | 1,886 | 95.39% |
| 5 | 54 | 1,758 | 66 | 168 | 1,878 | 93.61% |
| 10 | 101 | 1,645 | 112 | 188 | 1,858 | 88.54% |

At k=5, **168**/2,046 rows have no valid target: **126** invalid/stale quote origins and **42** insufficient contiguous future samples. The k=5 denominator of 1,878 *excludes* those missing outcomes; class shares are not percentages of all 2,046 raw snapshots.

### Preliminary interpretation (assistant-generated)

Using a fixed ±0.2% label threshold on a regular 15-second quote grid produces a high stationary share in this one-stock/two-day example; that share is lower by k=10 than k=1. This finding illustrates the critical effect of data cadence, horizon definition and missing-value exclusion on class balance. It does **not** show how much of FI-2010's day-eight stationary shift was caused by label construction, because the original securities, source microstructure and calendar differ.

## Independent quote-level replication — completed

A **second** ephemeral run on the **same pinned publisher revision and stock-file SHA256** independently recomputed all labels from source quotes using a separate, deliberately slower algorithm. The two implementations agreed for **all 2,046 origin rows at each of the five horizons** (**10,230 comparisons; zero mismatches**, including excluded origins). This establishes agreement between two code paths on the accepted stock/quote inputs; it does **not** certify the source's original quote accuracy, exchange semantics, or anything about FI-2010 original labels.

- [Completed independent empirical GitHub Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43102185079)
- **95 synthetic tests passed** on both Python 3.11 and Python 3.12.
- Original ±0.2% threshold, horizon 5, day-separated class counts:

| Source trading day | Up | Stationary | Down | Unlabelled | Eligible | Stationary / eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-01-04 | 26 | 878 | 35 | 84 | 939 | 93.50% |
| 2022-01-05 | 28 | 880 | 31 | 84 | 939 | 93.72% |

- **Predetermined descriptive threshold sensitivity at k=5, on the same 1,878 eligible rows (no model tuning):**

| Relative threshold | Up | Stationary | Down | Unlabelled | Stationary / eligible |
| --- | ---: | ---: | ---: | ---: | ---: |
| ±0.1% | 244 | 1,366 | 268 | 168 | 72.74% |
| ±0.2% | 54 | 1,758 | 66 | 168 | 93.61% |
| ±0.4% | 14 | 1,859 | 5 | 168 | 98.99% |

- Source-quality audit on 2,046 selected observations: 104 locked/crossed/nonpositive snapshots; 37 stale or missing source-event timestamps; 2 missing/null depth flags; 2 absent best quotes; 2 consecutive 15-second-grid gaps exceeding the provisional 30-second tolerance. **Quality counters may overlap** and must not be added together as mutually exclusive exclusions. At k=5, 126 origin rows were invalid/stale and another 42 had insufficient contiguous future.
- The threshold change is a *deliberate change of label definitions*; larger stationary shares are mechanically expected as the neutral band widens. This alone does not show that market prices or the FI-2010 publisher labels were erroneous.

### Next preregistered source-construction question (not yet run)

Does the same threshold/cadence effect persist **across different stocks and days**? Define a deterministic, source-blind small panel before opening additional files (e.g., first five eligible stock filenames in the publisher manifest, earliest ten dates each), document any missing sessions/exclusions, rerun stock/day boundaries and independent label verification, and compare class balance under the same thresholds. Reserve a separate later set of days for any eventual predictive study. Keep raw vendor data outside Git; remain within CC BY-NC 4.0 noncommercial terms.


## Open scientific questions

1. Quantify by-day differences in class proportions for this stock and the **stated** source flags, without interpreting them as financial alpha.
2. Test how a *predeclared* threshold sensitivity grid (0.1%, 0.2%, 0.4% at k=5) changes class balances; this is descriptive methodology inspection, not threshold tuning for performance.
3. Have an **independent raw-quote label algorithm** verify every eligible/excluded origin, not merely the class totals, to distinguish implementation arithmetic from underlying source issues.
4. Investigate source/provider discontinuities or stale quote causes separately; do not confuse unavailable future targets with stationary price changes.
5. Do not extrapolate to profitable market making, fill/queue priority or modern forecasts. A 2-day, 1-stock exploratory audit is not a time-block holdout.
6. Preserve FI-2010 days 9 and 10, still unopened. FI-2010 original mid-price/session-boundary verification remains unresolved and is **not solved by this Shenzhen source**.
