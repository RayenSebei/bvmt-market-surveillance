"""
Phase 1 — Volume & Price Anomaly Detector for BVMT market surveillance.

This is a statistical screening tool, not a legal finding. It uses the
same kind of approach real exchanges and regulators use
(SEC, ESMA, FINRA market surveillance systems): flag abnormal patterns
that historically correlate with manipulation/insider-trading cases, so
a human can investigate further. It does not establish wrongdoing.

Two signals computed per ticker, per day:
  1. Volume anomaly: rolling z-score of volume vs trailing baseline.
     A spike means trading activity far outside the norm for that stock.
  2. Price-volume divergence: large single-day return co-occurring with
     a volume anomaly. This is the classic "something happened that the
     market knew about before it was public" pattern.

IMPORTANT CAVEAT: without disclosure/news timestamps (Phase 2), this
script cannot tell the difference between:
  - a real red flag (info leaked before public announcement), and
  - a routine, fully-explained event (rights issue, dividend, split).
So treat every flagged row as "needs manual research," not "confirmed
anomaly." Phase 2 will cross-reference BVMT's avis-décisions bulletin
to auto-distinguish explained vs unexplained spikes.

Usage:
    python src/detection/anomaly_detector.py
Reads bvmt_data/_all_tickers_full.csv, writes:
    bvmt_data/anomaly_flags.csv      (every flagged ticker/date)
    bvmt_data/anomaly_summary.csv    (one row per ticker, flag counts)
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = os.path.join("bvmt_data", "_all_tickers_full.csv")
OUT_FLAGS = os.path.join("bvmt_data", "anomaly_flags.csv")
OUT_SUMMARY = os.path.join("bvmt_data", "anomaly_summary.csv")
OUT_QUALITY = os.path.join("bvmt_data", "anomaly_data_quality.csv")

# Tickers to exclude from analysis entirely
EXCLUDE_TICKERS = ["TBIDX", "PLTU"]  # index + known-incomplete ticker

# Tuning parameters — these are reasonable starting points, not gospel.
# Tighten/loosen after seeing how many flags come out.
VOLUME_ROLLING_WINDOW = 60     # trading days for the volume baseline
VOLUME_Z_THRESHOLD = 3.0       # how many std devs above normal = anomaly
RETURN_Z_THRESHOLD = 3.0       # how many std devs of daily return = large move
MIN_HISTORY_DAYS = 60          # don't flag anything until baseline is established

# On very stable names, the trailing std can be near-zero, which would make
# the z-score blow up even for a small move. Flooring the std at a small value
# keeps the score interpretable without hiding genuine outliers.
MIN_LOG_VOLUME_STD = 0.10      # floor std of log(1+volume)
MIN_RETURN_STD = 0.01          # floor return std at 1% (absolute daily return)
MAX_RETURN_GAP_DAYS = 10       # beyond this, a "daily" return isn't really daily
OHLC_POLICIES = {"raw", "clamp_close", "quarantine"}


def ohlc_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Return row-level OHLC issues without modifying the supplied observations."""
    numeric = df[["ouverture", "haut", "bas", "cloture", "volume"]].apply(
        pd.to_numeric, errors="coerce"
    )
    invalid_range = numeric["bas"] > numeric["haut"]
    open_outside = (numeric["ouverture"] < numeric["bas"]) | (
        numeric["ouverture"] > numeric["haut"]
    )
    close_below = numeric["cloture"] < numeric["bas"]
    close_above = numeric["cloture"] > numeric["haut"]
    missing = numeric.isna().any(axis=1)
    negative = (numeric < 0).any(axis=1)
    affected = invalid_range | open_outside | close_below | close_above | missing | negative

    columns = [
        "symbole", "ticker_name", "date", "ouverture", "haut", "bas",
        "cloture", "volume",
    ]
    issues = df.loc[affected, columns].copy()
    if issues.empty:
        return issues.assign(issue_types=pd.Series(dtype=str), close_departure=pd.Series(dtype=float))

    def labels(index: int) -> str:
        values = []
        for mask, label in (
            (invalid_range, "LOW_ABOVE_HIGH"),
            (open_outside, "OPEN_OUTSIDE_RANGE"),
            (close_below, "CLOSE_BELOW_LOW"),
            (close_above, "CLOSE_ABOVE_HIGH"),
            (missing, "MISSING_OR_NON_NUMERIC_OHLCV"),
            (negative, "NEGATIVE_OHLCV"),
        ):
            if bool(mask.loc[index]):
                values.append(label)
        return "|".join(values)

    issues["issue_types"] = [labels(index) for index in issues.index]
    issues["close_departure"] = pd.concat(
        [
            (numeric.loc[affected, "bas"] - numeric.loc[affected, "cloture"]).clip(lower=0),
            (numeric.loc[affected, "cloture"] - numeric.loc[affected, "haut"]).clip(lower=0),
        ],
        axis=1,
    ).max(axis=1)
    return issues


def apply_ohlc_policy(
    df: pd.DataFrame, policy: str = "raw"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply an explicit OHLC policy and return data plus an auditable issue log.

    ``raw`` is the scientifically conservative default: source observations are
    retained verbatim. ``clamp_close`` reproduces the legacy close-only correction,
    while ``quarantine`` excludes every row with an OHLCV issue from analysis.
    """
    if policy not in OHLC_POLICIES:
        raise ValueError(f"Unknown OHLC policy {policy!r}; expected one of {sorted(OHLC_POLICIES)}")

    result = df.copy()
    issues = ohlc_quality_issues(result)
    issues["policy"] = policy
    issues["action"] = "retained_raw"
    if issues.empty:
        return result, issues

    if policy == "clamp_close":
        valid_range = result["bas"] <= result["haut"]
        result.loc[valid_range, "cloture"] = result.loc[
            valid_range, ["cloture", "bas"]
        ].max(axis=1)
        result.loc[valid_range, "cloture"] = result.loc[
            valid_range, ["cloture", "haut"]
        ].min(axis=1)
        issues["action"] = "close_clamped_where_range_valid"
    elif policy == "quarantine":
        result = result.drop(index=issues.index).copy()
        issues["action"] = "excluded_from_analysis"
    return result, issues


def load_data(path, ohlc_policy="raw", quality_log_path=None):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[~df["symbole"].isin(EXCLUDE_TICKERS)].copy()
    df = df.sort_values(["symbole", "date"]).reset_index(drop=True)
    df, issues = apply_ohlc_policy(df, ohlc_policy)
    if quality_log_path is not None:
        quality_path = Path(quality_log_path)
        quality_path.parent.mkdir(parents=True, exist_ok=True)
        issues.to_csv(quality_path, index=False)
    return df


def valid_prior_rolling_stats(
    values: pd.Series, window: int
) -> tuple[pd.Series, pd.Series]:
    """Mean/std of the last ``window`` valid values, excluding the current one."""
    valid_values = values.dropna()
    prior_valid_values = valid_values.shift(1)
    valid_mean = prior_valid_values.rolling(window, min_periods=window).mean()
    valid_std = prior_valid_values.rolling(window, min_periods=window).std()
    mean = pd.Series(np.nan, index=values.index, dtype=float)
    std = pd.Series(np.nan, index=values.index, dtype=float)
    mean.loc[valid_values.index] = valid_mean
    std.loc[valid_values.index] = valid_std
    return mean, std


def compute_signals(df):
    results = []

    for symbole, g in df.groupby("symbole"):
        g = g.sort_values("date").reset_index(drop=True)
        if len(g) < MIN_HISTORY_DAYS:
            continue  # too little history to establish a reliable baseline

        g["daily_return"] = g["cloture"].pct_change()

        # Illiquid BVMT names can go weeks or months between trades. pct_change()
        # just compares consecutive rows, so a stock reactivating after a long gap
        # gets its entire multi-month cumulative move treated as a single "daily"
        # return, which blows up return_zscore (seen: several names hitting
        # z=20-26 on their first trade back after 150+ day gaps, all on unrelated
        # dates — a data-gap artifact, not a same-day price move). Null out any
        # return computed across a gap larger than MAX_RETURN_GAP_DAYS so it
        # doesn't feed the z-score baseline or get flagged as a spike.
        gap_days = g["date"].diff().dt.days
        g.loc[gap_days > MAX_RETURN_GAP_DAYS, "daily_return"] = np.nan

        # Volume z-score vs trailing rolling window (excludes current day
        # from its own baseline via shift(1), avoiding look-ahead/self-bias).
        # Volume is log-transformed first: raw daily volume for a stock is
        # heavily right-skewed (long stretches near the typical level, with
        # occasional multi-hundred-x spikes), so a z-score on the raw values
        # isn't statistically meaningful — it produces implausible magnitudes
        # (e.g. Z=700+) on illiquid names instead of a real z-score, which
        # should rarely exceed ~10-15. log1p compresses that skew so the
        # z-score reflects how unusual the spike actually is.
        log_volume = np.log1p(g["volume"])
        roll_mean = log_volume.shift(1).rolling(
            VOLUME_ROLLING_WINDOW, min_periods=MIN_HISTORY_DAYS
        ).mean()
        roll_std = log_volume.shift(1).rolling(
            VOLUME_ROLLING_WINDOW, min_periods=MIN_HISTORY_DAYS
        ).std()
        roll_std_safe = roll_std.where(roll_std > MIN_LOG_VOLUME_STD, MIN_LOG_VOLUME_STD)
        g["volume_zscore"] = (log_volume - roll_mean) / roll_std_safe.replace(0, np.nan)

        # Return z-score vs the most recent valid returns. A NaN introduced for
        # a long trading gap is not a new observation and must not blank the
        # next 60 rows. Build the baseline on the compact sequence of valid
        # returns, still excluding the current return and requiring 60 prior
        # valid observations. This is a correctness rule, not event tuning.
        ret_roll_mean, ret_roll_std = valid_prior_rolling_stats(
            g["daily_return"], VOLUME_ROLLING_WINDOW
        )
        ret_std_safe = ret_roll_std.where(ret_roll_std > MIN_RETURN_STD, MIN_RETURN_STD)
        g["return_zscore"] = (g["daily_return"] - ret_roll_mean) / ret_std_safe.replace(0, np.nan)

        g["volume_anomaly"] = g["volume_zscore"] > VOLUME_Z_THRESHOLD
        g["price_anomaly"] = g["return_zscore"].abs() > RETURN_Z_THRESHOLD
        g["combined_anomaly"] = g["volume_anomaly"] & g["price_anomaly"]

        results.append(g)

    if not results:
        empty = df.iloc[0:0].copy()
        empty["daily_return"] = pd.Series(dtype=float)
        empty["volume_zscore"] = pd.Series(dtype=float)
        empty["return_zscore"] = pd.Series(dtype=float)
        empty["volume_anomaly"] = pd.Series(dtype=bool)
        empty["price_anomaly"] = pd.Series(dtype=bool)
        empty["combined_anomaly"] = pd.Series(dtype=bool)
        return empty
    return pd.concat(results, ignore_index=True)


def summarize(df):
    flagged = df[df["volume_anomaly"] | df["price_anomaly"]].copy()

    summary = (
        flagged.groupby("symbole")
        .agg(
            ticker_name=("ticker_name", "first"),
            volume_anomalies=("volume_anomaly", "sum"),
            price_anomalies=("price_anomaly", "sum"),
            combined_anomalies=("combined_anomaly", "sum"),
            first_flag=("date", "min"),
            last_flag=("date", "max"),
        )
        .reset_index()
        .sort_values("combined_anomalies", ascending=False)
    )
    return flagged, summary


if __name__ == "__main__":
    print("Loading and cleaning data...")
    df = load_data(DATA_PATH, ohlc_policy="raw", quality_log_path=OUT_QUALITY)
    print(f"  {df['symbole'].nunique()} tickers, {len(df)} rows after exclusions")

    print("\nComputing volume and price anomaly signals...")
    df = compute_signals(df)

    print("\nSummarizing flagged events...")
    flagged, summary = summarize(df)

    flagged_out = flagged[[
        "symbole", "ticker_name", "date", "cloture", "volume",
        "daily_return", "volume_zscore", "return_zscore",
        "volume_anomaly", "price_anomaly", "combined_anomaly",
    ]]
    flagged_out.to_csv(OUT_FLAGS, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    print(f"\n{len(flagged)} flagged rows across {summary.shape[0]} tickers.")
    print(f"  {flagged['combined_anomaly'].sum()} are COMBINED anomalies "
          f"(both volume spike + large price move same day — highest priority).")
    print(f"\nSaved: {OUT_FLAGS}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_QUALITY} (source rows retained; review before choosing another policy)")

    print("\nTop 10 tickers by combined anomaly count:")
    print(summary.head(10).to_string(index=False))

    print("\n--- VALIDATION CHECK ---")
    print("Search for 'TINV' or Tuninvest's actual ticker code in anomaly_flags.csv")
    print("for the Oct-Nov 2025 window. If flagged there, the detector correctly")
    print("caught the real documented case — strong validation signal.")
