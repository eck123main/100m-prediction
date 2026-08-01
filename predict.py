"""
Prediction functions: rank a field by recency-weighted time (baseline),
or simulate the race with Monte Carlo to get win probabilities.
"""

import sys

import pandas as pd
import numpy as np

# Windows consoles default to cp1252, which can't encode every character in
# athlete names (e.g. accented letters) — force utf-8 so warning prints don't
# crash instead of just printing a name.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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


def elo_win_probs(athlete_names, stats_table):
    """Win probabilities from head-to-head Elo rating alone (ignores time/
    consistency/reliability entirely) — the Bradley-Terry extension of the
    pairwise Elo formula: p_i proportional to 10^(elo_i/400). An athlete with
    no rating history still gets a rating (BASE_ELO, via compute_stats_before),
    so this never excludes anyone in the field the way simulate_race can."""
    field = stats_table.loc[stats_table.index.intersection(athlete_names)]

    missing = set(athlete_names) - set(field.index)
    if missing:
        print(f"Warning: no usable data for {missing} — excluded from prediction")

    strength = 10 ** (field["elo"] / 400)
    return (strength / strength.sum()).sort_values(ascending=False)


def blend_win_probs(mc_probs, elo_probs, elo_weight=0.5):
    """Combine the time-based Monte Carlo probabilities with the head-to-head
    Elo probabilities. Reindexed to their union since simulate_race can
    exclude athletes (missing time data, below min_races) that elo_win_probs
    never does — a missing side contributes 0 rather than dropping the
    athlete — then renormalized to sum to 1."""
    idx = mc_probs.index.union(elo_probs.index)
    mc = mc_probs.reindex(idx).fillna(0)
    elo = elo_probs.reindex(idx).fillna(0)
    blended = (1 - elo_weight) * mc + elo_weight * elo
    return (blended / blended.sum()).sort_values(ascending=False)


def predict_race_full(athlete_names, stats_table, n_simulations=10000, min_races=1, elo_weight=0.5):
    """Recommended prediction: blend the time-based Monte Carlo simulation
    with head-to-head Elo. elo_weight=0.5 backtested best among {0.3, 0.5,
    0.7} in backtest.py — Elo alone underperforms the time-based model
    (weaker standalone signal), but blended in it beats pure Monte Carlo in
    every slice tested, catching close/uncertain races a solo recency-
    weighted time average misses."""
    mc_probs = simulate_race(athlete_names, stats_table, n_simulations=n_simulations, min_races=min_races)
    elo_probs = elo_win_probs(athlete_names, stats_table)
    return blend_win_probs(mc_probs, elo_probs, elo_weight=elo_weight)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python predict.py "Athlete Name" "Athlete Name" ...')
        sys.exit(1)

    from features import load_clean_data, compute_all_time_stats

    field = [name.strip().title() for name in sys.argv[1:]]

    df = load_clean_data()
    stats = compute_all_time_stats(df)
    probs = predict_race_full(field, stats)

    print(f"\n100m final prediction — {len(field)} athletes requested, {len(probs)} matched")
    print(f"Data through {df['date'].max().date()}\n")

    table = stats.loc[probs.index, ["weighted_avg_time", "finish_rate", "races_used", "elo"]].copy()
    table.insert(0, "win_prob", probs)

    for rank, (name, row) in enumerate(table.iterrows(), start=1):
        print(f"  {rank}. {name:<28} {row['win_prob']:>5.1%}   "
              f"time~{row['weighted_avg_time']:.2f}s   finish_rate={row['finish_rate']:.0%}   "
              f"races={int(row['races_used'])}   elo={row['elo']:.0f}")

    unmatched = set(field) - set(probs.index)
    if unmatched:
        print(f"\nNo usable data for: {sorted(unmatched)} — not included above")
    print()