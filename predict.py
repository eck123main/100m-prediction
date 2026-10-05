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

    if field.empty:
        return pd.Series(dtype=float)

    mu = field["weighted_avg_time"].to_numpy(dtype=float)
    sd = field["consistency"].fillna(fallback_std).to_numpy(dtype=float)
    fr = field["finish_rate"].fillna(fallback_finish_rate).to_numpy(dtype=float)

    # All runs at once: one row per simulated race, one column per athlete.
    finished = np.random.random((n_simulations, len(field))) <= fr
    times = np.where(finished, np.random.normal(mu, sd, (n_simulations, len(field))), np.inf)
    someone_finished = finished.any(axis=1)  # everyone DNF-ing is very rare; no winner
    winners = times[someone_finished].argmin(axis=1)
    wins = np.bincount(winners, minlength=len(field))

    win_probs = pd.Series(wins, index=field.index) / n_simulations
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


def predict_race_full(athlete_names, stats_table, n_simulations=10000, min_races=1, elo_weight=0.1):
    """Recommended prediction: blend the time-based Monte Carlo simulation
    with head-to-head Elo. elo_weight=0.1 was chosen in backtest.py by
    log-loss on finals before 2022 over a 0-1 grid, and holds up on 2022+
    finals (2026-10 rebuild: 295 finals, heats now rated as separate races).
    After the all-rounds championship data, 0.0 and 0.1 tie on pre-2022
    log-loss (1.471 vs 1.478) while 0.1 is clearly better on 2022+ (1.869
    vs 1.896), so 0.1 is kept.
    Elo alone is a weaker signal than the time model; a small weight helps
    probability calibration, larger weights hurt it."""
    mc_probs = simulate_race(athlete_names, stats_table, n_simulations=n_simulations, min_races=min_races)
    elo_probs = elo_win_probs(athlete_names, stats_table)
    return blend_win_probs(mc_probs, elo_probs, elo_weight=elo_weight)


def parse_odds(text):
    """'Name=2.5, Other Name=3.1' (decimal odds) -> bookmaker win probabilities.
    Implied probability is 1/odds; dividing by their sum removes the
    bookmaker's margin (overround) so they're comparable to the model's."""
    from features import ATHLETE_ALIASES
    odds = {}
    for part in text.split(","):
        if not part.strip():
            continue
        name, _, value = part.rpartition("=")
        name = name.strip().title()
        odds[ATHLETE_ALIASES.get(name, name)] = float(value)
    implied = pd.Series({n: 1 / o for n, o in odds.items()})
    return odds, implied / implied.sum()


def log_prediction(log_path, probs, field, race_url, data_through, odds=None):
    """Append one row per athlete in the field (unscored athletes get 0) so
    the prediction can be graded later against the actual result. If
    bookmaker odds are given, their margin-free probabilities are logged
    alongside so score_predictions.py can compare model vs market."""
    import os
    import subprocess
    from datetime import datetime, timezone

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    logged_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = pd.DataFrame({
        "logged_at": logged_at,
        "race_url": race_url,
        "athlete": field,
        "win_prob": [float(probs.get(a, 0.0)) for a in field],
        "data_through": str(data_through),
        "model_commit": commit,
    })
    if odds is not None:
        raw, book = odds
        rows["book_odds"] = [raw.get(a) for a in field]
        rows["book_prob"] = [float(book.get(a, 0.0)) for a in field]
    rows.to_csv(log_path, mode="a", header=not os.path.exists(log_path), index=False)


if __name__ == "__main__":
    import argparse

    from features import load_clean_data, compute_all_time_stats, compute_stats_before

    parser = argparse.ArgumentParser(description="Predict a men's 100m race.")
    parser.add_argument("athletes", nargs="*", help='athlete names, e.g. "Noah Lyles"')
    parser.add_argument("--startlist", metavar="URL",
                        help="fetch the field from a worldathletics.org race/meeting page "
                             "instead of typing names")
    parser.add_argument("--before", metavar="YYYY-MM-DD",
                        help="only use results before this date (replay a past race leak-free)")
    parser.add_argument("--odds", metavar='"NAME=ODDS,..."',
                        help='bookmaker decimal odds to log for comparison, e.g. '
                             '"Oblique Seville=2.5,Noah Lyles=3.2"')
    parser.add_argument("--log", nargs="?", const="predictions_log.csv", metavar="CSV",
                        help="append this prediction to a log (default predictions_log.csv) "
                             "so score_predictions.py can grade it once results are in")
    args = parser.parse_args()

    names = list(args.athletes)
    if args.startlist:
        from scraper import fetch_start_list
        names += fetch_start_list(args.startlist)
    if not names:
        parser.error("give athlete names and/or --startlist URL")
    from features import ATHLETE_ALIASES
    field = list(dict.fromkeys(
        ATHLETE_ALIASES.get(name.strip().title(), name.strip().title()) for name in names
    ))

    df = load_clean_data()
    if args.before:
        cutoff = pd.Timestamp(args.before)
        stats = compute_stats_before(cutoff, df)
        data_through = df.loc[df["date"] < cutoff, "date"].max().date()
    else:
        stats = compute_all_time_stats(df)
        data_through = df["date"].max().date()
    probs = predict_race_full(field, stats)

    print(f"\n100m final prediction — {len(field)} athletes requested, {len(probs)} matched")
    print(f"Data through {data_through}\n")

    table = stats.loc[probs.index, ["weighted_avg_time", "finish_rate", "races_used", "elo"]].copy()
    table.insert(0, "win_prob", probs)

    for rank, (name, row) in enumerate(table.iterrows(), start=1):
        print(f"  {rank}. {name:<28} {row['win_prob']:>5.1%}   "
              f"time~{row['weighted_avg_time']:.2f}s   finish_rate={row['finish_rate']:.0%}   "
              f"races={int(row['races_used'])}   elo={row['elo']:.0f}")

    if args.log:
        odds = parse_odds(args.odds) if args.odds else None
        if odds is not None:
            unknown = set(odds[0]) - set(field)
            if unknown:
                print(f"Warning: odds given for athletes not in the field: {sorted(unknown)}")
        log_prediction(args.log, probs, field, args.startlist, data_through, odds)
        print(f"Logged to {args.log}")

    unmatched = set(field) - set(probs.index)
    if unmatched:
        print(f"\nNo usable data for: {sorted(unmatched)} — not included above")
    print()
