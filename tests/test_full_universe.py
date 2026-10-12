import pandas as pd
import pytest

from src.detection.anomaly_detector import ohlc_quality_issues
from src.evaluation.full_universe import EXPECTED_COLUMNS, validate_frame


def sample_frame(symbol="AAA", rows=60):
    return pd.DataFrame({
        "ticker_name": ["Example"] * rows,
        "symbole": [symbol] * rows,
        "date": pd.date_range("2024-01-01", periods=rows),
        "ouverture": [10.0] * rows,
        "haut": [10.5] * rows,
        "bas": [9.5] * rows,
        "cloture": [10.0] * rows,
        "volume": [100] * rows,
    })[EXPECTED_COLUMNS]


def test_valid_individual_ticker_frame():
    assert validate_frame(sample_frame(), "AAA") == []


def test_individual_ticker_validation_finds_mismatch_and_duplicate():
    frame = sample_frame(symbol="BBB")
    frame.loc[1, "date"] = frame.loc[0, "date"]
    assert validate_frame(frame, "AAA") == [
        "symbol does not match filename",
        "duplicate date",
    ]


def test_ohlc_issue_log_preserves_provenance():
    frame = sample_frame()
    frame.loc[3, "cloture"] = 11.2
    issues = ohlc_quality_issues(frame)
    assert issues[["symbole", "date", "cloture", "haut"]].iloc[0].to_dict() == {
        "symbole": "AAA",
        "date": pd.Timestamp("2024-01-04"),
        "cloture": 11.2,
        "haut": 10.5,
    }
    assert issues.iloc[0]["close_departure"] == pytest.approx(0.7)
