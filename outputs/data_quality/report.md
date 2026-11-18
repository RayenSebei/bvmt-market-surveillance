# Phase 2 data quality review

Rows: 67,035; symbols: 85; latest date: 2026-10-12.
Duplicate symbol/date rows: 0; invalid dates: 0; OHLC/negative/missing numeric rows: 59; gaps >30 calendar days: 349.
Symbols with last observation >90 days before latest: 9 (ADWYA, AMS, CREAL, GIF, LSTR, MIP, SERVI, SOPAT, SOTEM).
Corporate-action suspects from >=15% daily close jumps or reference flags within +/-7 days of stored action news: 115; with stored action news: 28; existing reference flags tagged: 86.
New scrape rows reviewed: 140; classes: {'ZERO_VOLUME_OBSERVATION': 134, 'LARGE_CLOSE_JUMP': 5, 'OHLC_INCONSISTENCY': 1}. Every row remains flagged for manual review; no source value was changed.

These are mechanical checks and candidate context tags. A nearby headline does not prove a price move was caused by a corporate action. ilboursa is the sole stored news source. The sample's human_label and human_notes fields are intentionally empty.
