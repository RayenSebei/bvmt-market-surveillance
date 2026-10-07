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
- Phase 3: Limited headline evaluation to source-backed positive events with trading-window coverage, treated SOPAT only as a negative control and MIP only as exploratory, and retained every unresolved date as `SOURCE_NEEDED` rather than inferring or moving it.
- Phase 3: Kept the reference z cutoff 3.0 and 60-day rolling window unchanged; all other grid cells are sensitivity reporting only, and the 1,000-seed random baseline preserves each ticker's reference flag count.
- Phase 4: Used committed minimal read-only CSV fixtures for Flask endpoint tests because the host's pytest temporary directories have unusable Windows ACLs; this also guarantees tests never read or write canonical market data.
- Phase 5: Replaced CDN-dependent charts with native SVG/CSS so dashboard charts render without external network access; exposed generated evaluation CSVs through read-only Flask endpoints.
- Phase 5: Kept only the verified Overview screenshot after the browser sandbox blocked exporting five other successful in-browser captures; discarded four duplicate files rather than presenting them as different pages.
- Phase 6: Reported only generated results, expressed event metrics as counts, kept every unresolved case as `SOURCE_NEEDED`, and described the Groq and refined-watchlist changes as operational fixes rather than performance improvements.
