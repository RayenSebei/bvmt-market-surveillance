"""Write descriptive counts for the news-context and watchlist triage stages."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLASSIFIED_PATH = ROOT / "bvmt_data" / "anomaly_classified.csv"
WATCHLIST_PATH = ROOT / "bvmt_data" / "watchlist.csv"
REFINED_WATCHLIST_PATH = ROOT / "bvmt_data" / "watchlist_refined.csv"
EVENTS_PATH = ROOT / "outputs" / "evaluation" / "events_table.csv"
OUTPUT_PATH = ROOT / "outputs" / "evaluation" / "triage_stats.csv"
FUNNEL_OUTPUT_PATH = ROOT / "outputs" / "evaluation" / "watchlist_funnel.csv"
NEWS_MATCH_FOUND = "NEWS_MATCH_FOUND"
NO_LOCAL_MATCH = "NO_LOCAL_MATCH"
FUNNEL_COLUMNS = [
    "record_type",
    "event_id",
    "ticker",
    "event_date",
    "window_start",
    "window_end",
    "date",
    "volume_anomaly",
    "price_anomaly",
    "combined_anomaly",
    "status",
    "in_watchlist",
    "in_watchlist_refined",
    "exclusion_rule",
    "count",
]


def _true_mask(series: pd.Series) -> pd.Series:
    """Interpret CSV boolean values without changing their stored meaning."""
    return series.astype(str).str.strip().str.lower().eq("true")


def _is_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def _dated_keys(frame: pd.DataFrame) -> set[tuple[str, pd.Timestamp]]:
    dates = pd.to_datetime(frame["date"], errors="coerce").dt.normalize()
    return {
        (str(ticker), date)
        for ticker, date in zip(frame["symbole"], dates)
        if pd.notna(ticker) and pd.notna(date)
    }


def build_watchlist_funnel(
    classified: pd.DataFrame,
    watchlist: pd.DataFrame,
    refined_watchlist: pd.DataFrame,
    events: pd.DataFrame,
    window_days_before: int = 30,
    window_days_after: int = 5,
) -> pd.DataFrame:
    """Describe event-window flags and mutually exclusive watchlist outcomes."""
    required = {
        "classified": {
            "symbole", "date", "volume_anomaly", "price_anomaly",
            "combined_anomaly", "status",
        },
        "watchlist": {"symbole", "date"},
        "refined_watchlist": {"symbole", "date"},
        "events": {"event_id", "ticker", "event_date", "evaluable"},
    }
    frames = {
        "classified": classified,
        "watchlist": watchlist,
        "refined_watchlist": refined_watchlist,
        "events": events,
    }
    for name, columns in required.items():
        missing = columns.difference(frames[name].columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    flags = classified.copy()
    flags["date"] = pd.to_datetime(flags["date"], errors="coerce").dt.normalize()
    combined = _true_mask(flags["combined_anomaly"])
    news_matched = flags["status"].eq(NEWS_MATCH_FOUND)
    exclusion_rule = pd.Series("", index=flags.index, dtype="object")
    exclusion_rule.loc[~combined & ~news_matched] = "single_signal_only"
    exclusion_rule.loc[combined & news_matched] = "news_matched"
    exclusion_rule.loc[~combined & news_matched] = "both"
    flags["exclusion_rule"] = exclusion_rule

    watchlist_keys = _dated_keys(watchlist)
    refined_keys = _dated_keys(refined_watchlist)
    evaluable = events.loc[_true_mask(events["evaluable"])].copy()
    evaluable["event_date"] = pd.to_datetime(
        evaluable["event_date"], errors="coerce"
    ).dt.normalize()

    rows = []
    for event in evaluable.itertuples(index=False):
        window_start = event.event_date - pd.Timedelta(int(window_days_before), unit="days")
        window_end = event.event_date + pd.Timedelta(int(window_days_after), unit="days")
        nearby = flags.loc[
            flags["symbole"].eq(event.ticker)
            & flags["date"].between(window_start, window_end, inclusive="both")
        ].sort_values("date")
        if nearby.empty:
            rows.append({
                "record_type": "event_no_flags",
                "event_id": event.event_id,
                "ticker": event.ticker,
                "event_date": event.event_date.date(),
                "window_start": window_start.date(),
                "window_end": window_end.date(),
                "status": "NO_FLAGS_IN_PRIMARY_WINDOW",
            })
            continue
        for flag in nearby.itertuples(index=False):
            key = (str(flag.symbole), flag.date)
            rows.append({
                "record_type": "event_flag",
                "event_id": event.event_id,
                "ticker": event.ticker,
                "event_date": event.event_date.date(),
                "window_start": window_start.date(),
                "window_end": window_end.date(),
                "date": flag.date.date(),
                "volume_anomaly": _is_true(flag.volume_anomaly),
                "price_anomaly": _is_true(flag.price_anomaly),
                "combined_anomaly": _is_true(flag.combined_anomaly),
                "status": flag.status,
                "in_watchlist": key in watchlist_keys,
                "in_watchlist_refined": key in refined_keys,
                "exclusion_rule": flag.exclusion_rule,
            })

    outcome_masks = {
        "single_signal_only": ~combined & ~news_matched,
        "news_matched": combined & news_matched,
        "both": ~combined & news_matched,
    }
    for rule, mask in outcome_masks.items():
        rows.append({
            "record_type": "funnel_count",
            "exclusion_rule": rule,
            "count": int(mask.sum()),
        })

    result = pd.DataFrame(rows, columns=FUNNEL_COLUMNS)
    result["count"] = pd.array(result["count"], dtype="Int64")
    return result


def build_triage_stats(
    classified: pd.DataFrame,
    watchlist: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Return descriptive counts without changing detection or prioritization."""
    required = {
        "classified": (classified, {"symbole", "date", "status", "category"}),
        "watchlist": (watchlist, {"symbole", "date"}),
        "events": (events, {"ticker", "evaluable"}),
    }
    for name, (frame, columns) in required.items():
        missing = columns.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    matched = classified["status"].eq(NEWS_MATCH_FOUND)
    rows = [
        {"section": "flags", "metric": "total_flags", "category": "", "count": len(classified)},
        {
            "section": "news_context",
            "metric": "flags_with_matched_news_context",
            "category": "",
            "count": int(matched.sum()),
        },
        {
            "section": "news_context",
            "metric": "flags_without_matched_news_context",
            "category": "",
            "count": int((~matched).sum()),
        },
    ]

    categories = (
        classified.loc[matched, "category"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    for category, count in categories[categories.ne("")].value_counts().sort_index().items():
        rows.append(
            {
                "section": "classification_category",
                "metric": "matched_news_category",
                "category": category,
                "count": int(count),
            }
        )

    classified_dates = pd.to_datetime(classified["date"], errors="coerce").dt.normalize()
    watchlist_dates = pd.to_datetime(watchlist["date"], errors="coerce").dt.normalize()
    watchlist_keys = {
        (str(symbol), date)
        for symbol, date in zip(watchlist["symbole"], watchlist_dates)
        if pd.notna(symbol) and pd.notna(date)
    }
    surviving_flags = sum(
        (str(symbol), date) in watchlist_keys
        for symbol, date in zip(classified["symbole"], classified_dates)
        if pd.notna(symbol) and pd.notna(date)
    )
    rows.extend(
        [
            {
                "section": "watchlist",
                "metric": "anomaly_flags_in_refined_watchlist",
                "category": "",
                "count": int(surviving_flags),
            },
            {
                "section": "watchlist",
                "metric": "refined_watchlist_rows",
                "category": "",
                "count": len(watchlist),
            },
        ]
    )

    evaluable = events["evaluable"].astype(str).str.lower().eq("true")
    evaluated_tickers = set(events.loc[evaluable, "ticker"].dropna().astype(str))
    watchlist_tickers = set(watchlist["symbole"].dropna().astype(str))
    rows.extend(
        [
            {
                "section": "evaluated_events",
                "metric": "evaluated_event_tickers_total",
                "category": "",
                "count": len(evaluated_tickers),
            },
            {
                "section": "evaluated_events",
                "metric": "evaluated_event_tickers_on_refined_watchlist",
                "category": "",
                "count": len(evaluated_tickers & watchlist_tickers),
            },
        ]
    )
    return pd.DataFrame(rows, columns=["section", "metric", "category", "count"])


def main(
    classified_path: Path = CLASSIFIED_PATH,
    watchlist_path: Path = WATCHLIST_PATH,
    refined_watchlist_path: Path = REFINED_WATCHLIST_PATH,
    events_path: Path = EVENTS_PATH,
    output_path: Path = OUTPUT_PATH,
    funnel_output_path: Path = FUNNEL_OUTPUT_PATH,
) -> int:
    classified = pd.read_csv(classified_path)
    watchlist = pd.read_csv(watchlist_path)
    refined_watchlist = pd.read_csv(refined_watchlist_path)
    events = pd.read_csv(events_path)
    stats = build_triage_stats(
        classified,
        refined_watchlist,
        events,
    )
    funnel = build_watchlist_funnel(
        classified,
        watchlist,
        refined_watchlist,
        events,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats.to_csv(output_path, index=False)
    funnel.to_csv(funnel_output_path, index=False)
    print(stats.to_string(index=False))
    print(f"Saved {output_path}")
    print(funnel.to_string(index=False))
    print(f"Saved {funnel_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
