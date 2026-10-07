"""Compare the reference screen with simple volume, return, and random baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.evaluation.evaluate import (
    OUTPUT_DIR, eligible_positive_events, event_hits, flags_per_ticker_year,
    load_config, load_inputs, negative_control_count, precision_at_k,
)


def draw_random_flags(candidate_dates, counts, rng):
    symbols, dates, scores = [], [], []
    for ticker, count in counts.items():
        candidates = candidate_dates[ticker]
        take = min(int(count), len(candidates))
        indexes = rng.choice(len(candidates), size=take, replace=False)
        symbols.extend([ticker] * take)
        dates.extend(candidates[indexes])
        scores.extend(rng.random(take))
    return (
        np.asarray(symbols, dtype=object),
        np.asarray(dates, dtype="datetime64[ns]"),
        np.asarray(scores),
    )


def window_flag_counts_numpy(symbols, dates, event_windows):
    return [
        int(np.sum((symbols == ticker) & (dates >= start) & (dates <= end)))
        for ticker, start, end in event_windows
    ]


def method_row(name, flags, trading, positives30, positives60, events, config):
    before = config["primary_window_days_before"]
    secondary = config["secondary_window_days_before"]
    after = config["window_days_after"]
    hit30 = event_hits(flags, positives30, before, after)
    hit60 = event_hits(flags, positives60, secondary, after)
    p20 = precision_at_k(flags, positives30, before, after, [20]).iloc[0]["precision_at_k"]
    return {
        "method": name, "flag_count": len(flags),
        "flags_per_ticker_year": flags_per_ticker_year(flags, trading),
        "recall_30d": hit30["hit"].mean() if len(hit30) else np.nan,
        "recall_60d": hit60["hit"].mean() if len(hit60) else np.nan,
        "precision_at_20": p20,
        "negative_control_flags_30d": negative_control_count(flags, events, before, after),
    }


def random_average(trading, reference, positives30, positives60, events, config):
    rng = np.random.default_rng(20261006)
    counts = reference.groupby("symbole").size().to_dict()
    candidate_dates = {
        ticker: group["date"].to_numpy()
        for ticker, group in trading.groupby("symbole")
        if ticker in counts
    }
    constant_flag_rate = flags_per_ticker_year(reference, trading)
    before = int(config["primary_window_days_before"])
    secondary = int(config["secondary_window_days_before"])
    after = int(config["window_days_after"])

    def windows(frame, days_before):
        result = []
        for row in frame.itertuples(index=False):
            event_date = pd.Timestamp(row.event_date)
            result.append((
                row.ticker,
                np.datetime64(event_date - pd.Timedelta(days=days_before)),
                np.datetime64(event_date + pd.Timedelta(days=after)),
            ))
        return result

    positive30_windows = windows(positives30, before)
    positive60_windows = windows(positives60, secondary)
    negative_windows = windows(
        events[events["label_role"].eq("negative") & events["event_date"].notna()], before
    )
    rows = []
    for _ in range(int(config["random_seeds"])):
        symbol_array, date_array, score_array = draw_random_flags(
            candidate_dates, counts, rng
        )

        def event_recall(event_windows):
            if not event_windows:
                return np.nan
            hits = [count > 0 for count in window_flag_counts_numpy(symbol_array, date_array, event_windows)]
            return float(np.mean(hits))

        top_indexes = np.argsort(score_array)[::-1][:20]
        top_matches = 0
        for index in top_indexes:
            if any(
                symbol_array[index] == ticker and start <= date_array[index] <= end
                for ticker, start, end in positive30_windows
            ):
                top_matches += 1
        negative_count = sum(window_flag_counts_numpy(symbol_array, date_array, negative_windows))
        rows.append({
            "flag_count": len(symbol_array),
            "flags_per_ticker_year": constant_flag_rate,
            "recall_30d": event_recall(positive30_windows),
            "recall_60d": event_recall(positive60_windows),
            "precision_at_20": top_matches / len(top_indexes) if len(top_indexes) else np.nan,
            "negative_control_flags_30d": negative_count,
        })
    averaged = pd.DataFrame(rows).mean(numeric_only=True).to_dict()
    averaged["method"] = f"random_same_count_mean_{config['random_seeds']}_seeds"
    return averaged


def write_baseline_svg(table: pd.DataFrame):
    width, height = 820, 330
    bars = []
    colors = ["#0f766e", "#2563eb", "#7c3aed", "#94a3b8"]
    for i, row in table.reset_index(drop=True).iterrows():
        value = 0.0 if pd.isna(row["recall_30d"]) else float(row["recall_30d"])
        x = 70 + i * 180
        bar_height = 190 * value
        bars.append(f'<rect x="{x}" y="{260-bar_height:.1f}" width="110" height="{bar_height:.1f}" rx="6" fill="{colors[i]}"/><text x="{x+55}" y="{285}" text-anchor="middle" font-family="Arial" font-size="12" fill="#334155">{row["method"][:18]}</text><text x="{x+55}" y="{245-bar_height:.1f}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#0f172a">{value:.0%}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#f8fafc"/><text x="36" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#0f172a">30-day recall by method</text><text x="36" y="62" font-family="Arial" font-size="13" fill="#64748b">Tiny source-backed set; comparisons are descriptive, not conclusive.</text><line x1="40" y1="260" x2="790" y2="260" stroke="#cbd5e1"/>{"".join(bars)}</svg>'
    (OUTPUT_DIR / "baseline_comparison.svg").write_text(svg, encoding="utf-8")


def main() -> int:
    config = load_config()
    trading, reference, events = load_inputs()
    before, secondary = config["primary_window_days_before"], config["secondary_window_days_before"]
    positives30 = eligible_positive_events(trading, events, before)
    positives60 = eligible_positive_events(trading, events, secondary)
    volume = reference[reference["volume_anomaly"].astype(str).str.lower().eq("true")].copy()
    returns = reference[reference["price_anomaly"].astype(str).str.lower().eq("true")].copy()
    rows = [
        method_row("reference_union", reference, trading, positives30, positives60, events, config),
        method_row("volume_zscore_only", volume, trading, positives30, positives60, events, config),
        method_row("absolute_return_only", returns, trading, positives30, positives60, events, config),
        random_average(trading, reference, positives30, positives60, events, config),
    ]
    table = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "baseline_comparison.csv", index=False)
    write_baseline_svg(table)
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
