# BVMT Market Surveillance — Project Report

> **Final delivery report**
>
> **Delivered dataset:** 85 local symbols, 61,812 price rows
>
> **Reference screen:** rolling window 60, z-score cutoff 3.0
>
> **Purpose:** statistical screening for human review, not a legal finding

## Plain-English summary

- The project checks local BVMT price and volume history for observations that are unusual relative to each stock's own recent history.
- The corrected 85-symbol run produced 947 review flags and 14 refined-watchlist rows.
- Against the small sourced case set, it matched 0 of 2 events in the 30-day window and 0 of 3 events in the 60-day window.
- None of the 20 highest-ranked flags is near either primary-window event; incomplete event labels mean this does not prove those flags are false positives.
- Results are case studies for human review, not a statistical performance estimate or a legal conclusion.

## Abstract

This project builds a transparent statistical screening workflow for the Tunisian stock market. It reads historical price, volume, and news records; flags unusual activity; adds possible public-news context; and presents a review queue in a web dashboard. The corrected reference detector produced 947 flags, or 2.397 flags per ticker-year. In a small source-backed evaluation, it matched 0 of 2 positive events in the primary window and 0 of 3 in the secondary window. Every result is a prompt for human review.

## 1. Introduction and context

The Bourse de Valeurs Mobilières de Tunis (BVMT) contains many thinly traded shares. On these shares, a large price or volume movement may be important, but it may also be ordinary market noise. A useful first screening system should therefore be transparent, reproducible, and careful about its claims.

The project has three goals:

1. detect unusual price and volume observations with simple statistical rules;
2. add news and event context so a person can review the flags efficiently; and
3. evaluate the rules honestly against a small, source-audited event set.

The system does not train a machine-learning model. The labeled sample is too small for that approach to be defensible.

### Glossary

- **Z-score:** how far an observation is from a stock's recent average, measured in recent standard deviations.
- **Rolling window:** the moving block of earlier observations used to calculate that recent average and variation.
- **Volume:** the number of shares traded in an observed session.
- **Delisting:** removal of a security from exchange trading.
- **Recall:** how many known, evaluable events had at least one nearby flag, always reported here as “x of n events.”
- **Baseline:** a simpler comparison method used to show whether the reference rule adds useful signal.
- **False positive:** a flag that review later determines is not associated with the event or condition being studied.

## 2. Data

The canonical local data is in `bvmt_data/`. The delivered derived price file, `_all_tickers_full.csv`, contains 61,812 observations for 85 symbols from 17 June 2021 to 17 June 2026. It is rebuilt from the valid individual ticker files before analysis. The protected `_all_tickers_combined.csv` remains unchanged with 44,531 observations for 60 symbols, and the combined news file remains unchanged with 11,850 records.

The 25 price symbols omitted from the protected combined file are AB, ADWYA, AETEC, AL, AMS, ARTES, ASSAD, ASSMA, AST, ATB, ATL, BH, BHASS, BHL, BIAT, BL, BNA, BNASS, BT, BTE, CC, CELL, CREAL, TJARI, and TJL. Repository code showed the cause: the scraper skipped a ticker when its individual CSV already existed but built the combined output only from frames downloaded in that run. The code now rebuilds a combined output from all individual files after a future authorized scrape; no scraper was run for this delivery. UBCI, TINV, and UADH were already present. **CGF and TSI have no ticker files, are not in either price dataset, and cannot be evaluated.**

The evaluation event table is separate at `data/evaluation/events.csv`. Its primary date is the earliest public suspension, court ruling, or first announcement found in repository evidence. It also preserves every original date from `labeled_events.csv` and a later public date where one exists. Missing evidence is written as `SOURCE_NEEDED`; dates are never guessed or moved to improve a result.

## 3. Methods

### 3.1 Statistical screen

The reference detector works independently for each ticker. It requires 60 valid prior observations for each rolling baseline and excludes the current observation from that baseline, preventing look-ahead. Source OHLC values are retained; 58 close-range violations are recorded in `anomaly_data_quality.csv` rather than silently corrected.

- Volume is transformed with `log(1 + volume)` before its z-score is calculated. This reduces the effect of very large values in thinly traded shares.
- The volume standard deviation has a floor of 0.10.
- The return standard deviation has a floor of 0.01, equal to a one-point daily return scale.
- A return across a trading gap longer than 10 calendar days is excluded because it is not a true one-day return.
- A volume or absolute-return z-score above 3.0 creates a reference flag.

These parameters were not changed after looking at the labeled events. The 16-cell sensitivity grid is reporting only.

### 3.2 Context and review queue

The next stages cross-reference flags with local news, classify the available context, and produce a smaller watchlist. Matches use neutral `NEWS_MATCH_FOUND` and `NO_LOCAL_MATCH` labels. Each match records whether the headline was available by the flag date or is later retrospective context. The corrected run produces 14 refined rows; absence of a local match is a prioritisation cue, not evidence of misconduct.

### 3.3 AI-assisted triage

Groq triage uses `openai/gpt-oss-120b`, configured through `GROQ_MODEL`. An earlier 40-token response used 38 tokens for reasoning and ended with empty visible content. The client now requests a 1,500-token budget, low reasoning effort, and JSON output. Empty content is retried and then skipped safely while preserving the previous output.

The earlier 17-row run used 17 calls under a hard 40-call ceiling. Its output belongs to the superseded queue and is preserved for provenance but hidden by the dashboard because it does not match the current 14-row refined queue. AI triage now requires explicit `--with-ai`; these opinions are never verdicts and never change evaluation labels or detector parameters.

## 4. Evaluation design

The primary hit window was defined before calculation: from 30 calendar days before through 5 days after the event. A secondary view starts 60 days before and ends 5 days after. A positive event is eligible for headline recall only when it has a repository source and enough trading-window coverage.

The reported measures are:

- recall on eligible positive events;
- precision at 10, 20, and 50 ranked flags, ordered by `max(abs(volume_zscore), abs(return_zscore))`, with earlier date and ticker symbol as tie-breaks;
- flags per ticker-year;
- lead-time and coverage detail;
- behavior near the SOPAT negative control; and
- comparison with volume-only, return-only, and same-count random baselines.

This definition of precision is conservative because many real events are not labeled.

### 4.1 Event audit

| Event | Primary date/type | Original label | Secondary date | Source/confidence | Evaluable | Reason |
|---|---|---|---|---|---|---|
| TINV | 2025-10-06, other | 2025-10-06 | — | `SOURCE_NEEDED`, low | No | No supporting repository source |
| UADH | 2026-03-24, suspension | 2026-03-24 | — | `SOURCE_NEEDED`, low | No | No supporting repository source |
| TSI | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No ticker data; cannot be evaluated |
| CGF | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No ticker data; cannot be evaluated |
| UBCI | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No event date or supporting source |
| GIF Filter | 2024-10-25, suspension | 2024-10-25 | 2024-11-12 | [IlBoursa](https://www.ilboursa.com/marches/la-bourse-de-tunis-decide-la-radiation-de-la-societe-gif-filter_49247), high | Yes | Source and primary-window coverage available |
| Electrostar (LSTR) | 2024-07-23, suspension | 2024-07-23 | 2024-07-24 | [IlBoursa](https://www.ilboursa.com/marches/en-cessation-de-paiement-le-tribunal-declare-la-faillite-de-la-societe-electrostar_47391), high | Yes | Source and primary-window coverage available |
| Servicom (SERVI) | 2024-01-11, suspension | 2024-01-11 | 2024-03-27 | [IlBoursa](https://www.ilboursa.com/marches/le-tribunal-de-tunis-declare-la-faillite-de-la-societe-servicom_45451), high | No | Trading data ends before the primary window |
| MIP | 2024-08-05, public announcement | 2024-09-10 | 2024-09-10 | [IlBoursa](https://www.ilboursa.com/marches/vers-la-mise-en-faillite-directe-de-la-societe-mip_47579), medium | No | Exploratory event excluded from headline metrics |
| SOPAT | 2023-09-19, public announcement | 2023-09-20 | 2023-09-20 | [IlBoursa](https://www.ilboursa.com/marches/le-groupe-la-rose-blanche-retire-la-sopat-de-la-cote-de-la-bourse_42686), high | No | Negative control, not a positive event |

The TINV label remains 6 October 2025. Its stored date type is `other`, explicitly not `public_announcement`, and it has no supporting repository source. The detector flags on 13 October and 22 October 2025 are after the label. The date was not moved to improve the result.

## 5. Results

There are 3 source-backed positive events. The 30-day denominator is 2 because GIF and LSTR have trading observations in that window, while SERVI's trading data ends on 30 November 2023, before its 30-day window begins. The 60-day window starts early enough to overlap SERVI's last observations, so its denominator is 3. The corrected reference detector matched 0 of 2 events in the primary window and 0 of 3 events in the secondary window.

| Method | Flags | Flags per ticker-year | Recall, -30/+5 | Recall, -60/+5 | Precision at 20 | SOPAT-window flags |
|---|---:|---:|---:|---:|---:|---:|
| Reference union | 947 | 2.397 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| Volume z-score only | 192 | 0.486 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| Absolute return only | 771 | 1.952 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 flags in 1 window |
| Random, same count, mean of 1,000 seeds | 947 | 2.397 | 0.059 of 2 events on average | 0.111 of 3 events on average | 0 of 20 flags on average | 0.315 flags in 1 window on average |

For the reference detector, precision at 10, 20, and 50 is 0 of 10, 0 of 20, and 0 of 50 ranked flags. The **0 of 20** result means none of the 20 largest ranking scores occurs inside the fixed primary window around GIF or LSTR. It does not establish that those 20 flags are false positives because the event list is small and incomplete.

No corrected reference flag falls in either fixed event window. The former GIF hit depended on the superseded warm-up and silent close-correction behavior and is not retained as evidence.

The reference detector does not beat the absolute-return-only baseline on recall or precision. Both match 0 of 2 events in the primary window, 0 of 3 events in the secondary window, and 0 of 20 top-ranked flags, while the reference produces 947 flags and the return-only baseline produces 771.

The sensitivity grid contains 16 parameter combinations, each requiring its full configured history. Four 20-observation cells match 1 of 2 events; the other 12 cells match 0 of 2. Flag load ranges from 209 to 2,532. This grid was not used to choose a new reference setting.

### 5.1 Ranking and top 20

Flags are ranked by `max(abs(volume_zscore), abs(return_zscore))`, highest first. Ties use earlier date and then ticker symbol. “Illiquid” means the ticker's median daily volume is at or below 500 shares, the 25th percentile across tickers represented in corrected reference flags. This liquidity label does not affect the ranking or detector.

| Rank | Ticker | Date | Ranking z-score | Illiquid |
|---:|---|---|---:|---|
| 1 | CITY | 2026-04-27 | 21.748 | No |
| 2 | CITY | 2026-04-28 | 19.703 | No |
| 3 | PGH | 2021-11-30 | 17.375 | No |
| 4 | ARTES | 2023-07-31 | 11.690 | No |
| 5 | ICF | 2022-09-01 | 11.664 | Yes |
| 6 | SOTET | 2025-07-29 | 11.502 | No |
| 7 | BNA | 2025-06-17 | 11.060 | No |
| 8 | ARTES | 2022-07-06 | 11.018 | No |
| 9 | BIAT | 2024-11-29 | 10.447 | No |
| 10 | CITY | 2024-07-08 | 9.696 | No |
| 11 | SMART | 2025-06-19 | 9.049 | No |
| 12 | STAR | 2025-09-17 | 8.657 | No |
| 13 | CITY | 2022-07-20 | 8.634 | No |
| 14 | TJARI | 2021-12-06 | 8.489 | No |
| 15 | ASSMA | 2026-06-17 | 7.671 | Yes |
| 16 | ASSAD | 2021-09-29 | 7.542 | No |
| 17 | SAM | 2023-07-31 | 7.452 | No |
| 18 | STPAP | 2026-04-27 | 7.398 | No |
| 19 | TJARI | 2025-04-30 | 7.360 | No |
| 20 | TPR | 2022-07-27 | 7.228 | No |

### 5.2 Coverage comparison

All 85 individual files pass the delivered build's input checks. PLTU has only 41 observations and is excluded from the reference anomaly detector as known-incomplete. The 85-symbol derived file adds the 25 valid omitted symbols without changing protected inputs. The archived 60-symbol outputs used the superseded 20-observation warm-up and silent close clamping, so their flag counts and event hits are retained only as provenance and are not directly comparable with the corrected reference.

![Baseline comparison](../outputs/evaluation/baseline_comparison.svg)

*Figure 1. Primary-window event hits for the delivered reference and three simple baselines. Counts are descriptive because the evaluable sample is very small.*

![Sensitivity heatmap](../outputs/evaluation/sensitivity_heatmap.svg)

*Figure 2. Event-hit counts across the fixed reporting grid. The grid was not used to change the reference parameters.*

## 6. Dashboard

The Flask dashboard has six English pages: Overview, Anomaly Feed, Stock Search, News Feed, Pipeline Status, and Evaluation. The two previously reported chart failures were not reproducible through their APIs. The old dashboard depended on external Chart.js delivery, so the final version replaces it with native SVG and CSS charts. The browser test showed distinct content on all six pages and no console warning or error.

![Dashboard overview](screenshots/overview.png)

*Figure 3. Dashboard Overview page using the delivered local outputs. Other requested page captures are listed as TODOs rather than linked as missing images.*

## 7. Limitations

- The headline denominator is only 2 evaluable positive events in the primary window and 3 in the secondary window; this is too small for a general performance estimate.
- Exact binomial intervals would be extremely wide and would not solve the evidence problem.
- Five positive cases remain `SOURCE_NEEDED`.
- CGF and TSI are not present in the price dataset and cannot be evaluated; they must not be interpreted as tested misses.
- There is no independent test set.
- The original reference parameters were hand chosen, although they were not tuned on this event set.
- Delisted firms can lose trading coverage before an event.
- The available files may have survivorship bias and missing public-news context.
- The protected 60-symbol combined file omitted 25 valid individual ticker files because of the scraper merge bug; the delivered derived file corrects coverage, but future data refreshes still require review.
- The ranked precision calculation underestimates unknown relevant cases.
- AI triage depends on an external model and can be inconsistent; its output requires human review.

## 8. Conclusion and future work

The project now provides a clean, reproducible screening workflow with explicit assumptions and an honest evaluation. Its strongest feature is transparency: each flag can be traced to a simple rule, each event has a source status, and missing evidence is not hidden.

Future work should expand the independently sourced event set, add formal market-calendar event studies, record disclosure timestamps, compare additional robust statistics, and evaluate on a later untouched period. A trained model should be considered only after a much larger labeled dataset exists.

## 9. Reproducibility

From the repository root:

```bash
python -m venv .venv
# Activate the environment, then:
python -m pip install -r requirements.txt
python run_all.py --skip-ai
python -m pytest -q
python app.py
```

`python run_all.py` includes optional AI triage but still uses existing local data. Scraping requires the explicit `--with-scrape` flag and was not used for this delivery.

Generated 85-symbol evaluation files are in `outputs/evaluation/`. The main tables are `events_table.csv`, `metrics.csv`, `baseline_comparison.csv`, `sensitivity.csv`, `top_20_flags.csv`, and `universe_comparison.csv`. The earlier 60-symbol outputs remain in `outputs/evaluation_60symbol/`.

## 10. References and data sources

- Local BVMT price and news extracts in `bvmt_data/`.
- Source URLs preserved in `data/evaluation/events.csv` and listed in the event audit above.
- Project methods and fixed parameters in `src/detection/anomaly_detector.py` and `src/evaluation/`.
- Full generated evaluation statement in `outputs/evaluation/summary.md`.

## Screenshot TODO

The following captures are intentionally not linked until real files are supplied:

- Anomaly Feed
- Stock Search
- News Feed
- Pipeline Status
- Evaluation
