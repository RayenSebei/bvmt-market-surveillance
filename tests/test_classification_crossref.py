import pandas as pd

from src.detection.crossref_legal_events import check_matches
from src.validation.classify_anomalies import (
    classify_anomalies, classify_headline, find_nearby_news,
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


def test_classification_marks_explained_and_unexplained():
    anomalies = pd.DataFrame({
        "symbole": ["AAA", "BBB"], "date": ["2025-01-10", "2025-01-10"],
        "combined_anomaly": [True, True],
    })
    news = pd.DataFrame({
        "symbole": ["AAA"], "news_date": pd.to_datetime(["2025-01-11"]),
        "headline": ["Résultats annuels"],
    })
    result = classify_anomalies(anomalies, news).set_index("symbole")
    assert result.loc["AAA", "status"] == "EXPLAINED"
    assert result.loc["BBB", "status"] == "UNEXPLAINED"


def test_cross_reference_window_is_inclusive():
    flags = pd.DataFrame({
        "symbole": ["AAA", "AAA"],
        "date": pd.to_datetime(["2025-01-05", "2025-01-04"]),
    })
    matched = check_matches(flags, "AAA", "2025-01-10", "fixture")
    assert matched["date"].tolist() == [pd.Timestamp("2025-01-05")]
