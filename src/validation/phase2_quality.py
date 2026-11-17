"""Read-only Phase 2 quality review and derived corporate-action context."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.validation.classify_anomalies import classify_headline

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/data_quality"
ACTION_WORDS = r"dividende|split|fractionnement|augmentation de capital|actions gratuites|droit de souscription|offre publique|retrait|radiation"


def review_scrape_rows(rows: pd.DataFrame) -> pd.DataFrame:
    reviewed = rows.copy()
    def classify(row: pd.Series) -> str:
        if pd.notna(row["ohlc_issue"]) and str(row["ohlc_issue"]).strip():
            return "OHLC_INCONSISTENCY"
        if bool(row["zero_volume"]):
            return "ZERO_VOLUME_OBSERVATION"
        if bool(row["abs_return_gt_15pct"]):
            return "LARGE_CLOSE_JUMP"
        return "OTHER_NEW_OBSERVATION"
    reviewed["review_class"] = reviewed.apply(classify, axis=1)
    reviewed["review_status"] = "flagged_for_review"
    reviewed["review_note"] = "Rule-based classification only; source observation and corporate-action adjustment not verified."
    return reviewed


def corporate_action_suspects(trading: pd.DataFrame, news: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    data = trading.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["symbole", "date"])
    data["close_return"] = data.groupby("symbole")["cloture"].pct_change(fill_method=None)
    data["gap_days"] = data.groupby("symbole")["date"].diff().dt.days
    data.loc[data["gap_days"] > 10, "close_return"] = pd.NA
    n = news.copy()
    n["date"] = pd.to_datetime(n["date_str"], format="%d/%m/%y", errors="coerce")
    n = n[n["headline"].fillna("").str.contains(ACTION_WORDS, case=False, regex=True)]
    actions = n[["symbole", "date", "headline", "url"]].dropna(subset=["date"])
    rows = []
    for stock in data.groupby("symbole"):
        symbol, group = stock
        significant = group[group["close_return"].abs() >= 0.15]
        local = actions[actions["symbole"] == symbol]
        for item in significant.itertuples():
            nearby = local[(local["date"] - item.date).abs().dt.days <= 7].copy()
            nearby["distance"] = (nearby["date"] - item.date).abs().dt.days
            match = nearby.sort_values(["distance", "date"]).head(1)
            rows.append({"symbole": symbol, "date": item.date, "close_return": item.close_return,
                "reason": "large_close_jump_with_nearby_action_news" if len(match) else "large_close_jump_no_stored_action_news",
                "nearby_headline": match["headline"].iloc[0] if len(match) else "",
                "nearby_news_date": match["date"].iloc[0] if len(match) else pd.NaT,
                "nearby_url": match["url"].iloc[0] if len(match) else ""})
    result = pd.DataFrame(rows)
    ref = flags[["symbole", "date"]].copy()
    ref["date"] = pd.to_datetime(ref["date"])
    result["reference_flag"] = result.set_index(["symbole", "date"]).index.isin(ref.set_index(["symbole", "date"]).index)
    return result


def news_label_sample(news: pd.DataFrame, n: int = 100, seed: int = 20261006) -> pd.DataFrame:
    frame = news[["symbole", "date_str", "headline", "url"]].drop_duplicates("url").copy()
    frame["rule_category"] = frame["headline"].map(classify_headline)
    categories = sorted(frame["rule_category"].dropna().unique())
    quota = max(1, n // len(categories))
    selected = pd.concat([g.sample(n=min(quota, len(g)), random_state=seed) for _, g in frame.groupby("rule_category")])
    if len(selected) < n:
        remaining = frame.drop(selected.index)
        selected = pd.concat([selected, remaining.sample(n=min(n - len(selected), len(remaining)), random_state=seed)])
    selected = selected.head(n).sort_values(["rule_category", "symbole", "date_str"]).reset_index(drop=True)
    selected.insert(0, "sample_id", [f"N{i:03d}" for i in range(1, len(selected) + 1)])
    selected["human_label"] = ""
    selected["human_notes"] = ""
    return selected


def main() -> int:
    trading = pd.read_csv(ROOT / "bvmt_data/_all_tickers_full.csv", parse_dates=["date"])
    flags = pd.read_csv(ROOT / "bvmt_data/anomaly_flags.csv", parse_dates=["date"])
    news = pd.read_csv(ROOT / "bvmt_data/_all_news_combined.csv")
    audit = pd.read_csv(ROOT / "docs/NEW_SCRAPE_ROW_AUDIT.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    review = review_scrape_rows(audit)
    review.to_csv(OUT / "new_scrape_row_review.csv", index=False)
    suspects = corporate_action_suspects(trading, news, flags)
    suspects.to_csv(OUT / "corporate_action_suspects.csv", index=False)
    news_label_sample(news).to_csv(ROOT / "data/evaluation/news_label_sample.csv", index=False)
    duplicate = int(trading.duplicated(["symbole", "date"]).sum())
    invalid_dates = int(trading["date"].isna().sum())
    numeric = trading[["ouverture", "haut", "bas", "cloture", "volume"]]
    ohlc = int(((trading["bas"] > trading["haut"]) | (trading["ouverture"] < trading["bas"]) | (trading["ouverture"] > trading["haut"]) | (trading["cloture"] < trading["bas"]) | (trading["cloture"] > trading["haut"]) | numeric.isna().any(axis=1) | (numeric < 0).any(axis=1)).sum())
    ordered = trading.sort_values(["symbole", "date"])
    gaps = ordered.groupby("symbole")["date"].diff().dt.days
    long_gaps = int((gaps > 30).sum())
    latest = trading["date"].max()
    stale = trading.groupby("symbole")["date"].max()
    stale_symbols = stale[(latest - stale).dt.days > 90].index.tolist()
    report = ["# Phase 2 data quality review", "", f"Rows: {len(trading):,}; symbols: {trading.symbole.nunique()}; latest date: {latest.date()}.",
        f"Duplicate symbol/date rows: {duplicate}; invalid dates: {invalid_dates}; OHLC/negative/missing numeric rows: {ohlc}; gaps >30 calendar days: {long_gaps}.",
        f"Symbols with last observation >90 days before latest: {len(stale_symbols)} ({', '.join(stale_symbols)}).",
        f"Corporate-action suspects from ≥15% daily close jumps: {len(suspects)}; with stored action news within ±7 days: {int(suspects['nearby_url'].fillna('').ne('').sum())}; existing reference flags tagged: {int(suspects['reference_flag'].sum())}.",
        f"New scrape rows reviewed: {len(review)}; classes: {review.review_class.value_counts().to_dict()}. Every row remains flagged for manual review; no source value was changed.",
        "", "These are mechanical checks and candidate context tags. A nearby headline does not prove a price move was caused by a corporate action. ilboursa is the sole stored news source. The sample's human_label and human_notes fields are intentionally empty."]
    (OUT / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
