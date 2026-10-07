# BVMT Market Surveillance — Project Report

## Abstract

This project builds a transparent statistical screening workflow for the Tunisian stock market. It reads historical price, volume, and news records; flags unusual activity; adds possible public-news context; and presents a review queue in a web dashboard. The reference detector produced 1,027 flags across the observed data, or 3.607 flags per ticker-year. In a small source-backed evaluation, it matched 1 of 2 positive events that had trading data in the fixed evaluation window. This is a case-study-level evaluation, not a statistical performance estimate. Every result is a prompt for human review, not a legal conclusion.

## 1. Introduction and context

The Bourse de Valeurs Mobilières de Tunis (BVMT) contains many thinly traded shares. On these shares, a large price or volume movement may be important, but it may also be ordinary market noise. A useful first screening system should therefore be transparent, reproducible, and careful about its claims.

The project has three goals:

1. detect unusual price and volume observations with simple statistical rules;
2. add news and event context so a person can review the flags efficiently; and
3. evaluate the rules honestly against a small, source-audited event set.

The system does not train a machine-learning model. The labeled sample is too small for that approach to be defensible.

## 2. Data

The canonical local dataset is in `bvmt_data/`. The combined price file contains 44,531 observations for 60 symbols from 17 June 2021 to 17 June 2026. The combined news file contains 11,850 records. There are 85 valid individual ticker CSVs locally; Stock Search now merges those files with the combined list, so BIAT, BNA, and 23 other locally available symbols are no longer omitted. Individual ticker and news CSVs remain unchanged by this delivery work.

The evaluation event table is separate at `data/evaluation/events.csv`. Its primary date is the earliest public suspension, court ruling, or first announcement found in repository evidence. It also preserves every original date from `labeled_events.csv` and a later public date where one exists. Missing evidence is written as `SOURCE_NEEDED`; dates are never guessed or moved to improve a result.

## 3. Methods

### 3.1 Statistical screen

The reference detector works independently for each ticker. It uses the previous 60 trading observations as its rolling baseline and excludes the current observation from that baseline, preventing look-ahead.

- Volume is transformed with `log(1 + volume)` before its z-score is calculated. This reduces the effect of very large values in thinly traded shares.
- The volume standard deviation has a floor of 0.10.
- The return standard deviation has a floor of 0.01, equal to a one-point daily return scale.
- A return across a trading gap longer than 10 calendar days is excluded because it is not a true one-day return.
- A volume or absolute-return z-score above 3.0 creates a reference flag.

These parameters were not changed after looking at the labeled events. The 16-cell sensitivity grid is reporting only.

### 3.2 Context and review queue

The next stages cross-reference flags with local news, classify the available context, and produce a smaller watchlist. During the final pipeline repair, `watchlist_refined.csv` changed from 107 stale rows to 12 current rows because its input changed to the current 12-row `watchlist.csv`. The former 107-row file was an old artifact produced from an earlier, larger watchlist. Classification now runs before refinement, so refinement receives the current input. No detector threshold, refinement rule, or labeled-event parameter changed.

### 3.3 AI-assisted triage

Groq triage uses `openai/gpt-oss-120b`, configured through `GROQ_MODEL`. An earlier 40-token response used 38 tokens for reasoning and ended with empty visible content. The client now requests a 1,500-token budget, low reasoning effort, and JSON output. Empty content is retried and then skipped safely while preserving the previous output.

The authorized 12-row run returned 8 `worth_investigating` draft assessments and 4 `likely_noise` draft assessments, with no empty reasoning fields. These are opinions for human review, never verdicts. The model does not change the reference evaluation labels or detector parameters.

## 4. Evaluation design

The primary hit window was defined before calculation: from 30 calendar days before through 5 days after the event. A secondary view starts 60 days before and ends 5 days after. A positive event is eligible for headline recall only when it has a repository source and enough trading-window coverage.

The reported measures are:

- recall on eligible positive events;
- precision at 10, 20, and 50 ranked flags, where a match means proximity to a known event;
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
| TSI | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No event date or supporting source |
| CGF | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No event date or supporting source |
| UBCI | —, other | — | — | `SOURCE_NEEDED`, not assessed | No | No event date or supporting source |
| GIF Filter | 2024-10-25, suspension | 2024-10-25 | 2024-11-12 | [IlBoursa](https://www.ilboursa.com/marches/la-bourse-de-tunis-decide-la-radiation-de-la-societe-gif-filter_49247), high | Yes | Source and primary-window coverage available |
| Electrostar (LSTR) | 2024-07-23, suspension | 2024-07-23 | 2024-07-24 | [IlBoursa](https://www.ilboursa.com/marches/en-cessation-de-paiement-le-tribunal-declare-la-faillite-de-la-societe-electrostar_47391), high | Yes | Source and primary-window coverage available |
| Servicom (SERVI) | 2024-01-11, suspension | 2024-01-11 | 2024-03-27 | [IlBoursa](https://www.ilboursa.com/marches/le-tribunal-de-tunis-declare-la-faillite-de-la-societe-servicom_45451), high | No | Trading data ends before the primary window |
| MIP | 2024-08-05, public announcement | 2024-09-10 | 2024-09-10 | [IlBoursa](https://www.ilboursa.com/marches/vers-la-mise-en-faillite-directe-de-la-societe-mip_47579), medium | No | Exploratory event excluded from headline metrics |
| SOPAT | 2023-09-19, public announcement | 2023-09-20 | 2023-09-20 | [IlBoursa](https://www.ilboursa.com/marches/le-groupe-la-rose-blanche-retire-la-sopat-de-la-cote-de-la-bourse_42686), high | No | Negative control, not a positive event |

The TINV label remains 6 October 2025. Its stored date type is `other`, explicitly not `public_announcement`, and it has no supporting repository source. The detector flags on 13 October and 22 October 2025 are after the label. The date was not moved to improve the result.

## 5. Results

There are 3 source-backed positive events. Two have trading data in the primary window and all 3 have trading data in the secondary window. The reference detector matched 1 of 2 events in the primary window and 1 of 3 events in the secondary window.

| Method | Flags | Flags per ticker-year | Recall, -30/+5 | Recall, -60/+5 | Precision at 20 | SOPAT-window flags |
|---|---:|---:|---:|---:|---:|---:|
| Reference union | 1,027 | 3.607 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 |
| Volume z-score only | 140 | 0.492 | 0 of 2 events | 0 of 3 events | 0 of 20 flags | 0 |
| Absolute return only | 903 | 3.171 | 1 of 2 events | 1 of 3 events | 0 of 20 flags | 0 |
| Random, same count, mean of 1,000 seeds | 1,027 | 3.607 | 0.492 of 2 events on average | 0.929 of 3 events on average | 0.008 of 20 flags on average | 0.600 on average |

For the reference detector, precision at 10, 20, and 50 is 0 of 10, 0 of 20, and 0 of 50 ranked flags. This result looks weak, but it must not be read as proof that every other flag is irrelevant: the event list is known to be incomplete.

GIF is the only reference hit. Its first matching flag is 22 October 2024: 3 days before the primary suspension date of 25 October and 21 days before the secondary article date of 12 November.

The reference detector does not beat the absolute-return-only baseline on recall or precision. Both match 1 of 2 events in the primary window, 1 of 3 events in the secondary window, and 0 of 20 top-ranked flags, while the reference produces 1,027 flags and the return-only baseline produces 903. The reference matches more events than the volume-only baseline, but with a much larger review load.

The sensitivity grid contains 16 parameter combinations. Primary recall remains 1 of 2 events in 14 cells. It becomes 0 of 2 events only for a 120-day window with z cutoffs of 3.5 and 4.0. Flag load ranges from 329 to 1,862. This grid was not used to choose a new reference setting.

![Baseline comparison](../outputs/evaluation/baseline_comparison.svg)

![Sensitivity heatmap](../outputs/evaluation/sensitivity_heatmap.svg)

## 6. Dashboard

The Flask dashboard has six English pages: Overview, Anomaly Feed, Stock Search, News Feed, Pipeline Status, and Evaluation. The two previously reported chart failures were not reproducible through their APIs. The old dashboard depended on external Chart.js delivery, so the final version replaces it with native SVG and CSS charts. The browser test showed distinct content on all six pages and no console warning or error.

![Dashboard overview](screenshots/overview.png)

The Overview image above is the only screenshot currently referenced. Additional page captures can be added under `docs/screenshots/` without changing the report text or results.

## 7. Limitations

- The headline denominator is only 2 evaluable positive events in the primary window and 3 in the secondary window; this is too small for a general performance estimate.
- Exact binomial intervals would be extremely wide and would not solve the evidence problem.
- Five positive cases remain `SOURCE_NEEDED`.
- There is no independent test set.
- The original reference parameters were hand chosen, although they were not tuned on this event set.
- Delisted firms can lose trading coverage before an event.
- The available files may have survivorship bias and missing public-news context.
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

Generated evaluation files are in `outputs/evaluation/`. The main tables are `events_table.csv`, `metrics.csv`, `baseline_comparison.csv`, and `sensitivity.csv`.

## 10. References and data sources

- Local BVMT price and news extracts in `bvmt_data/`.
- Source URLs preserved in `data/evaluation/events.csv` and listed in the event audit above.
- Project methods and fixed parameters in `src/detection/anomaly_detector.py` and `src/evaluation/`.
- Full generated evaluation statement in `outputs/evaluation/summary.md`.
