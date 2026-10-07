from pathlib import Path

import pandas as pd

from src.scraping.scrape_ilboursa import (
    PRICE_COLUMNS,
    rebuild_combined_from_individual_files,
)


def ticker_frame(symbol, date, close):
    return pd.DataFrame({
        "ticker_name": [symbol],
        "symbole": [symbol],
        "date": [date],
        "ouverture": [close],
        "haut": [close],
        "bas": [close],
        "cloture": [close],
        "volume": [100],
    })[PRICE_COLUMNS]


def test_rebuild_combined_includes_existing_and_new_individual_files():
    directory = Path(__file__).parent / "fixtures" / "scraper_rebuild_tmp"
    try:
        ticker_frame("AB", "2024-01-02", 10.0).to_csv(directory / "AB.csv", index=False)
        ticker_frame("BIAT", "2024-01-03", 20.0).to_csv(directory / "BIAT.csv", index=False)
        ticker_frame("IGNORE", "2024-01-04", 30.0).to_csv(
            directory / "watchlist.csv", index=False
        )

        combined = rebuild_combined_from_individual_files(directory)

        assert combined["symbole"].tolist() == ["AB", "BIAT"]
        written = pd.read_csv(directory / "_all_tickers_combined.csv")
        assert written["symbole"].tolist() == ["AB", "BIAT"]
    finally:
        for path in directory.glob("*.csv"):
            path.unlink(missing_ok=True)
