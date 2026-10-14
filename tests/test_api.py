import os
from pathlib import Path

import pandas as pd
import pytest

import app as dashboard


@pytest.fixture
def client(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures" / "api_data"
    monkeypatch.setattr(dashboard, "DATA_DIR", fixture_dir)
    monkeypatch.setattr(dashboard, "EVALUATION_DIR", Path(__file__).parent / "fixtures" / "evaluation")
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_ENABLED", False)
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_NETWORK_SCRAPE_ENABLED", False)
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_TOKEN", "")
    dashboard.scrape_state.update({"running": False, "last_run": None, "last_status": "never", "log": []})
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
    monkeypatch.setattr(dashboard.threading, "Thread", DummyThread)
    dashboard.app.config.update(TESTING=True)
    return dashboard.app.test_client()


@pytest.mark.parametrize("method,path", [
    ("get", "/"),
    ("get", "/api/status"),
    ("get", "/api/kpis"),
    ("get", "/api/anomalies"), ("get", "/api/anomalies/timeline"),
    ("get", "/api/anomalies/search"), ("get", "/api/anomaly/AAA/2025-01-02"),
    ("get", "/api/news/recent"), ("get", "/api/news/by_ticker?ticker=AAA"),
    ("get", "/api/stock/AAA"), ("get", "/api/tickers"),
    ("get", "/api/summary"), ("get", "/api/news/categories"),
    ("get", "/api/watchlist"), ("get", "/api/overview"),
    ("get", "/api/overview/calendar"), ("get", "/api/overview/radar"),
    ("get", "/api/playground"), ("get", "/api/case-studies"),
    ("get", "/api/evaluation/metrics"), ("get", "/api/evaluation/baselines"),
    ("get", "/api/evaluation/sensitivity"), ("get", "/api/evaluation/events"),
])
def test_every_endpoint_smoke(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 200


def test_terminal_route_and_read_only_api_smoke(client):
    page = client.get("/terminal")
    data = client.get("/api/command-center?days=30")

    assert (dashboard.FRONTEND_DIR / "package.json").is_file()
    assert page.status_code in {200, 503}
    if page.status_code == 503:
        assert "Terminal build unavailable" in page.get_json()["error"]
    assert data.status_code == 200
    assert data.get_json()["metrics"]["flags"] == 1


def test_tickers_merge_combined_and_individual_files(client):
    response = client.get("/api/tickers")
    assert response.status_code == 200
    tickers = {row["symbole"]: row["name"] for row in response.get_json()}
    assert tickers == {
        "AAA": "Alpha",
        "BIAT": "BIAT",
        "BNA": "BANQUE NATIONALE AGRICOLE",
    }


def test_csv_cache_reloads_after_file_mtime_changes(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures" / "cache_tmp"
    fixture_dir.mkdir(exist_ok=True)
    path = fixture_dir / "sample.csv"
    monkeypatch.setattr(dashboard, "DATA_DIR", fixture_dir)
    try:
        pd.DataFrame({"value": [1]}).to_csv(path, index=False)
        first = dashboard.load_csv("sample.csv")
        first.loc[0, "value"] = 99
        assert dashboard.load_csv("sample.csv").loc[0, "value"] == 1

        prior_mtime = path.stat().st_mtime_ns
        pd.DataFrame({"value": [2]}).to_csv(path, index=False)
        os.utime(path, ns=(prior_mtime + 1_000_000_000, prior_mtime + 1_000_000_000))

        assert dashboard.load_csv("sample.csv").loc[0, "value"] == 2
    finally:
        path.unlink(missing_ok=True)
        fixture_dir.rmdir()


def test_identical_requests_return_identical_json(client):
    first = client.get("/api/overview")
    second = client.get("/api/overview")

    assert first.status_code == second.status_code == 200
    assert first.get_json() == second.get_json()


def test_pipeline_execution_is_disabled_by_default(client):
    response = client.post("/api/scrape", json={"mode": "analysis"})
    assert response.status_code == 404
    assert client.get("/api/scrape/status").status_code == 404


def test_pipeline_status_log_requires_bearer_token(client, monkeypatch):
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_ENABLED", True)
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_TOKEN", "test-secret")
    dashboard.scrape_state["log"] = ["sensitive pipeline detail"]

    assert client.get("/api/scrape/status").status_code == 401
    response = client.get(
        "/api/scrape/status", headers={"Authorization": "Bearer test-secret"}
    )
    assert response.status_code == 200
    assert response.get_json()["log"] == ["sensitive pipeline detail"]


def test_pipeline_execution_requires_token_and_explicit_mode(client, monkeypatch):
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_ENABLED", True)
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_TOKEN", "test-secret")
    assert client.post("/api/scrape", json={"mode": "analysis"}).status_code == 401
    headers = {"Authorization": "Bearer test-secret"}
    assert client.post("/api/scrape", headers=headers, json={}).status_code == 400
    response = client.post("/api/scrape", headers=headers, json={"mode": "analysis"})
    assert response.status_code == 202


def test_network_scrape_needs_separate_opt_in(client, monkeypatch):
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_ENABLED", True)
    monkeypatch.setitem(dashboard.app.config, "PIPELINE_API_TOKEN", "test-secret")
    response = client.post(
        "/api/scrape",
        headers={"Authorization": "Bearer test-secret"},
        json={"mode": "scrape"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("path", ["/api/stock/BAD!", "/api/anomaly/BAD!/2025-01-02"])
def test_ticker_path_validation_rejects_invalid_symbols(client, path):
    assert client.get(path).status_code == 400


def test_news_query_validation_and_url_safety(client):
    assert client.get("/api/news/by_ticker?ticker=BAD!").status_code == 400
    assert dashboard.safe_http_url("javascript:alert(1)") == ""
    assert dashboard.safe_http_url("https://example.test/news") == "https://example.test/news"


def test_kpi_timestamps_do_not_fabricate_pipeline_run(client):
    payload = client.get("/api/kpis").get_json()
    assert payload["pipeline_last_run_at"] is None
    assert payload["last_scrape"] is None
    assert payload["data_as_of"] == "2025-01-02"
    assert payload["dashboard_checked_at"]


def test_stale_ai_watchlist_is_not_used(monkeypatch):
    refined = pd.DataFrame({
        "symbole": ["AAA"], "date": ["2025-01-01"], "source": ["spike_detector"],
        "status": ["NO_LOCAL_MATCH"], "volume_zscore": [4.0],
    })
    assessed = refined.copy()
    assessed["date"] = "2024-12-31"
    assessed["ai_assessment"] = "worth_investigating"

    def fake_load(name, **_kwargs):
        return assessed.copy() if name == "watchlist_ai_assessed.csv" else refined.copy()

    monkeypatch.setattr(dashboard, "load_csv", fake_load)
    current, fresh = dashboard.load_current_watchlist()
    assert fresh is False
    assert current.equals(refined)


def test_matching_ai_watchlist_is_used(monkeypatch):
    refined = pd.DataFrame({
        "symbole": ["AAA"], "date": ["2025-01-01"], "source": ["spike_detector"],
        "status": ["NO_LOCAL_MATCH"], "volume_zscore": [4.0],
    })
    assessed = refined.copy()
    assessed["ai_assessment"] = "uncertain"

    def fake_load(name, **_kwargs):
        return assessed.copy() if name == "watchlist_ai_assessed.csv" else refined.copy()

    monkeypatch.setattr(dashboard, "load_csv", fake_load)
    current, fresh = dashboard.load_current_watchlist()
    assert fresh is True
    assert current.iloc[0]["ai_assessment"] == "uncertain"


def test_watchlist_explained_scope_returns_only_news_matches(client, monkeypatch):
    classified = pd.DataFrame({
        "symbole": ["AAA", "BBB"],
        "ticker_name": ["Alpha", "Beta"],
        "date": ["2025-01-02", "2025-01-03"],
        "status": ["NEWS_MATCH_FOUND", "NO_LOCAL_MATCH"],
        "volume_zscore": [4.2, 3.5],
        "return_zscore": [1.0, 4.1],
        "volume_anomaly": [True, False],
        "price_anomaly": [False, True],
        "matched_headline": ["Alpha update", ""],
        "matched_news_date": ["2025-01-02", ""],
        "gap_days": [0, None],
        "category": ["company_update", ""],
    })

    original_load = dashboard.load_csv

    def fake_load(name, **kwargs):
        if name == "anomaly_classified.csv":
            return classified.copy()
        return original_load(name, **kwargs)

    monkeypatch.setattr(dashboard, "load_csv", fake_load)
    response = client.get("/api/watchlist?scope=explained")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["scope"] == "explained"
    assert payload["total"] == 1
    assert payload["rows"][0]["symbole"] == "AAA"
    assert payload["rows"][0]["news_nearby"] is True
    assert client.get("/api/watchlist?scope=invalid").status_code == 400


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
    assert payload["rows"][0]["signal_intensity"] == "High"


def test_stock_range_is_optional_and_flag_details_are_additive(client):
    default = client.get("/api/stock/AAA").get_json()
    all_rows = client.get("/api/stock/AAA?range=ALL").get_json()
    assert default == all_rows
    assert all_rows[1]["flag"]["signal"] == "Volume + Price"
    assert "volume_zscore" in all_rows[1]
    assert "return_zscore" in all_rows[1]


def test_calendar_and_radar_endpoints_use_real_flag_rows(client):
    calendar = client.get("/api/overview/calendar").get_json()
    radar = client.get("/api/overview/radar").get_json()
    assert sum(day["count"] for day in calendar) == len(radar)
    assert {"volume_zscore", "return_zscore", "news_status"} <= set(radar[0])


def test_playground_is_read_only_generated_grid(client):
    payload = client.get("/api/playground?z=3&window=60").get_json()
    assert payload["flag_count"] == 10
    assert payload["exploratory"] is True
    assert payload["changes_reference_detector"] is False
    assert client.get("/api/playground?z=2.7&window=60").status_code == 400


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


@pytest.mark.parametrize("query", [
    "date_from=not-a-date",
    "date_from=2025-02-01&date_to=2025-01-01",
    "min_z=-1",
    "min_z=not-a-number",
    "sort=unknown",
    "status=explained",
    "signal=combined",
    "intensity=critical",
    "page=one",
])
def test_anomaly_search_rejects_invalid_query_values(client, query):
    response = client.get(f"/api/anomalies/search?{query}")
    assert response.status_code == 400
    assert response.get_json()["error"]
