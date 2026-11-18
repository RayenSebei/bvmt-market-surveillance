# BVMT Market Surveillance: verified fact sheet

Sources: `../README.md`, `../docs/REPORT.md`, `../outputs/evaluation/summary.md`, `../frontend/README.md`, `../src/detection/anomaly_detector.py`, `../bvmt_data/anomaly_flags.csv`, `../bvmt_data/GIF.csv`, and `../data/evaluation/events.csv`.

- Scope: independent academic statistical screening for human review at the Tunis Stock Exchange. It does not establish fraud.
- Data: 85 symbols, 67,035 source observations, 17 June 2021 to 12 October 2026. The local combined price file has 6,594 observations in 2021, 10,918 in 2022, 10,457 in 2023, 11,775 in 2024, 14,842 in 2025, and 12,449 in 2026. The years at either end are partial.
- Engine: rolling z-scores for absolute daily return and log(1 + volume); 60 valid prior observations, excluding the current observation; cutoff 3.0. The code applies standard-deviation floors and omits returns across gaps longer than 10 calendar days.
- Workflow: price and local news CSVs, anomaly and decay detection, news context, classification, refined watchlist, optional Groq draft triage, human review. Flask research dashboard and optional React/TypeScript Market Command Center.
- Results: 1,414 reference flags. The refined watchlist has 16 rows: 10 spike cases and 6 decay cases. This is not a count of confirmed misconduct.
- Evaluation: three source-backed positive events with trading coverage. GIF was flagged on 22 October 2024, three calendar days before its 25 October suspension; LSTR and SERVI were missed. Reference recall is 1/3 in the fixed -30/+5 day window. Precision@10, @20, and @50 are each zero against the incomplete label registry. The reference detector has the same recall and precision@20 as the return-only baseline while producing 177 more flags.
- GIF example: 22 October close TND 0.44, volume 14,344, daily return 10%, return z-score 5.236, volume z-score 1.341. This was a return-only flag and did not enter the refined watchlist. It is a retrospective case study, not proof of advance prediction or fraud.
- Evaluation caveat: three events and incomplete labels cannot support a general performance estimate. No independent test set exists. Thin liquidity, data gaps, incomplete news, and survivorship bias matter.

