# Case 017 — Prospective ranking-versus-calibration challenger design

**Protocol only. No authorization to read prices, fit a challenger, inspect sealed finals, or deploy.**

## Motivation
Case 016's spent confirmation exhibits stock-day directional AP lift, while earlier alert policies have negative hypothetical +1/-4 utility. The March-trained balanced model ranks better on stock-day AP but has worse probability Brier than the unweighted model. These facts motivate separate hypotheses, not a combined trading claim.

## Frozen questions for a *future independent* calendar
1. **Ranking replication:** Do original balanced and unweighted models preserve positive per-stock-day AP minus class prevalence for up and down, when all three stocks are paired by date? The primary statistic is the unweighted mean stock-day AP lift, with day-cluster bootstrap seed 7007, 2,000 resamples.
2. **Calibration:** Does the unweighted model retain lower matched-population Brier for up/down probabilities? Compare paired matched origins; no score-ratio-as-probability substitution.
3. **Decision policy:** Does any prospective abstaining policy produce strictly positive *predeclared* hypothetical +1 correct / -4 wrong utility relative to always abstaining (0), with sufficient source coverage? A policy is not eligible for this test until its parameters and source-only readiness rules are frozen **before** new confirmation labels are opened.
4. **Stability:** Report all-source and matched denominators, source unavailability, per-stock/per-day heterogeneity, tie handling, and the count of days with positive mean AP lift.

## Separation and governance
- Original models and feature definitions remain unchanged until an explicitly approved challenger protocol is committed.
- Case 016 October 13–26, 2022 confirmation is **spent**; cannot be used for policy optimization or as an independent new confirmation.
- Case 016 October 27–November 9, 2022 final remains **sealed**, alongside all earlier finals.
- If authorized, select the first sufficient number of common observed dates **strictly after 2022-11-09** from source **timestamps only**, authenticate original stock-member hashes, and commit the exact warmup/confirmation/sealed-final calendar before any new market price/depth/target read. Do not change the date rule after looking at source quality or outcomes.
- Reproduce 54,290 original fit examples and original two model specifications; no refit on future periods.
- Do not infer tradability, costs, market impact, or profit from snapshot AP; independent execution simulation and transaction-cost assumptions would be required.
- Report null/negative results, stop on source/label alignment failures, and leave PR #7 draft.

**Decision gate:** design is documented; *no new empirical experiment authorized by this document alone*.
