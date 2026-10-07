from pathlib import Path

import pytest

import app as dashboard


@pytest.fixture
def client(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures" / "api_data"
    monkeypatch.setattr(dashboard, "DATA_DIR", fixture_dir)
    monkeypatch.setattr(dashboard, "EVALUATION_DIR", Path(__file__).parent / "fixtures" / "evaluation")
    dashboard.scrape_state.update({"running": False, "last_run": None, "last_status": "never", "log": []})
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
    monkeypatch.setattr(dashboard.threading, "Thread", DummyThread)
    dashboard.app.config.update(TESTING=True)
    return dashboard.app.test_client()


@pytest.mark.parametrize("method,path", [
    ("get", "/"), ("get", "/wallstreet"), ("get", "/v2"),
    ("get", "/api/status"), ("post", "/api/scrape"),
    ("get", "/api/scrape/status"), ("get", "/api/kpis"),
    ("get", "/api/anomalies"), ("get", "/api/anomalies/timeline"),
    ("get", "/api/news/recent"), ("get", "/api/news/by_ticker?ticker=AAA"),
    ("get", "/api/stock/AAA"), ("get", "/api/tickers"),
    ("get", "/api/summary"), ("get", "/api/news/categories"),
    ("get", "/api/evaluation/metrics"), ("get", "/api/evaluation/baselines"),
    ("get", "/api/evaluation/sensitivity"), ("get", "/api/evaluation/events"),
])
def test_every_endpoint_smoke(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 200


def test_tickers_merge_combined_and_individual_files(client):
    response = client.get("/api/tickers")
    assert response.status_code == 200
    tickers = {row["symbole"]: row["name"] for row in response.get_json()}
    assert tickers == {
        "AAA": "Alpha",
        "BIAT": "BIAT",
        "BNA": "BANQUE NATIONALE AGRICOLE",
    }


@pytest.mark.parametrize("ticker", ["BIAT", "BNA"])
def test_stock_endpoint_reads_individual_ticker_files(client, ticker):
    response = client.get(f"/api/stock/{ticker}")
    assert response.status_code == 200
    assert response.get_json()[0]["date"] == "2025-01-01"
