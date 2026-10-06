# Engineering Decisions

- Phase 1: Kept the script copies invoked by `run_all.py` and removed docstring-only duplicates.
- Phase 1: Deleted `data/bvmt_data/` after preserving and verifying all 189 files at `../bvmt_backup/data_bvmt_data`; its `decay_classified.csv` had the same eight records as the canonical copy but different bytes.
- Phase 1: Removed the unused `gunicorn` dependency as the only Render-era deployment leftover; no Render configuration files existed.
