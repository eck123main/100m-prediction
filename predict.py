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
    history to trust (avoids overconfident predictions from sparse data).

    Each simulated run, an athlete first has to actually produce a valid time —
    drawn as a coin flip against their finish_rate — before their time even
    enters that run's comparison. This lets a DQ/DNF-prone athlete's history
    cost them win probability, instead of every simulated race assuming
    everyone finishes clean."""
    field = stats_table.loc[stats_table.index.intersection(athlete_names)].copy()
    field = field.dropna(subset=["weighted_avg_time"])
    field = field[field["races_used"] >= min_races]

    fallback_std = field["consistency"].mean() if "consistency" in field and field["consistency"].notna().any() else 0.05
    fallback_finish_rate = field["finish_rate"].mean() if "finish_rate" in field and field["finish_rate"].notna().any() else 0.95

    missing = set(athlete_names) - set(field.index)
    if missing:
        print(f"Warning: excluded (no data or below min_races={min_races}): {missing}")

    wins = {name: 0 for name in field.index}

    for _ in range(n_simulations):
        simulated_times = {}
        for name, row in field.iterrows():
            finish_rate = row["finish_rate"] if pd.notna(row.get("finish_rate")) else fallback_finish_rate
            if np.random.random() > finish_rate:
                continue  # simulated DNF/DQ/false start — not in this run's field
            std = row["consistency"] if pd.notna(row.get("consistency")) else fallback_std
            simulated_times[name] = np.random.normal(row["weighted_avg_time"], std)
        if not simulated_times:
            continue  # everyone simulated a non-finish this run (very rare)
        winner = min(simulated_times, key=simulated_times.get)
        wins[winner] += 1

    win_probs = pd.Series(wins) / n_simulations
    return win_probs.sort_values(ascending=False)