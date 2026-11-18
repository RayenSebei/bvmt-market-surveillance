# Phase 2 results — frozen-split comparison

The protocol in `EVALUATION_PROTOCOL_v2.md` was committed before candidate code or expanded-label hit inspection. The source-alignment rule in `PROTOCOL_AMENDMENTS.md` was committed before the corrections below. The date split is before 2025-01-01 for development and on/after for held out. The primary window is -30/+5 calendar days; the secondary is -60/+5. Intervals are two-sided 95% Wilson intervals for the small sourced event set, not accuracy estimates.

**Decision:** retain `reference_v1`. The development-selected candidate was `robust_z3`; it hit 0 of 1 held-out positives. Adoption required at least 10, a positive paired-bootstrap lower bound against both reference and the preselected best nonrandom baseline, and no workload/control increase. Its paired 95% interval versus v1 is [0.0, 0.0]; versus `simple_volume_spike` it is [-1.0, -1.0]. It fails the minimum sample and comparative tests. No threshold was retuned. The selection-lock annotation initially said negative-control event count; the implementation now uses the protocol-required negative-control flag count. The selected methods did not change.

Six detector variants were tried: robust_z3, robust_z4, market_adjusted_z3, activity_filtered_v1, persistent_v1, and decay_point_in_time. `market_wide_tag` is a seventh registered context tag, not a detector win; it tagged 0 of 1,399 stock reference flags under the fixed threshold. The market comparator is exact-date PX1/TUNINDEX. The latest-snapshot decay file was not scored as a historical prediction.

## Primary comparison

Each cell gives `k of n (Wilson low–high)`. `Flags/week` is over the split's observed calendar span. Negative-control flags are unique flags in any registered control window. `Random p` is a one-sided same-count-per-ticker permutation comparison with 1,000 placements and seed 20261006; high p values give no evidence against random placement under this limited label set.

| Method | Development | Dev flags/week | Dev control flags | Dev random p | Held out | Held flags/week | Held control flags | Held random p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `reference_v1` | 1 of 4 (0.05–0.70) | 4.08 | 4 | 0.687 | 0 of 1 (0.00–0.79) | 7.12 | 9 | 1.000 |
| `volume_only` | 0 of 4 (0.00–0.49) | 0.62 | 1 | 1.000 | 0 of 1 (0.00–0.79) | 0.90 | 0 | 1.000 |
| `return_only` | 1 of 4 (0.05–0.70) | 3.54 | 3 | 0.687 | 0 of 1 (0.00–0.79) | 6.30 | 9 | 1.000 |
| `market_adjusted_return_only` | 1 of 4 (0.05–0.70) | 3.24 | 3 | 0.656 | 0 of 1 (0.00–0.79) | 5.52 | 8 | 1.000 |
| `simple_volume_spike` | 4 of 4 (0.51–1.00) | 16.87 | 27 | 0.401 | 1 of 1 (0.21–1.00) | 24.38 | 10 | 0.841 |
| `top_2_per_month` | 0 of 4 (0.00–0.49) | 0.36 | 1 | 1.000 | 0 of 1 (0.00–0.79) | 0.47 | 0 | 1.000 |
| `robust_z3` | 2 of 4 (0.15–0.85) | 10.83 | 9 | 0.631 | 0 of 1 (0.00–0.79) | 21.94 | 20 | 1.000 |
| `robust_z4` | 1 of 4 (0.05–0.70) | 5.47 | 4 | 0.640 | 0 of 1 (0.00–0.79) | 11.39 | 11 | 1.000 |
| `market_adjusted_z3` | 1 of 4 (0.05–0.70) | 3.24 | 3 | 0.656 | 0 of 1 (0.00–0.79) | 5.52 | 8 | 1.000 |
| `activity_filtered_v1` | 1 of 4 (0.05–0.70) | 3.15 | 4 | 0.687 | 0 of 1 (0.00–0.79) | 5.71 | 9 | 1.000 |
| `persistent_v1` | 0 of 4 (0.00–0.49) | 0.91 | 0 | 1.000 | 0 of 1 (0.00–0.79) | 1.92 | 3 | 1.000 |
| `decay_point_in_time` | 0 of 4 (0.00–0.49) | 1.58 | 0 | 1.000 | 0 of 1 (0.00–0.79) | 0.90 | 0 | 1.000 |
| `same_count_random` | 0 of 4 (0.00–0.49) | 4.56 | 4 | 1.000 | 0 of 1 (0.00–0.79) | 6.17 | 3 | 1.000 |

## Secondary window and flag counts

The secondary window is descriptive and was not used to choose a detector.

| Method | Dev -60/+5 | Held -60/+5 | Dev flags | Held flags |
|---|---:|---:|---:|---:|
| `reference_v1` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 754 | 660 |
| `volume_only` | 0 of 4 (0.00–0.49) | 0 of 1 (0.00–0.79) | 115 | 83 |
| `return_only` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 653 | 584 |
| `market_adjusted_return_only` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 599 | 512 |
| `simple_volume_spike` | 4 of 4 (0.51–1.00) | 1 of 1 (0.21–1.00) | 3116 | 2260 |
| `top_2_per_month` | 0 of 4 (0.00–0.49) | 0 of 1 (0.00–0.79) | 67 | 44 |
| `robust_z3` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 2001 | 2034 |
| `robust_z4` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 1011 | 1056 |
| `market_adjusted_z3` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 599 | 512 |
| `activity_filtered_v1` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 581 | 529 |
| `persistent_v1` | 1 of 4 (0.05–0.70) | 0 of 1 (0.00–0.79) | 168 | 178 |
| `decay_point_in_time` | 0 of 4 (0.00–0.49) | 0 of 1 (0.00–0.79) | 292 | 83 |
| `same_count_random` | 2 of 4 (0.15–0.85) | 0 of 1 (0.00–0.79) | 842 | 572 |

## Label and quality audit

The registry gained **18 distinct sourced rows**; after correcting ADWYA, their roles are 13 negative, 3 exploratory, and 2 positive. Two new adverse events are the Sotipapier factory fire/suspension and Syphax bankruptcy public report; the latter has no primary-window trading observation and is excluded from recall. UADH's cited PDF anchors the suspension on March 25, 2026; TSI has a CMF source but no listed trading series. TINV, CGF, and UBCI retain `SOURCE_NEEDED` for the original claims/dates. These categories reflect public events, not misconduct verdicts.

## Before and after the source-alignment corrections

The table compares the committed output before amendment (`f75eb07`) with the rerun. Each hit cell includes its two-sided 95% Wilson interval. `Control` is the count of flags in separate ticker windows. `Collapsed` uses the larger of the two ticker flag counts for the shared PGH/LNDOR notice, then adds flags in all other control windows; this treats that notice as one cluster without hiding either ticker's observations. The last two columns show the corrected result with both accounting choices.

| Method | Development hits before → after | Held-out hits before → after | Dev control before → after | Held control before → after | Dev collapsed | Held collapsed |
|---|---|---|---:|---:|---:|---:|
| `reference_v1` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 4 → 4 | 9 → 9 | 4 | 9 |
| `volume_only` | 0/4 (0.00–0.49) → same | 0/1 (0.00–0.79) → same | 1 → 1 | 0 → 0 | 1 | 0 |
| `return_only` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 3 → 3 | 9 → 9 | 3 | 9 |
| `market_adjusted_return_only` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 3 → 3 | 8 → 8 | 3 | 8 |
| `simple_volume_spike` | 4/4 (0.51–1.00) → same | 1/1 (0.21–1.00) → same | 28 → 27 | 10 → 10 | 27 | 10 |
| `top_2_per_month` | 0/4 (0.00–0.49) → same | 0/1 (0.00–0.79) → same | 1 → 1 | 0 → 0 | 1 | 0 |
| `robust_z3` | 2/4 (0.15–0.85) → same | 0/1 (0.00–0.79) → same | 9 → 9 | 20 → 20 | 9 | 20 |
| `robust_z4` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 4 → 4 | 11 → 11 | 4 | 11 |
| `market_adjusted_z3` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 3 → 3 | 8 → 8 | 3 | 8 |
| `activity_filtered_v1` | 1/4 (0.05–0.70) → same | 0/1 (0.00–0.79) → same | 4 → 4 | 9 → 9 | 4 | 9 |
| `persistent_v1` | 0/4 (0.00–0.49) → same | 0/1 (0.00–0.79) → same | 0 → 0 | 3 → 3 | 0 | 3 |
| `decay_point_in_time` | 0/4 (0.00–0.49) → same | 0/1 (0.00–0.79) → same | 0 → 0 | 0 → 0 | 0 | 0 |
| `same_count_random` | 0/4 (0.00–0.49) → same | 0/1 (0.00–0.79) → same | 4 → 4 | 3 → 3 | 4 | 2 |

No method changed hit/miss status, its denominator, or its Wilson interval. The UADH one-day shift moved the `simple_volume_spike` first lead from 6 to 7 days without losing either of its two flags. ADWYA's removal from negative controls reduced only the development `simple_volume_spike` control count (28 to 27). Collapsing the shared PGH/LNDOR notice reduces only `same_count_random` held-out control flags (3 to 2). The Phase 2 verdict remains **retain `reference_v1`**. The auxiliary `baseline_comparison.csv` random baseline mean also changed (secondary recall 0.3756 → 0.3728; mean control flags 6.954 → 6.722) because its seeded random placements were evaluated against the shifted UADH window and reduced control set; these are not candidate wins.

Reference reproduction: 1,414 stored flags and 1 of the original 3 positives; on the expanded set it is 1 of 5 primary and 2 of 5 secondary. The expanded primary Wilson interval is 0.04–0.62. First matching flags and signed lead days for each event/method are in `outputs/evaluation/phase2_event_hits.csv`.

The derived quality review found 0 duplicate ticker/date rows, 0 invalid dates, 59 OHLC or invalid-numeric rows, and 349 gaps over 30 calendar days. The 140 new-scrape rows remain flagged for review: 134 zero-volume, five large-jump, one OHLC-inconsistent. The derived suspect list contains 115 rows: 92 large close jumps (five with nearby stored action news) and 23 additional reference flags near stored action news. It tags 86 reference flags. No source CSV was edited. ilboursa is the sole stored news source. The 100-headline sample leaves `human_label` empty.

## What a skeptical reviewer could still criticize

- The positive set is selected from discoverable public events, not a representative sample of all adverse days. The held-out positive count is one; paired-bootstrap intervals are degenerate.
- Multiple negative controls are routine corporate actions, but some share a ticker or underlying notice. They are not independent random negatives.
- A local-news match may be incomplete or after the flag; absence of a match is not an anomaly by itself.
- Unadjusted price series, thin trading, quote errors, and delistings can produce large z-scores. The top 20 review is provisional, not ground truth.
- The simple volume-spike baseline reaches all five positives only with far more flags per week. A hit count alone is not a performance win.
- No AI triage was run. Its possible future output is an unvalidated draft opinion; the proposed human-agreement study is in `REPORT.md`.
