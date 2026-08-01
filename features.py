"""
Turn race-level rows into athlete-level features: cleaning, recency-weighted
average time, consistency, and cutoff-based stats for leak-free backtesting.
"""

import pandas as pd
import numpy as np

HALF_LIFE_DAYS = 365 * 2  # a race's weight halves every ~2 years

# Men's 100m world record is 9.58s; even a weak heat qualifier at the
# competition levels this scraper covers finishes well under 13s. Times
# outside this band are scraper mismatches (wrong row/column picked up from
# a results table), not real races — e.g. one row records 45.12s.
MIN_PLAUSIBLE_TIME = 9.0
MAX_PLAUSIBLE_TIME = 13.0


def load_clean_data(csv_path="100m_races_dataset.csv"):
    """Load the dataset and clean names/dates/round so grouping works correctly."""
    df = pd.read_csv(csv_path)
    df["ATHLETE"] = df["ATHLETE"].str.strip().str.title()
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    implausible = (df["time"] < MIN_PLAUSIBLE_TIME) | (df["time"] > MAX_PLAUSIBLE_TIME)
    df.loc[implausible, "time"] = np.nan

    # Derive round from the URL itself instead of trusting the stored column,
    # since older scrapes (before the round column existed) left it as NaN.
    def infer_round(url):
        if "/semi-final/" in url:
            return "semi-final"
        elif "/heats/" in url:
            return "heats"
        else:
            return "final"

    df["round"] = df["source_url"].apply(infer_round)

    coefficient = estimate_wind_coefficient(df)
    df["adj_time"] = df["time"] - coefficient * df["wind"]
    df["adj_time"] = df["adj_time"].fillna(df["time"])
    df.attrs["wind_coefficient"] = coefficient

    round_offsets = estimate_round_offsets(df)
    df["adj_time"] = df["adj_time"] - df["round"].map(round_offsets).fillna(0)
    df.attrs["round_offsets"] = round_offsets

    return df


def estimate_wind_coefficient(df, min_races=3, min_wind_std=0.3):
    """Seconds of time per 1 m/s of wind, estimated as a within-athlete
    fixed-effects regression: compares each athlete only against their own
    times across their own varying wind conditions, so a fast athlete who
    happens to race in windier conditions than a slow athlete doesn't get
    mistaken for a wind effect. Uses the whole dataset regardless of any
    backtest cutoff — this is a shared physical relationship (wind's effect
    on sprint time), not information about who wins a specific future race.

    Only athletes with min_races+ races and real variation in the wind
    they've faced (min_wind_std) contribute, since an athlete who has only
    ever raced in +0.5 conditions can't tell us anything about the slope."""
    valid = df.dropna(subset=["time", "wind"])
    counts = valid.groupby("ATHLETE").size()
    wind_std = valid.groupby("ATHLETE")["wind"].std()
    eligible = counts[(counts >= min_races) & (wind_std.reindex(counts.index).fillna(0) >= min_wind_std)].index
    valid = valid[valid["ATHLETE"].isin(eligible)]

    if len(valid) == 0:
        return 0.0

    dt = valid["time"] - valid.groupby("ATHLETE")["time"].transform("mean")
    dw = valid["wind"] - valid.groupby("ATHLETE")["wind"].transform("mean")

    denom = (dw ** 2).sum()
    if denom == 0:
        return 0.0
    return (dt * dw).sum() / denom


def estimate_round_offsets(df, baseline_round="final", min_races=3):
    """Seconds each round tends to run slower/faster than an athlete's own
    final-round pace, estimated the same fixed-effects way as the wind
    coefficient: only compares an athlete against their own times across
    rounds, so it isn't confounded by weaker athletes appearing in heats
    more often than finals. Only athletes with min_races+ races across 2+
    distinct rounds contribute, since the comparison needs actual variation.

    Returns {round_name: offset_seconds}, where offset is subtracted from
    adj_time to get a 'final-equivalent' estimate — heats typically comes
    out positive since athletes often ease off once they've qualified."""
    valid = df.dropna(subset=["adj_time", "round"])
    counts = valid.groupby("ATHLETE").size()
    rounds_per_athlete = valid.groupby("ATHLETE")["round"].nunique()
    eligible = counts[(counts >= min_races) & (rounds_per_athlete.reindex(counts.index).fillna(0) >= 2)].index
    valid = valid[valid["ATHLETE"].isin(eligible)]

    if len(valid) == 0:
        return {baseline_round: 0.0}

    demeaned = valid["adj_time"] - valid.groupby("ATHLETE")["adj_time"].transform("mean")
    round_effect = demeaned.groupby(valid["round"]).mean()

    baseline = round_effect.get(baseline_round, 0.0)
    return (round_effect - baseline).to_dict()


def compute_reliability_before(cutoff_date, df, prior_strength=8):
    """Per-athlete rate of producing a valid time (i.e. not a DNF/DQ/DNS), using
    only races strictly before cutoff_date. Shrunk toward the field-wide average
    via a Beta prior (worth prior_strength races) so an athlete with only 1-2
    starts doesn't get scored as a false 0% or 100% reliable."""
    history = df[df["date"] < cutoff_date]
    if len(history) == 0:
        return pd.DataFrame(columns=["starts", "finishes", "finish_rate"])

    prior_rate = history["time"].notna().mean()
    alpha0 = prior_rate * prior_strength
    beta0 = (1 - prior_rate) * prior_strength

    def reliability(group):
        starts = len(group)
        finishes = group["time"].notna().sum()
        finish_rate = (finishes + alpha0) / (starts + alpha0 + beta0)
        return pd.Series({"starts": starts, "finishes": finishes, "finish_rate": finish_rate})

    return history.groupby("ATHLETE").apply(reliability, include_groups=False)


def compute_stats_before(cutoff_date, df):
    """Recency-weighted stats using only races strictly before cutoff_date.
    Prevents leaking a target race's own result into an athlete's 'known form'."""
    history = df[df["date"] < cutoff_date]
    if len(history) == 0:
        return pd.DataFrame(columns=["weighted_avg_time", "races_used", "consistency",
                                      "finish_rate", "starts", "finishes"])

    def recency_weighted_avg(group):
        valid = group.dropna(subset=["adj_time", "date"])
        if len(valid) == 0:
            return pd.Series({"weighted_avg_time": np.nan, "races_used": 0, "consistency": np.nan})

        days_ago = (cutoff_date - valid["date"]).dt.days
        weights = 0.5 ** (days_ago / HALF_LIFE_DAYS)
        weighted_avg = (valid["adj_time"] * weights).sum() / weights.sum()
        consistency = valid["adj_time"].std()

        return pd.Series({
            "weighted_avg_time": weighted_avg,
            "races_used": len(valid),
            "consistency": consistency
        })

    stats = history.groupby("ATHLETE").apply(recency_weighted_avg, include_groups=False)
    reliability = compute_reliability_before(cutoff_date, df)
    return stats.join(reliability[["finish_rate", "starts", "finishes"]])


def compute_all_time_stats(df):
    """Recency-weighted stats using every race in the dataset (no cutoff).
    Use this for real predictions on upcoming races, not backtests."""
    reference_date = df["date"].max()
    return compute_stats_before(reference_date + pd.Timedelta(days=1), df)