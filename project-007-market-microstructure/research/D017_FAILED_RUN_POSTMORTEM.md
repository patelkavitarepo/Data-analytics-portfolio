# Case 017 — Failed empirical reporting run / confirmation consumed

**Status: STOPPED. No success claim. No rerun authorized.**

- GitHub Actions run: https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43301370130
- Calendar SHA: `aa7f367a54c8d0651da232d0b9dc3dde2a4c99915f7126ce7ec02bbf372b0dd5`.
- Three pinned stock members authenticated successfully: `000012.SZ`, `000025.SZ`, `000031.SZ`.
- After computing model audit aggregates in memory, the runner called `day_cluster_ap_lift(result)` and raised `ValueError("missing/nonfinite stock-day AP or base rate")` at `microstructure/information_bootstrap.py:43`.
- The failure occurred **before** the `D017_INFORMATION_AGGREGATES_BEGIN` marker; no full confirmation aggregate report was emitted. Therefore **no empirical ranking, calibration, or comparison results are available to report**.
- The failure indicates at least one stock-day/direction has undefined or nonfinite AP/base-rate under the bootstrap's strict complete-data requirement. The precise stock-day and missingness cause are **not identifiable from the emitted log**. Do not speculate that the signal vanished or survived.
- Confirmation dates **2022-12-08–2022-12-21 are spent** because the program accessed their labels. Warmup **2022-11-10–2022-12-07**. New final **2022-12-22–2023-01-05 remains sealed**, alongside all previous finals.
- Synthetic CI previously passed **218 tests on Python 3.11 and 3.12**, but synthetic fixtures did not expose this empirical missingness path.

## Safe next work
1. Add **synthetic-only** regression tests for missing AP, absent positives, and paired-stock-day alignment.
2. Define a missingness-aware, explicitly denominated aggregate reporting rule **before** any future independent experiment. Do not impute undefined AP as zero or silently drop stock-days.
3. For a genuinely independent empirical test, freeze a **new** calendar using source timestamps only strictly after 2023-01-05, then commit it before reading prices/labels.
4. Do **not** rerun D017 against its spent confirmation to obtain favorable results, or access its sealed final.
5. Keep PR #7 draft and avoid deployment/profitability claims.

**Conclusion:** D017 is an operational/reporting failure, not a positive or negative scientific result about the directional hypothesis.
