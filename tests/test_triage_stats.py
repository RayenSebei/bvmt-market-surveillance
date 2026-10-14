from pathlib import Path

import pandas as pd

from src.evaluation.triage_stats import build_triage_stats


def test_triage_stats_use_existing_offline_fixtures():
    fixtures = Path(__file__).parent / "fixtures"
    classified = pd.read_csv(fixtures / "api_data" / "anomaly_classified.csv")
    classified["status"] = "NEWS_MATCH_FOUND"
    watchlist = classified[["symbole", "date"]].copy()
    events = pd.read_csv(fixtures / "evaluation" / "events_table.csv")

    stats = build_triage_stats(classified, watchlist, events)
    counts = stats.set_index("metric")["count"]

    assert counts["total_flags"] == 1
    assert counts["flags_with_matched_news_context"] == 1
    assert counts["flags_without_matched_news_context"] == 0
    assert counts["matched_news_category"] == 1
    assert counts["anomaly_flags_in_refined_watchlist"] == 1
    assert counts["evaluated_event_tickers_on_refined_watchlist"] == 1
