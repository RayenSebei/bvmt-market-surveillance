# Engineering Decisions

- Phase 1: Kept the script copies invoked by `run_all.py` and removed docstring-only duplicates.
- Phase 1: Deleted `data/bvmt_data/` after preserving and verifying all 189 files at `../bvmt_backup/data_bvmt_data`; its `decay_classified.csv` had the same eight records as the canonical copy but different bytes.
- Phase 1: Removed the unused `gunicorn` dependency as the only Render-era deployment leftover; no Render configuration files existed.
- Phase 2: Made analysis-only execution the default and required the explicit `--with-scrape` flag for all network scrapers.
- Phase 2: Ordered classification before watchlist refinement so refinement always uses the current run, and preserved the last AI output whenever Groq or its client is unavailable.
- Phase 2: Used bounded dependency versions rather than unverified exact future versions; no packages were downloaded because network access was restricted to one Groq check.
- Integrity audit: Defined protected raw data case-sensitively as `<TICKER>.csv` matching `^[A-Z0-9]+\.csv$`, every `news_*.csv`, and the two `_all_*_combined.csv` files; the earlier 179 count used PowerShell's case-insensitive `-match` and incorrectly included lowercase `watchlist.csv`, while corrected `-cmatch` gives 178 protected files plus nine derived CSVs = 187 total.
- Integrity audit: `watchlist_refined.csv` changed from 107 stale rows to 12 because the old artifact did not correspond to the current 12-row `watchlist.csv`; classification now runs before refinement, with no detector or refinement parameter change, so the refined output is regenerated from the current input.
- Groq triage: Configured `openai/gpt-oss-120b` for low reasoning effort, JSON output, and 1,500 completion tokens because the 40-token diagnostic ended by length after spending 38 tokens on reasoning and returned empty content; empty content now retries and any final failure preserves the previous AI file.
