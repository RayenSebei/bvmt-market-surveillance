"""
BVMT Market Surveillance Dashboard - Backend API
Reads real CSV data from your bvmt_data folder.
No fake data. All endpoints serve real scraped files.
"""

import os
import hmac
import math
import re
import sys
import threading
import subprocess
from functools import lru_cache
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider
from src.evaluation.provenance import MANIFEST_PATH, verify_manifest
from src.detection.anomaly_detector import compute_signals


class NaNSafeJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that converts NaN/Inf floats to None (JSON null)."""
    def default(self, o):
        if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
            return None
        return super().default(o)

    def dumps(self, obj, **kwargs):
        return super().dumps(obj, **kwargs)


def safe_val(v, fallback=None):
    """Return fallback if v is NaN/None/NaT, else v."""
    try:
        if v is None:
            return fallback
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return fallback
        if pd.isna(v):
            return fallback
    except (TypeError, ValueError):
        pass
    return v

app = Flask(__name__)
app.json_provider_class = NaNSafeJSONProvider
app.json = NaNSafeJSONProvider(app)


def env_true(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


cors_origins = [
    origin.strip() for origin in os.environ.get("BVMT_CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

# ── DATA DIRECTORY ──────────────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("DATA_DIR", "./bvmt_data"))
EVALUATION_DIR = Path(os.environ.get("EVALUATION_DIR", "./outputs/evaluation"))
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
TICKER_FILE_PATTERN = re.compile(r"^[A-Z0-9]+$")
NEWS_MATCH_STATUSES = {"NEWS_MATCH_FOUND", "EXPLAINED"}
NO_MATCH_STATUSES = {"NO_LOCAL_MATCH", "UNEXPLAINED"}
WATCHLIST_FRESHNESS_COLUMNS = (
    "symbole", "date", "source", "priority", "status", "volume_zscore",
    "return_zscore", "combined_anomaly", "matched_news_date", "matched_headline",
)

# ── SCRAPER SCRIPT PATH ──────────────────────────────────────────────────────
# Point this to your existing scraper/pipeline entry point
SCRAPER_SCRIPT = os.environ.get("SCRAPER_SCRIPT", "./scraper/run_pipeline.py")
app.config.update(
    PIPELINE_API_ENABLED=env_true("BVMT_ENABLE_PIPELINE_API"),
    PIPELINE_NETWORK_SCRAPE_ENABLED=env_true("BVMT_ENABLE_NETWORK_SCRAPE"),
    PIPELINE_API_TOKEN=os.environ.get("BVMT_PIPELINE_API_TOKEN", ""),
    CACHE_WARMUP_ENABLED=env_true("BVMT_WARM_CACHE", True),
)

# ── SCRAPE STATE ─────────────────────────────────────────────────────────────
scrape_state = {
    "running": False,
    "last_run": None,
    "last_status": "never",
    "log": []
}
scrape_lock = threading.Lock()
cache_lock = threading.RLock()
_csv_cache = {}
_news_lookup_cache = {}
_ticker_list_cache = {}
STARTUP_DATA_CSVS = (
    "_all_tickers_full.csv",
    "_all_news_combined.csv",
    "anomaly_flags.csv",
    "anomaly_classified.csv",
    "anomaly_summary.csv",
    "watchlist_refined.csv",
    "watchlist_ai_assessed.csv",
    "decay_classified.csv",
)
STARTUP_EVALUATION_CSVS = (
    "metrics.csv",
    "baseline_comparison.csv",
    "sensitivity.csv",
    "events_table.csv",
)


def _freeze_cache_value(value):
    """Convert common pandas read options into a stable, hashable cache key."""
    if isinstance(value, dict):
        return ("dict", tuple(sorted((str(key), _freeze_cache_value(item)) for key, item in value.items())))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(_freeze_cache_value(item) for item in value))
    if isinstance(value, (set, frozenset)):
        return (type(value).__name__, tuple(sorted(_freeze_cache_value(item) for item in value)))
    if isinstance(value, Path):
        return ("path", str(value))
    try:
        hash(value)
    except TypeError:
        return ("identity", id(value))
    return ("value", value)


def _path_cache_key(path: Path, kwargs: dict) -> tuple:
    resolved = str(path.resolve())
    mtime_ns = path.stat().st_mtime_ns
    options = tuple(sorted((key, _freeze_cache_value(value)) for key, value in kwargs.items()))
    return resolved, mtime_ns, options


def _load_csv_path(path: Path, label: str, **kwargs) -> pd.DataFrame:
    if not path.exists():
        app.logger.warning(f"{label} file not found: {path}")
        return pd.DataFrame()
    try:
        key = _path_cache_key(path, kwargs)
        with cache_lock:
            cached = _csv_cache.get(key)
        if cached is None:
            loaded = pd.read_csv(path, **kwargs)
            with cache_lock:
                stale = [item for item in _csv_cache if item[0] == key[0] and item != key]
                for item in stale:
                    _csv_cache.pop(item, None)
                _csv_cache[key] = loaded
            cached = loaded
        return cached.copy()
    except Exception as exc:
        app.logger.error(f"Error reading {path}: {exc}")
        return pd.DataFrame()


def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """Load a CSV from DATA_DIR. Returns empty DataFrame on error."""
    return _load_csv_path(DATA_DIR / filename, "Data", **kwargs)


def load_evaluation_csv(filename: str) -> pd.DataFrame:
    """Load a generated evaluation table without modifying it."""
    return _load_csv_path(EVALUATION_DIR / filename, "Evaluation")


def is_true(value) -> bool:
    return str(value).strip().lower() == "true"


def safe_http_url(value) -> str:
    """Return only absolute HTTP(S) URLs suitable for an external link."""
    candidate = str(safe_val(value, "")).strip()
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return candidate


def valid_ticker(ticker: str) -> bool:
    return bool(TICKER_FILE_PATTERN.fullmatch(ticker.strip().upper()))


def watchlist_rows_match(refined: pd.DataFrame, assessed: pd.DataFrame) -> bool:
    """Return whether an AI-assessed copy was derived from the current queue."""
    if refined.empty or assessed.empty or len(refined) != len(assessed):
        return False
    columns = [
        column for column in WATCHLIST_FRESHNESS_COLUMNS
        if column in refined.columns and column in assessed.columns
    ]
    if not {"symbole", "date"}.issubset(columns):
        return False
    sort_columns = [column for column in ("symbole", "date", "source") if column in columns]

    def normalized(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame[columns].copy()
        for column in columns:
            result[column] = result[column].fillna("").astype(str)
        return result.sort_values(sort_columns).reset_index(drop=True)

    return normalized(refined).equals(normalized(assessed))


def load_current_watchlist() -> tuple[pd.DataFrame, bool]:
    refined = load_csv("watchlist_refined.csv")
    assessed = load_csv("watchlist_ai_assessed.csv")
    if watchlist_rows_match(refined, assessed):
        return assessed, True
    return refined, False


def has_news_match(value) -> bool:
    return str(value).strip().upper() in NEWS_MATCH_STATUSES


def has_no_local_match(value) -> bool:
    return str(value).strip().upper() in NO_MATCH_STATUSES


def number(value, digits=2, integer=False):
    """Convert a CSV value to a JSON-safe number without inventing a default."""
    try:
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        parsed = float(value)
        return int(parsed) if integer else round(parsed, digits)
    except (TypeError, ValueError):
        return None


def signal_type(row) -> str:
    volume = is_true(row.get("volume_anomaly", ""))
    price = is_true(row.get("price_anomaly", ""))
    if volume and price:
        return "Volume + Price"
    if volume:
        return "Volume spike"
    if price:
        return "Price anomaly"
    return "Unknown"


def signal_intensity(z) -> str:
    if z is None:
        return "Unknown"
    if abs(float(z)) >= 4.0:
        return "High"
    if abs(float(z)) >= 2.5:
        return "Medium"
    return "Low"


def risk_level(z) -> str:
    """Deprecated compatibility alias for the non-probabilistic intensity band."""
    return signal_intensity(z)


def news_lookup():
    """Return immutable-by-convention news data and indexes cached by source mtime."""
    path = DATA_DIR / "_all_news_combined.csv"
    if not path.exists():
        return pd.DataFrame(), {}, {}
    try:
        key = (str(path.resolve()), path.stat().st_mtime_ns)
    except OSError as exc:
        app.logger.error(f"Error reading {path}: {exc}")
        return pd.DataFrame(), {}, {}
    with cache_lock:
        cached = _news_lookup_cache.get(key)
    if cached is not None:
        return cached

    news = load_csv("_all_news_combined.csv")
    if news.empty:
        return news, {}, {}
    news["parsed_date"] = pd.to_datetime(news.get("date_str"), format="%d/%m/%y", errors="coerce")
    by_headline = {}
    by_date = {}
    for _, item in news.iterrows():
        symbol = str(item.get("symbole", "")).strip().upper()
        headline = str(safe_val(item.get("headline"), "")).strip()
        date = item.get("parsed_date")
        url = safe_http_url(item.get("url"))
        if symbol and headline:
            by_headline[(symbol, headline)] = url
        if symbol and pd.notna(date) and url:
            by_date.setdefault((symbol, date.strftime("%Y-%m-%d")), url)
    result = (news, by_headline, by_date)
    with cache_lock:
        stale = [item for item in _news_lookup_cache if item[0] == key[0] and item != key]
        for item in stale:
            _news_lookup_cache.pop(item, None)
        _news_lookup_cache[key] = result
    return result


def warm_startup_caches() -> None:
    """Optionally preload frequently used read-only tables before serving requests."""
    for filename in STARTUP_DATA_CSVS:
        if (DATA_DIR / filename).is_file():
            load_csv(filename)
    for filename in STARTUP_EVALUATION_CSVS:
        if (EVALUATION_DIR / filename).is_file():
            load_evaluation_csv(filename)
    news_lookup()


def anomaly_record(row, headline_urls=None, date_urls=None):
    headline_urls = headline_urls or {}
    date_urls = date_urls or {}
    symbol = str(safe_val(row.get("symbole"), "")).strip().upper()
    date_value = pd.to_datetime(row.get("date"), errors="coerce")
    date = date_value.strftime("%Y-%m-%d") if pd.notna(date_value) else ""
    headline = str(safe_val(row.get("matched_headline"), "")).strip()
    matched_date_value = pd.to_datetime(row.get("matched_news_date"), errors="coerce")
    matched_date = matched_date_value.strftime("%Y-%m-%d") if pd.notna(matched_date_value) else ""
    max_z = max(
        abs(number(row.get("volume_zscore")) or 0),
        abs(number(row.get("return_zscore")) or 0),
    )
    status = str(safe_val(row.get("status"), "")).upper()
    nearby = has_news_match(status)
    gap_days = number(row.get("gap_days"), integer=True)
    explicit_as_of = row.get("news_available_as_of_flag")
    explicit_post = row.get("post_event_news_context")
    available_as_of = (
        is_true(explicit_as_of)
        if explicit_as_of is not None and not pd.isna(explicit_as_of)
        else nearby and gap_days is not None and gap_days <= 0
    )
    post_event = (
        is_true(explicit_post)
        if explicit_post is not None and not pd.isna(explicit_post)
        else nearby and gap_days is not None and gap_days > 0
    )
    if available_as_of:
        news_status = "News available by flag date"
    elif post_event:
        news_status = "Post-event news context"
    elif nearby:
        news_status = "News match; timing unavailable"
    else:
        news_status = "No local news match"
    return {
        "symbole": symbol,
        "ticker_name": safe_val(row.get("ticker_name"), symbol),
        "date": date,
        "cloture": number(row.get("cloture"), 3),
        "volume": number(row.get("volume"), integer=True),
        "daily_return": number(row.get("daily_return"), 6),
        "volume_zscore": number(row.get("volume_zscore")),
        "return_zscore": number(row.get("return_zscore")),
        "max_zscore": round(max_z, 2),
        "signal": signal_type(row),
        "signal_intensity": signal_intensity(max_z),
        "risk": signal_intensity(max_z),
        "status": status,
        "news_nearby": nearby,
        "news_status": news_status,
        "news_available_as_of_flag": bool(available_as_of),
        "post_event_news_context": bool(post_event),
        "news_match_timing": str(safe_val(row.get("news_match_timing"), "")).strip(),
        "matched_headline": headline,
        "matched_news_date": matched_date,
        "gap_days": gap_days,
        "category": str(safe_val(row.get("category"), "")).strip(),
        "news_url": headline_urls.get((symbol, headline), "") or date_urls.get((symbol, matched_date), ""),
    }


def run_scraper_background(mode: str):
    """Run an explicitly authorized pipeline mode in a background thread."""
    try:
        command = [sys.executable, SCRAPER_SCRIPT]
        if mode == "scrape":
            command.append("--with-scrape")
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=300
        )
        output = result.stdout.splitlines()[-20:]
        errors = [f"stderr: {line}" for line in result.stderr.splitlines()[-10:]]
        scrape_state["log"] = [f"mode={mode}", *output, *errors]
        scrape_state["last_status"] = "success" if result.returncode == 0 else "error"
    except FileNotFoundError:
        scrape_state["last_status"] = "error"
        scrape_state["log"] = ["Scraper script not found at: " + SCRAPER_SCRIPT]
    except subprocess.TimeoutExpired:
        scrape_state["last_status"] = "timeout"
        scrape_state["log"] = ["Scraper timed out after 5 minutes"]
    except Exception as e:
        scrape_state["last_status"] = "error"
        scrape_state["log"] = [str(e)]
    finally:
        with scrape_lock:
            scrape_state["running"] = False
            scrape_state["last_run"] = datetime.now().astimezone().isoformat()


# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/terminal")
def terminal():
    """Serve the optional built terminal without replacing the research dashboard."""
    dist = FRONTEND_DIR / "dist"
    if not (dist / "index.html").is_file():
        return jsonify({"error": "Terminal build unavailable; run npm ci and npm run build in frontend/"}), 503
    return send_from_directory(dist, "index.html")


@app.route("/assets/<path:filename>")
def terminal_asset(filename):
    return send_from_directory(FRONTEND_DIR / "dist" / "assets", filename)


@app.route("/favicon.svg")
def terminal_icon():
    return send_from_directory(FRONTEND_DIR / "public", "favicon.svg")


@app.route("/api/command-center")
def api_command_center():
    from src.dashboard import command_center

    days = request.args.get("days", "90")
    if days not in {"30", "90", "365"}:
        return jsonify({"error": "days must be 30, 90, or 365"}), 400
    result, status = command_center(
        load_csv("_all_tickers_full.csv"), load_csv("anomaly_flags.csv"), int(days)
    )
    return jsonify(result), status


@app.route("/api/status")
def api_status():
    """Pipeline health + last scrape info."""
    files = {
        "tickers": (DATA_DIR / "_all_tickers_full.csv").exists(),
        "news": (DATA_DIR / "_all_news_combined.csv").exists(),
        "anomaly_flags": (DATA_DIR / "anomaly_flags.csv").exists(),
        "anomaly_classified": (DATA_DIR / "anomaly_classified.csv").exists(),
        "anomaly_summary": (DATA_DIR / "anomaly_summary.csv").exists(),
        "evaluation": (EVALUATION_DIR / "metrics.csv").exists(),
    }
    evaluation_freshness = verify_manifest(MANIFEST_PATH)
    return jsonify({
        "files": files,
        "scraper": scrape_state,
        "data_dir": str(DATA_DIR),
        "evaluation_freshness": evaluation_freshness,
    })


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """Run an explicitly enabled and authenticated analysis pipeline job."""
    if not app.config["PIPELINE_API_ENABLED"]:
        return jsonify({"error": "Pipeline execution API is disabled"}), 404
    expected = str(app.config.get("PIPELINE_API_TOKEN", ""))
    if not expected:
        return jsonify({"error": "Pipeline execution API is not configured"}), 503
    authorization = request.headers.get("Authorization", "")
    supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify({"error": "Unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "")).strip().lower()
    if mode not in {"analysis", "scrape"}:
        return jsonify({"error": "mode must be 'analysis' or 'scrape'"}), 400
    if mode == "scrape" and not app.config["PIPELINE_NETWORK_SCRAPE_ENABLED"]:
        return jsonify({"error": "Network scraping is disabled"}), 403
    with scrape_lock:
        if scrape_state["running"]:
            return jsonify({"message": "Pipeline already running", "state": scrape_state}), 409
        scrape_state.update({
            "running": True,
            "last_status": "running",
            "log": [f"mode={mode}", f"requested_at={datetime.now().astimezone().isoformat()}"],
        })
    t = threading.Thread(target=run_scraper_background, args=(mode,), daemon=True)
    t.start()
    return jsonify({"message": f"{mode} pipeline started", "state": scrape_state}), 202


@app.route("/api/scrape/status")
def api_scrape_status():
    if not app.config["PIPELINE_API_ENABLED"]:
        return jsonify({"error": "Pipeline execution API is disabled"}), 404
    expected = str(app.config.get("PIPELINE_API_TOKEN", ""))
    if not expected:
        return jsonify({"error": "Pipeline execution API is not configured"}), 503
    authorization = request.headers.get("Authorization", "")
    supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(scrape_state)


@app.route("/api/kpis")
def api_kpis():
    """Summary KPIs for the top bar."""
    tickers_df = load_csv("_all_tickers_full.csv")
    news_df    = load_csv("_all_news_combined.csv")
    flags_df   = load_csv("anomaly_flags.csv")
    classified = load_csv("anomaly_classified.csv")

    n_tickers   = tickers_df["symbole"].nunique() if not tickers_df.empty else 0
    n_news      = len(news_df) if not news_df.empty else 0
    data_start = ""
    data_end = ""
    if not tickers_df.empty and "date" in tickers_df.columns:
        dates = pd.to_datetime(tickers_df["date"], errors="coerce")
        if dates.notna().any():
            data_start = dates.min().strftime("%Y-%m-%d")
            data_end = dates.max().strftime("%Y-%m-%d")
    news_as_of = ""
    if not news_df.empty and "date_str" in news_df.columns:
        news_dates = pd.to_datetime(news_df["date_str"], format="%d/%m/%y", errors="coerce")
        if news_dates.notna().any():
            news_as_of = news_dates.max().strftime("%Y-%m-%d")

    # Flagged = combined_anomaly == True in the most recent 30 days of *scraped* data.
    # Anchored to the latest date actually present in the data, not datetime.now(),
    # since this is a periodically-scraped dataset, not a live feed. Anchoring to
    # wall-clock time made this KPI silently drop to 0 between scrapes.
    flagged_30d = 0
    if not flags_df.empty and "date" in flags_df.columns:
        flags_df["date"] = pd.to_datetime(flags_df["date"], errors="coerce")
        latest_date = flags_df["date"].max()
        recent = pd.DataFrame()
        if pd.notna(latest_date):
            cutoff = latest_date - timedelta(days=30)
            recent = flags_df[flags_df["date"] >= cutoff]
        if "combined_anomaly" in recent.columns:
            col = recent["combined_anomaly"].astype(str).str.strip().str.lower()
            vol_col = recent["volume_anomaly"].astype(str).str.strip().str.lower() if "volume_anomaly" in recent.columns else pd.Series(dtype=str)
            pri_col = recent["price_anomaly"].astype(str).str.strip().str.lower() if "price_anomaly" in recent.columns else pd.Series(dtype=str)
            flagged_30d = int(((col == "true") | (vol_col == "true") | (pri_col == "true")).sum())

    news_match_count = 0
    no_local_match_count = 0
    high_intensity_count = 0
    if not classified.empty:
        if "status" in classified.columns:
            st_col = classified["status"].astype(str).str.upper()
            news_match_count = int(st_col.isin(NEWS_MATCH_STATUSES).sum())
            no_local_match_count = int(st_col.isin(NO_MATCH_STATUSES).sum())
        
        # High risk: abs z_score >= 4.0
        vz = classified["volume_zscore"].abs() if "volume_zscore" in classified.columns else pd.Series(0, index=classified.index)
        rz = classified["return_zscore"].abs() if "return_zscore" in classified.columns else pd.Series(0, index=classified.index)
        max_z = pd.concat([vz, rz], axis=1).max(axis=1)
        high_intensity_count = int((max_z >= 4.0).sum())

    total_classified = len(classified) if not classified.empty else 0
    total_anomalies = total_classified if total_classified > 0 else (len(flags_df) if not flags_df.empty else 0)
    triage_rate = round(news_match_count / total_classified * 100, 1) if total_classified else 0

    return jsonify({
        "n_tickers": n_tickers,
        "n_news": n_news,
        "flagged_30d": flagged_30d,
        "triage_rate": triage_rate,
        "total_classified": total_classified,
        "explained": news_match_count,
        "news_nearby_count": news_match_count,
        "news_match_count": news_match_count,
        "total_anomalies": total_anomalies,
        "high_intensity_count": high_intensity_count,
        "high_risk_count": high_intensity_count,
        "unexplained_count": no_local_match_count,
        "no_local_match_count": no_local_match_count,
        "last_scrape": scrape_state.get("last_run"),
        "pipeline_last_run_at": scrape_state.get("last_run"),
        "dashboard_checked_at": datetime.now().astimezone().isoformat(),
        "data_as_of": data_end,
        "news_as_of": news_as_of,
        "data_start": data_start,
        "data_end": data_end,
        "evaluation_freshness": verify_manifest(MANIFEST_PATH),
    })


@app.route("/api/anomalies")
def api_anomalies():
    """Top anomalies sorted by highest absolute z-score."""
    df = load_csv("anomaly_classified.csv")
    if df.empty:
        return jsonify([])

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    # Keep only actual anomalies (volume or price flagged)
    mask = df["volume_anomaly"].astype(str).str.strip().str.lower() == "true"
    mask = mask | (df["price_anomaly"].astype(str).str.strip().str.lower() == "true")
    df = df[mask].copy()

    df["max_zscore"] = df[["volume_zscore", "return_zscore"]].abs().max(axis=1)
    df = df.sort_values("max_zscore", ascending=False).head(50)
    _, headline_urls, date_urls = news_lookup()
    return jsonify([anomaly_record(row, headline_urls, date_urls) for _, row in df.iterrows()])


@app.route("/api/anomalies/search")
def api_anomalies_search():
    """Filter and paginate the complete anomaly review queue."""
    df = load_csv("anomaly_classified.csv")
    if df.empty:
        return jsonify({"rows": [], "total": 0, "page": 1, "page_size": 25, "pages": 0})
    df = df.copy()
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    volume = df.get("volume_anomaly", pd.Series(False, index=df.index)).astype(str).str.strip().str.lower().eq("true")
    price = df.get("price_anomaly", pd.Series(False, index=df.index)).astype(str).str.strip().str.lower().eq("true")
    df = df[volume | price].copy()
    df["max_zscore"] = df[["volume_zscore", "return_zscore"]].apply(pd.to_numeric, errors="coerce").abs().max(axis=1)

    ticker = request.args.get("ticker", "").strip().lower()
    if ticker:
        text = df.get("symbole", "").astype(str) + " " + df.get("ticker_name", "").astype(str)
        df = df[text.str.lower().str.contains(ticker, regex=False)]
    status = request.args.get("status", "").strip().lower()
    if status and status not in {"nearby", "news_nearby", "none", "no_news"}:
        return jsonify({"error": "Invalid status filter"}), 400
    if status in {"nearby", "news_nearby"}:
        df = df[df.get("status", "").astype(str).str.upper().isin(NEWS_MATCH_STATUSES)]
    elif status in {"none", "no_news"}:
        df = df[df.get("status", "").astype(str).str.upper().isin(NO_MATCH_STATUSES)]
    signal = request.args.get("signal", "").strip().lower()
    if signal and signal not in {"volume", "price"}:
        return jsonify({"error": "Invalid signal filter"}), 400
    if signal:
        signal_mask = volume if signal == "volume" else price
        df = df[signal_mask.reindex(df.index, fill_value=False)]
    category = request.args.get("category", "").strip().lower()
    if category:
        df = df[df.get("category", "").fillna("").astype(str).str.lower() == category]
    raw_date_from = request.args.get("date_from", "").strip()
    raw_date_to = request.args.get("date_to", "").strip()
    date_from = pd.to_datetime(raw_date_from, format="%Y-%m-%d", errors="coerce")
    date_to = pd.to_datetime(raw_date_to, format="%Y-%m-%d", errors="coerce")
    if raw_date_from and pd.isna(date_from):
        return jsonify({"error": "date_from must use YYYY-MM-DD"}), 400
    if raw_date_to and pd.isna(date_to):
        return jsonify({"error": "date_to must use YYYY-MM-DD"}), 400
    if pd.notna(date_from) and pd.notna(date_to) and date_from > date_to:
        return jsonify({"error": "date_from must not be after date_to"}), 400
    if pd.notna(date_from):
        df = df[df["date"] >= date_from]
    if pd.notna(date_to):
        df = df[df["date"] <= date_to]
    raw_min_z = request.args.get("min_z", "").strip()
    try:
        min_z = float(raw_min_z) if raw_min_z else None
    except ValueError:
        return jsonify({"error": "min_z must be a non-negative number"}), 400
    if min_z is not None and (not math.isfinite(min_z) or min_z < 0):
        return jsonify({"error": "min_z must be a non-negative number"}), 400
    if min_z is not None:
        df = df[df["max_zscore"] >= min_z]
    intensity = request.args.get("intensity", request.args.get("risk", "")).strip().title()
    if intensity and intensity not in {"High", "Medium", "Low"}:
        return jsonify({"error": "Invalid signal intensity filter"}), 400
    if intensity:
        df = df[df["max_zscore"].map(signal_intensity) == intensity]

    sort = request.args.get("sort", "z")
    if sort not in {"z", "date", "ticker"}:
        return jsonify({"error": "Invalid sort"}), 400
    if sort == "date":
        df = df.sort_values(["date", "symbole"], ascending=[False, True])
    elif sort == "ticker":
        df = df.sort_values(["symbole", "date"], ascending=[True, False])
    else:
        df = df.sort_values(
            ["max_zscore", "date", "symbole"], ascending=[False, False, True]
        )
    total = len(df)
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(5000, max(1, int(request.args.get("page_size", 25))))
    except ValueError:
        return jsonify({"error": "page and page_size must be integers"}), 400
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size]
    _, headline_urls, date_urls = news_lookup()
    rows = [anomaly_record(row, headline_urls, date_urls) for _, row in page_df.iterrows()]
    return jsonify({
        "rows": rows, "total": total, "page": page, "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    })


@app.route("/api/anomaly/<ticker>/<date>")
def api_anomaly_detail(ticker, date):
    ticker = ticker.strip().upper()
    if not valid_ticker(ticker):
        return jsonify({"error": "Invalid ticker"}), 400
    target = pd.to_datetime(date, format="%Y-%m-%d", errors="coerce")
    if pd.isna(target):
        return jsonify({"error": "Invalid date"}), 400
    classified = load_csv("anomaly_classified.csv")
    if classified.empty:
        return jsonify({"error": "Flag not found"}), 404
    classified["parsed_date"] = pd.to_datetime(classified.get("date"), errors="coerce")
    match = classified[(classified.get("symbole", "").astype(str).str.upper() == ticker) & (classified["parsed_date"] == target)]
    if match.empty:
        return jsonify({"error": "Flag not found"}), 404
    news, headline_urls, date_urls = news_lookup()
    flag = anomaly_record(match.iloc[0], headline_urls, date_urls)
    nearby_news = []
    if not news.empty:
        local = news[(news.get("symbole", "").astype(str).str.upper() == ticker)].copy()
        local["gap_days"] = (local["parsed_date"] - target).dt.days
        local = local[local["gap_days"].between(-7, 7)].sort_values("parsed_date")
        for _, item in local.iterrows():
            nearby_news.append({
                "date": item["parsed_date"].strftime("%Y-%m-%d") if pd.notna(item["parsed_date"]) else "",
                "headline": safe_val(item.get("headline"), "not available"),
                "url": safe_http_url(item.get("url")),
                "gap_days": number(item.get("gap_days"), integer=True),
            })
    prices = load_csv(f"{ticker}.csv")
    if prices.empty:
        full = load_csv("_all_tickers_full.csv")
        prices = full[full.get("symbole", "").astype(str).str.upper() == ticker].copy() if not full.empty else pd.DataFrame()
    chart = []
    if not prices.empty:
        prices["date"] = pd.to_datetime(prices.get("date"), errors="coerce")
        prices = prices[prices["date"].between(target - timedelta(days=30), target + timedelta(days=30))].sort_values("date")
        chart = [{"date": row["date"].strftime("%Y-%m-%d"), "cloture": number(row.get("cloture"), 3)} for _, row in prices.iterrows() if pd.notna(row["date"])]
    watch, ai_output_fresh = load_current_watchlist()
    watch_item = None
    if not watch.empty:
        watch["parsed_date"] = pd.to_datetime(watch.get("date"), errors="coerce")
        found = watch[(watch.get("symbole", "").astype(str).str.upper() == ticker) & (watch["parsed_date"] == target)]
        if not found.empty:
            row = found.iloc[0]
            watch_item = {
                "tag": safe_val(row.get("tag"), "not available"),
                "ai_assessment": safe_val(row.get("ai_assessment"), "not available"),
                "ai_reasoning": safe_val(row.get("ai_reasoning"), "not available"),
                "ai_output_fresh": ai_output_fresh,
            }
    return jsonify({"flag": flag, "news": nearby_news, "prices": chart, "watchlist": watch_item})



@app.route("/api/anomalies/timeline")
def api_anomaly_timeline():
    """Daily anomaly count for the past 90 days — for chart."""
    df = load_csv("anomaly_flags.csv")
    if df.empty:
        return jsonify([])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    latest_date = df["date"].max()
    if pd.isna(latest_date):
        return jsonify([])
    # Anchored to the latest scraped date, not datetime.now() — see note in api_kpis().
    cutoff = latest_date - timedelta(days=90)
    df = df[df["date"] >= cutoff]

    if "combined_anomaly" not in df.columns:
        return jsonify([])

    ca = df["volume_anomaly"].astype(str).str.strip().str.lower() == "true"
    ca = ca | (df["price_anomaly"].astype(str).str.strip().str.lower() == "true")
    daily = (
        df[ca]
        .groupby(df["date"].dt.date)
        .size()
        .reset_index(name="count")
    )
    daily["date"] = daily["date"].astype(str)
    return jsonify(daily.to_dict(orient="records"))


@app.route("/api/news/recent")
def api_news_recent():
    """Recent news; default remains 30 rows for backward compatibility."""
    df = load_csv("_all_news_combined.csv")
    if df.empty:
        return jsonify([])
    try:
        limit = min(500, max(1, int(request.args.get("limit", 30))))
    except ValueError:
        limit = 30
    ticker = request.args.get("ticker", "").strip().upper()
    if ticker:
        if not valid_ticker(ticker):
            return jsonify({"error": "Invalid ticker"}), 400
        df = df[df.get("symbole", "").astype(str).str.upper() == ticker]
    df["parsed_date"] = pd.to_datetime(df["date_str"], format="%d/%m/%y", errors="coerce")
    df = df.sort_values("parsed_date", ascending=False)
    classified = load_csv("anomaly_classified.csv")
    linked = {}
    names = {}
    if not classified.empty:
        for _, flag in classified.iterrows():
            symbol = str(flag.get("symbole", "")).upper()
            names[symbol] = safe_val(flag.get("ticker_name"), symbol)
            headline = str(safe_val(flag.get("matched_headline"), "")).strip()
            if headline:
                linked.setdefault((symbol, headline), str(safe_val(flag.get("date"), "")))
    category_filter = request.args.get("category", "").strip().lower()
    if category_filter:
        allowed = set()
        if not classified.empty:
            cats = classified[classified.get("category", "").fillna("").astype(str).str.lower() == category_filter]
            cat_symbols = cats.get("symbole", pd.Series("", index=cats.index)).astype(str).str.upper()
            cat_headlines = cats.get("matched_headline", pd.Series("", index=cats.index)).astype(str)
            allowed = set(zip(cat_symbols, cat_headlines))
        news_symbols = df.get("symbole", pd.Series("", index=df.index)).astype(str).str.upper()
        news_headlines = df.get("headline", pd.Series("", index=df.index)).astype(str)
        keys = pd.MultiIndex.from_arrays([news_symbols, news_headlines])
        df = df[keys.isin(allowed)]
    df = df.head(limit)

    records = []
    for _, row in df.iterrows():
        records.append({
            "symbole":   row.get("symbole", ""),
            "date":      row.get("date_str", ""),
            "time":      row.get("time_str", ""),
            "headline":  row.get("headline", ""),
            "url":       safe_http_url(row.get("url")),
            "ticker_name": names.get(str(row.get("symbole", "")).upper(), str(row.get("symbole", ""))),
            "linked_flag_date": linked.get((str(row.get("symbole", "")).upper(), str(row.get("headline", ""))), ""),
        })
    return jsonify(records)


@app.route("/api/news/by_ticker")
def api_news_by_ticker():
    """News for a specific ticker. ?ticker=BIAT"""
    ticker = request.args.get("ticker", "").upper()
    if not ticker:
        return jsonify([])
    if not valid_ticker(ticker):
        return jsonify({"error": "Invalid ticker"}), 400

    df = load_csv("_all_news_combined.csv")
    if df.empty:
        return jsonify([])

    df = df[df["symbole"].str.upper() == ticker]
    df["parsed_date"] = pd.to_datetime(df["date_str"], format="%d/%m/%y", errors="coerce")
    df = df.sort_values("parsed_date", ascending=False)

    records = []
    for _, row in df.iterrows():
        records.append({
            "symbole":  row.get("symbole", ""),
            "date":     row.get("date_str", ""),
            "time":     row.get("time_str", ""),
            "headline": row.get("headline", ""),
            "url":      safe_http_url(row.get("url")),
        })
    return jsonify(records)


@app.route("/api/stock/<ticker>")
def api_stock(ticker):
    """OHLCV history. Default remains the last 252 trading days."""
    ticker = ticker.strip().upper()
    if not valid_ticker(ticker):
        return jsonify({"error": "Invalid ticker"}), 400
    df = load_csv(f"{ticker}.csv")

    if df.empty:
        # Try combined file
        combined = load_csv("_all_tickers_full.csv")
        if not combined.empty and "symbole" in combined.columns:
            df = combined[combined["symbole"].str.upper() == ticker].copy()

    if df.empty:
        return jsonify({"error": f"No data found for {ticker}"}), 404

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")
    signals = compute_signals(df.copy())
    signal_rows = {}
    if not signals.empty:
        signal_rows = {
            row["date"].strftime("%Y-%m-%d"): row
            for _, row in signals.iterrows() if pd.notna(row.get("date"))
        }
    range_value = request.args.get("range", "1Y").upper()
    window = {"3M": 63, "6M": 126, "1Y": 252}.get(range_value, 252)
    if range_value == "ALL":
        window = None
    if window:
        df = df.tail(window)

    # Get anomaly flags for this ticker
    flags = load_csv("anomaly_classified.csv")
    anomaly_rows = {}
    _, headline_urls, date_urls = news_lookup()
    if not flags.empty and "symbole" in flags.columns:
        tf = flags[flags["symbole"].str.upper() == ticker].copy()
        if not tf.empty:
            tf["date"] = pd.to_datetime(tf["date"], errors="coerce")
            va = tf["volume_anomaly"].astype(str).str.strip().str.lower() == "true"
            pa = tf["price_anomaly"].astype(str).str.strip().str.lower() == "true"
            for _, flag_row in tf[va | pa].iterrows():
                if pd.notna(flag_row["date"]):
                    anomaly_rows[flag_row["date"].strftime("%Y-%m-%d")] = anomaly_record(flag_row, headline_urls, date_urls)

    records = []
    for _, row in df.iterrows():
        d = str(row["date"].date()) if pd.notna(row["date"]) else ""
        signal_row = signal_rows.get(d, {})
        records.append({
            "date":      d,
            "ouverture": round(float(row["ouverture"]), 3) if pd.notna(row.get("ouverture")) else None,
            "haut":      round(float(row["haut"]), 3)      if pd.notna(row.get("haut"))      else None,
            "bas":       round(float(row["bas"]), 3)        if pd.notna(row.get("bas"))       else None,
            "cloture":   round(float(row["cloture"]), 3)   if pd.notna(row.get("cloture"))   else None,
            "volume":    int(row["volume"])                 if pd.notna(row.get("volume"))    else None,
            "volume_zscore": number(signal_row.get("volume_zscore")),
            "return_zscore": number(signal_row.get("return_zscore")),
            "anomaly":   d in anomaly_rows,
            "flag":      anomaly_rows.get(d),
        })
    return jsonify(records)


@app.route("/api/tickers")
def api_tickers():
    """List of all available ticker symbols."""
    resolved_dir = str(DATA_DIR.resolve())
    try:
        directory_mtime = DATA_DIR.stat().st_mtime_ns
    except OSError:
        directory_mtime = None
    source_mtimes = []
    for path in DATA_DIR.glob("*.csv"):
        if path.name == "_all_tickers_full.csv" or TICKER_FILE_PATTERN.fullmatch(path.stem):
            try:
                source_mtimes.append((path.name, path.stat().st_mtime_ns))
            except OSError:
                source_mtimes.append((path.name, None))
    cache_key = (resolved_dir, directory_mtime, tuple(sorted(source_mtimes)))
    with cache_lock:
        cached = _ticker_list_cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    tickers = {}
    combined = load_csv("_all_tickers_full.csv")
    if not combined.empty and "symbole" in combined.columns:
        for _, row in combined.drop_duplicates("symbole").iterrows():
            symbol = str(row["symbole"]).strip().upper()
            if not symbol:
                continue
            name = str(row.get("ticker_name", symbol)).strip()
            tickers[symbol] = name or symbol

    # The combined file can be incomplete even when canonical per-ticker files
    # are present. Merge both sources so Stock Search exposes every local file.
    for path in DATA_DIR.glob("*.csv"):
        symbol = path.stem
        if not TICKER_FILE_PATTERN.fullmatch(symbol):
            continue
        if symbol not in tickers:
            name = symbol
            try:
                sample = pd.read_csv(path, nrows=1)
                if not sample.empty and "ticker_name" in sample.columns:
                    candidate = str(sample.iloc[0]["ticker_name"]).strip()
                    name = candidate or symbol
            except Exception as exc:
                app.logger.warning(f"Could not read ticker metadata from {path}: {exc}")
            tickers[symbol] = name

    result = [{"symbole": symbol, "name": tickers[symbol]} for symbol in sorted(tickers)]
    with cache_lock:
        stale = [item for item in _ticker_list_cache if item[0] == resolved_dir and item != cache_key]
        for item in stale:
            _ticker_list_cache.pop(item, None)
        _ticker_list_cache[cache_key] = result
    return jsonify(result)


@app.route("/api/summary")
def api_summary():
    """anomaly_summary.csv contents."""
    df = load_csv("anomaly_summary.csv")
    if df.empty:
        return jsonify([])
    return jsonify(df.fillna("").to_dict(orient="records"))


@app.route("/api/news/categories")
def api_news_categories():
    """Count news items per category from anomaly_classified."""
    df = load_csv("anomaly_classified.csv")
    if df.empty or "category" not in df.columns:
        return jsonify([])
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    cats = df["category"].dropna()
    cats = cats[cats != ""]
    counts = cats.value_counts().reset_index()
    counts.columns = ["category", "count"]
    return jsonify(counts.to_dict(orient="records"))


@app.route("/api/watchlist")
def api_watchlist():
    """Read-only refined triage queue and volume-decay cases."""
    scope = request.args.get("scope", "queue").strip().lower()
    if scope not in {"queue", "explained"}:
        return jsonify({"error": "Invalid watchlist scope"}), 400

    refined, ai_output_fresh = load_current_watchlist()
    assessment = request.args.get("assessment", "").strip().lower()
    tag = request.args.get("tag", "").strip().upper()
    if scope == "explained":
        refined = load_csv("anomaly_classified.csv")
        ai_output_fresh = False
        if not refined.empty:
            status = refined.get("status", pd.Series("", index=refined.index)).astype(str).str.upper()
            refined = refined[status.isin(NEWS_MATCH_STATUSES)].copy()
            refined["_date"] = pd.to_datetime(refined.get("date"), errors="coerce")
            refined = refined.sort_values(["_date", "symbole"], ascending=[False, True])
    elif not refined.empty:
        if assessment and "ai_assessment" in refined.columns:
            refined = refined[refined["ai_assessment"].fillna("").astype(str).str.lower() == assessment]
        if tag and "tag" in refined.columns:
            refined = refined[refined["tag"].fillna("").astype(str).str.upper() == tag]
    _, headline_urls, date_urls = news_lookup()
    rows = []
    for _, row in refined.iterrows():
        item = anomaly_record(row, headline_urls, date_urls)
        item.update({
            "priority": number(row.get("priority"), integer=True),
            "tag": safe_val(row.get("tag"), "not available"),
            "co_flagged_count": number(row.get("co_flagged_count"), integer=True),
            "excess_return": number(row.get("excess_return"), 6),
            "index_return": number(row.get("index_return"), 6),
            "ai_assessment": safe_val(row.get("ai_assessment"), "not available"),
            "ai_reasoning": safe_val(row.get("ai_reasoning"), "not available"),
        })
        rows.append(item)
    decay = load_csv("decay_classified.csv")
    if decay.empty:
        decay = load_csv("decay_flags.csv")
    decay_rows = [{
        "symbole": safe_val(row.get("symbole"), ""),
        "ticker_name": safe_val(row.get("ticker_name"), safe_val(row.get("symbole"), "")),
        "baseline_volume": number(row.get("baseline_volume"), integer=True),
        "recent_volume": number(row.get("recent_volume"), integer=True),
        "decline_ratio": number(row.get("decline_ratio"), 4),
        "last_active_date": safe_val(row.get("last_active_date"), "not available"),
        "days_since_active": number(row.get("days_since_active"), integer=True),
        "news_status": (
            "News match found" if has_news_match(row.get("status", ""))
            else "No local news match"
        ),
    } for _, row in decay.iterrows()]
    return jsonify({
        "rows": rows,
        "total": len(rows),
        "scope": scope,
        "decay": decay_rows,
        "decay_total": len(decay_rows),
        "ai_output_fresh": ai_output_fresh,
    })


@app.route("/api/overview")
def api_overview():
    classified = load_csv("anomaly_classified.csv")
    if classified.empty:
        return jsonify({"monthly": [], "top_tickers": [], "recent": [], "split": {"nearby": 0, "none": 0}})
    classified = classified.copy()
    classified["date"] = pd.to_datetime(classified.get("date"), errors="coerce")
    classified["max_zscore"] = classified[["volume_zscore", "return_zscore"]].apply(pd.to_numeric, errors="coerce").abs().max(axis=1)
    monthly = classified.dropna(subset=["date"]).groupby(classified["date"].dt.to_period("M")).size().reset_index(name="count")
    monthly["date"] = monthly["date"].astype(str)
    top = classified.groupby(["symbole", "ticker_name"], dropna=False).size().reset_index(name="count").sort_values("count", ascending=False).head(10)
    _, headline_urls, date_urls = news_lookup()
    recent = classified.sort_values("date", ascending=False).head(5)
    status = classified.get("status", "").astype(str).str.upper()
    return jsonify({
        "monthly": monthly.to_dict(orient="records"),
        "top_tickers": top.fillna("").to_dict(orient="records"),
        "recent": [anomaly_record(row, headline_urls, date_urls) for _, row in recent.iterrows()],
        "split": {
            "nearby": int(status.isin(NEWS_MATCH_STATUSES).sum()),
            "none": int(status.isin(NO_MATCH_STATUSES).sum()),
        },
    })


@app.route("/api/overview/calendar")
def api_overview_calendar():
    """Daily flag counts for the complete history, used by the calendar view."""
    flags = load_csv("anomaly_flags.csv")
    if flags.empty:
        return jsonify([])
    flags["date"] = pd.to_datetime(flags.get("date"), errors="coerce")
    daily = flags.dropna(subset=["date"]).groupby("date").size().reset_index(name="count")
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    return jsonify(daily.to_dict(orient="records"))


@app.route("/api/overview/radar")
def api_overview_radar():
    """Return every real flag for the volume/return surveillance scatter."""
    classified = load_csv("anomaly_classified.csv")
    if classified.empty:
        return jsonify([])
    _, headline_urls, date_urls = news_lookup()
    return jsonify([
        anomaly_record(row, headline_urls, date_urls)
        for _, row in classified.iterrows()
    ])


@lru_cache(maxsize=64)
def cached_playground(z_cutoff: float, rolling_window: int, source_mtime: int) -> dict:
    """Read a generated sensitivity cell; source_mtime invalidates the cache."""
    del source_mtime
    sensitivity = load_evaluation_csv("sensitivity.csv")
    if sensitivity.empty:
        return {}
    z_values = pd.to_numeric(sensitivity.get("z_cutoff"), errors="coerce")
    windows = pd.to_numeric(sensitivity.get("rolling_window"), errors="coerce")
    match = sensitivity[(z_values == z_cutoff) & (windows == rolling_window)]
    if match.empty:
        return {}
    row = match.iloc[0]
    eligible = load_evaluation_csv("metrics.csv")
    denominator = 0
    if not eligible.empty:
        found = eligible[eligible.get("metric") == "eligible_positive_events_30d"]
        if not found.empty:
            denominator = int(float(found.iloc[0]["value"]))
    recall = number(row.get("recall_30d"), 6) or 0
    return {
        "z_cutoff": z_cutoff,
        "rolling_window": rolling_window,
        "flag_count": number(row.get("flag_count"), integer=True),
        "flags_per_ticker_year": number(row.get("flags_per_ticker_year"), 3),
        "event_hits": round(recall * denominator),
        "event_denominator": denominator,
        "exploratory": True,
        "changes_reference_detector": False,
    }


@app.route("/api/playground")
def api_playground():
    """Cached, read-only view of the precomputed detector sensitivity grid."""
    try:
        z_cutoff = float(request.args.get("z", "3.0"))
        rolling_window = int(request.args.get("window", "60"))
    except ValueError:
        return jsonify({"error": "z and window must be numeric"}), 400
    if z_cutoff not in {2.5, 3.0, 3.5, 4.0} or rolling_window not in {20, 40, 60, 120}:
        return jsonify({"error": "Choose a generated sensitivity-grid value"}), 400
    path = EVALUATION_DIR / "sensitivity.csv"
    mtime = path.stat().st_mtime_ns if path.exists() else 0
    result = cached_playground(z_cutoff, rolling_window, mtime)
    return jsonify(result) if result else (jsonify({"error": "Sensitivity data unavailable"}), 404)


@app.route("/api/evaluation/metrics")
def api_evaluation_metrics():
    df = load_evaluation_csv("metrics.csv")
    return jsonify(df.fillna("").to_dict(orient="records"))


@app.route("/api/evaluation/baselines")
def api_evaluation_baselines():
    df = load_evaluation_csv("baseline_comparison.csv")
    return jsonify(df.fillna("").to_dict(orient="records"))


@app.route("/api/evaluation/sensitivity")
def api_evaluation_sensitivity():
    df = load_evaluation_csv("sensitivity.csv")
    return jsonify(df.fillna("").to_dict(orient="records"))


@app.route("/api/evaluation/events")
def api_evaluation_events():
    df = load_evaluation_csv("events_table.csv")
    return jsonify(df.fillna("").to_dict(orient="records"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    if app.config["CACHE_WARMUP_ENABLED"]:
        warm_startup_caches()
    app.run(host=host, port=port, debug=False)
