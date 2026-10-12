"""Incrementally update BVMT OHLCV files from ilboursa.com.

The updater keeps existing observations immutable, refreshes a seven-day overlap
for validation, and appends only genuinely new symbol/date rows. Files are
written atomically after schema and numeric validation. Statistical flags remain
screening signals for human review, not fraud verdicts.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.ilboursa.com/marches/download/{ticker}"
TICKER_FILE_PATTERN = re.compile(r"^[A-Z0-9]+\.csv$")
PRICE_COLUMNS = [
    "ticker_name", "symbole", "date", "ouverture", "haut", "bas", "cloture", "volume",
]
NUMERIC_COLUMNS = ["ouverture", "haut", "bas", "cloture", "volume"]
DEFAULT_START = datetime(2021, 6, 17)
OVERLAP_DAYS = 7
REQUESTED_MISSING = ("CGF", "TSI")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def get_csrf_token(session, ticker):
    url = BASE_URL.format(ticker=ticker)
    response = session.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    if token_input is None:
        raise RuntimeError(f"No CSRF token found for {ticker}")
    return token_input["value"]


def fetch_chunk(session, ticker, date_from, date_to):
    url = BASE_URL.format(ticker=ticker)
    payload = {
        "dtFrom": date_from.strftime("%Y-%m-%d"),
        "dtTo": date_to.strftime("%Y-%m-%d"),
        "__RequestVerificationToken": get_csrf_token(session, ticker),
    }
    response = session.post(url, data=payload, headers={"Referer": url}, timeout=15)
    response.raise_for_status()
    return response.text


def discover_tickers(session, sample_ticker="PX1"):
    response = session.get(BASE_URL.format(ticker=sample_ticker), timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    candidates = [select for select in soup.find_all("select") if len(select.find_all("option")) > 50]
    if not candidates:
        return []
    return [
        (option.get("value", "").strip().upper(), option.get_text(strip=True))
        for option in candidates[0].find_all("option")
        if option.get("value", "").strip()
    ]


def parse_csv_chunk(text):
    try:
        return pd.read_csv(
            io.StringIO(text), sep=";", decimal=",", parse_dates=["date"], dayfirst=True
        )
    except (ValueError, pd.errors.ParserError):
        return None


def fetch_chunk_with_retry(
    session, ticker, date_from, date_to, max_retries=3, pause=1.5
):
    last_error = "unknown error"
    for attempt in range(1, max_retries + 1):
        try:
            frame = parse_csv_chunk(fetch_chunk(session, ticker, date_from, date_to))
            if frame is not None and not frame.empty:
                return frame, None
            last_error = "response did not contain price rows"
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            last_error = str(exc)
        if attempt < max_retries:
            time.sleep(pause * attempt)
    return None, {
        "ticker": ticker,
        "from": date_from.date().isoformat(),
        "to": date_to.date().isoformat(),
        "reason": last_error,
    }


def download_full_history(
    ticker, start_date, end_date, chunk_days=89, pause=1.5, session=None
):
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
    frames, failures = [], []
    current_start = pd.Timestamp(start_date).to_pydatetime()
    final_date = pd.Timestamp(end_date).to_pydatetime()
    while current_start <= final_date:
        current_end = min(current_start + timedelta(days=chunk_days), final_date)
        frame, failure = fetch_chunk_with_retry(
            session, ticker, current_start, current_end, pause=pause
        )
        if frame is not None:
            frames.append(frame)
        if failure is not None:
            failures.append(failure)
            if not frames:
                break
        current_start = current_end + timedelta(days=1)
        time.sleep(pause)
    if not frames:
        return pd.DataFrame(), failures
    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    return combined.drop_duplicates(subset=["date"]).sort_values("date"), failures


def normalize_price_frame(frame: pd.DataFrame, symbol: str, name: str) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [str(column).strip().lower() for column in result.columns]
    required = {"date", *NUMERIC_COLUMNS}
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(f"{symbol}: missing columns {missing}")
    result["symbole"] = symbol
    result["ticker_name"] = name or symbol
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result[NUMERIC_COLUMNS] = result[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if result["date"].isna().any() or result[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError(f"{symbol}: invalid date or numeric OHLCV value")
    if (result["volume"] < 0).any():
        raise ValueError(f"{symbol}: negative volume")
    result = result[PRICE_COLUMNS].sort_values("date").drop_duplicates(["symbole", "date"])
    return result.reset_index(drop=True)


def load_existing_price(path: Path, symbol: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=PRICE_COLUMNS)
    frame = pd.read_csv(path)
    if list(frame.columns) != PRICE_COLUMNS:
        raise ValueError(f"Unexpected ticker schema in {path}")
    name = str(frame["ticker_name"].dropna().iloc[0]) if not frame.empty else symbol
    normalized = normalize_price_frame(frame, symbol, name)
    if len(normalized) != len(frame):
        raise ValueError(f"{symbol}: existing file contains duplicate symbol/date rows")
    return normalized


def merge_price_history(existing: pd.DataFrame, incoming: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if existing.empty:
        merged = incoming.copy()
        return merged.sort_values("date").reset_index(drop=True), len(merged)
    last_date = existing["date"].max()
    additions = incoming[incoming["date"] > last_date].copy()
    merged = pd.concat([existing, additions], ignore_index=True)
    merged = merged.sort_values("date").drop_duplicates(["symbole", "date"], keep="first")
    return merged.reset_index(drop=True), len(additions)


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = frame.copy()
    if "date" in output.columns:
        parsed = pd.to_datetime(output["date"], errors="coerce")
        output["date"] = parsed.dt.strftime("%Y-%m-%d")
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(handle)
    temporary_path = Path(temporary_name)
    try:
        output.to_csv(temporary_path, index=False, lineterminator="\n")
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def individual_ticker_paths(out_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in out_dir.glob("*.csv")
        if TICKER_FILE_PATTERN.fullmatch(path.name) and path.name != "SHA256SUMS.csv"
    )


def rebuild_combined_from_individual_files(
    out_dir, output_name="_all_tickers_combined.csv"
):
    directory = Path(out_dir)
    frames = [load_existing_price(path, path.stem) for path in individual_ticker_paths(directory)]
    if not frames:
        raise ValueError(f"No individual ticker CSVs found in {directory}")
    master = pd.concat(frames, ignore_index=True).sort_values(["symbole", "date"])
    if master.duplicated(["symbole", "date"]).any():
        raise ValueError("Combined price history contains duplicate symbol/date rows")
    atomic_write_csv(master, directory / output_name)
    return master.reset_index(drop=True)


def verify_snapshot_rows_unchanged(snapshot_dir: Path, data_dir: Path) -> None:
    errors = []
    for snapshot_path in individual_ticker_paths(snapshot_dir):
        current_path = data_dir / snapshot_path.name
        if not current_path.exists():
            errors.append(f"missing current file {snapshot_path.name}")
            continue
        old = load_existing_price(snapshot_path, snapshot_path.stem).set_index(["symbole", "date"])
        current = load_existing_price(current_path, current_path.stem).set_index(["symbole", "date"])
        shared = current.reindex(old.index)
        if shared.isna().all(axis=1).any() or not old.equals(shared[old.columns]):
            errors.append(f"old rows changed in {snapshot_path.name}")
    if errors:
        raise ValueError("Snapshot integrity validation failed: " + " | ".join(errors))


def ticker_inventory(data_dir: Path, discovered: list[tuple[str, str]]) -> list[tuple[str, str]]:
    names = {code: name or code for code, name in discovered}
    for path in individual_ticker_paths(data_dir):
        frame = pd.read_csv(path, usecols=["ticker_name"], nrows=1)
        names.setdefault(path.stem, str(frame.iloc[0, 0]) if not frame.empty else path.stem)
    for code in REQUESTED_MISSING:
        names.setdefault(code, code)
    return sorted(names.items())


def incremental_update(
    data_dir: Path,
    end_date: datetime,
    snapshot_dir: Path | None = None,
    pause: float = 1.5,
) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)
    discovered = discover_tickers(session)
    inventory = ticker_inventory(data_dir, discovered)
    failures, report_rows = [], []
    for position, (symbol, name) in enumerate(inventory, start=1):
        print(f"[{position}/{len(inventory)}] Updating prices for {symbol}...", flush=True)
        path = data_dir / f"{symbol}.csv"
        existing = load_existing_price(path, symbol)
        start = (
            existing["date"].max().to_pydatetime() - timedelta(days=OVERLAP_DAYS)
            if not existing.empty else DEFAULT_START
        )
        incoming, failed_ranges = download_full_history(
            symbol, start, end_date, pause=pause, session=session
        )
        failures.extend(failed_ranges)
        added = 0
        if not incoming.empty:
            normalized = normalize_price_frame(incoming, symbol, name)
            merged, added = merge_price_history(existing, normalized)
            if added or not path.exists():
                atomic_write_csv(merged, path)
        if not existing.empty and not incoming.empty:
            last_date = max(existing["date"].max(), incoming["date"].max())
        elif not existing.empty:
            last_date = existing["date"].max()
        elif not incoming.empty:
            last_date = incoming["date"].max()
        else:
            last_date = pd.NaT
        report_rows.append({
            "ticker": symbol,
            "rows_before": len(existing),
            "rows_added": added,
            "last_date": last_date.date().isoformat() if pd.notna(last_date) else "unavailable",
            "status": "failed" if failed_ranges and incoming.empty else "updated",
        })
        print(
            f"  {symbol}: +{added} rows; latest "
            f"{last_date.date().isoformat() if pd.notna(last_date) else 'unavailable'}",
            flush=True,
        )
    failure_columns = ["ticker", "from", "to", "reason"]
    atomic_write_csv(pd.DataFrame(failures, columns=failure_columns), data_dir / "_failed_price_chunks.csv")
    combined = rebuild_combined_from_individual_files(data_dir, "_all_tickers_combined.csv")
    rebuild_combined_from_individual_files(data_dir, "_all_tickers_full.csv")
    if snapshot_dir is not None:
        verify_snapshot_rows_unchanged(snapshot_dir, data_dir)
    report = pd.DataFrame(report_rows)
    print(
        f"Price update: {int(report['rows_added'].sum())} rows added; "
        f"{int(report['rows_added'].gt(0).sum())} tickers updated; "
        f"{int(report['status'].eq('failed').sum())} failed."
    )
    print(
        f"Combined history: {len(combined)} rows, {combined['symbole'].nunique()} symbols, "
        f"{combined['date'].min().date()} to {combined['date'].max().date()}."
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("bvmt_data"))
    parser.add_argument("--snapshot-dir", type=Path)
    parser.add_argument(
        "--end-date",
        type=lambda value: datetime.strptime(value, "%Y-%m-%d"),
        default=datetime.combine(date.today(), datetime.min.time()),
    )
    parser.add_argument("--pause", type=float, default=1.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    incremental_update(args.data_dir, args.end_date, args.snapshot_dir, args.pause)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
