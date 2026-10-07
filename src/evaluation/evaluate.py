"""Evaluate ranked screening flags against a small source-backed event set."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "bvmt_data" / "_all_tickers_full.csv"
FLAGS_PATH = ROOT / "bvmt_data" / "anomaly_flags.csv"
EVENTS_PATH = ROOT / "data" / "evaluation" / "events.csv"
CONFIG_PATH = Path(__file__).with_name("config.json")
OUTPUT_DIR = ROOT / "outputs" / "evaluation"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_inputs(
    data_path: Path = DATA_PATH,
    flags_path: Path = FLAGS_PATH,
    events_path: Path = EVENTS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trading = pd.read_csv(data_path, parse_dates=["date"])
    flags = pd.read_csv(flags_path, parse_dates=["date"])
    events = pd.read_csv(events_path)
    for column in ("event_date", "original_label_date", "secondary_date"):
        events[column] = pd.to_datetime(events[column], errors="coerce")
    events["include_headline"] = events["include_headline"].astype(str).str.lower().eq("true")
    return trading, flags, events


def coverage_table(trading: pd.DataFrame, events: pd.DataFrame, lookback: int) -> pd.DataFrame:
    bounds = trading.groupby("symbole")["date"].agg(["min", "max"])
    rows = []
    for event in events.itertuples(index=False):
        event_date = pd.Timestamp(event.event_date) if pd.notna(event.event_date) else pd.NaT
        start = event_date - pd.Timedelta(int(lookback), unit="D") if pd.notna(event_date) else pd.NaT
        if event.ticker in bounds.index:
            first, last = bounds.loc[event.ticker, ["min", "max"]]
            overlap = pd.notna(start) and last >= start and first <= event_date + pd.Timedelta(5, unit="D")
            gap = (event_date - last).days if pd.notna(event_date) else np.nan
        else:
            first = last = pd.NaT
            overlap = False
            gap = np.nan
        rows.append({
            "event_id": event.event_id, "ticker": event.ticker,
            "first_trading_date": first, "last_trading_date": last,
            "days_from_last_trade_to_event": gap,
            f"has_{lookback}d_window_coverage": bool(overlap),
        })
    return pd.DataFrame(rows)


def eligible_positive_events(
    trading: pd.DataFrame, events: pd.DataFrame, lookback: int
) -> pd.DataFrame:
    coverage = coverage_table(trading, events, lookback)
    merged = events.merge(coverage[["event_id", f"has_{lookback}d_window_coverage"]], on="event_id")
    return merged[
        merged["include_headline"]
        & merged["label_role"].eq("positive")
        & merged["source"].ne("SOURCE_NEEDED")
        & merged["event_date"].notna()
        & merged[f"has_{lookback}d_window_coverage"]
    ].copy()


def flag_matches_event(flag_date: pd.Timestamp, ticker: str, event: pd.Series, before: int, after: int) -> bool:
    event_date = pd.Timestamp(event["event_date"])
    return (
        ticker == event["ticker"]
        and event_date - pd.Timedelta(int(before), unit="D") <= flag_date
        <= event_date + pd.Timedelta(int(after), unit="D")
    )


def event_hits(flags: pd.DataFrame, events: pd.DataFrame, before: int, after: int) -> pd.DataFrame:
    rows = []
    for event in events.itertuples(index=False):
        event_date = pd.Timestamp(event.event_date)
        start = event_date - pd.Timedelta(int(before), unit="D")
        end = event_date + pd.Timedelta(int(after), unit="D")
        matched = flags[
            flags["symbole"].eq(event.ticker)
            & flags["date"].between(start, end, inclusive="both")
        ].sort_values("date")
        rows.append({
            "event_id": event.event_id,
            "hit": not matched.empty,
            "matching_flags": len(matched),
            "first_matching_flag": matched["date"].min() if not matched.empty else pd.NaT,
            "lead_time_days": (
                (event_date - matched["date"].min()).days if not matched.empty else np.nan
            ),
        })
    return pd.DataFrame(rows)


def flags_per_ticker_year(flags: pd.DataFrame, trading: pd.DataFrame) -> float:
    bounds = trading.groupby("symbole")["date"].agg(["min", "max"])
    ticker_years = ((bounds["max"] - bounds["min"]).dt.days / 365.25).clip(lower=1 / 365.25).sum()
    return float(len(flags) / ticker_years)


def ranked_flags(flags: pd.DataFrame) -> pd.DataFrame:
    ranked = flags.copy()
    ranked["screening_score"] = ranked[["volume_zscore", "return_zscore"]].abs().max(axis=1)
    return ranked.sort_values(["screening_score", "date"], ascending=[False, True]).reset_index(drop=True)


def precision_at_k(
    flags: pd.DataFrame, events: pd.DataFrame, before: int, after: int, values: list[int]
) -> pd.DataFrame:
    ranked = ranked_flags(flags)
    rows = []
    for k in values:
        top = ranked.head(k)
        matches = 0
        for flag in top.itertuples(index=False):
            if any(
                flag_matches_event(flag.date, flag.symbole, event, before, after)
                for _, event in events.iterrows()
            ):
                matches += 1
        rows.append({"k": k, "known_event_nearby_flags": matches, "precision_at_k": matches / len(top) if len(top) else np.nan})
    return pd.DataFrame(rows)


def negative_control_count(flags: pd.DataFrame, events: pd.DataFrame, before: int, after: int) -> int:
    negatives = events[
        events["label_role"].eq("negative") & events["event_date"].notna()
    ]
    return int(sum(
        any(flag_matches_event(flag.date, flag.symbole, event, before, after) for _, event in negatives.iterrows())
        for flag in flags.itertuples(index=False)
    ))


def write_summary_svg(metrics: pd.DataFrame, path: Path) -> None:
    values = metrics.set_index("metric")["value"]
    recall = float(values.get("recall_30d", 0) or 0)
    event_count = int(values.get("eligible_positive_events_30d", 0) or 0)
    hit_count = recall * event_count
    hit_label = (
        f"{int(round(hit_count))} of {event_count}"
        if abs(hit_count - round(hit_count)) < 1e-9
        else f"{hit_count:.3f} of {event_count}"
    )
    false_flags = int(float(values.get("negative_control_flags_30d", 0) or 0))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="260" viewBox="0 0 760 260">
<rect width="760" height="260" fill="#f8fafc"/><text x="36" y="42" font-family="Arial" font-size="22" font-weight="700" fill="#0f172a">Reference detector evaluation</text>
<text x="36" y="82" font-family="Arial" font-size="15" fill="#475569">Recall within 30 days before to 5 days after sourced positive events</text>
<rect x="36" y="102" width="620" height="28" rx="6" fill="#e2e8f0"/><rect x="36" y="102" width="{620 * recall:.1f}" height="28" rx="6" fill="#0f766e"/>
<text x="670" y="123" font-family="Arial" font-size="16" font-weight="700" fill="#0f172a">{hit_label}</text>
<text x="36" y="178" font-family="Arial" font-size="15" fill="#475569">Flags near the SOPAT negative control</text>
<text x="36" y="218" font-family="Arial" font-size="36" font-weight="700" fill="#b45309">{false_flags}</text>
<text x="72" y="216" font-family="Arial" font-size="14" fill="#64748b">false-alarm behaviour must be reviewed, not treated as proof</text></svg>'''
    path.write_text(svg, encoding="utf-8")


def main(
    data_path: Path = DATA_PATH,
    flags_path: Path = FLAGS_PATH,
    events_path: Path = EVENTS_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> int:
    config = load_config()
    before = int(config["primary_window_days_before"])
    secondary = int(config["secondary_window_days_before"])
    after = int(config["window_days_after"])
    trading, flags, events = load_inputs(data_path, flags_path, events_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    coverage30 = coverage_table(trading, events, before)
    coverage60 = coverage_table(trading, events, secondary)
    coverage = coverage30.merge(
        coverage60[["event_id", f"has_{secondary}d_window_coverage"]], on="event_id"
    )
    positives30 = eligible_positive_events(trading, events, before)
    positives60 = eligible_positive_events(trading, events, secondary)
    hits30 = event_hits(flags, positives30, before, after)
    hits60 = event_hits(flags, positives60, secondary, after)
    precision = precision_at_k(flags, positives30, before, after, config["precision_at_k"])

    event_results = events.merge(coverage, on=["event_id", "ticker"], how="left")
    event_results = event_results.merge(hits30.add_suffix("_30d"), left_on="event_id", right_on="event_id_30d", how="left").drop(columns=["event_id_30d"])
    event_results = event_results.merge(hits60.add_suffix("_60d"), left_on="event_id", right_on="event_id_60d", how="left").drop(columns=["event_id_60d"])
    event_results["secondary_lead_time_days_30d"] = (
        event_results["secondary_date"] - event_results["first_matching_flag_30d"]
    ).dt.days.where(event_results["hit_30d"].eq(True))

    metrics = pd.DataFrame([
        {"metric": "sourced_positive_events", "value": int(events["include_headline"].mul(events["label_role"].eq("positive")).sum()), "detail": "before coverage exclusions"},
        {"metric": "eligible_positive_events_30d", "value": len(positives30), "detail": "source-backed and trading-window coverage"},
        {"metric": "eligible_positive_events_60d", "value": len(positives60), "detail": "source-backed and trading-window coverage"},
        {"metric": "recall_30d", "value": hits30["hit"].mean() if len(hits30) else np.nan, "detail": f"window -{before}/+{after} calendar days"},
        {"metric": "recall_60d", "value": hits60["hit"].mean() if len(hits60) else np.nan, "detail": f"window -{secondary}/+{after} calendar days"},
        {"metric": "flag_count", "value": len(flags), "detail": "reference detector union"},
        {"metric": "flags_per_ticker_year", "value": flags_per_ticker_year(flags, trading), "detail": "all reference flags / observed ticker-years"},
        {"metric": "negative_control_flags_30d", "value": negative_control_count(flags, events, before, after), "detail": "SOPAT window"},
    ])

    event_results.to_csv(output_dir / "event_results.csv", index=False)
    events_table = event_results[[
        "event_id", "ticker", "event_name", "event_date", "event_date_type",
        "original_label_date", "secondary_date",
        "source", "confidence", "label_role", "include_headline",
        f"has_{before}d_window_coverage", "days_from_last_trade_to_event",
    ]].copy()
    events_table["evaluable"] = (
        events_table["include_headline"]
        & events_table["label_role"].eq("positive")
        & events_table["source"].ne("SOURCE_NEEDED")
        & events_table["event_date"].notna()
        & events_table[f"has_{before}d_window_coverage"]
    )
    def reason(row):
        if row["source"] == "SOURCE_NEEDED":
            return "no supporting repository source"
        if pd.isna(row["event_date"]):
            return "event date unavailable"
        if row["label_role"] == "negative":
            return "negative control, not a positive event"
        if row["label_role"] == "exploratory":
            return "exploratory case excluded from headline metrics"
        if not row[f"has_{before}d_window_coverage"]:
            return "trading data ends before the evaluation window"
        return "source-backed positive event with window coverage"
    events_table["evaluable_reason"] = events_table.apply(reason, axis=1)
    events_table.to_csv(output_dir / "events_table.csv", index=False)
    coverage.to_csv(output_dir / "coverage.csv", index=False)
    precision.to_csv(output_dir / "precision_at_k.csv", index=False)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    print(metrics.to_string(index=False))
    print(f"Saved evaluation outputs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
