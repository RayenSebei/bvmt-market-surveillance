"""Pre-registered Phase 2 screening variants; reference_v1 is never changed."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

INDEXES = {"PX1", "TBIDX", "PLTU"}


@dataclass(frozen=True)
class CandidateSettings:
    window: int = 60
    robust_volume_floor: float = 0.10
    return_floor: float = 0.01
    gap_days: int = 10
    activity_days: int = 20
    median_volume: float = 400.0
    persistence_days: int = 10
    market_wide_count: int = 10


def _prior_robust(values: pd.Series, window: int, floor: float) -> pd.Series:
    """Median/MAD of prior valid observations, with no current-row leakage."""
    valid = values.dropna()
    shifted = valid.shift(1)
    median = shifted.rolling(window, min_periods=window).median()
    mad = shifted.rolling(window, min_periods=window).apply(
        lambda a: np.median(np.abs(a - np.median(a))), raw=True
    )
    out = pd.Series(np.nan, index=values.index, dtype=float)
    out.loc[valid.index] = (valid - median) / (1.4826 * mad).clip(lower=floor)
    return out


def _prior_mean_z(values: pd.Series, window: int, floor: float) -> pd.Series:
    valid = values.dropna()
    shifted = valid.shift(1)
    mean = shifted.rolling(window, min_periods=window).mean()
    std = shifted.rolling(window, min_periods=window).std().clip(lower=floor)
    out = pd.Series(np.nan, index=values.index, dtype=float)
    out.loc[valid.index] = (valid - mean) / std
    return out


def score_trading(trading: pd.DataFrame, settings: CandidateSettings = CandidateSettings()) -> pd.DataFrame:
    """Point-in-time scores for each company observation, using exact-date PX1."""
    data = trading.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["symbole", "date"]).reset_index(drop=True)
    data["return"] = data.groupby("symbole")["cloture"].pct_change(fill_method=None)
    gaps = data.groupby("symbole")["date"].diff().dt.days
    data.loc[gaps > settings.gap_days, "return"] = np.nan
    market = data.loc[data["symbole"].eq("PX1"), ["date", "return"]].drop_duplicates("date")
    market = market.rename(columns={"return": "market_return"})
    data = data.loc[~data["symbole"].isin(INDEXES)].merge(market, on="date", how="left")
    data["excess_return"] = data["return"] - data["market_return"]
    blocks = []
    for _, group in data.groupby("symbole", sort=False):
        group = group.copy()
        group["robust_volume_z"] = _prior_robust(np.log1p(group["volume"].clip(lower=0)), settings.window, settings.robust_volume_floor)
        group["robust_return_z"] = _prior_robust(group["return"], settings.window, settings.return_floor)
        group["excess_return_z"] = _prior_mean_z(group["excess_return"], settings.window, settings.return_floor)
        prior_volume = group["volume"].shift(1).rolling(settings.window, min_periods=settings.window)
        group["prior_active_days"] = prior_volume.apply(lambda a: (a > 0).sum(), raw=True)
        group["prior_median_volume"] = prior_volume.median()
        blocks.append(group)
    return pd.concat(blocks, ignore_index=True) if blocks else data


def _dates(df: pd.DataFrame) -> pd.DataFrame:
    return df[["symbole", "date"]].drop_duplicates().sort_values(["date", "symbole"]).reset_index(drop=True)


def decay_point_in_time(trading: pd.DataFrame) -> pd.DataFrame:
    """Existing decay rule recomputed at month ends from information then available."""
    data = trading.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.loc[~data["symbole"].isin(INDEXES)].sort_values(["symbole", "date"])
    if data.empty:
        return _dates(data)
    month_ends = pd.date_range(data["date"].min(), data["date"].max(), freq="ME")
    rows = []
    for symbol, group in data.groupby("symbole"):
        for end in month_ends:
            history = group[group["date"] <= end]
            prior = history[(history["date"] > end - pd.DateOffset(months=12)) & (history["date"] <= end - pd.DateOffset(months=6))]
            recent = history[history["date"] > end - pd.DateOffset(months=6)]
            if prior.empty or recent.empty or prior["volume"].mean() < 1000:
                continue
            ratio = recent["volume"].mean() / prior["volume"].mean()
            positive = history.loc[history["volume"] > 0, "date"]
            inactivity = (end - positive.max()).days if len(positive) else 9999
            if ratio < 0.2 or inactivity >= 90:
                rows.append({"symbole": symbol, "date": end})
    return _dates(pd.DataFrame(rows, columns=["symbole", "date"]))


def candidate_flags(trading: pd.DataFrame, reference: pd.DataFrame, settings: CandidateSettings = CandidateSettings()) -> dict[str, pd.DataFrame]:
    scores = score_trading(trading, settings)
    ref = reference.copy()
    ref["date"] = pd.to_datetime(ref["date"])
    ref_stock = ref.loc[~ref["symbole"].isin(INDEXES)]
    robust = (scores["robust_volume_z"] > 3) | (scores["robust_return_z"].abs() >= 3)
    robust4 = (scores["robust_volume_z"] > 4) | (scores["robust_return_z"].abs() >= 4)
    excess = scores["excess_return_z"].abs() >= 3
    activity = scores[["symbole", "date", "volume", "prior_active_days", "prior_median_volume"]]
    activity = ref_stock.merge(activity, on=["symbole", "date"], how="inner")
    activity = activity[(activity["volume_y"] > 0) & (activity["prior_active_days"] >= settings.activity_days) & (activity["prior_median_volume"] >= settings.median_volume)]
    persistence = ref_stock.sort_values(["symbole", "date"]).copy()
    previous = persistence.groupby("symbole")["date"].shift(1)
    persistence = persistence[(persistence["date"] - previous).dt.days.le(settings.persistence_days)]
    market_counts = ref_stock.groupby("date")["symbole"].nunique()
    market_tag = ref_stock[["symbole", "date"]].copy()
    market_tag["market_wide"] = market_tag["date"].map(market_counts).ge(settings.market_wide_count)
    return {
        "robust_z3": _dates(scores.loc[robust]),
        "robust_z4": _dates(scores.loc[robust4]),
        "market_adjusted_z3": _dates(scores.loc[excess]),
        "activity_filtered_v1": _dates(activity),
        "persistent_v1": _dates(persistence),
        "decay_point_in_time": decay_point_in_time(trading),
        "market_wide_tag": market_tag.sort_values(["date", "symbole"]).reset_index(drop=True),
    }
