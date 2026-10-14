"""Write descriptive counts for the news-context and watchlist triage stages."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLASSIFIED_PATH = ROOT / "bvmt_data" / "anomaly_classified.csv"
WATCHLIST_PATH = ROOT / "bvmt_data" / "watchlist_refined.csv"
EVENTS_PATH = ROOT / "outputs" / "evaluation" / "events_table.csv"
OUTPUT_PATH = ROOT / "outputs" / "evaluation" / "triage_stats.csv"
NEWS_MATCH_FOUND = "NEWS_MATCH_FOUND"


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
    events_path: Path = EVENTS_PATH,
    output_path: Path = OUTPUT_PATH,
) -> int:
    stats = build_triage_stats(
        pd.read_csv(classified_path),
        pd.read_csv(watchlist_path),
        pd.read_csv(events_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats.to_csv(output_path, index=False)
    print(stats.to_string(index=False))
    print(f"Saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
