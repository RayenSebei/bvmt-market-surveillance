# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. An event's evaluation date is the earliest public suspension, court ruling, or first announcement found in the repository evidence; the original label and a later announcement are retained separately. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **6**.
- Source-backed positive events with trading data in the primary window: **5**.
- Source-backed positive events with trading data in the secondary window: **5**.
- Negative controls include benign buyouts and routine corporate actions; see the event audit.
- `SOURCE_NEEDED` and excluded: **TINV, CGF, UBCI**.
- TINV date problem: the label retains **2025-10-06** with date type **`other`**, not `public_announcement`, and has no supporting repository source. Detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Event audit

| Ticker | Primary date | Date type | Original label | Secondary date | Source | Confidence | Evaluable | Reason |
|---|---|---|---|---|---|---|---|---|
| TINV | 2025-10-06 | other | 2025-10-06 | — | `SOURCE_NEEDED` | low | No | no supporting repository source |
| UADH | 2026-03-25 | suspension | 2026-03-24 | 2026-03-25 | [source](https://www.bvmt.com.tn/sites/default/files/avis-decisions/uadh-tlyq-ltdwl.pdf) | high | Yes | source-backed positive event with window coverage |
| TSI | 2025-04-23 | public_announcement | 2025-04-23 | — | [source](https://www.cmf.tn/sites/default/files/pdfs/publications/bulletin-officiel/bo250423.pdf) | high | No | ticker has no stored trading observations |
| CGF | — | other | — | — | `SOURCE_NEEDED` | not_assessed | No | no supporting repository source |
| UBCI | — | other | — | — | `SOURCE_NEEDED` | not_assessed | No | no supporting repository source |
| GIF | 2024-10-25 | suspension | 2024-10-25 | 2024-11-12 | [source](https://tunis-stockexchange.com/en/node/6451) | high | Yes | source-backed positive event with window coverage |
| LSTR | 2024-07-23 | suspension | 2024-07-23 | 2024-07-24 | [source](https://managers.tn/2024/07/23/la-societe-electrostar-declaree-en-faillite/) | high | Yes | source-backed positive event with window coverage |
| SERVI | 2024-01-11 | suspension | 2024-01-11 | 2024-03-27 | [source](https://www.ilboursa.com/marches/suspension-de-la-cotation-du-titre-servicom_44316) | high | Yes | source-backed positive event with window coverage |
| MIP | 2024-08-05 | public_announcement | 2024-09-10 | 2024-09-10 | [source](https://www.ilboursa.com/marches/vers-la-mise-en-faillite-directe-de-la-societe-mip_47579) | medium | No | exploratory case excluded from headline metrics |
| SOPAT | 2023-09-19 | public_announcement | 2023-09-20 | 2023-09-20 | [source](https://www.ilboursa.com/marches/le-groupe-la-rose-blanche-retire-la-sopat-de-la-cote-de-la-bourse_42686) | high | No | negative control, not a positive event |
| OTH | 2021-10-29 | public_announcement | 2021-10-29 | — | [source](https://www.ilboursa.com/marches/onetech-holding-augmentation-de-capital-approuvee_31068) | high | No | negative control, not a positive event |
| LNDOR | 2021-11-26 | public_announcement | 2021-11-26 | — | [source](https://www.ilboursa.com/marches/land-or-l-augmentation-de-capital-approuvee-par-l-assemblee-generale-extraordinaire_31547) | high | No | negative control, not a positive event |
| ATB | 2021-11-26 | public_announcement | 2021-11-26 | — | [source](https://www.ilboursa.com/marches/atb-l-age-approuve-l-augmentation-de-capital-de-28-millions-de-dinars-reservee-a-l-arab-bank_31564) | high | No | negative control, not a positive event |
| ADWYA | 2022-06-07 | suspension | 2022-06-07 | — | [source](https://www.ilboursa.com/marches/suspension-de-la-cotation-des-titres-adwya_34995) | medium | No | exploratory case excluded from headline metrics |
| CREAL | 2022-11-14 | public_announcement | 2022-11-14 | — | [source](https://www.ilboursa.com/marches/cardinal-brands-nouvel-actionnaire-majoritaire-de-cerealis-lance-une-opa_37790) | high | No | negative control, not a positive event |
| WIFAK | 2023-01-09 | suspension | 2023-01-09 | — | [source](https://www.ilboursa.com/marches/suspension-de-la-cotation-des-titres-wifak-bank_38650) | medium | No | exploratory case excluded from headline metrics |
| STPAP | 2023-09-28 | suspension | 2023-09-28 | — | [source](https://www.ilboursa.com/marches/incendie-dans-l-usine-de-sotipapier-cotation-suspendue-a-la-bourse-de-tunis_42802) | high | Yes | source-backed positive event with window coverage |
| SPHAX | 2023-12-19 | public_announcement | 2023-12-19 | — | [source](https://www.ilboursa.com/marches/mise-en-faillite-de-la-compagnie-aerienne-syphax-airlines_44054) | high | No | ticker has no stored trading observations |
| SMART | 2024-10-31 | public_announcement | 2024-10-31 | — | [source](https://www.ilboursa.com/marches/smart-tunisie-augmentation-de-capital-annoncee_49080) | high | No | negative control, not a positive event |
| BIAT | 2024-11-27 | public_announcement | 2024-11-27 | — | [source](https://www.ilboursa.com/marches/biat-augmentation-de-capital-annoncee_49512) | high | No | negative control, not a positive event |
| SMD | 2025-03-13 | public_announcement | 2025-03-13 | — | [source](https://www.ilboursa.com/marches/sanimed-lance-une-augmentation-de-capital-de-10-millions-de-dinars_51474) | high | No | negative control, not a positive event |
| TJARI | 2025-03-14 | public_announcement | 2025-03-14 | — | [source](https://www.ilboursa.com/marches/attijari-bank-propose-un-dividende-de-5-dinars-par-action-et-une-augmentation-de-capital_51499) | high | No | negative control, not a positive event |
| MPBS | 2025-04-28 | public_announcement | 2025-04-28 | — | [source](https://www.ilboursa.com/marches/mpbs-propose-un-dividende-de-0-370-dinar-par-action-et-une-operation-de-split_52367) | high | No | negative control, not a positive event |
| DH | 2025-07-28 | public_announcement | 2025-07-28 | — | [source](https://www.ilboursa.com/marches/delice-holding-annonce-le-split-de-la-valeur-nominale-de-son-action-a-5-dinars_54085) | high | No | negative control, not a positive event |
| SIAME | 2025-11-14 | public_announcement | 2025-11-14 | — | [source](https://www.ilboursa.com/marches/la-siame-reporte-la-distribution-des-dividendes-au-titre-de-2024-sous-instruction-judiciaire_57655) | medium | No | exploratory case excluded from headline metrics |
| PGH | 2026-02-19 | suspension | 2026-02-19 | — | [source](https://www.ilboursa.com/marches/le-cmf-demande-la-suspension-de-cotation-des-titres-poulina-et-land-or_59920) | high | No | negative control, not a positive event |
| LNDOR | 2026-02-19 | suspension | 2026-02-19 | — | [source](https://www.ilboursa.com/marches/le-cmf-demande-la-suspension-de-cotation-des-titres-poulina-et-land-or_59920) | high | No | negative control, not a positive event |
| ASSMA | 2026-03-19 | public_announcement | 2026-03-19 | — | [source](https://www.ilboursa.com/marches/assurances-maghrebia-dividende-de-2-900-dinars-et-attribution-d-actions-gratuites_60570) | high | No | negative control, not a positive event |

## Reference results

- Primary recall: **1 of 5 events** (95% Wilson 0.04–0.62).
- Secondary recall: **2 of 5 events** (95% Wilson 0.12–0.77).
- Ranked known-event matches at k=10, 20, 50: **0 of 10 flags (95% Wilson 0.00–0.28), 0 of 20 flags (95% Wilson 0.00–0.16), 0 of 50 flags (95% Wilson 0.00–0.07)**, respectively. This underestimates real precision because most relevant events are not labeled.
- Flag load: **1414 flags**, or **3.369 flags per ticker-year**.
- Negative-control behavior: **13 flags near registered negative controls**.
- The fixed z=3.0, 60-day reference cell independently reports **1414 flags** and **1 of 5 events**.

### Lead time for each hit

- **GIF: 3 days to primary date 2024-10-25**; **21 days to secondary date 2024-11-12** (first matching flag 2024-10-22).

### Ranking and top 20 flags

Precision@k ranks every reference flag by **`max(abs(volume_zscore), abs(return_zscore))`**, highest first. Ties are resolved by earlier date and then ticker symbol. The displayed z-score is that ranking score. This rule was fixed independently of the event labels.

“Illiquid” means the ticker's median daily volume is at or below the 25th percentile across the 83 tickers represented in the delivered reference flag set. The resulting cutoff is **400.0 shares per observed trading day**; this descriptive label does not affect ranking or detection.

| Rank | Ticker | Date | Ranking z-score | Illiquid |
|---:|---|---|---:|---|
| 1 | CITY | 2026-04-27 | 21.748 | No |
| 2 | CITY | 2026-04-28 | 19.703 | No |
| 3 | BT | 2022-05-10 | 18.594 | No |
| 4 | PGH | 2021-11-30 | 17.375 | No |
| 5 | ADWYA | 2022-06-13 | 17.048 | No |
| 6 | SOMOC | 2025-05-13 | 14.513 | No |
| 7 | TRE | 2026-09-15 | 14.346 | No |
| 8 | TJARI | 2023-04-05 | 12.246 | No |
| 9 | SAM | 2023-04-20 | 12.240 | No |
| 10 | SIPHA | 2023-11-29 | 12.018 | Yes |
| 11 | STAR | 2025-03-12 | 11.968 | No |
| 12 | ARTES | 2023-07-31 | 11.690 | No |
| 13 | ICF | 2022-09-01 | 11.664 | Yes |
| 14 | SOTET | 2025-07-29 | 11.502 | No |
| 15 | BNA | 2025-06-17 | 11.060 | No |
| 16 | ARTES | 2022-07-06 | 11.018 | No |
| 17 | HL | 2026-06-30 | 10.755 | No |
| 18 | BIAT | 2024-11-29 | 10.447 | No |
| 19 | TINV | 2025-10-22 | 10.300 | Yes |
| 20 | NBL | 2025-06-11 | 10.010 | No |

The **0 of 20** result counts highest-scoring flags inside the fixed -30/+5-day windows around the 5 source-backed positive events with primary-window coverage. The repository event list is intentionally small and incomplete.

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Known-event@20 | Negative-control flags |
|---|---:|---:|---|---|---|---|
| reference_union | 1414 | 3.369 | 1 of 5 events | 2 of 5 events | 0 of 20 flags | 13 flags near negative controls |
| volume_zscore_only | 198 | 0.472 | 0 of 5 events | 0 of 5 events | 0 of 20 flags | 1 flags near negative controls |
| absolute_return_only | 1237 | 2.948 | 1 of 5 events | 2 of 5 events | 0 of 20 flags | 12 flags near negative controls |
| random_same_count_mean_1000_seeds | 1414 | 3.369 | 1.111 of 5 events on average | 1.864 of 5 events on average | 0.020 of 20 flags on average | 6.722 flags near negative controls on average |

The reference detector does **not** beat the absolute-return-only baseline on recall or precision: both match 1 of 5 events in the primary window, 2 of 5 events in the secondary window, and 0 of 20 flags at k=20, while the reference produces 1,414 flags versus 1,237. It does improve recall over the volume-only baseline in this tiny event set. The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds; its non-integer event and SOPAT counts are averages, not observed cases.

## Sensitivity grid

| Z cutoff | Rolling window | Flags | Flags/ticker-year | Primary recall |
|---:|---:|---:|---:|---|
| 2.5 | 20 | 3182 | 7.582 | 2 of 5 events |
| 2.5 | 40 | 2766 | 6.591 | 1 of 5 events |
| 2.5 | 60 | 2552 | 6.081 | 2 of 5 events |
| 2.5 | 120 | 2232 | 5.318 | 2 of 5 events |
| 3 | 20 | 1815 | 4.325 | 2 of 5 events |
| 3 | 40 | 1534 | 3.655 | 1 of 5 events |
| 3 | 60 | 1414 | 3.369 | 1 of 5 events |
| 3 | 120 | 1229 | 2.928 | 1 of 5 events |
| 3.5 | 20 | 1118 | 2.664 | 1 of 5 events |
| 3.5 | 40 | 933 | 2.223 | 1 of 5 events |
| 3.5 | 60 | 832 | 1.982 | 1 of 5 events |
| 3.5 | 120 | 692 | 1.649 | 0 of 5 events |
| 4 | 20 | 719 | 1.713 | 1 of 5 events |
| 4 | 40 | 596 | 1.420 | 1 of 5 events |
| 4 | 60 | 488 | 1.163 | 1 of 5 events |
| 4 | 120 | 397 | 0.946 | 0 of 5 events |

10 of 16 sensitivity cells match 1 of 5 events; 2 of 16 match 0 of 5 events. Flag load ranges from 397 to 3182. No cell was selected to improve the labeled-event result.




## Triage layer

These are descriptive pipeline counts, not performance measures.

- **1414** total anomaly flags: **548** with matched news context and **866** without.
- Matched-news classification categories: **buyout_opr: 1**, **capital_increase: 4**, **dividend: 18**, **earnings_results: 200**, **governance: 13**, **other_news: 311**, **suspension: 1**.
- **10 of 1414** anomaly flags survive into the **16-row** refined watchlist.
- **1 of 5** evaluated-event tickers appear on the refined watchlist.

The mutually exclusive watchlist funnel excludes **856** flags for being single-signal only, **11** for having matched news only, and **537** for both conditions. Across the evaluable primary windows, GIF had a flag on 2024-10-22, excluded by single signal only; UADH and LSTR and SERVI and STPAP had no flags. A missing ilboursa match alone is not suspicious.


## Limitations

Only 6 positive events have repository sources, only 5 overlap the trading-data window, and the Phase 2 held-out set remains tiny. Original reference parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. Known-event hit rates against this incomplete list can undercount relevant flags. These results cannot support a general performance claim or model training. Intervals are dominated by the tiny denominator.
