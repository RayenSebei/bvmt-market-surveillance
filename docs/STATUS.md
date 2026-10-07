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
