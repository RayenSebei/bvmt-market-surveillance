"""Read-only presentation aggregates. Never recalculates detector flags."""

import numpy as np
import pandas as pd


def command_center(prices, flags, days):
    if prices.empty or not {"date", "symbole", "cloture", "volume"}.issubset(prices.columns):
        return {"error": "Historical price dataset is unavailable"}, 503

    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
    invalid_dates = int(prices["date"].isna().sum())
    duplicate_rows = int(prices.duplicated(["symbole", "date"]).sum())
    missing_values = int(prices[["cloture", "volume"]].isna().any(axis=1).sum())
    valid = prices.dropna(subset=["date", "symbole"]).sort_values("date")
    if valid.empty:
        return {"error": "No valid historical observation dates"}, 503
    as_of = valid["date"].max()
    start = as_of - pd.Timedelta(int(days - 1), unit="D")
    observed = valid[valid["date"] >= start]
    flags_available = {"date", "symbole", "volume_anomaly", "price_anomaly"}.issubset(flags.columns)
    if not flags_available:
        return {"error": "Stored detector flags are unavailable"}, 503
    flags = flags.copy()
    flags["date"] = pd.to_datetime(flags["date"], errors="coerce")
    flags = flags[(flags["date"] >= start) & (flags["date"] <= as_of)].copy()
    for column in ("volume_anomaly", "price_anomaly"):
        flags[column] = flags[column].astype(str).str.strip().str.lower().eq("true")
    flags = flags[flags["volume_anomaly"] | flags["price_anomaly"]].copy()
    for column in ("volume_zscore", "return_zscore"):
        if column not in flags:
            flags[column] = np.nan
        flags[column] = pd.to_numeric(flags[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    flags["max_zscore"] = flags[["volume_zscore", "return_zscore"]].abs().max(axis=1)
    flags["signal"] = np.select(
        [flags["volume_anomaly"] & flags["price_anomaly"], flags["volume_anomaly"]],
        ["Volume + price", "Volume"], default="Price",
    )

    counts = flags.groupby("symbole").size()
    peak = flags.groupby("symbole")["max_zscore"].max()
    latest = valid.drop_duplicates("symbole", keep="last")
    symbols = []
    for _, row in latest.iterrows():
        symbol = str(row["symbole"])
        symbols.append({
            "symbol": symbol,
            "name": str(row.get("ticker_name", symbol)),
            "last_date": row["date"].strftime("%Y-%m-%d"),
            "flags": int(counts.get(symbol, 0)),
            "max_zscore": float(peak[symbol]) if symbol in peak and pd.notna(peak[symbol]) else None,
        })
    symbols.sort(key=lambda row: (-row["flags"], row["symbol"]))

    daily = flags.groupby("date").size()
    # Only dates with observed source rows are filled with zero. No invented sessions.
    dates = sorted(set(observed["date"]) | set(flags["date"]))
    timeline = [{"date": date.strftime("%Y-%m-%d"), "count": int(daily.get(date, 0))} for date in dates]
    records = []
    for _, row in flags.sort_values(["date", "max_zscore"], ascending=[False, False]).iterrows():
        records.append({
            "symbol": str(row["symbole"]), "name": str(row.get("ticker_name", row["symbole"])),
            "date": row["date"].strftime("%Y-%m-%d"), "signal": row["signal"],
            "max_zscore": float(row["max_zscore"]) if pd.notna(row["max_zscore"]) else None,
            "volume_zscore": float(row["volume_zscore"]) if pd.notna(row["volume_zscore"]) else None,
            "return_zscore": float(row["return_zscore"]) if pd.notna(row["return_zscore"]) else None,
        })
    z = flags["max_zscore"]
    distribution = [
        {"label": "< 3σ", "count": int((z < 3).sum())},
        {"label": "3–4σ", "count": int(((z >= 3) & (z < 4)).sum())},
        {"label": "4–6σ", "count": int(((z >= 4) & (z < 6)).sum())},
        {"label": "6–10σ", "count": int(((z >= 6) & (z < 10)).sum())},
        {"label": "≥ 10σ", "count": int((z >= 10).sum())},
        {"label": "Unscored", "count": int(z.isna().sum())},
    ]
    return {
        "as_of": as_of.strftime("%Y-%m-%d"), "start": start.strftime("%Y-%m-%d"),
        "data_start": valid["date"].min().strftime("%Y-%m-%d"), "days": days,
        "metrics": {"symbols": len(symbols), "observations": len(valid), "window_observations": len(observed),
                    "flags": len(flags), "flagged_symbols": int(flags["symbole"].nunique()),
                    "high_intensity": int((z >= 4).sum())},
        "quality": {"invalid_dates": invalid_dates, "duplicate_rows": duplicate_rows,
                    "missing_price_or_volume": missing_values,
                    "symbols_at_as_of": int((latest["date"] == as_of).sum()),
                    "lagging_symbols": int((latest["date"] < as_of).sum())},
        "symbols": symbols, "timeline": timeline, "anomalies": records,
        "distribution": distribution,
    }, 200
