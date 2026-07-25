"""
Turn race-level rows into athlete-level features: cleaning, recency-weighted
average time, consistency, and cutoff-based stats for leak-free backtesting.
"""

import pandas as pd
import numpy as np

HALF_LIFE_DAYS = 365 * 2  # a race's weight halves every ~2 years


def load_clean_data(csv_path="100m_races_dataset.csv"):
    """Load the dataset and clean names/dates so grouping by athlete works correctly."""
    df = pd.read_csv(csv_path)
    df["ATHLETE"] = df["ATHLETE"].str.strip().str.title()
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df


def compute_stats_before(cutoff_date, df):
    """Recency-weighted stats using only races strictly before cutoff_date.
    Prevents leaking a target race's own result into an athlete's 'known form'."""
    history = df[df["date"] < cutoff_date]

    def recency_weighted_avg(group):
        valid = group.dropna(subset=["time", "date"])
        if len(valid) == 0:
            return pd.Series({"weighted_avg_time": np.nan, "races_used": 0, "consistency": np.nan})

        days_ago = (cutoff_date - valid["date"]).dt.days
        weights = 0.5 ** (days_ago / HALF_LIFE_DAYS)
        weighted_avg = (valid["time"] * weights).sum() / weights.sum()
        consistency = valid["time"].std()

        return pd.Series({
            "weighted_avg_time": weighted_avg,
            "races_used": len(valid),
            "consistency": consistency
        })

    return history.groupby("ATHLETE").apply(recency_weighted_avg, include_groups=False)


def compute_all_time_stats(df):
    """Recency-weighted stats using every race in the dataset (no cutoff).
    Use this for real predictions on upcoming races, not backtests."""
    reference_date = df["date"].max()
    return compute_stats_before(reference_date + pd.Timedelta(days=1), df)