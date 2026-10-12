# BVMT Market Surveillance — October 2026 Report

> **Statistical screening tool for human review, not a fraud verdict.**

## Executive summary

The refreshed project covers **85 symbols and 67,035 price rows from 17 June 2021 through 12 October 2026**, plus **12,498 deduplicated news records**. With the fixed reference settings—60 valid prior observations and a z-score cutoff of 3.0—the pipeline produces **1,414 flags**, including **21 combined price-and-volume flags**, and a **16-row refined watchlist**.

The source-backed case study now has three evaluable positive events in both fixed windows. The detector hits **1 of 3**: GIF is a hit three days before suspension; LSTR is a miss; SERVI is a miss. SERVI was never evaluated in the earlier primary-window result. It became evaluable only because the October refresh newly downloaded SERVI trading data through **2024-01-08**, three days before its 2024-01-11 event. This denominator change is a data-coverage change, not tuning; thresholds, floors, windows, and event dates were unchanged.

## Data refresh and integrity

The incremental updater added **5,223 price rows across 79 ticker files** and **648 news rows**. It rebuilt both combined price files without altering any pre-snapshot source observation. CGF and TSI were explicitly attempted but unavailable, so no rows were invented.

The canonical pre-refresh combined news file contained **11,850 unique rows**. A previously reported count of 11,944 came from summing every per-symbol file, which accidentally included **94 rows in `news_GIF_test.csv`**, a test artifact intentionally excluded from the combined dataset. The correct reconciliation is **11,850 + 648 = 12,498**.

The 12 October market rows were retained. Collection completed at approximately 20:21 Tunis time, after the published exchange session closes, and 62 symbols had an observation that day versus 57–62 on the preceding sessions. These checks provide no indication that the final date is a partial intraday snapshot.

The read-only new-row audit is in [`NEW_SCRAPE_ROW_AUDIT.csv`](NEW_SCRAPE_ROW_AUDIT.csv). Among 5,223 appended rows, 140 merit review: 134 have zero volume, five have an absolute close-to-close return above 15%, and one has an OHLC inconsistency. Four of those rows are current flags—ASSAD on 2026-10-08, HL on 2026-06-30, SITS on 2026-06-26, and TRE on 2026-09-15—and each is in the greater-than-15% group. No zero-volume row and no OHLC-inconsistent row became a flag. The source rows were listed, not edited.

## Detector correctness

Returns across gaps longer than 10 calendar days are excluded. The return baseline is calculated from the most recent 60 valid prior returns, excluding the current observation. This prevents one excluded gap return from blanking the next 60 z-scores. The correction restored valid coverage without choosing parameters against event labels. Full historical before/after evidence is preserved in [`DETECTOR_RETURN_BASELINE_FIX.md`](DETECTOR_RETURN_BASELINE_FIX.md).

Source OHLC values remain raw. Quality issues are logged for human review rather than silently clamped. News classification preserves both the nearest headline available on or before a flag and the nearest later headline, so retrospective context cannot hide information available at the time.

## Evaluation

The primary window is 30 calendar days before through five days after each event. The secondary window begins 60 days before. The event registry has three sourced positives with coverage in both windows:

- **GIF, 2024-10-25:** hit; first matching flag 2024-10-22, three days before the event.
- **LSTR, 2024-07-23:** miss.
- **SERVI, 2024-01-11:** miss; newly evaluable because newly downloaded observations extend through 2024-01-08.

Current comparisons:

| Method | Flags | Flags/ticker-year | Primary recall | Secondary recall | Precision at 20 |
|---|---:|---:|---:|---:|---:|
| Reference union | 1,414 | 3.369 | 1 of 3 | 1 of 3 | 0 of 20 |
| Volume z-score only | 198 | 0.472 | 0 of 3 | 0 of 3 | 0 of 20 |
| Absolute return only | 1,237 | 2.948 | 1 of 3 | 1 of 3 | 0 of 20 |
| Random, same count, 1,000-seed mean | 1,414 | 3.369 | 0.666 of 3 | 1.075 of 3 | 0.014 of 20 |

The reference does not beat the return-only baseline on recall or precision and creates 177 more flags. The sensitivity grid ranges from 397 to 3,182 flags: 14 cells hit 1 of 3 events and two cells hit none. It is reporting only and was not used to change the reference detector. SOPAT remains the negative control with zero primary-window flags.

These results are descriptive case studies, not an accuracy estimate. Three positive events are far too few to support a general performance claim, and incomplete labels make precision conservative.

## Dashboard and reproducibility

The offline Flask dashboard exposes the complete review queue and adds a keyboard command palette, clickable flag calendar, volume/return surveillance radar, line/candlestick stock views, z-score panel, drag zoom, a read-only detector playground, and annotated GIF/LSTR case studies. All visuals use native SVG and remain responsive at 380 px. The evaluation page explicitly explains why SERVI changed the denominator and identifies its miss.

The generated manifest hashes text after canonical LF normalization, so freshness checks are portable across Windows, Linux, and macOS. Pipeline status logs require the explicitly enabled execution API and its bearer token. The default command performs analysis only and makes neither network nor AI calls.

## Limitations

- The sourced positive set contains only three evaluable events.
- CGF and TSI remain unavailable and cannot be evaluated.
- Thin trading, zero-volume observations, delistings, incomplete news, and survivorship bias affect interpretation.
- A nearby headline is context, not proof of cause; a missing headline is not evidence of misconduct.
- AI triage, when explicitly enabled, is a draft opinion for a human reviewer.

## Reproduce

```bash
python -m pip install -r requirements.txt
python run_all.py
python -m pytest -q
python app.py
```

Generated evaluation tables and the portable freshness manifest are in `outputs/evaluation/`.
