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
- Flag load: **1335 flags**, or **3.380 flags per ticker-year**.
- Negative-control behavior: **0 flags in 1 SOPAT window**.
- The fixed z=3.0, 60-day reference cell independently reports **1335 flags** and **1 of 2 events**.

### Lead time for each hit

- **GIF: 3 days to primary date 2024-10-25**; **21 days to secondary date 2024-11-12** (first matching flag 2024-10-22).

### Ranking and top 20 flags

Precision@k ranks every reference flag by **`max(abs(volume_zscore), abs(return_zscore))`**, highest first. Ties are resolved by earlier date and then ticker symbol. The displayed z-score is that ranking score. This rule was fixed independently of the event labels.

“Illiquid” means the ticker's median daily volume is at or below the 25th percentile across the 83 tickers represented in the delivered reference flag set. The resulting cutoff is **350.0 shares per observed trading day**; this descriptive label does not affect ranking or detection.

| Rank | Ticker | Date | Ranking z-score | Illiquid |
|---:|---|---|---:|---|
| 1 | CITY | 2026-04-27 | 21.748 | No |
| 2 | CITY | 2026-04-28 | 19.703 | No |
| 3 | BT | 2022-05-10 | 18.594 | No |
| 4 | PGH | 2021-11-30 | 17.375 | No |
| 5 | ADWYA | 2022-06-13 | 17.048 | No |
| 6 | SOMOC | 2025-05-13 | 14.513 | No |
| 7 | TJARI | 2023-04-05 | 12.246 | No |
| 8 | SAM | 2023-04-20 | 12.240 | No |
| 9 | SIPHA | 2023-11-29 | 12.018 | Yes |
| 10 | STAR | 2025-03-12 | 11.968 | No |
| 11 | ARTES | 2023-07-31 | 11.690 | No |
| 12 | ICF | 2022-09-01 | 11.664 | No |
| 13 | SOTET | 2025-07-29 | 11.502 | No |
| 14 | BNA | 2025-06-17 | 11.060 | No |
| 15 | ARTES | 2022-07-06 | 11.018 | No |
| 16 | BIAT | 2024-11-29 | 10.447 | No |
| 17 | TINV | 2025-10-22 | 10.300 | Yes |
| 18 | NBL | 2025-06-11 | 10.010 | No |
| 19 | CITY | 2024-07-08 | 9.696 | No |
| 20 | SITS | 2025-10-10 | 9.274 | No |

The **0 of 20** result means none of these 20 highest-scoring flags falls inside the fixed -30/+5-day window around either of the 2 source-backed positive events with primary-window coverage. It does not establish that the 20 flags are false positives: the repository event list is intentionally small and incomplete.

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Precision@20 | SOPAT-window flags |
|---|---:|---:|---|---|---|---|
| reference_union | 1335 | 3.380 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| volume_zscore_only | 192 | 0.486 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| absolute_return_only | 1162 | 2.942 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| random_same_count_mean_1000_seeds | 1335 | 3.380 | 0.515 of 2 events on average | 0.891 of 3 events on average | 0.007 of 20 flags on average | 0.395 flags in 1 window on average |

The reference detector does **not** beat the absolute-return-only baseline on recall or precision: both match 1 of 2 events in the primary window, 1 of 3 events in the secondary window, and 0 of 20 flags at k=20, while the reference produces 1,335 flags versus 1,162. It also does not improve recall over the volume-only baseline in this tiny event set. The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds; its non-integer event and SOPAT counts are averages, not observed cases.

## Sensitivity grid

| Z cutoff | Rolling window | Flags | Flags/ticker-year | Primary recall |
|---:|---:|---:|---:|---|
| 2.5 | 20 | 2943 | 7.450 | 1 of 2 events |
| 2.5 | 40 | 2574 | 6.516 | 1 of 2 events |
| 2.5 | 60 | 2372 | 6.005 | 1 of 2 events |
| 2.5 | 120 | 2056 | 5.205 | 1 of 2 events |
| 3 | 20 | 1680 | 4.253 | 1 of 2 events |
| 3 | 40 | 1434 | 3.630 | 1 of 2 events |
| 3 | 60 | 1335 | 3.380 | 1 of 2 events |
| 3 | 120 | 1148 | 2.906 | 1 of 2 events |
| 3.5 | 20 | 1039 | 2.630 | 1 of 2 events |
| 3.5 | 40 | 880 | 2.228 | 1 of 2 events |
| 3.5 | 60 | 790 | 2.000 | 1 of 2 events |
| 3.5 | 120 | 653 | 1.653 | 0 of 2 events |
| 4 | 20 | 670 | 1.696 | 1 of 2 events |
| 4 | 40 | 571 | 1.445 | 1 of 2 events |
| 4 | 60 | 470 | 1.190 | 1 of 2 events |
| 4 | 120 | 381 | 0.964 | 0 of 2 events |

14 of 16 sensitivity cells match 1 of 2 events; 2 of 16 match 0 of 2 events. Flag load ranges from 381 to 2943. No cell was selected to improve the labeled-event result.


## Universe coverage audit

The older combined file contains 60 symbols while 85 valid individual ticker files exist. The 25 omitted symbols are **AB, ADWYA, AETEC, AL, AMS, ARTES, ASSAD, ASSMA, AST, ATB, ATL, BH, BHASS, BHL, BIAT, BL, BNA, BNASS, BT, BTE, CC, CELL, CREAL, TJARI, TJL**. The derived 85-symbol file contains 61,812 source rows; the current detector excludes TBIDX and known-incomplete PLTU. No scraper or protected source file was changed or run.

The archived 60-symbol evaluation used the earlier 20-observation warm-up and silent close clamping. It is retained only as historical provenance and is **not directly comparable** to the corrected 60-valid-observation, raw-OHLC reference reported here.


## Limitations

Only 3 positive events have repository sources, only 2 overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. Precision against this incomplete event list can undercount relevant flags. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
