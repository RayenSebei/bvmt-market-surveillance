"""
FINAL PHASE — Add retrospective local-news context to every anomaly flag
and produce a prioritized watchlist. News proximity is not proof that a
headline caused a price move, and absence of a local match is not evidence
of misconduct.

Logic:
  - For every spike-detector flag (anomaly_flags.csv), search the flagged
    ticker's news for any headline within +/-7 calendar days. Found ->
    NEWS_MATCH_FOUND (tag with the closest headline, date, timing and
    category). Not found -> NO_LOCAL_MATCH.
  - For every decay-detector flag (decay_flags.csv), search for news
    within +/-60 days of the ticker's last active trading date (a wider
    window since "going dark" is a slower-moving story than a single-day
    spike).
  - Headlines are tagged into rough categories (bankruptcy, delisting,
    buyout/OPR, earnings, governance, etc.) via keyword matching, so you
    can see what KIND of news explains most flags, not just whether one
    exists.

CAVEAT: this is a heuristic keyword classifier, not NLP — it'll mislabel
some headlines and miss synonyms. Good enough to prioritize what to check
manually, not a substitute for reading the actual unexplained cases.

Reads:
    bvmt_data/anomaly_flags.csv
    bvmt_data/decay_flags.csv
    bvmt_data/_all_news_combined.csv
Writes:
    bvmt_data/anomaly_classified.csv
    bvmt_data/decay_classified.csv
    bvmt_data/watchlist.csv   <- the actual prioritized deliverable

Usage:
    python src/validation/classify_anomalies.py
"""

import os

import pandas as pd

OUT_DIR = "bvmt_data"
ANOMALY_PATH = os.path.join(OUT_DIR, "anomaly_flags.csv")
DECAY_PATH = os.path.join(OUT_DIR, "decay_flags.csv")
NEWS_PATH = os.path.join(OUT_DIR, "_all_news_combined.csv")

ANOMALY_WINDOW_DAYS = 7   # calendar days around a flagged date to search for news
DECAY_WINDOW_DAYS = 60    # wider window for decay tickers (slower-moving stories)
NEWS_MATCH_FOUND = "NEWS_MATCH_FOUND"
NO_LOCAL_MATCH = "NO_LOCAL_MATCH"

# Keyword categories, checked in this priority order against lowercased headlines.
CATEGORIES = [
    ("bankruptcy_distress", ["faillite", "redressement judiciaire", "cessation de paiement",
                              "liquidation judiciaire", "vente judiciaire"]),
    ("delisting_radiation", ["radiation", "radié", "radiee", "radiées", "radiés"]),
    ("suspension", ["suspension", "suspendu"]),
    ("buyout_opr", ["offre publique de retrait", " opr", "opr ", "rachat",
                     "offre publique d'achat", " opa"]),
    ("capital_increase", ["augmentation de capital"]),
    ("dividend", ["dividende"]),
    ("governance", ["conseil d'administration", "assemblée générale", " ago ",
                     "démission", "nomination"]),
    ("earnings_results", ["chiffre d'affaires", "résultats", "perte nette",
                           "bénéfice", "revenus", "chiffre d’affaires"]),
]


def load_news(path):
    df = pd.read_csv(path)
    df["news_date"] = pd.to_datetime(df["date_str"], format="%d/%m/%y", errors="coerce")
    df = df.dropna(subset=["news_date"])
    return df


def classify_headline(headline):
    h = str(headline).lower()
    for category, keywords in CATEGORIES:
        for kw in keywords:
            if kw in h:
                return category
    return "other_news"


def find_nearby_news(news_df, symbole, target_date, window_days):
    g = news_df[news_df["symbole"] == symbole]
    if g.empty:
        return None

    diffs = (g["news_date"] - target_date).dt.days
    nearby = g[diffs.abs() <= window_days].copy()
    if nearby.empty:
        return None

    nearby["gap_days"] = (nearby["news_date"] - target_date).dt.days
    nearby = nearby.reindex(nearby["gap_days"].abs().sort_values().index)
    return nearby.iloc[0]  # closest match by absolute distance


def classify_anomalies(anomaly_df, news_df):
    results = []
    for _, row in anomaly_df.iterrows():
        target_date = pd.Timestamp(row["date"])
        match = find_nearby_news(news_df, row["symbole"], target_date, ANOMALY_WINDOW_DAYS)

        out = row.to_dict()
        if match is not None:
            gap_days = int(match["gap_days"])
            out["status"] = NEWS_MATCH_FOUND
            out["matched_headline"] = match["headline"]
            out["matched_news_date"] = match["news_date"].date()
            out["gap_days"] = gap_days  # positive = news came AFTER the anomaly
            out["category"] = classify_headline(match["headline"])
            out["news_available_as_of_flag"] = gap_days <= 0
            out["post_event_news_context"] = gap_days > 0
            out["news_match_timing"] = (
                "AVAILABLE_AS_OF_FLAG" if gap_days <= 0 else "POST_EVENT_CONTEXT"
            )
        else:
            out["status"] = NO_LOCAL_MATCH
            out["matched_headline"] = None
            out["matched_news_date"] = None
            out["gap_days"] = None
            out["category"] = None
            out["news_available_as_of_flag"] = False
            out["post_event_news_context"] = False
            out["news_match_timing"] = "NO_LOCAL_MATCH"
        results.append(out)

    return pd.DataFrame(results)


def classify_decay(decay_df, news_df):
    results = []
    for _, row in decay_df.iterrows():
        symbole = row["symbole"]
        last_active = pd.to_datetime(row["last_active_date"], errors="coerce")

        out = row.to_dict()
        if pd.isna(last_active):
            out["status"] = NO_LOCAL_MATCH
            out["matched_headline"] = None
            out["matched_news_date"] = None
            out["gap_days"] = None
            out["category"] = None
            out["news_available_as_of_flag"] = False
            out["post_event_news_context"] = False
            out["news_match_timing"] = "NO_LOCAL_MATCH"
            results.append(out)
            continue

        match = find_nearby_news(news_df, symbole, last_active, DECAY_WINDOW_DAYS)
        if match is not None:
            gap_days = int(match["gap_days"])
            out["status"] = NEWS_MATCH_FOUND
            out["matched_headline"] = match["headline"]
            out["matched_news_date"] = match["news_date"].date()
            out["gap_days"] = gap_days
            out["category"] = classify_headline(match["headline"])
            out["news_available_as_of_flag"] = gap_days <= 0
            out["post_event_news_context"] = gap_days > 0
            out["news_match_timing"] = (
                "AVAILABLE_AS_OF_FLAG" if gap_days <= 0 else "POST_EVENT_CONTEXT"
            )
        else:
            out["status"] = NO_LOCAL_MATCH
            out["matched_headline"] = None
            out["matched_news_date"] = None
            out["gap_days"] = None
            out["category"] = None
            out["news_available_as_of_flag"] = False
            out["post_event_news_context"] = False
            out["news_match_timing"] = "NO_LOCAL_MATCH"
        results.append(out)

    return pd.DataFrame(results)


def build_watchlist(anomaly_classified, decay_classified):
    spike_watch = anomaly_classified[
        (anomaly_classified["status"] == NO_LOCAL_MATCH)
        & (anomaly_classified["combined_anomaly"] == True)  # noqa: E712
    ].copy()
    spike_watch["source"] = "spike_detector"
    spike_watch["priority"] = 1

    decay_watch = decay_classified[decay_classified["status"] == NO_LOCAL_MATCH].copy()
    decay_watch["source"] = "decay_detector"
    decay_watch["priority"] = 2

    watchlist = pd.concat([spike_watch, decay_watch], ignore_index=True, sort=False)
    watchlist = watchlist.sort_values("priority")
    return watchlist


if __name__ == "__main__":
    print("Loading data...")
    anomaly_df = pd.read_csv(ANOMALY_PATH)
    anomaly_df["date"] = pd.to_datetime(anomaly_df["date"])

    decay_df = pd.read_csv(DECAY_PATH)
    news_df = load_news(NEWS_PATH)

    print(f"  {len(anomaly_df)} anomaly flags, {len(decay_df)} decay flags, "
          f"{len(news_df)} news items")

    print(f"\nClassifying spike-detector anomalies against news (+/-{ANOMALY_WINDOW_DAYS} days)...")
    anomaly_classified = classify_anomalies(anomaly_df, news_df)
    anomaly_out = os.path.join(OUT_DIR, "anomaly_classified.csv")
    anomaly_classified.to_csv(anomaly_out, index=False)

    print(f"Classifying decay-detector flags against news (+/-{DECAY_WINDOW_DAYS} days)...")
    decay_classified = classify_decay(decay_df, news_df)
    decay_out = os.path.join(OUT_DIR, "decay_classified.csv")
    decay_classified.to_csv(decay_out, index=False)

    print("\nBuilding final prioritized watchlist...")
    watchlist = build_watchlist(anomaly_classified, decay_classified)
    watchlist_out = os.path.join(OUT_DIR, "watchlist.csv")
    watchlist.to_csv(watchlist_out, index=False)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    n_total = len(anomaly_classified)
    n_matched = (anomaly_classified["status"] == NEWS_MATCH_FOUND).sum()
    n_unmatched = n_total - n_matched
    print(f"\nSPIKE DETECTOR: {n_total} flagged rows")
    print(f"  Local news match: {n_matched} ({n_matched / n_total * 100:.1f}%)")
    print(f"  No local match:   {n_unmatched} ({n_unmatched / n_total * 100:.1f}%)")

    n_combined = (anomaly_classified["combined_anomaly"] == True).sum()  # noqa: E712
    n_combined_unmatched = (
        (anomaly_classified["combined_anomaly"] == True)  # noqa: E712
        & (anomaly_classified["status"] == NO_LOCAL_MATCH)
    ).sum()
    print(f"  Combined anomalies (highest priority): {n_combined} total, "
          f"{n_combined_unmatched} with NO_LOCAL_MATCH")

    print("\nMatched-news category breakdown (spike detector):")
    cat_counts = anomaly_classified[anomaly_classified["status"] == NEWS_MATCH_FOUND]["category"].value_counts()
    print(cat_counts.to_string())

    n_decay_total = len(decay_classified)
    n_decay_matched = (decay_classified["status"] == NEWS_MATCH_FOUND).sum()
    print(f"\nDECAY DETECTOR: {n_decay_total} flagged tickers")
    print(f"  Local news match: {n_decay_matched}")
    print(f"  No local match:   {n_decay_total - n_decay_matched}")

    print("\n" + "=" * 70)
    print(f"FINAL WATCHLIST: {len(watchlist)} flags without a local news match")
    print("(prioritization for manual research, not evidence of misconduct)")
    print("=" * 70)
    cols_to_show = [c for c in [
        "symbole", "ticker_name", "date", "source",
        "volume_zscore", "return_zscore", "decline_ratio",
    ] if c in watchlist.columns]
    print(watchlist[cols_to_show].head(30).to_string(index=False))

    print(f"\nSaved: {anomaly_out}")
    print(f"Saved: {decay_out}")
    print(f"Saved: {watchlist_out}  <- THIS is your actual deliverable")
