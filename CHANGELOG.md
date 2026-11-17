# Changelog

## Phase 2 methodological hardening — 2026-11-17

- Froze `reference_v1` and committed the evaluation protocol before implementing candidates.
- Added 18 source-backed event rows and an auditable date/source log. Upgraded UADH and TSI sources; retained unsupported TINV, CGF, and UBCI claims as `SOURCE_NEEDED`.
- Compared six predeclared candidate detectors with reference and fixed baselines across a date-based development/held-out split. None met the adoption rule; v1 remains the reference.
- Added Wilson intervals, permutation comparisons, lead-time rows, workload, derived data-quality and corporate-action review, and a 100-headline sample with empty human labels.
- Updated the React Evaluation page and read-only API. The legacy Flask UI remains available but is deprecated pending a separate migration.
