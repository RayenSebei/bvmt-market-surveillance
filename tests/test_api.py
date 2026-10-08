from pathlib import Path

import pandas as pd
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
    ("get", "/api/anomalies/search"), ("get", "/api/anomaly/AAA/2025-01-02"),
    ("get", "/api/news/recent"), ("get", "/api/news/by_ticker?ticker=AAA"),
    ("get", "/api/stock/AAA"), ("get", "/api/tickers"),
    ("get", "/api/summary"), ("get", "/api/news/categories"),
    ("get", "/api/watchlist"), ("get", "/api/overview"),
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


def test_anomaly_search_filters_and_paginates(client):
    response = client.get("/api/anomalies/search?status=none&min_z=4&page_size=1")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 1
    assert payload["page_size"] == 1
    assert payload["rows"][0]["news_status"] == "No local news match"


def test_stock_range_is_optional_and_flag_details_are_additive(client):
    default = client.get("/api/stock/AAA").get_json()
    all_rows = client.get("/api/stock/AAA?range=ALL").get_json()
    assert default == all_rows
    assert all_rows[1]["flag"]["signal"] == "Volume + Price"


def test_recent_news_optional_limit_and_ticker(client):
    rows = client.get("/api/news/recent?limit=1&ticker=AAA").get_json()
    assert len(rows) == 1
    assert rows[0]["symbole"] == "AAA"
    assert "linked_flag_date" in rows[0]


def test_anomaly_detail_returns_window_news_and_prices(client):
    payload = client.get("/api/anomaly/AAA/2025-01-02").get_json()
    assert payload["flag"]["symbole"] == "AAA"
    assert payload["prices"][-1]["date"] == "2025-01-02"
    assert payload["news"][0]["headline"] == "Alpha results"


def test_anomaly_record_distinguishes_post_event_context():
    row = pd.Series({
        "symbole": "AAA",
        "date": "2025-01-10",
        "status": "NEWS_MATCH_FOUND",
        "matched_news_date": "2025-01-11",
        "matched_headline": "Later context",
        "gap_days": 1,
        "news_available_as_of_flag": False,
        "post_event_news_context": True,
    })
    record = dashboard.anomaly_record(row)
    assert record["news_status"] == "Post-event news context"
    assert record["news_available_as_of_flag"] is False
    assert record["post_event_news_context"] is True
