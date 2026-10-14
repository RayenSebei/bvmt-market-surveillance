# Five-Minute Demo Script

## Before the demo

Run `python app.py`, open the eight-page dashboard at `http://127.0.0.1:5000`, and click **Start guided tour** on Case Studies if you want the built-in prompts. Do not scrape during the presentation.

## 0:00–0:40 — Purpose and coverage

Say: “This is a statistical screening tool for human review, not a fraud verdict. It covers 85 symbols, 67,035 price observations through 12 October 2026, and 12,498 deduplicated news records.”

## 0:40–1:25 — Overview

Say: “The reference detector produced 1,414 statistical flags, including 21 where price and volume were both unusual. The calendar opens any day directly in the filtered queue, and the radar compares volume and return z-scores.”

Press **Ctrl+K** and jump to a ticker to demonstrate the command palette.

## 1:25–2:10 — Anomaly Feed

Say: “This is the complete 1,414-row review queue. Filters, sorting, pagination, and CSV export all operate on the real generated results. A headline is context, not proof of cause.”

Open a row and point out the z-scores, as-of headline, later context, source link, and ±7-day news list.

## 2:10–2:55 — Stock Search

Say: “The stock view supports line and candlestick modes, drag-to-zoom, volume, and a separate z-score panel with the reference threshold lines. Red markers reopen the same evidence drawer.”

## 2:55–3:25 — Watchlist and Playground

Say: “The refined queue has 16 rows and there are 16 separate volume-decay cases. The Detector Playground reads the precomputed sensitivity grid live, but it is exploratory and does not change the reference detector.”

## 3:25–4:30 — Evaluation and Case Studies

Say: “The fixed primary window is 30 days before through five days after an event. All three sourced positives are now evaluable, and the reference detector hits 1 of 3. GIF is the hit; LSTR and SERVI are misses.”

Continue: “The denominator changed from two to three only because newly downloaded SERVI prices now extend through 8 January 2024, three days before its event. SERVI was not evaluated before. No threshold, window, floor, or event date was tuned.”

Say: “The return-only baseline also hits 1 of 3; volume-only hits 0 of 3. SOPAT is the negative control with zero flags in its primary window. Three events are a case study, not an accuracy estimate.”

## 4:30–5:00 — Close

Say: “The contribution is an auditable workflow: incremental collection, preserved source rows, transparent rules, time-aware news context, portable provenance hashes, offline tests, and a dashboard designed for human review.”

## Likely questions

### Is 1 of 3 an accuracy score?

No. Three events are much too few, and the label set is incomplete. It is reported only as a sourced case-study result.

### Why did SERVI enter the denominator?

The October refresh downloaded four January 2024 SERVI observations through 8 January. That created window coverage for the 11 January event. SERVI is a miss; the detector was not tuned.

### Why is precision at 20 zero?

None of the 20 largest scores is inside a fixed positive-event window. Incomplete event labels mean that does not prove those flags are false positives.

### What did the new-row quality audit find?

It listed 140 rows without modifying them: 134 zero-volume rows, five daily moves above 15%, and one OHLC inconsistency. Four large-return rows are flags; no zero-volume or OHLC-inconsistent row is flagged.
