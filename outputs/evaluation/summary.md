# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **3**.
- Source-backed positive events with trading data in the primary window: **2**.
- Negative control: **SOPAT's benign buyout/withdrawal**.
- `SOURCE_NEEDED` and excluded: **TINV, UADH, TSI, CGF, UBCI**.
- TINV date problem: the label retains **2025-10-06** with an unresolved date type and no supporting repository source; detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Reference results

- Primary recall: **1 of 2 events**.
- Secondary recall: **1 of 2 events**.
- Ranked known-event matches at k=10, 20, 50: **0 of 10, 0 of 20, 0 of 50 flags**, respectively. This underestimates real precision because most true events are not labeled.
- Flag load: **1027 flags**, or **3.607 flags per ticker-year**.
- Negative-control behavior: **0 flags** near SOPAT in the primary window.
- The fixed z=3.0, 60-day reference cell independently reports **1027 flags** and **1 of 2 events**.

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Precision@20 | SOPAT-window flags |
|---|---:|---:|---|---|---:|---:|
| reference_union | 1027 | 3.607 | 1 of 2 events | 1 of 2 events | 0.0000 | 0.000 |
| volume_zscore_only | 140 | 0.492 | 0 of 2 events | 0 of 2 events | 0.0000 | 0.000 |
| absolute_return_only | 903 | 3.171 | 1 of 2 events | 1 of 2 events | 0.0000 | 0.000 |
| random_same_count_mean_1000_seeds | 1027 | 3.607 | 0.363 of 2 events on average | 0.653 of 2 events on average | 0.0003 | 0.600 |

The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds. Its non-integer event count and SOPAT count are averages, not observed cases.

## Limitations

Only three positive events have repository sources, only two overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
