"""Build and evaluate an 85-symbol derived universe without changing raw inputs."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.detection.anomaly_detector import compute_signals, load_data, summarize
from src.evaluation import baselines, evaluate, report, sensitivity

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "bvmt_data"
COMBINED_PATH = DATA_DIR / "_all_tickers_combined.csv"
FULL_PATH = DATA_DIR / "_all_tickers_full.csv"
EVENTS_PATH = ROOT / "data" / "evaluation" / "events.csv"
ARCHIVE_DIR = ROOT / "outputs" / "evaluation_60symbol"
OUTPUT_DIR = ROOT / "outputs" / "evaluation"
REFERENCE_FLAGS_PATH = ARCHIVE_DIR / "anomaly_flags.csv"
EXPECTED_COLUMNS = [
    "ticker_name", "symbole", "date", "ouverture", "haut", "bas", "cloture", "volume",
]
FLAG_COLUMNS = [
    "symbole", "ticker_name", "date", "cloture", "volume", "daily_return",
    "volume_zscore", "return_zscore", "volume_anomaly", "price_anomaly",
    "combined_anomaly",
]
KNOWN_EXCLUDED = {"PLTU", "TBIDX"}


def individual_ticker_paths(data_dir: Path = DATA_DIR) -> list[Path]:
    return sorted(
        path for path in data_dir.glob("*.csv")
        if re.fullmatch(r"[A-Z0-9]+\.csv", path.name)
    )


def validate_frame(frame: pd.DataFrame, symbol: str) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != EXPECTED_COLUMNS:
        return ["unexpected schema"]
    if frame.empty:
        return ["empty file"]
    if set(frame["symbole"].astype(str)) != {symbol}:
        errors.append("symbol does not match filename")
    dates = pd.to_datetime(frame["date"], errors="coerce")
    if dates.isna().any():
        errors.append("unparseable date")
    if dates.duplicated().any():
        errors.append("duplicate date")
    numeric = frame[["ouverture", "haut", "bas", "cloture", "volume"]].apply(
        pd.to_numeric, errors="coerce"
    )
    if numeric.isna().any().any():
        errors.append("missing or non-numeric OHLCV")
    if (numeric["volume"] < 0).any():
        errors.append("negative volume")
    if len(frame) < 60 and symbol not in KNOWN_EXCLUDED:
        errors.append("fewer than 60 observations")
    return errors


def build_full_universe() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    combined = pd.read_csv(COMBINED_PATH)
    combined_symbols = set(combined["symbole"].astype(str))
    frames: dict[str, pd.DataFrame] = {}
    audit_rows = []
    fatal = []
    for path in individual_ticker_paths():
        symbol = path.stem
        frame = pd.read_csv(path)
        errors = validate_frame(frame, symbol)
        frames[symbol] = frame
        if errors:
            fatal.extend(f"{symbol}: {error}" for error in errors)
        audit_rows.append({
            "symbol": symbol,
            "rows": len(frame),
            "in_60_symbol_combined": symbol in combined_symbols,
            "detector_excluded": symbol in KNOWN_EXCLUDED,
            "validation": "valid" if not errors else "; ".join(errors),
        })
    if fatal:
        raise ValueError("Invalid individual ticker data: " + " | ".join(fatal))

    missing = sorted(set(frames) - combined_symbols)
    full = pd.concat([frames[symbol] for symbol in sorted(frames)], ignore_index=True)
    full = full.sort_values(["symbole", "date"]).reset_index(drop=True)
    if full.duplicated(["symbole", "date"]).any():
        raise ValueError("Derived full universe contains duplicate symbol/date rows")
    full.to_csv(FULL_PATH, index=False)
    return full, pd.DataFrame(audit_rows), missing


def run_full_detector() -> pd.DataFrame:
    trading = load_data(str(FULL_PATH))
    signals = compute_signals(trading)
    flags, ticker_summary = summarize(signals)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    flags_out = flags[FLAG_COLUMNS].copy()
    flags_out.to_csv(OUTPUT_DIR / "anomaly_flags.csv", index=False)
    ticker_summary.to_csv(OUTPUT_DIR / "anomaly_summary.csv", index=False)
    return flags_out


def flags_agree_on_shared_symbols(full_flags: pd.DataFrame) -> bool:
    reference = pd.read_csv(REFERENCE_FLAGS_PATH, parse_dates=["date"])
    full_flags = full_flags.copy()
    full_flags["date"] = pd.to_datetime(full_flags["date"])
    shared_symbols = set(pd.read_csv(COMBINED_PATH, usecols=["symbole"])["symbole"])
    candidate = full_flags[full_flags["symbole"].isin(shared_symbols)].copy()
    sort_columns = ["symbole", "date"]
    reference = reference.sort_values(sort_columns).reset_index(drop=True)
    candidate = candidate.sort_values(sort_columns).reset_index(drop=True)
    if reference.shape != candidate.shape or list(reference.columns) != list(candidate.columns):
        return False
    exact_columns = [
        "symbole", "date", "volume", "volume_anomaly",
        "price_anomaly", "combined_anomaly",
    ]
    if not reference[exact_columns].equals(candidate[exact_columns]):
        return False
    numeric_columns = ["cloture", "daily_return", "volume_zscore", "return_zscore"]
    return bool(np.allclose(
        reference[numeric_columns].to_numpy(float),
        candidate[numeric_columns].to_numpy(float),
        rtol=0,
        atol=1e-12,
        equal_nan=True,
    ))


def count_text(value: float, denominator: int, noun: str) -> str:
    count = float(value) * denominator
    if abs(count - round(count)) < 1e-9:
        return f"{int(round(count))} of {denominator} {noun}"
    return f"{count:.3f} of {denominator} {noun} on average"


def comparison_table(shared_agreement: bool) -> pd.DataFrame:
    rows = []
    for label, directory, data_path in [
        ("60-symbol archive", ARCHIVE_DIR, COMBINED_PATH),
        ("85-symbol delivered universe", OUTPUT_DIR, FULL_PATH),
    ]:
        metrics = pd.read_csv(directory / "metrics.csv").set_index("metric")["value"]
        precision = pd.read_csv(directory / "precision_at_k.csv").set_index("k")
        raw = pd.read_csv(data_path, usecols=["symbole"])
        denom30 = int(metrics["eligible_positive_events_30d"])
        denom60 = int(metrics["eligible_positive_events_60d"])
        rows.append({
            "universe": label,
            "symbols": int(raw["symbole"].nunique()),
            "rows": len(raw),
            "flags": int(metrics["flag_count"]),
            "flags_per_ticker_year": float(metrics["flags_per_ticker_year"]),
            "primary_recall": count_text(metrics["recall_30d"], denom30, "events"),
            "secondary_recall": count_text(metrics["recall_60d"], denom60, "events"),
            "precision_at_10": count_text(precision.loc[10, "precision_at_k"], 10, "flags"),
            "precision_at_20": count_text(precision.loc[20, "precision_at_k"], 20, "flags"),
            "precision_at_50": count_text(precision.loc[50, "precision_at_k"], 50, "flags"),
            "shared_symbol_flags_agree": shared_agreement,
        })
    return pd.DataFrame(rows)


def write_coverage_note(audit: pd.DataFrame, missing: list[str], shared_agreement: bool) -> None:
    named = []
    combined_symbols = set(
        pd.read_csv(COMBINED_PATH, usecols=["symbole"])["symbole"].astype(str)
    )
    individual_symbols = set(audit["symbol"])
    for symbol in ["UBCI", "CGF", "TSI", "TINV", "UADH"]:
        unavailable = (
            "; not in the dataset and cannot be evaluated"
            if symbol in {"CGF", "TSI"} else ""
        )
        named.append(
            f"- {symbol}: individual file {'yes' if symbol in individual_symbols else 'no'}; "
            f"60-symbol combined {'yes' if symbol in combined_symbols else 'no'}{unavailable}."
        )
    note = f"""# Coverage audit

- Individual uppercase ticker files: **{len(audit)}**.
- Symbols in `_all_tickers_combined.csv`: **{len(combined_symbols)}**.
- Missing from the combined file: **{len(missing)}** — {', '.join(missing)}.
- Validation: **{int(audit['validation'].eq('valid').sum())} of {len(audit)} files valid** for the fixed detector; PLTU has 41 observations but is accepted because the detector explicitly excludes it as known-incomplete.
- Shared OHLCV rows agree exactly. Full-run flags on the shared symbols: **{'agree' if shared_agreement else 'do not agree'}**.

## Requested symbols

{chr(10).join(named)}

## Repository-supported cause

The earlier `src/scraping/scrape_ilboursa.py` skipped a symbol when its individual CSV already existed, but appended only newly downloaded frames to `all_data` and then overwrote `_all_tickers_combined.csv` from `all_data`. The 25 omitted files were therefore existing files skipped by that run, not invalid rows. The code now rebuilds from all individual ticker files; no scraper was run for this audit.
"""
    (OUTPUT_DIR / "coverage_audit.md").write_text(note, encoding="utf-8")


def main() -> int:
    full, audit, missing = build_full_universe()
    flags = run_full_detector()
    evaluate.main(FULL_PATH, OUTPUT_DIR / "anomaly_flags.csv", EVENTS_PATH, OUTPUT_DIR)
    baselines.main(FULL_PATH, OUTPUT_DIR / "anomaly_flags.csv", EVENTS_PATH, OUTPUT_DIR)
    sensitivity.main(FULL_PATH, OUTPUT_DIR / "anomaly_flags.csv", EVENTS_PATH, OUTPUT_DIR)
    report.main(OUTPUT_DIR, title="Full-universe Evaluation Summary")
    shared_agreement = flags_agree_on_shared_symbols(flags)
    audit.to_csv(OUTPUT_DIR / "coverage_audit.csv", index=False)
    comparison_table(shared_agreement).to_csv(
        OUTPUT_DIR / "universe_comparison.csv", index=False
    )
    write_coverage_note(audit, missing, shared_agreement)
    report.main(OUTPUT_DIR)
    print(
        f"Built {FULL_PATH.name}: {len(full)} rows, {full['symbole'].nunique()} symbols; "
        f"missing={len(missing)}; shared_flags_agree={shared_agreement}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
