from __future__ import annotations

import pandas as pd

from src.detection.candidates_v2 import CandidateSettings, candidate_flags, score_trading
from src.evaluation.evaluate import wilson_interval
from src.evaluation.phase2 import paired_bootstrap
from src.validation.phase2_quality import review_scrape_rows


def test_scores_use_only_prior_history_and_exact_market_date():
    dates = pd.date_range("2024-01-01", periods=70, freq="D")
    base = pd.DataFrame({"symbole": "ABC", "date": dates, "cloture": [10.0] * 70, "volume": [500] * 70})
    index = pd.DataFrame({"symbole": "PX1", "date": dates[::2], "cloture": [100.0] * 35, "volume": [1000] * 35})
    data = pd.concat([base, index], ignore_index=True)
    settings = CandidateSettings(window=5)
    first = score_trading(data, settings)
    changed = data.copy()
    changed.loc[(changed.symbole == "ABC") & (changed.date == dates[-1]), "volume"] = 100000
    second = score_trading(changed, settings)
    earlier = first.date < dates[-1]
    pd.testing.assert_series_equal(first.loc[earlier, "robust_volume_z"], second.loc[earlier, "robust_volume_z"])
    assert pd.isna(first.loc[first.date.eq(dates[69]), "market_return"]).all()
    assert second.loc[second.date.eq(dates[-1]), "robust_volume_z"].iloc[0] > 3


def test_reference_filter_never_mutates_reference_rows():
    dates = pd.date_range("2024-01-01", periods=70, freq="D")
    trading = pd.DataFrame({"symbole": "ABC", "date": dates, "cloture": [10.0] * 70, "volume": [0] * 69 + [1000]})
    reference = trading.tail(1).copy()
    reference["volume_anomaly"] = True
    reference["price_anomaly"] = False
    original = reference.copy(deep=True)
    result = candidate_flags(trading, reference, CandidateSettings(window=5))
    assert result["activity_filtered_v1"].empty
    pd.testing.assert_frame_equal(reference, original)


def test_wilson_and_paired_interval_small_set():
    low, high = wilson_interval(1, 3)
    assert 0 < low < 1 / 3 < high < 1
    assert paired_bootstrap({"a"}, set(), ["a"]) == (1.0, 1.0)


def test_scrape_review_keeps_every_row_flagged():
    rows = pd.DataFrame({"ohlc_issue": [None, "CLOSE_ABOVE_HIGH", None], "zero_volume": [True, False, False], "abs_return_gt_15pct": [False, False, True]})
    reviewed = review_scrape_rows(rows)
    assert reviewed.review_class.tolist() == ["ZERO_VOLUME_OBSERVATION", "OHLC_INCONSISTENCY", "LARGE_CLOSE_JUMP"]
    assert set(reviewed.review_status) == {"flagged_for_review"}
