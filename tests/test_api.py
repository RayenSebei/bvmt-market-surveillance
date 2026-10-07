from pathlib import Path

import pytest

import app as dashboard


@pytest.fixture
def client(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures" / "api_data"
    monkeypatch.setattr(dashboard, "DATA_DIR", fixture_dir)
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
])
def test_every_endpoint_smoke(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 200
