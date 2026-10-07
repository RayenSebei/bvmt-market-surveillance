import numpy as np
import pandas as pd

from src.evaluation.baselines import draw_random_flags, window_flag_counts_numpy


def test_numpy_random_window_counts_match_pandas_for_20_seeds():
    candidates = {
        "AAA": pd.date_range("2025-01-01", periods=12, freq="D").to_numpy(),
        "BBB": pd.date_range("2025-02-01", periods=10, freq="D").to_numpy(),
    }
    counts = {"AAA": 4, "BBB": 3}
    windows = [
        ("AAA", np.datetime64("2025-01-03"), np.datetime64("2025-01-08")),
        ("BBB", np.datetime64("2025-02-05"), np.datetime64("2025-02-09")),
    ]
    rng = np.random.default_rng(20261006)
    for _ in range(20):
        symbols, dates, _scores = draw_random_flags(candidates, counts, rng)
        fast = window_flag_counts_numpy(symbols, dates, windows)
        slow_frame = pd.DataFrame({"symbole": symbols, "date": pd.to_datetime(dates)})
        slow = [
            int(
                (
                    slow_frame["symbole"].eq(ticker)
                    & slow_frame["date"].between(pd.Timestamp(start), pd.Timestamp(end))
                ).sum()
            )
            for ticker, start, end in windows
        ]
        assert fast == slow
