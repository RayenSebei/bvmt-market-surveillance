from pathlib import Path

import pandas as pd
import pytest

from src.scraping.scrape_ilboursa import (
    PRICE_COLUMNS,
    merge_price_history,
    normalize_price_frame,
    verify_snapshot_rows_unchanged,
)
from src.scraping.scrape_news import NEWS_COLUMNS, merge_news, normalize_news


def price_frame(symbol: str, rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "ticker_name": symbol,
            "symbole": symbol,
            "date": date,
            "ouverture": close,
            "haut": close,
            "bas": close,
            "cloture": close,
            "volume": 100,
        }
        for date, close in rows
    ])[PRICE_COLUMNS]


def test_incremental_price_merge_preserves_overlap_and_appends_new_date():
    existing = normalize_price_frame(
        price_frame("AAA", [("2026-01-01", 10.0), ("2026-01-02", 11.0)]),
        "AAA",
        "AAA",
    )
    refreshed = normalize_price_frame(
        price_frame("AAA", [("2026-01-02", 999.0), ("2026-01-03", 12.0)]),
        "AAA",
        "AAA",
    )

    merged, added = merge_price_history(existing, refreshed)

    assert added == 1
    assert merged["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01", "2026-01-02", "2026-01-03"
    ]
    assert merged.loc[merged["date"].eq(pd.Timestamp("2026-01-02")), "cloture"].item() == 11.0


def test_snapshot_check_detects_changed_historical_row():
    root = Path(__file__).parent / "fixtures" / "incremental_tmp"
    snapshot = root / "snapshot"
    current = root / "current"
    snapshot.mkdir(parents=True, exist_ok=True)
    current.mkdir(parents=True, exist_ok=True)
    try:
        price_frame("AAA", [("2026-01-01", 10.0)]).to_csv(snapshot / "AAA.csv", index=False)
        price_frame("AAA", [("2026-01-01", 11.0)]).to_csv(current / "AAA.csv", index=False)

        with pytest.raises(ValueError, match="old rows changed"):
            verify_snapshot_rows_unchanged(snapshot, current)
    finally:
        (snapshot / "AAA.csv").unlink(missing_ok=True)
        (current / "AAA.csv").unlink(missing_ok=True)
        snapshot.rmdir()
        current.rmdir()
        root.rmdir()


def test_incremental_news_merge_deduplicates_symbol_date_headline_url():
    existing = normalize_news(pd.DataFrame([
        {"date_str": "01/10/26", "time_str": "09:00", "headline": "Existing", "url": "https://example.test/1"}
    ], columns=NEWS_COLUMNS), "AAA")
    incoming = normalize_news(pd.DataFrame([
        {"date_str": "01/10/26", "time_str": "09:01", "headline": "Existing", "url": "https://example.test/1"},
        {"date_str": "02/10/26", "time_str": "10:00", "headline": "New", "url": "https://example.test/2"},
    ], columns=NEWS_COLUMNS), "AAA")

    merged, added = merge_news(existing, incoming, "AAA")

    assert added == 1
    assert merged["headline"].tolist() == ["New", "Existing"]
