"""Audit observations added since a preserved pre-refresh snapshot.

The audit is read-only with respect to market data. It lists newly appended
rows that have an OHLC inconsistency, zero volume, or an absolute close-to-close
return above 15%, then records whether the current detector flagged the row.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.detection.anomaly_detector import ohlc_quality_issues


DERIVED_STEMS = {
    "anomaly_classified",
    "anomaly_data_quality",
    "anomaly_flags",
    "anomaly_summary",
    "decay_classified",
    "decay_flags",
    "labeled_events",
    "watchlist",
    "watchlist_ai_assessed",
    "watchlist_refined",
}


def source_price_files(data_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(data_dir.glob("*.csv"))
        if not path.name.startswith(("_", "news_")) and path.stem not in DERIVED_STEMS
    ]


def build_audit(data_dir: Path, snapshot_dir: Path) -> pd.DataFrame:
    additions: list[pd.DataFrame] = []
    for current_path in source_price_files(data_dir):
        snapshot_path = snapshot_dir / current_path.name
        if not snapshot_path.exists():
            continue
        current = pd.read_csv(current_path)
        previous = pd.read_csv(snapshot_path)
        current["date"] = pd.to_datetime(current["date"])
        previous["date"] = pd.to_datetime(previous["date"])
        old_keys = set(zip(previous["symbole"].astype(str), previous["date"]))
        is_new = [
            (str(symbol), date) not in old_keys
            for symbol, date in zip(current["symbole"], current["date"])
        ]
        new_rows = current.loc[is_new].copy()
        if new_rows.empty:
            continue
        ordered = current.sort_values("date").copy()
        ordered["daily_return"] = pd.to_numeric(
            ordered["cloture"], errors="coerce"
        ).pct_change(fill_method=None)
        new_rows = new_rows.merge(
            ordered[["symbole", "date", "daily_return"]],
            on=["symbole", "date"],
            how="left",
        )
        additions.append(new_rows)

    if not additions:
        return pd.DataFrame()

    added = pd.concat(additions, ignore_index=True)
    issue_rows = ohlc_quality_issues(added.drop(columns=["daily_return"]))
    issue_map = {
        (str(row.symbole), pd.Timestamp(row.date)): row.issue_types
        for row in issue_rows.itertuples()
    }
    added["ohlc_issue"] = [
        issue_map.get((str(symbol), pd.Timestamp(date)), "")
        for symbol, date in zip(added["symbole"], added["date"])
    ]
    added["zero_volume"] = pd.to_numeric(added["volume"], errors="coerce").eq(0)
    added["abs_return_gt_15pct"] = added["daily_return"].abs().gt(0.15)

    flags_path = data_dir / "anomaly_flags.csv"
    flag_keys: set[tuple[str, pd.Timestamp]] = set()
    if flags_path.exists():
        flags = pd.read_csv(flags_path)
        flags["date"] = pd.to_datetime(flags["date"])
        flag_keys = set(zip(flags["symbole"].astype(str), flags["date"]))
    added["current_detector_flag"] = [
        (str(symbol), pd.Timestamp(date)) in flag_keys
        for symbol, date in zip(added["symbole"], added["date"])
    ]

    review = added[
        added["ohlc_issue"].ne("")
        | added["zero_volume"]
        | added["abs_return_gt_15pct"]
    ].copy()
    review["date"] = review["date"].dt.strftime("%Y-%m-%d")
    return review.sort_values(["symbole", "date"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot_dir", type=Path)
    parser.add_argument(
        "--data-dir", type=Path, default=Path("bvmt_data")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("docs/NEW_SCRAPE_ROW_AUDIT.csv")
    )
    args = parser.parse_args()
    audit = build_audit(args.data_dir, args.snapshot_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.output, index=False, lineterminator="\n")
    print(f"Wrote {len(audit):,} review rows to {args.output}")


if __name__ == "__main__":
    main()
