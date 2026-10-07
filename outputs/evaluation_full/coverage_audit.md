# Coverage audit

- Individual uppercase ticker files: **85**.
- Symbols in `_all_tickers_combined.csv`: **60**.
- Missing from the combined file: **25** — AB, ADWYA, AETEC, AL, AMS, ARTES, ASSAD, ASSMA, AST, ATB, ATL, BH, BHASS, BHL, BIAT, BL, BNA, BNASS, BT, BTE, CC, CELL, CREAL, TJARI, TJL.
- Validation: **85 of 85 files valid** for the fixed detector; PLTU has 41 observations but is accepted because the detector explicitly excludes it as known-incomplete.
- Shared OHLCV rows agree exactly. Full-run flags on the shared symbols: **agree**.

## Requested symbols

- UBCI: individual file yes; 60-symbol combined yes.
- CGF: individual file no; 60-symbol combined no.
- TSI: individual file no; 60-symbol combined no.
- TINV: individual file yes; 60-symbol combined yes.
- UADH: individual file yes; 60-symbol combined yes.

## Repository-supported cause

`src/scraping/scrape_ilboursa.py` skips a symbol when its individual CSV already exists, but appends only newly downloaded frames to `all_data` and then overwrites `_all_tickers_combined.csv` from `all_data`. The 25 omitted files are therefore the existing files skipped by that run, not invalid rows. No scraper or raw file was changed or run for this audit.
