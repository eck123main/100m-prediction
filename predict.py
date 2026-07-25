"""
Prediction functions: rank a field by recency-weighted time (baseline),
or simulate the race with Monte Carlo to get win probabilities.
"""

import pandas as pd
import numpy as np


def predict_race(athlete_names, stats_table):
    """Rank athletes by recency-weighted average time. Lower time = predicted higher finish."""
    field = stats_table.loc[stats_table.index.intersection(athlete_names)]
    field = field.dropna(subset=["weighted_avg_time"]).sort_values("weighted_avg_time")

    missing = set(athlete_names) - set(field.index)
    if missing:
        print(f"Warning: no usable data for {missing} — excluded from prediction")

    return field


def simulate_race(athlete_names, stats_table, n_simulations=10000, min_races=1):
    """Monte Carlo simulate the race: model each athlete as a normal distribution
    (mean = weighted_avg_time, spread = consistency), simulate many times, and
    return win probabilities. min_races filters out athletes with too little
    history to trust (avoids overconfident predictions from sparse data)."""
    field = stats_table.loc[stats_table.index.intersection(athlete_names)].copy()
    field = field.dropna(subset=["weighted_avg_time"])
    field = field[field["races_used"] >= min_races]

    fallback_std = field["consistency"].mean() if "consistency" in field and field["consistency"].notna().any() else 0.05

    missing = set(athlete_names) - set(field.index)
    if missing:
        print(f"Warning: excluded (no data or below min_races={min_races}): {missing}")

    wins = {name: 0 for name in field.index}

    for _ in range(n_simulations):
        simulated_times = {}
        for name, row in field.iterrows():
            std = row["consistency"] if pd.notna(row.get("consistency")) else fallback_std
            simulated_times[name] = np.random.normal(row["weighted_avg_time"], std)
        winner = min(simulated_times, key=simulated_times.get)
        wins[winner] += 1

    win_probs = pd.Series(wins) / n_simulations
    return win_probs.sort_values(ascending=False)