# Five-Minute Demo Script

## Before the demo

Run `python app.py` and open `http://127.0.0.1:5000`. Do not run the scraper during the presentation.

## 0:00–0:35 — Introduce the project

Say: “This is a statistical screening tool for the Tunisian stock market. It finds unusual price or volume activity and organizes it for human review. The banner is important: a flag is not a verdict.”

Point out the local data period, the 85 covered tickers, and the visible disclaimer.

## 0:35–1:15 — Overview

Click **Overview**.

Say: “The overview shows the full 85-symbol dataset and 1,454 statistical flags. The charts have labelled axes and are rendered locally, so the dashboard does not depend on an external chart service.”

## 1:15–1:55 — Anomaly Feed

Click **Anomaly Feed**.

Say: “This is the complete 1,454-row review queue. I can filter, sort, paginate, and export the current result. This row has news nearby; the timing and source are visible here, but nearby news is context, not proof of cause.”

Click a row with **News nearby**, open the drawer, and point to both plain-English z-score descriptions, the ±7-day news list, and the reminder about cause.

## 1:55–2:30 — Stock Search

Click **Stock Search** and select a ticker.

Say: “This page puts a signal back into its price history. Price and volume use separate labelled axes, the range buttons change the requested history, and hovering shows OHLCV plus the daily change.”

Click a red marker and say: “The same contextual drawer opens from the chart, so the reviewer never loses the link between a signal and its source data.”

## 2:30–3:00 — Watchlist

Click **Watchlist**.

Say: “The refined queue contains 17 rows. The colour chips are draft opinions from an external model, never findings, and the reasoning remains expandable for human review. Below it are 15 separate volume-decay cases.”

## 3:00–3:20 — Pipeline Status

Click **Pipeline Status**.

Say: “This page shows which generated files are available. The dashboard does not start scraping. The safe default command runs analysis from existing local data, and a network refresh needs an explicit option.”

## 3:20–4:35 — Evaluation

Click **Evaluation**.

Say: “The event window was fixed before calculation: 30 days before to 5 days after, with a secondary 60-day view. Three positive events have sources, but only two have enough trading data. The reference detector matches 1 of 2 events.”

Continue: “The return-only baseline also matches 1 of 2, while the volume-only baseline matches 0 of 2. SOPAT is the negative control and has 0 flags in its primary window. With only two evaluable positives, this is a case study, not a performance estimate.”

Point to the event audit and say: “TINV, UADH, TSI, CGF, and UBCI are marked `SOURCE_NEEDED` and excluded. I did not move the TINV date, even though its detector flags occur after the stored date.”

## 4:35–5:00 — Close

Say: “The main contribution is a complete and honest workflow: transparent rules, safe data handling, offline tests, source-aware evaluation, and a dashboard for review. The next step would be a larger independently sourced event set and an untouched future test period.”

## Likely questions

### 1. Why did you use z-scores?

They are simple to explain and show how unusual one observation is compared with that ticker’s recent history. I also use log volume, standard-deviation floors, and gap exclusion to reduce common problems.

### 2. Does 1 of 2 events mean the detector is 50% accurate?

No. The denominator is far too small. I report “1 of 2 events” and call it a case-study result, not a general accuracy estimate.

### 3. Why is precision at 20 equal to 0 of 20?

None of the top 20 ranked flags falls near the few eligible labeled events. The label set is incomplete, so this measure can miss relevant but unlabeled events; it still shows that ranking quality needs more study.

### 4. What does the AI model decide?

It does not decide a case. It writes a draft `worth_investigating` or `likely_noise` opinion with reasoning for a human reviewer. If the API fails, the pipeline keeps the previous output and continues safely.

### 5. Why did the refined watchlist shrink from 107 rows to 12?

The 107-row file was stale and did not match the current 12-row watchlist. The pipeline order was corrected so classification runs before refinement. No detector threshold or refinement parameter was changed.
