# Evaluation protocol v2 — frozen before candidate implementation

**Status:** Pre-registered for Phase 2. Commit this document before adding any candidate-detector code or inspecting new-event hit results. Do not revise thresholds, windows, splits, or adoption rules after this commit to fit outcomes. Any later amendment must be dated, identified as exploratory, and excluded from the registered comparison.

## Purpose and frozen reference

This is market surveillance and anomaly screening for human review. The existing `src/detection/anomaly_detector.py` and its 1,414-row output are `reference_v1`; its code, settings, and reference outputs remain untouched. Preserve a separate reproduction of its result on the original three sourced positive events: **1 of 3** in the primary window. Added labels change the expanded evaluation denominator, not that historical baseline statement. Do not use candidate results to alter `reference_v1`.

## Event registry and source rules

- Search only for events with earliest public information from 2021-06-01 through 2026-10-31. A label requires a directly accessible URL from BVMT, CMF, ilboursa, or credible press. Log every URL visited and the exact event claim it supports in `docs/EVENT_LABEL_LOG.md`.
- Record the earliest verifiable public-information date as `event_date`, and classify its type (suspension, halt, court ruling, sanction, public announcement, withdrawal, or other). A later article about an earlier event is not evidence that the earlier date was public unless it cites or links the primary notice. Preserve later dates in `secondary_date`, and never move a date to catch a flag.
- Positives are independently source-backed adverse market events or formal sanctions. Benign buyouts, routine corporate actions, and ordinary withdrawals are negative controls; ambiguous cases remain exploratory. A source is not a verdict of misconduct.
- Keep the existing CSV schema. Use `source=SOURCE_NEEDED`, `include_headline=false`, and a reason in `notes` when a specific claim or date lacks support. Record trading-window coverage separately. Missing ticker data or no observations in the evaluation window makes a sourced event non-evaluable, with an explicit reason.
- A reviewer should adjudicate each label without seeing detector hits. Duplicated articles about one underlying event become one event; record rejected duplicates and date alternatives in the log.

## Split and evaluation windows

- **Development:** event dates before 2025-01-01. **Held-out:** event dates on or after 2025-01-01. This calendar rule is fixed before new labels are collected and is independent of ticker or detector output. Do not inspect held-out event hits until the development choice is locked and recorded.
- The primary hit window is event date minus 30 through plus 5 **calendar days**, inclusive, with the same ticker. The secondary window is minus 60 through plus 5 days, descriptive only. A flag after the event is distinguished from an advance warning in lead-time reporting.
- A positive enters a split denominator only with a source URL, an unambiguous public date, `include_headline=true`, and at least one trading observation for that ticker in its primary window. Negative controls are reported separately. Events with missing coverage are listed but excluded from denominator.
- Trading history available to a candidate on date *t* ends before or at *t*. Rolling baselines exclude *t*. PX1 market returns must be joined on the exact date, never forward-filled. A retrospective latest-snapshot decay row is not a historical prediction.

## Registered candidate variants

All variants are run on the same stored universe and emit a dated `(symbol, date)` flag table without editing raw CSVs. Thresholds below are fixed before label research. Each row, including failed variants, remains in the comparison table.

| ID | Rule |
|---|---|
| `robust_z3` | Prior 60 valid log1p-volume and gap-guarded returns; median and 1.4826 × MAD; floors 0.10 and 0.01; positive volume z or absolute return z ≥3.0. |
| `robust_z4` | Same as `robust_z3`, cutoff 4.0. |
| `market_adjusted_z3` | Stock return minus same-date PX1 return; prior 60 valid excess returns, standard deviation floor 0.01, absolute z ≥3.0; no index match means no score. |
| `activity_filtered_v1` | `reference_v1` dated flags retained only when the prior 60 recorded sessions have ≥20 strictly positive-volume days and median volume ≥400 shares; suppress zero-volume current rows. |
| `persistent_v1` | A `reference_v1` flag is retained only if the same symbol has another reference flag in the preceding 10 calendar days, including neither future dates nor the current row twice. |
| `decay_point_in_time` | Recompute the existing six-month-vs-prior-six-month decay rule at each calendar month end using only history through that month end; baseline volume ≥1,000 and ratio <0.2, or ≥90 days since last positive-volume trade. Emit one symbol/month-end flag. The existing latest-snapshot decay file is shown separately as descriptive context, not scored as a historical predictor. |
| `market_wide_tag` | Add a context tag when ≥10 distinct stock symbols have a `reference_v1` flag on the same date. Preserve flag count and ranking; report tagged share, and do not count this as a new detector win. |

`PX1` is the stored TUNINDEX series. Exclude PX1 and TBIDX from company-flag candidate counts; keep `reference_v1` itself unchanged, including its PX1 rows. Candidate calculations may use PX1 only as a market comparator.

## Baselines and decision process

- Compare with `reference_v1`, existing volume-only and return-only reference channels, and the existing same-per-ticker-count random baseline. Add three fixed baselines: absolute market-adjusted return z ≥3.0; simple volume spike when current positive volume is ≥5× the median of the prior 60 sessions (median must be ≥400, no zero-volume flags); and top 2 non-index flags per calendar month ranked by reference screening score with date/symbol tie-breaks. The sensitivity grid is reporting only.
- Generate all registered variants on the development period. Choose at most one candidate for confirmatory held-out comparison by highest development primary recall, then lower flags per week, then fewer negative-control-window flags, then lexicographic ID. Lock and record that choice before computing held-out hits. Report every variant on both splits after locking. No held-out-driven parameter changes or variant selection.
- Report primary and secondary `k of n` event recall with two-sided 95% Wilson intervals; known-event-nearby flag hit rate at top 10/20/50 with Wilson intervals; first flag and signed lead time per hit; total flags; flags per calendar week of available trading data; and negative-control-window flag counts. A nearby known event is a limited label, not a precision ground truth for all flags.
- For each method's primary recall, run ≥1,000 same-count-per-ticker random placements on observed dates with fixed seed `20261006`; report the one-sided permutation p-value `(1 + count(random recall >= observed recall)) / (1 + seeds)` and the null mean. Use the same rules within each split.
- Adoption requires **at least 10 held-out sourced positive events**, a strictly positive lower bound of a 95% paired event-bootstrap interval (10,000 resamples; seed `20261006`) for the chosen candidate's primary recall difference versus **both** `reference_v1` and the best registered non-random baseline, no higher flags/week than `reference_v1`, and no increase in negative-control-window flags. If any condition fails or is inestimable, retain `reference_v1`. These thresholds and the choice rule do not change after viewing results.

## Reporting discipline

The final table contains development and held-out columns for every variant, with counts, intervals, workload, and status. Report the number of variants tried and any implementation or data failure. Label confidence intervals as sampling uncertainty under the small sourced set, not accuracy. Do not call missing local news suspicious by itself. Do not call AI triage validated; it is an unvalidated draft opinion and is not run in this protocol.
