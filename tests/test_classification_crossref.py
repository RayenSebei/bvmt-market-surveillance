import pandas as pd

from src.detection.crossref_legal_events import check_matches
from src.validation.classify_anomalies import (
    NEWS_MATCH_FOUND, NO_LOCAL_MATCH, classify_anomalies, classify_headline,
    find_nearby_news,
)


def test_headline_categories_and_nearest_news():
    news = pd.DataFrame({
        "symbole": ["AAA", "AAA"],
        "news_date": pd.to_datetime(["2025-01-08", "2025-01-11"]),
        "headline": ["Résultats annuels", "Augmentation de capital"],
    })
    match = find_nearby_news(news, "AAA", pd.Timestamp("2025-01-10"), 7)
    assert match["news_date"] == pd.Timestamp("2025-01-11")
    assert classify_headline(match["headline"]) == "capital_increase"


def test_classification_uses_neutral_match_labels_and_point_in_time_fields():
    anomalies = pd.DataFrame({
        "symbole": ["AAA", "BBB"], "date": ["2025-01-10", "2025-01-10"],
        "combined_anomaly": [True, True],
    })
    news = pd.DataFrame({
        "symbole": ["AAA"], "news_date": pd.to_datetime(["2025-01-11"]),
        "headline": ["Résultats annuels"],
    })
    result = classify_anomalies(anomalies, news).set_index("symbole")
    assert result.loc["AAA", "status"] == NEWS_MATCH_FOUND
    assert not bool(result.loc["AAA", "news_available_as_of_flag"])
    assert bool(result.loc["AAA", "post_event_news_context"])
    assert result.loc["AAA", "news_match_timing"] == "POST_EVENT_CONTEXT"
    assert result.loc["BBB", "status"] == NO_LOCAL_MATCH
    assert result.loc["BBB", "news_match_timing"] == "NO_LOCAL_MATCH"


def test_news_on_or_before_flag_is_available_as_of_flag():
    anomalies = pd.DataFrame({
        "symbole": ["AAA", "AAA"],
        "date": ["2025-01-10", "2025-01-11"],
        "combined_anomaly": [True, True],
    })
    news = pd.DataFrame({
        "symbole": ["AAA"],
        "news_date": pd.to_datetime(["2025-01-10"]),
        "headline": ["Résultats annuels"],
    })
    result = classify_anomalies(anomalies, news)
    assert result["news_available_as_of_flag"].tolist() == [True, True]
    assert result["post_event_news_context"].tolist() == [False, False]
    assert result["gap_days"].tolist() == [0, -1]


def test_later_headline_never_hides_available_as_of_context():
    anomalies = pd.DataFrame({
        "symbole": ["AAA"], "date": ["2025-01-10"], "combined_anomaly": [True],
    })
    news = pd.DataFrame({
        "symbole": ["AAA", "AAA"],
        "news_date": pd.to_datetime(["2025-01-07", "2025-01-11"]),
        "headline": ["Earlier disclosure", "Later follow-up"],
    })

    row = classify_anomalies(anomalies, news).iloc[0]

    assert row["matched_headline"] == "Earlier disclosure"
    assert row["as_of_headline"] == "Earlier disclosure"
    assert row["as_of_gap_days"] == -3
    assert row["later_headline"] == "Later follow-up"
    assert row["later_gap_days"] == 1
    assert bool(row["news_available_as_of_flag"])
    assert bool(row["post_event_news_context"])
    assert row["news_match_timing"] == "AS_OF_AND_POST_EVENT_CONTEXT"


def test_cross_reference_window_is_inclusive():
    flags = pd.DataFrame({
        "symbole": ["AAA", "AAA"],
        "date": pd.to_datetime(["2025-01-05", "2025-01-04"]),
    })
    matched = check_matches(flags, "AAA", "2025-01-10", "fixture")
    assert matched["date"].tolist() == [pd.Timestamp("2025-01-05")]
