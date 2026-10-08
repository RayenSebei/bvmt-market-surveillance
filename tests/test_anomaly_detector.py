import numpy as np
import pandas as pd
import pytest

from src.detection.anomaly_detector import apply_ohlc_policy, compute_signals


def series(volumes, closes=None, dates=None):
    size = len(volumes)
    closes = np.ones(size) * 10 if closes is None else np.asarray(closes, dtype=float)
    dates = pd.date_range("2025-01-01", periods=size, freq="D") if dates is None else dates
    return pd.DataFrame({
        "symbole": "TEST", "ticker_name": "Test Company", "date": dates,
        "ouverture": closes, "cloture": closes, "bas": closes,
        "haut": closes, "volume": volumes,
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


@pytest.mark.parametrize("prior_observations", [20, 59])
def test_volume_signal_requires_sixty_prior_observations(prior_observations):
    result = compute_signals(series([100] * prior_observations + [100_000]))
    if result.empty:
        return
    assert pd.isna(result.iloc[-1]["volume_zscore"])
    assert not bool(result.iloc[-1]["volume_anomaly"])


def test_volume_signal_starts_after_sixty_prior_observations():
    result = compute_signals(series([100] * 60 + [100_000]))
    assert pd.notna(result.iloc[-1]["volume_zscore"])
    assert bool(result.iloc[-1]["volume_anomaly"])


def test_return_signal_requires_sixty_valid_prior_returns():
    closes = [10.0]
    for _ in range(60):
        closes.append(closes[-1] * 1.001)
    closes.append(closes[-1] * 1.50)
    result = compute_signals(series([100] * len(closes), closes=closes))
    assert pd.isna(result.iloc[-2]["return_zscore"])
    assert pd.notna(result.iloc[-1]["return_zscore"])
    assert bool(result.iloc[-1]["price_anomaly"])


def test_gap_delays_return_baseline_until_sixty_valid_returns():
    dates = list(pd.date_range("2025-01-01", periods=31, freq="D"))
    dates += list(pd.date_range("2025-03-01", periods=31, freq="D"))
    closes = np.linspace(10, 11, len(dates))
    result = compute_signals(series([100] * len(dates), closes=closes, dates=dates))
    assert pd.isna(result.iloc[-1]["return_zscore"])


def test_default_raw_ohlc_policy_is_transparent_and_non_mutating():
    frame = series([100] * 60)
    frame.loc[0, ["bas", "haut", "cloture"]] = [9.0, 10.0, 10.5]
    processed, issues = apply_ohlc_policy(frame)
    assert processed.loc[0, "cloture"] == 10.5
    assert issues.loc[0, "issue_types"] == "CLOSE_ABOVE_HIGH"
    assert issues.loc[0, "action"] == "retained_raw"


def test_legacy_clamp_and_quarantine_policies_are_explicit():
    frame = series([100] * 60)
    frame.loc[0, ["bas", "haut", "cloture"]] = [9.0, 10.0, 10.5]
    clamped, clamp_log = apply_ohlc_policy(frame, "clamp_close")
    quarantined, quarantine_log = apply_ohlc_policy(frame, "quarantine")
    assert clamped.loc[0, "cloture"] == 10.0
    assert clamp_log.loc[0, "action"] == "close_clamped_where_range_valid"
    assert len(quarantined) == len(frame) - 1
    assert quarantine_log.loc[0, "action"] == "excluded_from_analysis"
