# Case 016 — Day-cluster uncertainty (D019)

**Read-only diagnostic of the already-spent 2022-10-13–2022-10-26 confirmation.** No market-source re-access, retraining, new threshold selection, or sealed-final inspection.

Source: Quant-Arena Public L1 (Quant Arena / LaPlace's Eye / Einsia AI), CC BY-NC 4.0 noncommercial. [Original successful run 43291108945](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43291108945). Frozen pre-price calendar SHA: `495ae84000e64114e445e7c7dbed9dec0b12d1379a53b954f9af5472b7a20899`.

The existing `microstructure/information_bootstrap.py` prespecifies seed **7007**, **2,000** resamples of **ten whole trading dates** with replacement, retaining all three stocks paired within each date. Statistic: arithmetic mean of stock-day directional average precision minus matched stock-day directional prevalence. Percentile bounds are linearly interpolated 2.5th and 97.5th percentiles. Calculations use the unchanged stock-day AP and base-rate aggregates from the successful run; no individual source prices or labels were reread.

| Original March-trained model | Direction | Mean AP lift (percentage points) | 95% day-cluster percentile interval (pp) |
|---|---|---:|---:|
| Balanced | Up | +4.879 | [+3.660, +6.113] |
| Balanced | Down | +9.210 | [+7.219, +11.247] |
| Unweighted | Up | +3.635 | [+2.674, +4.656] |
| Unweighted | Down | +6.136 | [+4.779, +7.577] |

All four **descriptive** bootstrap intervals exclude zero. They do **not** estimate pooled average precision, nor do they establish independent external replication, calibration quality, execution profitability, or reliable future generalization. The sample comprises only ten correlated trading days from one consumed confirmation period. Prior negative alert-utility findings remain in force.

**Decision:** continue separate ranking-versus-calibration investigation. Do not select an improved threshold or model on this spent confirmation. Any new challenger requires precommitted success criteria and a fresh source-timestamp-only date calendar. All earlier and D016 final periods remain sealed.
