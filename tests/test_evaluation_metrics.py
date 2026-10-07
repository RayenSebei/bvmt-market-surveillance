import pandas as pd

from src.evaluation.evaluate import event_hits, precision_at_k


def test_event_metrics_have_known_answers():
    events = pd.DataFrame({
        "event_id": ["A", "B"], "ticker": ["AAA", "BBB"],
        "event_date": pd.to_datetime(["2025-02-01", "2025-02-01"]),
    })
    flags = pd.DataFrame({
        "symbole": ["AAA", "CCC", "BBB"],
        "date": pd.to_datetime(["2025-01-20", "2025-01-25", "2024-11-01"]),
        "volume_zscore": [5.0, 4.0, 3.0], "return_zscore": [0.0, 0.0, 0.0],
    })
    hits = event_hits(flags, events, before=30, after=5)
    assert hits["hit"].tolist() == [True, False]
    assert hits.loc[0, "lead_time_days"] == 12
    precision = precision_at_k(flags, events, before=30, after=5, values=[2])
    assert precision.loc[0, "known_event_nearby_flags"] == 1
    assert precision.loc[0, "precision_at_k"] == 0.5
