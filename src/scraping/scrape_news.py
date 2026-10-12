"""Incrementally merge per-symbol ilboursa news archives."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from src.scraping.scrape_ilboursa import (
        HEADERS,
        atomic_write_csv,
        discover_tickers,
        ticker_inventory,
    )
except ModuleNotFoundError:  # direct ``python src/scraping/scrape_news.py``
    from scrape_ilboursa import (  # type: ignore[no-redef]
        HEADERS,
        atomic_write_csv,
        discover_tickers,
        ticker_inventory,
    )

NEWS_URL = "https://www.ilboursa.com/marches/news_valeur"
BASE_URL = "https://www.ilboursa.com/marches/"
NEWS_COLUMNS = ["date_str", "time_str", "headline", "url"]
NEWS_KEY = ["date_str", "headline", "url"]
NEWS_FILE_PATTERN = re.compile(r"^news_([A-Z0-9]+)\.csv$")


def fetch_news_page(session, ticker, page=1):
    params = {"s": ticker}
    if page > 1:
        params["p"] = page
    response = session.get(NEWS_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.text


def fetch_news_page_with_retry(session, ticker, page, retries=3, pause=1.5):
    last_error = "unknown error"
    for attempt in range(1, retries + 1):
        try:
            return fetch_news_page(session, ticker, page), None
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(pause * attempt)
    return None, {"ticker": ticker, "page": page, "reason": last_error}


def parse_news_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for span in soup.find_all("span", class_="sp1"):
        raw = span.get_text(strip=True)
        parts = raw.split(" ", 1)
        anchor = span.find_next_sibling("a")
        if anchor is None or not anchor.get("href", ""):
            continue
        href = anchor.get("href", "")
        items.append({
            "date_str": parts[0] if parts else "",
            "time_str": parts[1] if len(parts) > 1 else "",
            "headline": anchor.get_text(strip=True),
            "url": href if href.startswith("http") else BASE_URL + href,
        })
    return items


def normalize_news(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    result = frame.copy()
    missing = sorted(set(NEWS_COLUMNS) - set(result.columns))
    if missing:
        raise ValueError(f"{symbol}: missing news columns {missing}")
    result = result[NEWS_COLUMNS].fillna("")
    parsed = pd.to_datetime(result["date_str"], format="%d/%m/%y", errors="coerce")
    parsed = parsed.fillna(
        pd.to_datetime(result["date_str"], format="%d/%m/%Y", errors="coerce")
    )
    if parsed.isna().any() or result["headline"].astype(str).str.strip().eq("").any():
        raise ValueError(f"{symbol}: invalid news date or empty headline")
    result["_parsed_date"] = parsed
    result = result.drop_duplicates(NEWS_KEY, keep="first")
    return result.sort_values(["_parsed_date", "time_str"], ascending=[False, False]).drop(columns="_parsed_date").reset_index(drop=True)


def load_existing_news(path: Path, symbol: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=NEWS_COLUMNS)
    return normalize_news(pd.read_csv(path), symbol)


def news_keys(frame: pd.DataFrame) -> set[tuple[str, str, str]]:
    return set(frame[NEWS_KEY].astype(str).itertuples(index=False, name=None))


def scrape_incremental_ticker_news(
    session,
    ticker: str,
    existing: pd.DataFrame,
    max_pages: int = 30,
    pause: float = 1.5,
) -> tuple[pd.DataFrame, list[dict]]:
    known = news_keys(existing)
    collected, failures = [], []
    for page in range(1, max_pages + 1):
        html, failure = fetch_news_page_with_retry(session, ticker, page, pause=pause)
        if failure is not None:
            failures.append(failure)
            break
        items = parse_news_items(html)
        if not items:
            break
        page_frame = normalize_news(pd.DataFrame(items), ticker)
        unseen = page_frame[
            ~page_frame[NEWS_KEY].astype(str).apply(tuple, axis=1).isin(known)
        ]
        if not unseen.empty:
            collected.append(unseen)
            known.update(news_keys(unseen))
        if len(unseen) == 0 and not existing.empty:
            break
        time.sleep(pause)
    if not collected:
        return pd.DataFrame(columns=NEWS_COLUMNS), failures
    return normalize_news(pd.concat(collected, ignore_index=True), ticker), failures


def merge_news(existing: pd.DataFrame, incoming: pd.DataFrame, symbol: str) -> tuple[pd.DataFrame, int]:
    before = news_keys(existing)
    merged = normalize_news(pd.concat([existing, incoming], ignore_index=True), symbol)
    return merged, len(news_keys(merged) - before)


def news_symbols(data_dir: Path) -> set[str]:
    result = set()
    for path in data_dir.glob("news_*.csv"):
        match = NEWS_FILE_PATTERN.fullmatch(path.name)
        if match:
            result.add(match.group(1))
    return result


def rebuild_combined_news(data_dir: Path) -> pd.DataFrame:
    frames = []
    for symbol in sorted(news_symbols(data_dir)):
        frame = load_existing_news(data_dir / f"news_{symbol}.csv", symbol)
        if frame.empty:
            continue
        frame.insert(0, "symbole", symbol)
        frames.append(frame)
    if not frames:
        raise ValueError("No per-symbol news files are available")
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(["symbole", *NEWS_KEY], keep="first")
    parsed = pd.to_datetime(combined["date_str"], format="%d/%m/%y", errors="coerce")
    parsed = parsed.fillna(pd.to_datetime(combined["date_str"], format="%d/%m/%Y", errors="coerce"))
    combined["_parsed_date"] = parsed
    combined = combined.sort_values(["_parsed_date", "time_str"], ascending=[False, False]).drop(columns="_parsed_date")
    atomic_write_csv(combined, data_dir / "_all_news_combined.csv")
    return combined.reset_index(drop=True)


def incremental_news_update(data_dir: Path, pause: float = 1.5) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)
    discovered = discover_tickers(session)
    inventory = dict(ticker_inventory(data_dir, discovered))
    for symbol in news_symbols(data_dir):
        inventory.setdefault(symbol, symbol)
    failures, rows = [], []
    symbols = sorted(inventory)
    for position, symbol in enumerate(symbols, start=1):
        print(f"[{position}/{len(symbols)}] Updating news for {symbol}...", flush=True)
        path = data_dir / f"news_{symbol}.csv"
        existing = load_existing_news(path, symbol)
        incoming, ticker_failures = scrape_incremental_ticker_news(
            session, symbol, existing, pause=pause
        )
        failures.extend(ticker_failures)
        merged, added = merge_news(existing, incoming, symbol)
        if added or (not path.exists() and not merged.empty):
            atomic_write_csv(merged, path)
        rows.append({
            "ticker": symbol,
            "items_before": len(existing),
            "items_added": added,
            "status": "failed" if ticker_failures and incoming.empty else "updated",
        })
        print(f"  {symbol}: +{added} news items", flush=True)
    atomic_write_csv(
        pd.DataFrame(failures, columns=["ticker", "page", "reason"]),
        data_dir / "_failed_news_pages.csv",
    )
    combined = rebuild_combined_news(data_dir)
    report = pd.DataFrame(rows)
    print(
        f"News update: {int(report['items_added'].sum())} items added; "
        f"{int(report['items_added'].gt(0).sum())} tickers updated; "
        f"{int(report['status'].eq('failed').sum())} failed."
    )
    print(f"Combined news: {len(combined)} unique symbol/date/headline/url rows.")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("bvmt_data"))
    parser.add_argument("--pause", type=float, default=1.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    incremental_news_update(args.data_dir, args.pause)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
