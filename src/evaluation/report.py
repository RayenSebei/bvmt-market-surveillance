"""Build the evaluation summary from generated result tables."""

from __future__ import annotations

import numpy as np
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
    denominator60 = int(metrics["eligible_positive_events_60d"])
    sourced = int(metrics["sourced_positive_events"])
    source_needed = ", ".join(events.loc[events["source"].eq("SOURCE_NEEDED"), "ticker"])

    event_lines = []
    for row in events.itertuples(index=False):
        date = str(row.event_date)[:10] if pd.notna(row.event_date) else "—"
        original = str(row.original_label_date)[:10] if pd.notna(row.original_label_date) else "—"
        secondary_date = str(row.secondary_date)[:10] if pd.notna(row.secondary_date) else "—"
        source = "`SOURCE_NEEDED`" if row.source == "SOURCE_NEEDED" else f"[source]({row.source})"
        evaluable = "Yes" if str(row.evaluable).lower() == "true" else "No"
        event_lines.append(
            f"| {row.ticker} | {date} | {row.event_date_type} | {original} | {secondary_date} | {source} | "
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
            f"{ratio_text(row.recall_60d, denominator60)} | "
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
    lead_lines = []
    for row in hits.itertuples(index=False):
        secondary = ""
        if pd.notna(row.secondary_date):
            secondary = (
                f"; **{int(row.secondary_lead_time_days_30d)} days to secondary date "
                f"{str(row.secondary_date)[:10]}**"
            )
        lead_lines.append(
            f"- **{row.ticker}: {int(row.lead_time_days_30d)} days to primary date "
            f"{str(row.event_date)[:10]}**{secondary} "
            f"(first matching flag {str(row.first_matching_flag_30d)[:10]})."
        )
    if not lead_lines:
        lead_lines = ["- No evaluable positive event had a matching flag."]

    reference_baseline = baselines.loc[baselines["method"].eq("reference_union")].iloc[0]
    return_baseline = baselines.loc[baselines["method"].eq("absolute_return_only")].iloc[0]
    target_recall = 1 / denominator if denominator else float("nan")
    target_cells = int(np.isclose(sensitivity["recall_30d"], target_recall, equal_nan=False).sum())
    zero_cells = int(np.isclose(sensitivity["recall_30d"], 0, equal_nan=False).sum())

    text = f"""# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. An event's evaluation date is the earliest public suspension, court ruling, or first announcement found in the repository evidence; the original label and a later announcement are retained separately. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **{sourced}**.
- Source-backed positive events with trading data in the primary window: **{denominator}**.
- Source-backed positive events with trading data in the secondary window: **{denominator60}**.
- Negative control: **SOPAT's benign buyout/withdrawal**.
- `SOURCE_NEEDED` and excluded: **{source_needed}**.
- TINV date problem: the label retains **2025-10-06** with date type **`other`**, not `public_announcement`, and has no supporting repository source. Detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Event audit

| Ticker | Primary date | Date type | Original label | Secondary date | Source | Confidence | Evaluable | Reason |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(event_lines)}

## Reference results

- Primary recall: **{ratio_text(metrics['recall_30d'], denominator)}**.
- Secondary recall: **{ratio_text(metrics['recall_60d'], denominator60)}**.
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

The reference detector does **not** beat the absolute-return-only baseline on recall or precision: both match {ratio_text(reference_baseline.recall_30d, denominator)} in the primary window, {ratio_text(reference_baseline.recall_60d, denominator60)} in the secondary window, and {count_text(reference_baseline.precision_at_20, 20, 'flags')} at k=20, while the reference produces {int(reference_baseline.flag_count):,} flags versus {int(return_baseline.flag_count):,}. It matches more events than the volume-only baseline, but at a much higher flag load. The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds; its non-integer event and SOPAT counts are averages, not observed cases.

## Sensitivity grid

| Z cutoff | Rolling window | Flags | Flags/ticker-year | Primary recall |
|---:|---:|---:|---:|---|
{chr(10).join(sensitivity_lines)}

{target_cells} of {len(sensitivity)} sensitivity cells match {ratio_text(target_recall, denominator)}; {zero_cells} of {len(sensitivity)} match 0 of {denominator} events. Flag load ranges from {int(sensitivity['flag_count'].min())} to {int(sensitivity['flag_count'].max())}. No cell was selected to improve the labeled-event result.

## Limitations

Only {sourced} positive events have repository sources, only {denominator} overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. Precision against this incomplete event list can undercount relevant flags. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
"""
    (OUTPUT_DIR / "summary.md").write_text(text, encoding="utf-8")
    print(f"Saved {OUTPUT_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
