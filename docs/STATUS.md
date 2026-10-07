# Delivery Status

## Phase 1 — Cleanup (complete, commit `78eed82`)

- Done: Confirmed duplicate scripts differ only in usage docstrings or equivalent string spelling; kept the copies used by `run_all.py`.
- Done: Confirmed the stale `decay_classified.csv` has the same eight data rows as the primary file and preserved a verified 189-file backup at `../bvmt_backup/data_bvmt_data` before deletion.
- Done: Removed scratch/debug files, stale duplicate data, and the unused Render-era dependency.
- Next: Complete Phase 2 pipeline work.
- Blockers: None.

## Phase 2 — Pipeline, key, and model (complete, commit `aca2db1`)

- Done: Added bounded dependencies and corrected `.env.example` without touching `.env`.
- Done: Added `GROQ_MODEL` support, robust JSON extraction, mock coverage, and graceful output preservation on missing key/client/API failure.
- Done: One permitted live Groq request returned HTTP 200 for `openai/gpt-oss-120b`; the response content field was empty, so no result was interpreted.
- Done: Added an analysis-only default runner with `--with-scrape` and `--skip-ai`, readable progress, and fail-fast errors.
- Done: Verified the snapshot at `../bvmt_snapshot` (187 files), then completed the default pipeline without scraping; AI triage preserved its existing output because `openai` is not installed locally.
- Done: The run changed five derived files at the byte level; four were semantically unchanged, while `watchlist_refined.csv` correctly shrank from 107 stale rows to the current 12-row watchlist because classification now precedes refinement.
- Done: All 178 protected raw CSVs match the snapshot (manifest SHA-256 `99dc1b74585dc846ed17f5e0403a0d6b6ab0069d792ebe6af9660b33b9647e8d`).
- Next: Build the source-backed evaluation framework, baselines, and sensitivity analysis.
- Blockers: The optional AI package is absent locally; graceful fallback is verified and requirements now declare it.

## Step A — Integrity audit

- Done: Compared all 187 canonical data files with `../bvmt_snapshot` by filename and SHA-256.
- Done: Six derived files differ: `anomaly_classified.csv`, `anomaly_flags.csv`, `anomaly_summary.csv`, `decay_classified.csv`, `watchlist.csv`, and `watchlist_refined.csv`; all but `watchlist_refined.csv` are semantically unchanged rewrites.
- Done: Zero of 178 protected raw files differ. Protected means case-sensitive uppercase ticker CSVs, `news_*.csv`, `_all_tickers_combined.csv`, and `_all_news_combined.csv`.
- Done: Row counts before → after: anomaly flags 1027 → 1027; anomaly classified 1027 → 1027; anomaly summary 58 → 58; watchlist 12 → 12; watchlist refined 107 → 12; decay flags 8 → 8; decay classified 8 → 8.
- Done: The 179 → 178 correction was required because PowerShell `-match` is case-insensitive and mistakenly counted lowercase `watchlist.csv` as an uppercase ticker filename; the total is 178 protected + 9 derived = 187.
- Next: Step B Groq fix.
- Blockers: None.

## Step B — Groq triage fix

- Done: Installed only `requirements.txt` into the project `.venv`.
- Done: Diagnostic metadata confirmed `finish_reason=length`, 40 completion tokens, 38 reasoning tokens, 154 reasoning characters, and empty content.
- Done: Raised the completion budget to 1,500, requested low reasoning effort and JSON output, and added retry coverage for empty content.
- Done: Mock suite passes (4 tests), including empty-content retry and configured request fields.
- Done: The first post-fix live test returned a valid non-empty assessment.
- Done: Completed the authorized 12-row full triage; output has 12 rows, 8 `worth_investigating`, 4 `likely_noise`, and no empty reasoning. These are draft opinions for human review, never verdicts.
- Done: Used 15 live calls in total across the earlier empty-response check, diagnostic/fix checks, and the 12-row run; within the maximum of 20.
- Next: Finish and verify the source-backed evaluation framework, equivalence test, figures, and summary.
- Blockers: None.

## Step C — Phase 3 evaluation

- Done: Added a source-audited event table with date type, source, confidence, evaluability, and exclusion reason.
- Done: Defined the primary window as -30/+5 calendar days and secondary window as -60/+5 before computing metrics.
- Done: Produced reference metrics, precision@10/20/50, coverage/lead-time detail, volume and return baselines, a 1,000-seed same-count random baseline, the 16-cell sensitivity grid, two SVG figures, and `outputs/evaluation/summary.md`.
- Done: Added a 20-seed equivalence test showing NumPy window counts exactly match the slower pandas calculation; focused suite passes 5 tests.
- Done: Headline result is 1 of 2 evaluable events for both windows; source-backed positives are 3, but SERVI lacks window coverage. SOPAT has 0 reference flags in its primary window.
- Done: Reference parameters remain z=3.0 and rolling window=60; no labeled-event tuning occurred.
- Done: All 178 protected raw files still match `../bvmt_snapshot`.
- Next: Phase 4 comprehensive offline tests.
- Blockers: The evaluation is case-study-level only; five events remain `SOURCE_NEEDED`, and the evaluable positive denominator is two.

## Phase 4 — Tests

- Done: Added synthetic detector tests for spike detection, flat series, standard-deviation floors, gap-day exclusion, and no look-ahead.
- Done: Added classification/cross-reference fixtures, toy evaluation metrics, runner argument/fail-fast checks, Groq mocks, and the 20-seed random-baseline equivalence check.
- Done: Smoke-tested all 15 Flask routes (including the three dashboard aliases and mocked scrape trigger) against committed read-only fixtures.
- Done: Full offline suite passes: 32 tests in 0.90 seconds, with network access blocked and no canonical data writes.
- Next: Phase 5 professional dashboard, Evaluation page, chart review, and screenshots.
- Blockers: None.

## Phase 5 — Dashboard

- Done: Rebuilt the dashboard as a responsive, self-contained English interface with Overview, Anomaly Feed, Stock Search, News Feed, Pipeline Status, and Evaluation pages.
- Done: Added the required banner: “Statistical screening tool for human review, not a fraud verdict.”
- Done: Replaced the externally hosted chart library with native SVG/CSS charts; the timeline reads `anomaly_flags.csv`, while news categories read `anomaly_classified.csv` through their existing APIs.
- Done: Added read-only evaluation endpoints for metrics, baselines, sensitivity, and the event audit; all are covered by fixtures and endpoint tests.
- Done: Browser-tested every page against the real local outputs. Each page rendered its distinct content, the Evaluation page showed 1 of 2 primary recall and SOPAT as the negative control, and the browser console had no warnings or errors.
- Done: Full offline suite passes: 36 tests in 0.90 seconds; compilation succeeds.
- Partial: Saved the verified Overview capture at `docs/screenshots/overview.png`. The browser sandbox permitted all six in-browser captures but blocked exporting the remaining five captures to the repository; no synthetic or mislabeled screenshots were retained.
- Next: Phase 6 report, demo script, README, final integrity checks, and final commit.
- Blockers: Five requested screenshot files could not be exported from the browser sandbox in this environment.

## Phase 6 — Report, demo, and README

- Done: Rewrote `README.md` to match the 60-ticker local dataset, analysis-first runner, optional Groq triage, current results, and limitations.
- Done: Added `docs/REPORT.md` with data, methods, the Groq response fix, the 107 → 12 refined-watchlist explanation, event audit, real result and baseline tables, sensitivity, limitations, reproducibility, and sources.
- Done: Added `docs/DEMO_SCRIPT.md` with a timed five-minute six-page walkthrough and five likely teacher questions.
- Done: Final offline suite passes: 36 tests. Compilation succeeds, and all 11 final smoke-test endpoints return HTTP 200.
- Done: All 178 protected raw CSV hashes match `../bvmt_snapshot`. Seven derived CSVs differ after the pipeline and authorized AI run: anomaly flags/classification/summary, decay classification, watchlist, refined watchlist, and AI-assessed watchlist.
- Done: No scraper or detector was run during Phases 4–6; `.env` was not touched; nothing was pushed.
- Next: None. Delivery is complete except for the screenshot export limitation recorded in Phase 5.
- Blockers: The repository contains only the verified Overview screenshot; five other pages were visually verified but could not be exported through the browser sandbox.

## Dashboard stock coverage correction

- Done: Confirmed the dropdown exposed only the 60 symbols in `_all_tickers_combined.csv`, although 85 canonical uppercase ticker files exist locally.
- Done: Changed `/api/tickers` to merge the combined symbols with valid individual ticker files. The resulting list contains all 85 local symbols, including BIAT and BNA; no data was downloaded or modified.
- Done: Constrained chart SVGs to their responsive panel so the Stock Search plot and labels cannot render outside the white card.
- Done: Added regression coverage for BIAT/BNA discovery and individual-file stock histories.
- Done: Browser QA loaded BIAT with 252 observations, confirmed 85 dropdown symbols, confirmed the chart bounds remain inside the panel, and found no console warnings or errors. The offline suite passes 39 tests.
- Next: Re-run the source-backed evaluation and refresh the report and README.
- Blockers: The message referenced a new sourced event table, but the only attachment was a dashboard screenshot and contained no event rows; no event was invented or changed.

## Evaluation rerun after dashboard review

- Done: Kept the 10-row audited `data/evaluation/events.csv` unchanged because no new event rows or sources were present in the request or image attachment; TINV remains date type `other`, explicitly not a public announcement.
- Done: Re-ran evaluation, baselines over 1,000 deterministic random seeds, the 16-cell sensitivity grid, and summary generation without changing z=3.0 or the 60-day reference window.
- Done: Results remain 1 of 2 events in both reference windows, 0 of 10/20/50 ranked flags, 1,027 flags, 3.607 flags per ticker-year, GIF lead time 21 days, and 0 flags in 1 SOPAT window.
- Done: Expanded `outputs/evaluation/summary.md` with the full evaluability audit, lead time, count-form metrics, all baselines, the complete sensitivity grid, and the explicit conclusion that the reference does not beat the return-only baseline on recall or precision.
- Next: Expand the watchlist decision record, then synchronize the report and README.
- Blockers: New event rows still require the missing sourced table; existing `SOURCE_NEEDED` rows remain excluded.

## Watchlist decision clarification

- Done: Expanded `docs/DECISIONS.md` into an explicit paragraph: the input changed to the current 12-row `watchlist.csv`; the old 107-row refined artifact was stale; no detector or refinement parameter changed.
- Next: Synchronize the report and README with the rerun outputs and screenshot state.
- Blockers: None.

## Report and README synchronization

- Done: Updated the report and README from the rerun outputs; the evaluation numbers remain unchanged because the audited event set did not change.
- Done: Added the 85-file Stock Search coverage, full event evaluability, TINV's non-public date type, GIF's 21-day lead time, and the explicit comparison showing that the reference does not beat the return-only baseline on recall or precision.
- Done: Retained only the valid Overview screenshot link and removed the obsolete browser-export explanation; the user can add the remaining captures under `docs/screenshots/`.
- Next: Run the final offline tests, endpoint checks, and protected-raw hash audit.
- Blockers: The missing sourced event table prevents adding the requested new event rows.

## Final verification after evaluation follow-up

- Done: Full offline suite passes: 40 tests in 0.89 seconds; compilation succeeds.
- Done: All 13 real-data smoke endpoints return HTTP 200, including `/api/tickers`, `/api/stock/BIAT`, `/api/stock/BNA`, and all evaluation APIs. The ticker endpoint returns 85 symbols.
- Done: SHA-256 comparison covers 187 canonical CSVs; all 178 protected raw files match `../bvmt_snapshot` with zero differences.
- Done: Confirmed the report, README, and evaluation summary contain no claim that the reference beats the return-only baseline and no prohibited output wording.
- Next: None until the missing sourced event table or additional dashboard screenshots are supplied.
- Blockers: No new event rows could be added because the referenced sourced table was absent.

## Event-date rule and rerun

- Done: Recorded the earliest-public-event rule before changing the event table; preserved `original_label_date` and added `secondary_date` for all 10 audited rows.
- Done: Rechecked GIF, LSTR, SERVI, MIP, and SOPAT against the user-verified GIF facts and stored repository evidence. Primary dates are now GIF 2024-10-25, LSTR 2024-07-23, SERVI 2024-01-11, MIP 2024-08-05, and SOPAT 2023-09-19.
- Done: Re-ran the reference evaluation without changing detector parameters. Primary recall remains 1 of 2 events; secondary recall is 1 of 3 events because SERVI has 60-day, but not 30-day, coverage.
- Done: GIF's 2024-10-22 flag is 3 days before the suspension and 21 days before the later article date. Report and README numbers were synchronized.
- Next: Audit the 25 symbols omitted from the 60-symbol combined file, validate all 85 individual files, and—if valid—build and evaluate the separate full-universe derived file.
- Blockers: None.

## Coverage audit and full-universe comparison

- Done: Confirmed 60 symbols in `_all_tickers_combined.csv` and 85 uppercase individual ticker files. The 25 missing symbols are AB, ADWYA, AETEC, AL, AMS, ARTES, ASSAD, ASSMA, AST, ATB, ATL, BH, BHASS, BHL, BIAT, BL, BNA, BNASS, BT, BTE, CC, CELL, CREAL, TJARI, and TJL.
- Done: Established from repository code that the scraper skips existing individual files but concatenates only newly downloaded frames when rebuilding the combined file. UBCI, TINV, and UADH are present in both; CGF and TSI are absent from both and have no individual files.
- Done: Validated all 85 individual files for schema, symbol identity, dates, numeric OHLCV, duplicates, and detector history requirements. PLTU has 41 rows but is accepted because the detector explicitly excludes it as known-incomplete.
- Done: Created the separate derived `_all_tickers_full.csv` with 61,812 rows across 85 symbols, then ran the unchanged reference detector and evaluation into `outputs/evaluation_full/`.
- Done: Shared OHLCV rows and flags agree across all 60 shared symbols. The 60-symbol reference has 1,027 flags and 3.607 flags/ticker-year; the 85-symbol comparison has 1,454 and 3.681. Both report 1 of 2 primary events, 1 of 3 secondary events, and 0 of 20 flags at precision@20.
- Next: Document the exact ranking rule, produce the top-20 flag table with an explicit illiquidity definition, and explain 0 of 20 in plain language.
- Blockers: None.

## Scraper combined-file rebuild fix

- Done: Recorded that CGF and TSI have no ticker files, are not in either price universe, and cannot be evaluated; they remain `SOURCE_NEEDED`, not tested misses.
- Done: Fixed `src/scraping/scrape_ilboursa.py` so a future authorized scrape rebuilds its combined output from every valid uppercase individual ticker CSV instead of only files downloaded in that run.
- Done: Added a file-based unit test proving both a pre-existing ticker and a newly present ticker are included. The scraper was not run, no network was used, and no raw file changed.
- Next: Snapshot canonical data to `../bvmt_snapshot2`, adopt `_all_tickers_full.csv` in the analysis-only pipeline, archive the 60-symbol evaluation, and regenerate all derived outputs for 85 symbols.
- Blockers: None.

## Adopted 85-symbol delivered universe

- Done: Created `../bvmt_snapshot2` before regeneration and verified all 188 copied files by SHA-256.
- Done: Added the full-universe build as the first analysis step, switched the detector, decay analysis, refinement, validation, evaluation, and dashboard reads to `_all_tickers_full.csv`, and kept `_all_tickers_combined.csv` untouched.
- Done: Archived the prior 60-symbol evaluation under `outputs/evaluation_60symbol/`; `outputs/evaluation/` now contains the 85-symbol delivered evaluation. Shared-symbol flags still agree.
- Done: Ran the default analysis pipeline with scraping and AI disabled, then ran the separately authorized Groq triage for all 17 refined rows. It used 17 calls, produced 8 `likely_noise`, 8 `worth_investigating`, and 1 `uncertain` draft assessments, with no empty reasoning.
- Done: Derived row counts changed as follows: anomaly flags 1,027 → 1,454; classified anomalies 1,027 → 1,454; anomaly summary 58 → 83; watchlist 12 → 17; refined watchlist 12 → 17; decay flags 8 → 15; decay classification 8 → 15; AI-assessed watchlist 12 → 17.
- Done: Headline evaluation is 1 of 2 primary-window events, 1 of 3 secondary-window events, and 0 of 20 top-ranked flags; detector settings remain z=3.0 and rolling window=60.
- Done: Full offline suite passes 44 tests, and all 178 protected raw files match `../bvmt_snapshot2`.
- Next: Add the exact precision-ranking rule, the top-20/illiquidity table, and the plain-language interpretation.
- Blockers: None.

## Precision ranking and top-20 audit

- Done: Defined the ranking score as `max(abs(volume_zscore), abs(return_zscore))`, descending, with earlier date and ticker symbol as deterministic tie-breaks.
- Done: Defined “illiquid” without event labels as ticker median daily volume at or below the 25th percentile across the 83 tickers represented in delivered reference flags; the generated cutoff is 349.5 shares per observed trading day.
- Done: Generated `outputs/evaluation/top_20_flags.csv` and added the complete table to `summary.md`. Three of the top 20 are labeled illiquid: MIP, SIPHA, and TINV.
- Done: Explained that 0 of 20 means none of the 20 highest scores lies in the fixed primary window around GIF or LSTR; it does not prove the other flags are false positives because event labels are incomplete.
- Next: Rewrite the non-technical report last, then synchronize README and run final verification.
- Blockers: None.

## Non-technical final report

- Done: Rewrote `docs/REPORT.md` from the final generated 85-symbol results with a title block, five-line plain-English summary, seven-term glossary, exact denominator explanation, top-20 ranking table, 60-vs-85 comparison, limitations, and captions for all three linked figures.
- Done: Stated explicitly that CGF and TSI are not in the dataset and cannot be evaluated, and documented the 25-symbol scraper merge bug as a coverage limitation.
- Done: Synchronized README with 61,812 rows, 1,454 flags, 3.681 flags/ticker-year, 17 refined and AI-assessed rows, current evaluation counts, archive location, and ranking method.
- Done: Replaced the user-facing verdict banner with “not a legal finding.” Missing page captures are an unlinked TODO list at the end of the report; all three retained image links exist.
- Next: Run the complete final test suite, protected-raw hash audit, real-data API smoke test, and repository consistency checks.
- Blockers: Five dashboard page screenshots remain TODOs for the user to add.
