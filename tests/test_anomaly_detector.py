import numpy as np
import pandas as pd

from src.detection.anomaly_detector import compute_signals


def series(volumes, closes=None, dates=None):
    size = len(volumes)
    closes = np.ones(size) * 10 if closes is None else np.asarray(closes, dtype=float)
    dates = pd.date_range("2025-01-01", periods=size, freq="D") if dates is None else dates
    return pd.DataFrame({
        "symbole": "TEST", "ticker_name": "Test Company", "date": dates,
        "cloture": closes, "bas": closes, "haut": closes, "volume": volumes,
    })


def test_volume_spike_is_flagged():
    result = compute_signals(series([100] * 79 + [100_000]))
    assert bool(result.iloc[-1]["volume_anomaly"])


def test_flat_series_is_not_flagged():
    result = compute_signals(series([100] * 80))
    assert not result["volume_anomaly"].any()
    assert not result["price_anomaly"].any()


def test_standard_deviation_floor_limits_score():
    result = compute_signals(series([100] * 79 + [200]))
    expected = (np.log1p(200) - np.log1p(100)) / 0.10
    assert result.iloc[-1]["volume_zscore"] == pytest.approx(expected)


def test_gap_day_return_is_excluded():
    dates = list(pd.date_range("2025-01-01", periods=79, freq="D")) + [pd.Timestamp("2025-04-15")]
    closes = [10] * 79 + [20]
    result = compute_signals(series([100] * 80, closes=closes, dates=dates))
    assert pd.isna(result.iloc[-1]["daily_return"])
    assert not bool(result.iloc[-1]["price_anomaly"])


def test_future_row_does_not_change_prior_score():
    base = series([100] * 79 + [500])
    extended = pd.concat([
        base,
        series([1_000_000], closes=[10], dates=[pd.Timestamp("2025-03-22")]),
    ], ignore_index=True)
    before = compute_signals(base).iloc[-1]
    after = compute_signals(extended).iloc[-2]
    assert after["volume_zscore"] == pytest.approx(before["volume_zscore"])


import pytest
