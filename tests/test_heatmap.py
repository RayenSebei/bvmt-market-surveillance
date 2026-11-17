import pandas as pd

from src.heatmap import build_heatmap


def test_heatmap_uses_stored_sessions_and_marks_nontraders():
    dates = pd.date_range("2025-12-20", periods=24, freq="B")
    prices = pd.DataFrame(
        [
            {"symbole": "AAA", "ticker_name": "Alpha", "date": d, "cloture": 10 + i, "volume": 100}
            for i, d in enumerate(dates)
        ]
        + [
            {"symbole": "BBB", "ticker_name": "Beta", "date": d, "cloture": 5, "volume": 50}
            for d in dates[:-1]
        ]
    )
    flags = pd.DataFrame([
        {"symbole": "AAA", "date": dates[-2], "volume_anomaly": True, "price_anomaly": False,
         "volume_zscore": 4.5, "return_zscore": -1.0},
    ])
    for tf in ("1D", "1W", "1M", "YTD"):
        response = build_heatmap(prices, flags, tf)
        assert response["as_of"] == dates[-1].strftime("%Y-%m-%d")
        alpha, beta = response["symbols"]
        assert alpha["flags_30d"] == 1
        assert alpha["max_abs_z_30d"] == 4.5
        assert alpha["avg_traded_value_20d"] == sum((10 + i) * 100 for i in range(4, 24)) / 20
        assert beta["traded_on_asof"] is False
        assert beta["change_pct"] is None
        assert beta["last_date"] == dates[-2].strftime("%Y-%m-%d")
        assert alpha["change_pct"] is not None
