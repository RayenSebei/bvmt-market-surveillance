from pathlib import Path

import pandas as pd

from src.evaluation.triage_stats import build_triage_stats, build_watchlist_funnel


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


def test_watchlist_funnel_uses_mutually_exclusive_exclusion_rules():
    classified = pd.DataFrame({
        "symbole": ["AAA", "AAA", "AAA", "AAA"],
        "date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
        "volume_anomaly": [True, True, False, True],
        "price_anomaly": [True, False, True, True],
        "combined_anomaly": [True, False, False, True],
        "status": ["NO_LOCAL_MATCH", "NO_LOCAL_MATCH", "NEWS_MATCH_FOUND", "NEWS_MATCH_FOUND"],
    })
    watchlist = classified.iloc[[0]][["symbole", "date"]]
    events = pd.DataFrame({
        "event_id": ["AAA-2025", "BBB-2025"],
        "ticker": ["AAA", "BBB"],
        "event_date": ["2025-01-05", "2025-01-05"],
        "evaluable": [True, True],
    })

    funnel = build_watchlist_funnel(classified, watchlist, watchlist, events)
    counts = funnel.loc[funnel["record_type"].eq("funnel_count")].set_index(
        "exclusion_rule"
    )["count"]

    assert counts.to_dict() == {
        "single_signal_only": 1,
        "news_matched": 1,
        "both": 1,
    }
    event_flags = funnel.loc[funnel["record_type"].eq("event_flag")]
    assert event_flags["in_watchlist"].tolist() == [True, False, False, False]
    assert "BBB" in funnel.loc[funnel["record_type"].eq("event_no_flags"), "ticker"].tolist()
