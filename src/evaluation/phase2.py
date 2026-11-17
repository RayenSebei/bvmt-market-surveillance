"""Frozen-split Phase 2 comparison of all registered screening methods."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.detection.candidates_v2 import INDEXES, candidate_flags, score_trading
from src.evaluation.evaluate import coverage_table, event_hits, ranked_flags

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/evaluation"
SEED = 20261006


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return max(0.0, center - half), min(1.0, center + half)


def _keys(df: pd.DataFrame) -> pd.DataFrame:
    return df[["symbole", "date"]].drop_duplicates().sort_values(["date", "symbole"]).reset_index(drop=True)


def _events(events: pd.DataFrame, trading: pd.DataFrame, lookback: int = 30) -> pd.DataFrame:
    coverage = coverage_table(trading, events, lookback)
    covered = f"has_{lookback}d_window_coverage"
    e = events.merge(coverage[["event_id", covered]], on="event_id")
    e["include_headline"] = e["include_headline"].astype(str).str.lower().eq("true")
    return e[e["label_role"].eq("positive") & e["include_headline"] & e["source"].ne("SOURCE_NEEDED") & e["event_date"].notna() & e[covered]]


def _hit_ids(flags: pd.DataFrame, events: pd.DataFrame, before: int = 30) -> set[str]:
    if events.empty:
        return set()
    return set(event_hits(flags, events, before, 5).loc[lambda d: d["hit"], "event_id"])


def _neg_count(flags: pd.DataFrame, negatives: pd.DataFrame) -> int:
    if flags.empty or negatives.empty:
        return 0
    matched = pd.Series(False, index=flags.index)
    for event in negatives.itertuples():
        date = pd.Timestamp(event.event_date)
        matched |= flags["symbole"].eq(event.ticker) & flags["date"].between(date - pd.Timedelta(days=30), date + pd.Timedelta(days=5))
    return int(matched.sum())


def _neg_count_collapsed(flags: pd.DataFrame, negatives: pd.DataFrame) -> int:
    """Count the shared PGH/LNDOR notice once, using the larger ticker flag count."""
    correlated = {"PGH-2026-buyout", "LNDOR-2026-buyout"}
    separate = negatives[~negatives["event_id"].isin(correlated)]
    members = negatives[negatives["event_id"].isin(correlated)]
    return _neg_count(flags, separate) + max(
        (_neg_count(flags, members[members["event_id"].eq(event_id)]) for event_id in correlated),
        default=0,
    )


def _random_flags(observed: pd.DataFrame, method: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    dates_by_symbol = {s: g["date"].to_numpy() for s, g in observed.groupby("symbole")}
    rows = []
    for symbol, count in method.groupby("symbole").size().items():
        dates = dates_by_symbol.get(symbol)
        if dates is None or len(dates) == 0:
            continue
        chosen = rng.choice(dates, size=min(count, len(dates)), replace=False)
        rows.extend((symbol, pd.Timestamp(d)) for d in chosen)
    return pd.DataFrame(rows, columns=["symbole", "date"])


def permutation(flags: pd.DataFrame, observed: pd.DataFrame, events: pd.DataFrame, seeds: int = 1000) -> tuple[float, float]:
    if events.empty:
        return np.nan, np.nan
    actual = len(_hit_ids(flags, events))
    rng = np.random.default_rng(SEED)
    simulations = np.zeros(seeds, dtype=int)
    for symbol, symbol_events in events.groupby("ticker"):
        dates = observed.loc[observed["symbole"].eq(symbol), "date"].to_numpy(dtype="datetime64[ns]")
        count = int(flags["symbole"].eq(symbol).sum())
        if len(dates) == 0 or count == 0:
            continue
        count = min(count, len(dates))
        masks = [((dates >= (pd.Timestamp(e.event_date) - pd.Timedelta(days=30)).to_datetime64()) &
                  (dates <= (pd.Timestamp(e.event_date) + pd.Timedelta(days=5)).to_datetime64()))
                 for e in symbol_events.itertuples()]
        for i in range(seeds):
            chosen = rng.choice(len(dates), size=count, replace=False)
            simulations[i] += sum(bool(mask[chosen].any()) for mask in masks)
    counts = simulations
    return float(counts.mean()), float((1 + (counts >= actual).sum()) / (seeds + 1))


def paired_bootstrap(a: set[str], b: set[str], ids: list[str], samples: int = 10000) -> tuple[float, float]:
    if not ids:
        return np.nan, np.nan
    diff = np.array([int(i in a) - int(i in b) for i in ids])
    draws = np.random.default_rng(SEED).choice(diff, size=(samples, len(ids)), replace=True).mean(axis=1)
    return tuple(float(x) for x in np.quantile(draws, [0.025, 0.975]))


def main(trading_path: Path = ROOT / "bvmt_data/_all_tickers_full.csv",
         reference_path: Path = ROOT / "bvmt_data/anomaly_flags.csv",
         events_path: Path = ROOT / "data/evaluation/events.csv", out: Path = OUT) -> int:
    trading = pd.read_csv(trading_path, parse_dates=["date"])
    ref = pd.read_csv(reference_path, parse_dates=["date"])
    events = pd.read_csv(events_path)
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    positive = _events(events, trading)
    positive60 = _events(events, trading, 60)
    negative = events[events["label_role"].eq("negative") & events["event_date"].notna() & events["source"].ne("SOURCE_NEEDED")]
    candidate = candidate_flags(trading, ref)
    scored = score_trading(trading)
    stock_ref = ref[~ref["symbole"].isin(INDEXES)]
    ranked = ranked_flags(ref)
    ranked["month"] = ranked["date"].dt.to_period("M")
    top_month = ranked[~ranked["symbole"].isin(INDEXES)].groupby("month", sort=True).head(2)
    # The frozen reference includes PX1 rows; preserve their per-symbol count
    # in the registered random baseline even though candidates exclude indices.
    observed = _keys(trading[~trading["symbole"].isin({"TBIDX", "PLTU"})])
    methods = {
        "reference_v1": _keys(ref),
        "volume_only": _keys(ref[ref["volume_anomaly"].astype(str).str.lower().eq("true")]),
        "return_only": _keys(ref[ref["price_anomaly"].astype(str).str.lower().eq("true")]),
        "market_adjusted_return_only": _keys(scored[scored["excess_return_z"].abs() >= 3]),
        "simple_volume_spike": _keys(scored[(scored["volume"] > 0) & (scored["prior_median_volume"] >= 400) & (scored["volume"] >= 5 * scored["prior_median_volume"])]),
        "top_2_per_month": _keys(top_month),
        **{name: _keys(value) for name, value in candidate.items() if name != "market_wide_tag"},
    }
    methods["same_count_random"] = _keys(_random_flags(observed, methods["reference_v1"], np.random.default_rng(SEED)))
    cut = pd.Timestamp("2025-01-01")
    dev = positive[positive["event_date"] < cut]
    hold = positive[positive["event_date"] >= cut]
    dev60 = positive60[positive60["event_date"] < cut]
    hold60 = positive60[positive60["event_date"] >= cut]
    dev_negative = negative[negative["event_date"] < cut]
    hold_negative = negative[negative["event_date"] >= cut]
    candidate_names = [x for x in candidate if x != "market_wide_tag"]
    dev_hits = {name: _hit_ids(methods[name], dev) for name in methods}
    # Selection is entirely development-based. Persist it before touching held-out hits.
    def workload(name: str, start: pd.Timestamp, end: pd.Timestamp) -> float:
        count = int(methods[name]["date"].between(start, end).sum())
        return count / max((end - start).days / 7, 1)
    dev_start, dev_end = pd.Timestamp(observed["date"].min()), cut - pd.Timedelta(days=1)
    hold_start, hold_end = cut, pd.Timestamp(observed["date"].max())
    choice = sorted(candidate_names, key=lambda n: (-len(dev_hits[n]), workload(n, dev_start, dev_end), _neg_count(methods[n], dev_negative), n))[0]
    baseline_names = ["volume_only", "return_only", "market_adjusted_return_only", "simple_volume_spike", "top_2_per_month"]
    best_baseline = sorted(baseline_names, key=lambda n: (-len(dev_hits[n]), workload(n, dev_start, dev_end), n))[0]
    out.mkdir(parents=True, exist_ok=True)
    lock = {"split_date": "2025-01-01", "selected_candidate": choice, "selected_baseline": best_baseline,
            "selection_basis": "development recall, then flags/week, then negative-control flag count, then ID", "candidate_variants": candidate_names}
    lock_path = out / "phase2_selection_lock.json"
    if lock_path.exists():
        previous = json.loads(lock_path.read_text(encoding="utf-8"))
        if previous != lock:
            old_basis = "development recall, then flags/week, then negative-control event count, then ID"
            if previous.get("selection_basis") == old_basis and {k: v for k, v in previous.items() if k != "selection_basis"} == {k: v for k, v in lock.items() if k != "selection_basis"}:
                lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
            else:
                raise ValueError("Phase 2 development selection changed; investigate before held-out scoring")
    else:
        lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    hold_hits = {name: _hit_ids(methods[name], hold) for name in methods}
    table = []
    detail = []
    for name, flags in methods.items():
        for split, e, negatives, hits, start, end in (("dev", dev, dev_negative, dev_hits[name], dev_start, dev_end), ("held_out", hold, hold_negative, hold_hits[name], hold_start, hold_end)):
            n, k = len(e), len(hits)
            low, high = wilson(k, n)
            period_flags = flags[flags["date"].between(start, end)]
            null_mean, pvalue = permutation(period_flags, observed[observed["date"].between(start, end)], e)
            e60 = dev60 if split == "dev" else hold60
            hits60 = _hit_ids(flags, e60, before=60)
            low60, high60 = wilson(len(hits60), len(e60))
            table.append({"method": name, "split": split, "hits": k, "events": n, "recall": k / n if n else np.nan,
                "wilson_low": low, "wilson_high": high, "secondary_hits": len(hits60), "secondary_events": len(e60),
                "secondary_wilson_low": low60, "secondary_wilson_high": high60,
                "flags": len(period_flags), "flags_per_week": workload(name, start, end),
                "negative_control_flags": _neg_count(flags, negatives),
                "negative_control_flags_collapsed": _neg_count_collapsed(flags, negatives),
                "random_mean_hits": null_mean, "permutation_p": pvalue})
            if not e.empty:
                h = event_hits(flags, e, 30, 5)
                h.insert(0, "split", split)
                h.insert(0, "method", name)
                detail.append(h)
    result = pd.DataFrame(table)
    result.to_csv(out / "phase2_comparison.csv", index=False)
    pd.concat(detail, ignore_index=True).to_csv(out / "phase2_event_hits.csv", index=False)
    candidate_ci = paired_bootstrap(hold_hits[choice], hold_hits["reference_v1"], hold["event_id"].tolist())
    baseline_ci = paired_bootstrap(hold_hits[choice], hold_hits[best_baseline], hold["event_id"].tolist())
    adopt = (len(hold) >= 10 and candidate_ci[0] > 0 and baseline_ci[0] > 0
             and workload(choice, hold_start, hold_end) <= workload("reference_v1", hold_start, hold_end)
             and _neg_count(methods[choice], hold_negative) <= _neg_count(methods["reference_v1"], hold_negative))
    verdict = {**lock, "held_out_positives": len(hold), "candidate_minus_reference_bootstrap_95": candidate_ci,
               "candidate_minus_baseline_bootstrap_95": baseline_ci, "adopt_candidate": bool(adopt),
               "market_wide_tagged": int(candidate["market_wide_tag"]["market_wide"].sum()),
               "market_wide_total": len(candidate["market_wide_tag"])}
    (out / "phase2_verdict.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(result.to_string(index=False))
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
