"""
Scoring rules and checks for win-probability forecasts of one race.

Log-loss (the "ignorance" score) stays the main metric — it's local and
proper, and Wheatcroft (2019) argues it beats the Brier score and the RPS
for choosing between sports forecasters. Brier and calibration error are
reported next to it because they don't blow up on one near-zero miss, so
they show whether a log-loss change comes from a few cold-start races or
from the whole set.
"""

import numpy as np
import pandas as pd

EPS = 1e-3  # floor on the winner's probability so log-loss stays finite


def winner_log_loss(probs, winner, eps=EPS):
    """-log(probability given to the actual winner), floored at eps."""
    return -np.log(max(float(probs.get(winner, 0.0)), eps))


def multiclass_brier(probs, field, winner):
    """Sum over the whole field of (p_i - won_i)^2. 0 is perfect, 2 is the
    worst possible. Athletes the model left out count as p = 0."""
    p = np.array([float(probs.get(a, 0.0)) for a in field])
    y = np.array([a == winner for a in field], dtype=float)
    return float(((p - y) ** 2).sum())


def calibration_table(prob, won, bins=(0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0)):
    """Per-entrant calibration: bucket every (athlete, race) probability and
    compare the mean forecast with how often those athletes actually won.
    Uses every entrant, not just the top pick, so it has many more points
    than the top-pick table in backtest.py."""
    d = pd.DataFrame({"prob": np.asarray(prob, dtype=float), "won": np.asarray(won, dtype=float)})
    d["bucket"] = pd.cut(d["prob"], bins=list(bins), include_lowest=True)
    return d.groupby("bucket", observed=True).agg(
        mean_prob=("prob", "mean"), win_rate=("won", "mean"), count=("won", "size"))


def expected_calibration_error(prob, won, bins=(0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0)):
    """Count-weighted mean |forecast - outcome rate| over the buckets of
    calibration_table. 0 means perfectly calibrated."""
    t = calibration_table(prob, won, bins)
    if t["count"].sum() == 0:
        return np.nan
    return float((t["count"] * (t["mean_prob"] - t["win_rate"]).abs()).sum() / t["count"].sum())


def paired_bootstrap_ci(new, old, n_boot=2000, seed=0, level=0.95):
    """Mean of (new - old) per race with a percentile bootstrap CI.
    Negative = new is better for loss metrics. Returns (mean, lo, hi)."""
    diff = np.asarray(new, dtype=float) - np.asarray(old, dtype=float)
    if len(diff) == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = rng.choice(diff, (n_boot, len(diff))).mean(axis=1)
    a = (1 - level) / 2 * 100
    return float(diff.mean()), float(np.percentile(boot, a)), float(np.percentile(boot, 100 - a))
