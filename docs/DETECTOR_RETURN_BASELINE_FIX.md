# Return-baseline correctness fix

> **Historical before/after evidence:** the counts below deliberately preserve the pre-refresh dataset and are not current dashboard totals.

This change is a correctness fix, not tuning against labeled events. The reference
settings remain a 60-observation baseline, a z-score cutoff of 3.0, a 1% return
standard-deviation floor, and a 10-calendar-day maximum gap for a daily return.

Previously, a deliberately missing return at a trading gap entered a fixed
60-row rolling window and suppressed the return z-score for the following 60
rows. The corrected calculation compacts the series to valid returns, requires
60 valid prior returns, and excludes the current return from its own baseline.
A return measured across a gap remains missing and cannot be flagged.

## Reference detector: before and after

All figures below use the same 61,812-row, 85-symbol stored dataset ending
2026-06-17. The detector analyzes 83 symbols after its documented exclusions.

| Measure | Before | After |
|---|---:|---:|
| Eligible rows (at least 61 prior stored observations) | 55,604 | 55,604 |
| Eligible rows without return z-score | 17,257 (31.04%) | 947 (1.70%) |
| Union flags | 947 | 1,335 |
| 30-day sourced-event recall | 0 of 2 | 1 of 2 |
| 60-day sourced-event recall | 0 of 3 | 1 of 3 |
| Flags near SOPAT negative control, 30-day window | 0 | 0 |

The remaining missing scores are expected where the current observation itself
follows a gap and therefore has no valid daily return.

## Source-backed event results

| Event | 30-day before | 30-day after | 60-day before | 60-day after |
|---|---|---|---|---|
| GIF suspension/delisting | no hit | hit on 2024-10-22 (3 days before) | no hit | hit on 2024-10-22 (3 days before) |
| LSTR suspension/bankruptcy | no hit | no hit | no hit | no hit |
| SERVI suspension/bankruptcy | not eligible | not eligible | no hit | no hit |

This tiny event set is descriptive evidence only. It is not sufficient for model
selection, calibrated performance claims, or fraud conclusions.

## Baselines

| Method | Flags before | Flags after | 30-day recall before | 30-day recall after | 60-day recall before | 60-day recall after |
|---|---:|---:|---:|---:|---:|---:|
| Reference union | 947 | 1,335 | 0 of 2 | 1 of 2 | 0 of 3 | 1 of 3 |
| Volume z-score only | 192 | 192 | 0 of 2 | 0 of 2 | 0 of 3 | 0 of 3 |
| Absolute return only | 771 | 1,162 | 0 of 2 | 1 of 2 | 0 of 3 | 1 of 3 |
| Random, same per-symbol count (1,000 seeds) | 947 | 1,335 | 0.059 of 2 average | 0.515 of 2 average | 0.111 of 3 average | 0.891 of 3 average |

## Sensitivity grid

Each cell is reported as `flags / sourced 30-day event hits`. Parameters were
not changed in response to these results; the reference remains z=3.0 and 60
valid prior observations.

| z cutoff | Window | Before | After |
|---:|---:|---:|---:|
| 2.5 | 20 | 2,532 / 1 of 2 | 2,943 / 1 of 2 |
| 2.5 | 40 | 1,994 / 0 of 2 | 2,574 / 1 of 2 |
| 2.5 | 60 | 1,732 / 0 of 2 | 2,372 / 1 of 2 |
| 2.5 | 120 | 1,279 / 0 of 2 | 2,056 / 1 of 2 |
| 3.0 | 20 | 1,414 / 1 of 2 | 1,680 / 1 of 2 |
| 3.0 | 40 | 1,091 / 0 of 2 | 1,434 / 1 of 2 |
| 3.0 | 60 | 947 / 0 of 2 | 1,335 / 1 of 2 |
| 3.0 | 120 | 709 / 0 of 2 | 1,148 / 1 of 2 |
| 3.5 | 20 | 867 / 1 of 2 | 1,039 / 1 of 2 |
| 3.5 | 40 | 662 / 0 of 2 | 880 / 1 of 2 |
| 3.5 | 60 | 540 / 0 of 2 | 790 / 1 of 2 |
| 3.5 | 120 | 389 / 0 of 2 | 653 / 0 of 2 |
| 4.0 | 20 | 552 / 1 of 2 | 670 / 1 of 2 |
| 4.0 | 40 | 414 / 0 of 2 | 571 / 1 of 2 |
| 4.0 | 60 | 317 / 0 of 2 | 470 / 1 of 2 |
| 4.0 | 120 | 209 / 0 of 2 | 381 / 0 of 2 |
