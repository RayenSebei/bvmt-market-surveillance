# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. An event's evaluation date is the earliest public suspension, court ruling, or first announcement found in the repository evidence; the original label and a later announcement are retained separately. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **3**.
- Source-backed positive events with trading data in the primary window: **2**.
- Source-backed positive events with trading data in the secondary window: **3**.
- Negative control: **SOPAT's benign buyout/withdrawal**.
- `SOURCE_NEEDED` and excluded: **TINV, UADH, TSI, CGF, UBCI**.
- TINV date problem: the label retains **2025-10-06** with date type **`other`**, not `public_announcement`, and has no supporting repository source. Detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Event audit

| Ticker | Primary date | Date type | Original label | Secondary date | Source | Confidence | Evaluable | Reason |
|---|---|---|---|---|---|---|---|---|
| TINV | 2025-10-06 | other | 2025-10-06 | — | `SOURCE_NEEDED` | low | No | no supporting repository source |
| UADH | 2026-03-24 | suspension | 2026-03-24 | — | `SOURCE_NEEDED` | low | No | no supporting repository source |
| TSI | — | other | — | — | `SOURCE_NEEDED` | not_assessed | No | no supporting repository source |
| CGF | — | other | — | — | `SOURCE_NEEDED` | not_assessed | No | no supporting repository source |
| UBCI | — | other | — | — | `SOURCE_NEEDED` | not_assessed | No | no supporting repository source |
| GIF | 2024-10-25 | suspension | 2024-10-25 | 2024-11-12 | [source](https://www.ilboursa.com/marches/la-bourse-de-tunis-decide-la-radiation-de-la-societe-gif-filter_49247) | high | Yes | source-backed positive event with window coverage |
| LSTR | 2024-07-23 | suspension | 2024-07-23 | 2024-07-24 | [source](https://www.ilboursa.com/marches/en-cessation-de-paiement-le-tribunal-declare-la-faillite-de-la-societe-electrostar_47391) | high | Yes | source-backed positive event with window coverage |
| SERVI | 2024-01-11 | suspension | 2024-01-11 | 2024-03-27 | [source](https://www.ilboursa.com/marches/le-tribunal-de-tunis-declare-la-faillite-de-la-societe-servicom_45451) | high | No | trading data ends before the evaluation window |
| MIP | 2024-08-05 | public_announcement | 2024-09-10 | 2024-09-10 | [source](https://www.ilboursa.com/marches/vers-la-mise-en-faillite-directe-de-la-societe-mip_47579) | medium | No | exploratory case excluded from headline metrics |
| SOPAT | 2023-09-19 | public_announcement | 2023-09-20 | 2023-09-20 | [source](https://www.ilboursa.com/marches/le-groupe-la-rose-blanche-retire-la-sopat-de-la-cote-de-la-bourse_42686) | high | No | negative control, not a positive event |

## Reference results

- Primary recall: **1 of 2 events**.
- Secondary recall: **1 of 3 events**.
- Ranked known-event matches at k=10, 20, 50: **0 of 10 flags, 0 of 20 flags, 0 of 50 flags**, respectively. This underestimates real precision because most relevant events are not labeled.
- Flag load: **1027 flags**, or **3.607 flags per ticker-year**.
- Negative-control behavior: **0 flags in 1 SOPAT window**.
- The fixed z=3.0, 60-day reference cell independently reports **1027 flags** and **1 of 2 events**.

### Lead time for each hit

- **GIF: 3 days to primary date 2024-10-25**; **21 days to secondary date 2024-11-12** (first matching flag 2024-10-22).

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Precision@20 | SOPAT-window flags |
|---|---:|---:|---|---|---|---|
| reference_union | 1027 | 3.607 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| volume_zscore_only | 140 | 0.492 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| absolute_return_only | 903 | 3.171 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| random_same_count_mean_1000_seeds | 1027 | 3.607 | 0.492 of 2 events on average | 0.929 of 3 events on average | 0.008 of 20 flags on average | 0.600 flags in 1 window on average |

The reference detector does **not** beat the absolute-return-only baseline on recall or precision: both match 1 of 2 events in the primary window, 1 of 3 events in the secondary window, and 0 of 20 flags at k=20, while the reference produces 1,027 flags versus 903. It matches more events than the volume-only baseline, but at a much higher flag load. The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds; its non-integer event and SOPAT counts are averages, not observed cases.

## Sensitivity grid

| Z cutoff | Rolling window | Flags | Flags/ticker-year | Primary recall |
|---:|---:|---:|---:|---|
| 2.5 | 20 | 1779 | 6.248 | 1 of 2 events |
| 2.5 | 40 | 1862 | 6.540 | 1 of 2 events |
| 2.5 | 60 | 1806 | 6.343 | 1 of 2 events |
| 2.5 | 120 | 1755 | 6.164 | 1 of 2 events |
| 3 | 20 | 1010 | 3.547 | 1 of 2 events |
| 3 | 40 | 1047 | 3.677 | 1 of 2 events |
| 3 | 60 | 1027 | 3.607 | 1 of 2 events |
| 3 | 120 | 986 | 3.463 | 1 of 2 events |
| 3.5 | 20 | 625 | 2.195 | 1 of 2 events |
| 3.5 | 40 | 648 | 2.276 | 1 of 2 events |
| 3.5 | 60 | 617 | 2.167 | 1 of 2 events |
| 3.5 | 120 | 569 | 1.998 | 0 of 2 events |
| 4 | 20 | 395 | 1.387 | 1 of 2 events |
| 4 | 40 | 420 | 1.475 | 1 of 2 events |
| 4 | 60 | 371 | 1.303 | 1 of 2 events |
| 4 | 120 | 329 | 1.155 | 0 of 2 events |

14 of 16 sensitivity cells match 1 of 2 events; 2 of 16 match 0 of 2 events. Flag load ranges from 329 to 1862. No cell was selected to improve the labeled-event result.

## Limitations

Only 3 positive events have repository sources, only 2 overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. Precision against this incomplete event list can undercount relevant flags. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
