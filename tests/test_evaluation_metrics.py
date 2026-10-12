import pandas as pd

from src.evaluation.evaluate import event_hits, precision_at_k, ranked_flags
from src.evaluation.report import count_text, ratio_text
from src.evaluation.sensitivity import parameter_flags


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


def test_evaluation_counts_are_reported_with_denominators():
    assert ratio_text(0.5, 2) == "1 of 2 events"
    assert ratio_text(0.1815, 2) == "0.363 of 2 events on average"
    assert count_text(0.0, 20, "flags") == "0 of 20 flags"


def test_ranking_score_ties_and_illiquidity_are_deterministic():
    flags = pd.DataFrame({
        "symbole": ["BBB", "AAA", "CCC"],
        "date": pd.to_datetime(["2025-01-02", "2025-01-01", "2025-01-03"]),
        "volume_zscore": [4.0, -4.0, 3.0],
        "return_zscore": [1.0, 2.0, -5.0],
    })
    trading = pd.DataFrame({
        "symbole": ["AAA", "AAA", "BBB", "BBB", "CCC", "CCC"],
        "volume": [10, 20, 100, 200, 1000, 2000],
    })
    ranked = ranked_flags(flags, trading)
    assert ranked["symbole"].tolist() == ["CCC", "AAA", "BBB"]
    assert ranked["screening_score"].tolist() == [5.0, 4.0, 4.0]
    assert ranked.set_index("symbole")["illiquid"].to_dict() == {
        "AAA": True, "BBB": False, "CCC": False,
    }


def test_sensitivity_window_requires_its_full_prior_history():
    def trading(volumes):
        return pd.DataFrame({
            "symbole": ["AAA"] * len(volumes),
            "date": pd.date_range("2025-01-01", periods=len(volumes)),
            "cloture": [10.0] * len(volumes),
            "volume": volumes,
        })

    before_sixty = parameter_flags(trading([100] * 59 + [100_000]), 60, 3.0)
    after_sixty = parameter_flags(trading([100] * 60 + [100_000]), 60, 3.0)
    assert before_sixty.empty
    assert len(after_sixty) == 1


def test_sensitivity_return_window_uses_valid_returns_across_gap():
    dates = list(pd.date_range("2025-01-01", periods=35, freq="D"))
    dates += list(pd.date_range("2025-03-01", periods=36, freq="D"))
    closes = [10.0]
    for _ in range(len(dates) - 2):
        closes.append(closes[-1] * 1.001)
    closes.append(closes[-1] * 1.5)
    trading = pd.DataFrame({
        "symbole": ["AAA"] * len(dates),
        "date": dates,
        "cloture": closes,
        "volume": [100] * len(dates),
    })

    flags = parameter_flags(trading, window=60, cutoff=3.0)

    assert flags["date"].tolist() == [dates[-1]]
