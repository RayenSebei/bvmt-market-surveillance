"""Build the evaluation summary from generated result tables."""

from __future__ import annotations

import pandas as pd

from src.evaluation.evaluate import OUTPUT_DIR


def ratio_text(value: float, denominator: int) -> str:
    numerator = float(value) * denominator
    if abs(numerator - round(numerator)) < 1e-9:
        return f"{int(round(numerator))} of {denominator} events"
    return f"{numerator:.3f} of {denominator} events on average"


def count_text(value: float, denominator: int, noun: str) -> str:
    count = float(value) * denominator
    if abs(count - round(count)) < 1e-9:
        return f"{int(round(count))} of {denominator} {noun}"
    return f"{count:.3f} of {denominator} {noun} on average"


def main() -> int:
    metrics = pd.read_csv(OUTPUT_DIR / "metrics.csv").set_index("metric")["value"]
    baselines = pd.read_csv(OUTPUT_DIR / "baseline_comparison.csv")
    precision = pd.read_csv(OUTPUT_DIR / "precision_at_k.csv")
    sensitivity = pd.read_csv(OUTPUT_DIR / "sensitivity.csv")
    events = pd.read_csv(OUTPUT_DIR / "events_table.csv")
    event_results = pd.read_csv(OUTPUT_DIR / "event_results.csv")
    denominator = int(metrics["eligible_positive_events_30d"])
    sourced = int(metrics["sourced_positive_events"])
    source_needed = ", ".join(events.loc[events["source"].eq("SOURCE_NEEDED"), "ticker"])

    event_lines = []
    for row in events.itertuples(index=False):
        date = str(row.event_date)[:10] if pd.notna(row.event_date) else "—"
        source = "`SOURCE_NEEDED`" if row.source == "SOURCE_NEEDED" else f"[source]({row.source})"
        evaluable = "Yes" if str(row.evaluable).lower() == "true" else "No"
        event_lines.append(
            f"| {row.ticker} | {date} | {row.event_date_type} | {source} | "
            f"{row.confidence} | {evaluable} | {row.evaluable_reason} |"
        )

    baseline_lines = []
    for row in baselines.itertuples(index=False):
        negative = (
            f"{row.negative_control_flags_30d:.3f} flags in 1 window on average"
            if row.method.startswith("random_")
            else f"{int(round(row.negative_control_flags_30d))} flags in 1 window"
        )
        baseline_lines.append(
            f"| {row.method} | {int(round(row.flag_count))} | "
            f"{row.flags_per_ticker_year:.3f} | {ratio_text(row.recall_30d, denominator)} | "
            f"{ratio_text(row.recall_60d, denominator)} | "
            f"{count_text(row.precision_at_20, 20, 'flags')} | {negative} |"
        )

    sensitivity_lines = []
    for row in sensitivity.itertuples(index=False):
        sensitivity_lines.append(
            f"| {row.z_cutoff:g} | {int(row.rolling_window)} | {int(row.flag_count)} | "
            f"{row.flags_per_ticker_year:.3f} | {ratio_text(row.recall_30d, denominator)} |"
        )

    precision_text = ", ".join(
        f"{int(row.known_event_nearby_flags)} of {int(row.k)} flags"
        for row in precision.itertuples(index=False)
    )
    reference = sensitivity[
        (sensitivity["z_cutoff"] == 3.0) & (sensitivity["rolling_window"] == 60)
    ].iloc[0]
    hits = event_results[event_results["hit_30d"].astype(str).str.lower().eq("true")]
    lead_lines = [
        f"- **{row.ticker}: {int(row.lead_time_days_30d)} days** "
        f"(first matching flag {str(row.first_matching_flag_30d)[:10]})."
        for row in hits.itertuples(index=False)
    ] or ["- No evaluable positive event had a matching flag."]

    text = f"""# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **{sourced}**.
- Source-backed positive events with trading data in the primary window: **{denominator}**.
- Negative control: **SOPAT's benign buyout/withdrawal**.
- `SOURCE_NEEDED` and excluded: **{source_needed}**.
- TINV date problem: the label retains **2025-10-06** with date type **`other`**, not `public_announcement`, and has no supporting repository source. Detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Event audit

| Ticker | Event date | Date type | Source | Confidence | Evaluable | Reason |
|---|---|---|---|---|---|---|
{chr(10).join(event_lines)}

## Reference results

- Primary recall: **{ratio_text(metrics['recall_30d'], denominator)}**.
- Secondary recall: **{ratio_text(metrics['recall_60d'], denominator)}**.
- Ranked known-event matches at k=10, 20, 50: **{precision_text}**, respectively. This underestimates real precision because most relevant events are not labeled.
- Flag load: **{int(metrics['flag_count'])} flags**, or **{metrics['flags_per_ticker_year']:.3f} flags per ticker-year**.
- Negative-control behavior: **{int(metrics['negative_control_flags_30d'])} flags in 1 SOPAT window**.
- The fixed z=3.0, 60-day reference cell independently reports **{int(reference.flag_count)} flags** and **{ratio_text(reference.recall_30d, denominator)}**.

### Lead time for each hit

{chr(10).join(lead_lines)}

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Precision@20 | SOPAT-window flags |
|---|---:|---:|---|---|---|---|
{chr(10).join(baseline_lines)}

The reference detector does **not** beat the absolute-return-only baseline on recall or precision: both match 1 of 2 events in both windows and 0 of 20 top-ranked flags, while the reference produces 1,027 flags versus 903. It matches more events than the volume-only baseline, but at a much higher flag load. The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds; its non-integer event and SOPAT counts are averages, not observed cases.

## Sensitivity grid

| Z cutoff | Rolling window | Flags | Flags/ticker-year | Primary recall |
|---:|---:|---:|---:|---|
{chr(10).join(sensitivity_lines)}

Fourteen of 16 sensitivity cells match 1 of 2 events. The 120-day cells at z=3.5 and z=4.0 match 0 of 2 events. Flag load ranges from {int(sensitivity['flag_count'].min())} to {int(sensitivity['flag_count'].max())}. No cell was selected to improve the labeled-event result.

## Limitations

Only {sourced} positive events have repository sources, only {denominator} overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. Precision against this incomplete event list can undercount relevant flags. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
"""
    (OUTPUT_DIR / "summary.md").write_text(text, encoding="utf-8")
    print(f"Saved {OUTPUT_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
