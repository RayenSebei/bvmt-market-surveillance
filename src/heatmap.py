"""Read-only aggregates for the stored BVMT market map."""

import math

import pandas as pd


def _finite(value):
    if pd.isna(value):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def build_heatmap(prices: pd.DataFrame, flags: pd.DataFrame, timeframe: str) -> dict:
    if prices.empty or not {"symbole", "date", "cloture", "volume"}.issubset(prices.columns):
        return {"error": "Historical price dataset is unavailable"}
    rows = prices.copy()
    rows["date"] = pd.to_datetime(rows["date"], errors="coerce")
    rows["cloture"] = pd.to_numeric(rows["cloture"], errors="coerce")
    rows["volume"] = pd.to_numeric(rows["volume"], errors="coerce")
    rows = rows.dropna(subset=["symbole", "date"]).sort_values(["symbole", "date"])
    if rows.empty:
        return {"error": "No valid historical observation dates"}
    as_of = rows["date"].max()
    end = as_of.strftime("%Y-%m-%d")
    recent_flags = flags.copy()
    if {"symbole", "date"}.issubset(recent_flags.columns):
        recent_flags["date"] = pd.to_datetime(recent_flags["date"], errors="coerce")
        recent_flags = recent_flags[
            (recent_flags["date"] > as_of - pd.Timedelta(days=30))
            & (recent_flags["date"] <= as_of)
        ]
        if {"volume_anomaly", "price_anomaly"}.issubset(recent_flags.columns):
            triggered = recent_flags["volume_anomaly"].astype(str).str.lower().eq("true") | recent_flags[
                "price_anomaly"
            ].astype(str).str.lower().eq("true")
            recent_flags = recent_flags[triggered]
    else:
        recent_flags = pd.DataFrame(columns=["symbole"])
    for column in ("volume_zscore", "return_zscore"):
        recent_flags[column] = pd.to_numeric(recent_flags.get(column), errors="coerce")
    recent_flags["max_abs_z"] = recent_flags[["volume_zscore", "return_zscore"]].abs().max(axis=1)
    flag_count = recent_flags.groupby("symbole").size()
    flag_peak = recent_flags.groupby("symbole")["max_abs_z"].max()
    result = []
    for symbol, group in rows.groupby("symbole", sort=True):
        # These stored index series are not traded company shares; their volume
        # cannot be compared with stock turnover in a market-size map.
        if symbol in {"PX1", "TBIDX"}:
            continue
        group = group.sort_values("date").drop_duplicates("date", keep="last")
        last = group.iloc[-1]
        traded = bool(last["date"] == as_of)
        valid_close = group.dropna(subset=["cloture"])
        if timeframe == "YTD":
            base = valid_close[valid_close["date"].dt.year < as_of.year].tail(1)
        else:
            offset = {"1D": 2, "1W": 6, "1M": 22}[timeframe]
            base = valid_close.iloc[-offset:-offset + 1] if len(valid_close) >= offset else valid_close.iloc[0:0]
        current = _finite(last["cloture"])
        prior = _finite(base.iloc[0]["cloture"]) if not base.empty else None
        change = (current / prior - 1) * 100 if traded and current is not None and prior not in (None, 0) else None
        values = group.tail(20).copy()
        values["traded_value"] = values["cloture"] * values["volume"]
        average = values["traded_value"].replace([float("inf"), -float("inf")], float("nan")).mean()
        name = last.get("ticker_name")
        result.append({
            "symbol": str(symbol),
            "name": str(name) if pd.notna(name) and str(name).strip() else str(symbol),
            "last_date": last["date"].strftime("%Y-%m-%d"),
            "close": current,
            "change_pct": _finite(change),
            "avg_traded_value_20d": _finite(average),
            "traded_on_asof": traded,
            "flags_30d": int(flag_count.get(symbol, 0)),
            "max_abs_z_30d": _finite(flag_peak.get(symbol, float("nan"))),
        })
    return {"as_of": end, "symbols": result}
