# Phase 2 starting audit

1. The delivered analysis has 85 stored series—83 company-share symbols plus PX1 (TUNINDEX) and TBIDX (Tunisian Bond Index)—and 67,035 observations through 2026-10-12; the source CSVs are inputs, not files to edit.
2. `anomaly_detector.py` excludes TBIDX and PLTU, but not PX1/TUNINDEX; PX1 has 15 rows in the delivered reference flag file.
3. The existing spike detector uses 60 prior observations, a 3.0 z cutoff, log1p volume, standard-deviation floors, and a 10-day return-gap guard.
4. Its delivered reference output is 1,414 flags; the original three sourced positives give 1 of 3 primary-window hits.
5. `refine_watchlist.py` already builds the PX1 index return and index z-score for watchlist context; it does not change the reference detector.
6. That watchlist code already computes `excess_return` as stock return minus same-day index return, but candidate evaluation does not yet use it.
7. The same code already tags selected watchlist rows `MARKET_WIDE` or `COMPANY_SPECIFIC`; the tag is not available for every detector flag.
8. `decay_detector.py` already compares recent and prior six-month volume, flags ratio below 0.2 or 90 inactive days, and uses a 1,000-share baseline floor; its current output is a latest-snapshot result, not historical point-in-time predictions.
9. Evaluation has three sourced positives, one SOPAT negative control, five `SOURCE_NEEDED` cases, a 1,000-seed random comparator, and a 16-cell sensitivity grid for reporting.
10. There is no locked development/held-out event split, no Wilson intervals or paired adoption test, and no comprehensive candidate comparison; these are Phase 2 additions.
