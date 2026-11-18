# Top 20 reference flags: screening review

The fixed ranking is `max(abs(volume_zscore), abs(return_zscore))` from `outputs/evaluation/top_20_flags.csv`. I checked each dated source observation and stored ilboursa headlines within seven calendar days. The categories below are provisional review buckets. **“Genuine unexplained” means no verified corporate action or data error in the stored material; it does not mean misconduct.** A nearby headline is context, not proof of cause.

| Rank | Ticker / date | Review class | Basis and remaining question |
|---:|---|---|---|
| 1 | CITY 2026-04-27 | data glitch suspected | Close fell 58% to 8.9496 on 57 shares, then reversed next day. Stored earnings/dividend news does not explain the one-day round trip; verify source quote and adjustment. |
| 2 | CITY 2026-04-28 | data glitch suspected | Close rebounded 156% to 22.92. Same round trip as rank 1; one underlying data-quality question. |
| 3 | BT 2022-05-10 | genuine unexplained | Close fell 18.5% on 12,566 shares; nearby stored item is a general bank profile, not an action notice. Check official dividend/rights history. |
| 4 | PGH 2021-11-30 | likely corporate action | Stored same-day article reports four block transactions totaling over 71 million dinars; 5.76 million share volume corroborates a block-trade context. |
| 5 | ADWYA 2022-06-13 | likely corporate action | Close rose 20.2% after June 7 takeover and trading suspension; 22,413 shares. |
| 6 | SOMOC 2025-05-13 | genuine unexplained | Close fell 21.1% on 170,482 shares; no nearby stored issuer headline. Needs source and corporate-action review. |
| 7 | TRE 2026-09-15 | likely corporate action | Close fell 28.1%; stored September 14–18 items discuss a Tunis Re capital increase. Exact adjustment mechanics still need verification. |
| 8 | TJARI 2023-04-05 | likely corporate action | Close rose 12.2%; April 3 stored dividend and results announcements provide context, not proof of cause. |
| 9 | SAM 2023-04-20 | genuine unexplained | Close rose 20.2% on 177,726 shares; April 14 earnings news is nearby, but no specific corporate-action adjustment is verified. |
| 10 | SIPHA 2023-11-29 | thin-trading artifact | Close fell 16.1% on 53 shares; median observed volume is 28. No nearby stored headline. |
| 11 | STAR 2025-03-12 | genuine unexplained | Close rose 12.0% on 706 shares; March 7 dividend/results item is nearby but cannot establish cause. |
| 12 | ARTES 2023-07-31 | likely corporate action | Close rose 20.4%; July 26 stored article announced a doubled dividend. Check ex-dividend timing. |
| 13 | ICF 2022-09-01 | thin-trading artifact | Median observed volume is 385 and return is 12.3%; August 29 earnings report provides context. Review liquidity before treating as abnormal. |
| 14 | SOTET 2025-07-29 | genuine unexplained | Close fell 14.3%; July 24 interim-results article is nearby, but no action adjustment is verified. |
| 15 | BNA 2025-06-17 | genuine unexplained | Close fell 11.1% on 3,610 shares; no nearby stored issuer headline. |
| 16 | ARTES 2022-07-06 | genuine unexplained | Close fell 11.7% on 1,535 shares; no nearby stored issuer headline. Verify ex-dividend history. |
| 17 | HL 2026-06-30 | genuine unexplained | Close rose 21.2% on 21,613 shares; no nearby stored issuer headline. |
| 18 | BIAT 2024-11-29 | likely corporate action | Close fell 10.4% two days after stored capital-increase announcement; adjustment remains unverified. |
| 19 | TINV 2025-10-22 | thin-trading artifact | Close rose 29.9% after a nine-day gap on 841 shares; median volume 299. The old October 6 case label has no verified public source. |
| 20 | NBL 2025-06-11 | genuine unexplained | Close fell 16.5%; June 9 stored articles mention a loss and TSI impact. These are context, not a confirmed mechanical explanation. |

Totals: six likely corporate-action contexts, two suspected data glitches, three thin-trading artifacts, and nine genuine unexplained screening flags. The 20 ranks are **not** a random sample and the categories are not ground-truth labels. Source observations were left unchanged.
