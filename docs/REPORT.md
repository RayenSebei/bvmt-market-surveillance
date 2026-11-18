# BVMT Market Surveillance — October 2026 Report

> **Statistical screening tool for human review, not a fraud verdict.**

## Executive summary

The refreshed project covers **85 stored series and 67,035 price rows from 17 June 2021 through 12 October 2026**: 83 company-share symbols plus PX1 (TUNINDEX) and TBIDX (Tunisian Bond Index). It also contains **12,498 deduplicated news records**. With the fixed reference settings—60 valid prior observations and a z-score cutoff of 3.0—the pipeline produces **1,414 flags**, including **21 combined price-and-volume flags**, and a **16-row refined watchlist**.

The original three sourced positives still reproduce **1 of 3** for `reference_v1`: GIF is a hit, LSTR and SERVI are misses. The expanded Phase 2 registry has **5 evaluable sourced positives**, with reference recall **1 of 5** (95% Wilson 0.04–0.62). Only one positive is held out, so no new method qualifies for adoption. The six registered candidate variants, all baselines, dates, and uncertainty intervals are in [PHASE2_RESULTS.md](PHASE2_RESULTS.md).

## Data refresh and integrity

The incremental updater added **5,223 price rows across 79 ticker files** and **648 news rows**. It rebuilt both combined price files without altering any pre-snapshot source observation. CGF and TSI were explicitly attempted but unavailable, so no rows were invented.

The canonical pre-refresh combined news file contained **11,850 unique rows**. A previously reported count of 11,944 came from summing every per-symbol file, which accidentally included **94 rows in `news_GIF_test.csv`**, a test artifact intentionally excluded from the combined dataset. The correct reconciliation is **11,850 + 648 = 12,498**.

The 12 October market rows were retained. Collection completed at approximately 20:21 Tunis time, after the published exchange session closes, and 62 symbols had an observation that day versus 57–62 on the preceding sessions. These checks provide no indication that the final date is a partial intraday snapshot.

The read-only new-row audit is in [`NEW_SCRAPE_ROW_AUDIT.csv`](NEW_SCRAPE_ROW_AUDIT.csv). Among 5,223 appended rows, 140 merit review: 134 have zero volume, five have an absolute close-to-close return above 15%, and one has an OHLC inconsistency. Four of those rows are current flags—ASSAD on 2026-10-08, HL on 2026-06-30, SITS on 2026-06-26, and TRE on 2026-09-15—and each is in the greater-than-15% group. No zero-volume row and no OHLC-inconsistent row became a flag. The source rows were listed, not edited.

## Detector correctness

Returns across gaps longer than 10 calendar days are excluded. The return baseline is calculated from the most recent 60 valid prior returns, excluding the current observation. This prevents one excluded gap return from blanking the next 60 z-scores while keeping the reference calculation independent of the event labels.

Source OHLC values remain raw. Quality issues are logged for human review rather than silently clamped. News classification preserves both the nearest headline available on or before a flag and the nearest later headline, so retrospective context cannot hide information available at the time.

## Original three-case reference audit

The original reference cross-check has three sourced positives with coverage in both windows. The primary window is 30 calendar days before through five days after each event; the secondary starts 60 days before. These historical figures are preserved separately from the expanded Phase 2 comparison:

- **GIF, 2024-10-25:** hit; first matching flag 2024-10-22, three days before the event.
- **LSTR, 2024-07-23:** miss.
- **SERVI, 2024-01-11:** miss; newly evaluable because newly downloaded observations extend through 2024-01-08.

Original three-case comparisons:

| Method | Flags | Flags/ticker-year | Primary recall | Secondary recall | Precision at 20 |
|---|---:|---:|---:|---:|---:|
| Reference union | 1,414 | 3.369 | 1 of 3 | 1 of 3 | 0 of 20 |
| Volume z-score only | 198 | 0.472 | 0 of 3 | 0 of 3 | 0 of 20 |
| Absolute return only | 1,237 | 2.948 | 1 of 3 | 1 of 3 | 0 of 20 |
| Random, same count, 1,000-seed mean | 1,414 | 3.369 | 0.666 of 3 | 1.075 of 3 | 0.014 of 20 |

The reference did not beat the return-only baseline in the original three-case comparison and created 177 more flags. The sensitivity grid is reporting only and was not used to change the reference detector. Expanded Phase 2 controls and results are reported separately.

These are descriptive case studies, not an accuracy estimate. The expanded set and its one-positive held-out split remain far too small to support a general performance claim.

## Dashboard and reproducibility

The React terminal displays the expanded method comparison and Wilson intervals. The seven-page Flask `templates/` + `static/` dashboard is deprecated but retained while remaining features are migrated and API coverage is checked. Remove it only in a separate reviewed change after parity, redirects, and screenshots are verified.

The generated manifest hashes text after canonical LF normalization, so freshness checks are portable across Windows, Linux, and macOS. Pipeline status logs require the explicitly enabled execution API and its bearer token. The default command reads source CSVs and regenerates evaluation outputs without network or AI calls.

## Limitations

- The expanded sourced positive set contains only five evaluable events, with one held-out event. Wilson and bootstrap intervals cannot rescue the small denominator.
- TINV, CGF, and UBCI have unsupported original claims/dates. TSI has a CMF source but no listed trading series; UADH has a BVMT source.
- Thin trading, zero-volume observations, delistings, incomplete news, and survivorship bias affect interpretation.
- ilboursa is the single stored news source. A nearby headline is context, not proof of cause; a missing local match is not suspicious by itself. The rule-based news sample has 100 empty human-label cells for review.
- AI triage was not run. If explicitly enabled later, it produces an **unvalidated draft opinion**. To test it, sample cases before viewing AI output, collect two independent human priority labels, measure agreement (including chance-adjusted agreement), and review disagreements. Do not claim validation until that protocol is completed.

## Reproduce

```bash
python -m pip install -r requirements.txt
python run_all.py
python -m pytest -q
python app.py
```

Generated evaluation tables and the portable freshness manifest are in `outputs/evaluation/`.
