from pathlib import Path

import pytest

import app as dashboard


@pytest.mark.parametrize("ticker", ["BH", "BIAT", "BNA", "ATB", "GIF"])
def test_every_stock_flag_has_a_detail_route(ticker, monkeypatch):
    """Every marker returned by Stock Search must open a JSON detail payload."""
    monkeypatch.setattr(dashboard, "DATA_DIR", Path(dashboard.__file__).parent / "bvmt_data")
    dashboard.app.config.update(TESTING=True)
    client = dashboard.app.test_client()

    stock_response = client.get(f"/api/stock/{ticker}?range=ALL")
    assert stock_response.status_code == 200
    assert stock_response.is_json
    flagged_rows = [row for row in stock_response.get_json() if row.get("anomaly")]
    assert flagged_rows, f"Expected at least one stored flag for {ticker}"

    for row in flagged_rows:
        detail_response = client.get(f"/api/anomaly/{ticker}/{row['date']}")
        assert detail_response.status_code == 200, (
            f"Flag marker {ticker} {row['date']} has no detail route"
        )
        assert detail_response.is_json
        assert detail_response.get_json()["flag"]["date"] == row["date"]
