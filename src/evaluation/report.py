"""Build the concise evaluation summary from generated result tables."""

from __future__ import annotations

import pandas as pd

from src.evaluation.evaluate import OUTPUT_DIR


def ratio_text(value: float, denominator: int) -> str:
    numerator = value * denominator
    if abs(numerator - round(numerator)) < 1e-9:
        return f"{int(round(numerator))} of {denominator} events"
    return f"{numerator:.3f} of {denominator} events on average"


def main() -> int:
    metrics = pd.read_csv(OUTPUT_DIR / "metrics.csv").set_index("metric")["value"]
    baselines = pd.read_csv(OUTPUT_DIR / "baseline_comparison.csv")
    precision = pd.read_csv(OUTPUT_DIR / "precision_at_k.csv")
    sensitivity = pd.read_csv(OUTPUT_DIR / "sensitivity.csv")
    events = pd.read_csv(OUTPUT_DIR / "events_table.csv")
    denominator = int(metrics["eligible_positive_events_30d"])
    sourced = int(metrics["sourced_positive_events"])
    source_needed = ", ".join(events.loc[events["source"].eq("SOURCE_NEEDED"), "ticker"])

    baseline_lines = []
    for row in baselines.itertuples(index=False):
        baseline_lines.append(
            f"| {row.method} | {int(round(row.flag_count))} | "
            f"{row.flags_per_ticker_year:.3f} | {ratio_text(row.recall_30d, denominator)} | "
            f"{ratio_text(row.recall_60d, denominator)} | "
            f"{row.precision_at_20:.4f} | {row.negative_control_flags_30d:.3f} |"
        )
    precision_text = ", ".join(
        f"{int(row.known_event_nearby_flags)} of {int(row.k)}" for row in precision.itertuples(index=False)
    )
    reference = sensitivity[(sensitivity["z_cutoff"] == 3.0) & (sensitivity["rolling_window"] == 60)].iloc[0]

    text = f"""# Evaluation Summary

## Scope

This is a case-study-level evaluation, not a statistical performance estimate. The fixed primary window counts a flag from 30 calendar days before through 5 days after an event; the secondary view starts 60 days before. Detector parameters remain at the original reference values (z cutoff 3.0 and rolling window 60); the sensitivity grid is reporting only.

- Source-backed positive events: **{sourced}**.
- Source-backed positive events with trading data in the primary window: **{denominator}**.
- Negative control: **SOPAT's benign buyout/withdrawal**.
- `SOURCE_NEEDED` and excluded: **{source_needed}**.
- TINV date problem: the label retains **2025-10-06** with an unresolved date type and no supporting repository source; detector flags on **2025-10-13** and **2025-10-22** occur after that date. The date was not moved and TINV is excluded from headline metrics.

## Reference results

- Primary recall: **{ratio_text(metrics['recall_30d'], denominator)}**.
- Secondary recall: **{ratio_text(metrics['recall_60d'], denominator)}**.
- Ranked known-event matches at k=10, 20, 50: **{precision_text} flags**, respectively. This underestimates real precision because most true events are not labeled.
- Flag load: **{int(metrics['flag_count'])} flags**, or **{metrics['flags_per_ticker_year']:.3f} flags per ticker-year**.
- Negative-control behavior: **{int(metrics['negative_control_flags_30d'])} flags** near SOPAT in the primary window.
- The fixed z=3.0, 60-day reference cell independently reports **{int(reference.flag_count)} flags** and **{ratio_text(reference.recall_30d, denominator)}**.

## Baseline comparison

| Method | Flags | Flags/ticker-year | Recall -30/+5 | Recall -60/+5 | Precision@20 | SOPAT-window flags |
|---|---:|---:|---|---|---:|---:|
{chr(10).join(baseline_lines)}

The random method keeps the reference number of flags per ticker and averages 1,000 deterministic seeds. Its non-integer event count and SOPAT count are averages, not observed cases.

## Limitations

Only three positive events have repository sources, only two overlap the trading-data window, and no independent test set exists. Original parameters were hand chosen, labels are incomplete, delisted companies create coverage gaps, and survivorship bias is possible. These results cannot support a general performance claim or model training. Exact binomial intervals would still be dominated by the tiny denominator.
"""
    (OUTPUT_DIR / "summary.md").write_text(text, encoding="utf-8")
    print(f"Saved {OUTPUT_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
