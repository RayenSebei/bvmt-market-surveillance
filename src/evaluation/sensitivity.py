"""Report, but do not tune, detector sensitivity over fixed parameter grids."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.detection.anomaly_detector import (
    MAX_RETURN_GAP_DAYS, MIN_LOG_VOLUME_STD, MIN_RETURN_STD,
)
from src.evaluation.evaluate import (
    OUTPUT_DIR, eligible_positive_events, event_hits, flags_per_ticker_year,
    load_config, load_inputs,
)


def parameter_flags(trading: pd.DataFrame, window: int, cutoff: float) -> pd.DataFrame:
    frames = []
    for _, group in trading.groupby("symbole"):
        group = group.sort_values("date").copy()
        if len(group) < 60:
            continue
        group["daily_return"] = group["cloture"].pct_change()
        group.loc[group["date"].diff().dt.days > MAX_RETURN_GAP_DAYS, "daily_return"] = np.nan
        log_volume = np.log1p(group["volume"])
        volume_mean = log_volume.shift(1).rolling(window, min_periods=20).mean()
        volume_std = log_volume.shift(1).rolling(window, min_periods=20).std().clip(lower=MIN_LOG_VOLUME_STD)
        return_mean = group["daily_return"].shift(1).rolling(window, min_periods=20).mean()
        return_std = group["daily_return"].shift(1).rolling(window, min_periods=20).std().clip(lower=MIN_RETURN_STD)
        group["volume_zscore"] = (log_volume - volume_mean) / volume_std
        group["return_zscore"] = (group["daily_return"] - return_mean) / return_std
        frames.append(group[(group["volume_zscore"] > cutoff) | (group["return_zscore"].abs() > cutoff)])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def write_heatmap(table: pd.DataFrame, event_count: int) -> None:
    windows = sorted(table["rolling_window"].unique())
    cutoffs = sorted(table["z_cutoff"].unique())
    cells = []
    for row_i, cutoff in enumerate(cutoffs):
        for col_i, window in enumerate(windows):
            row = table[(table["z_cutoff"] == cutoff) & (table["rolling_window"] == window)].iloc[0]
            recall = 0 if pd.isna(row["recall_30d"]) else float(row["recall_30d"])
            shade = int(235 - 150 * recall)
            hit_count = recall * event_count
            hit_label = f"{int(round(hit_count))} of {event_count}" if abs(hit_count - round(hit_count)) < 1e-9 else f"{hit_count:.3f} of {event_count}"
            x, y = 170 + col_i * 120, 95 + row_i * 55
            cells.append(f'<rect x="{x}" y="{y}" width="112" height="47" rx="4" fill="rgb({shade},{min(245,shade+35)},{min(245,shade+30)})"/><text x="{x+56}" y="{y+29}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">{hit_label}</text>')
    xlabels = ''.join(f'<text x="{226+i*120}" y="82" text-anchor="middle" font-family="Arial" font-size="13">{w} days</text>' for i,w in enumerate(windows))
    ylabels = ''.join(f'<text x="150" y="{125+i*55}" text-anchor="end" font-family="Arial" font-size="13">z = {c:g}</text>' for i,c in enumerate(cutoffs))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360"><rect width="100%" height="100%" fill="#f8fafc"/><text x="30" y="36" font-family="Arial" font-size="22" font-weight="700">Sensitivity: 30-day event hits</text><text x="30" y="58" font-family="Arial" font-size="13" fill="#64748b">Reporting grid only; reference parameters remain z=3 and 60 days.</text>{xlabels}{ylabels}{"".join(cells)}</svg>'
    (OUTPUT_DIR / "sensitivity_heatmap.svg").write_text(svg, encoding="utf-8")


def main() -> int:
    config = load_config()
    trading, _, events = load_inputs()
    positives = eligible_positive_events(trading, events, config["primary_window_days_before"])
    rows = []
    for cutoff in config["sensitivity_z_cutoffs"]:
        for window in config["sensitivity_rolling_windows"]:
            flags = parameter_flags(trading, int(window), float(cutoff))
            hits = event_hits(flags, positives, config["primary_window_days_before"], config["window_days_after"])
            rows.append({
                "z_cutoff": cutoff, "rolling_window": window,
                "flag_count": len(flags),
                "flags_per_ticker_year": flags_per_ticker_year(flags, trading),
                "recall_30d": hits["hit"].mean() if len(hits) else np.nan,
            })
    table = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "sensitivity.csv", index=False)
    write_heatmap(table, len(positives))
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
