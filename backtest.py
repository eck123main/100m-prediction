"""
Backtest the model against real finals: for each final, rebuild every
athlete's stats using only data known before that race (via
compute_stats_before), predict the field, and compare to what actually
happened. Every race is genuinely leak-free — no result is ever used to
predict itself.
"""

import numpy as np
import pandas as pd

from features import compute_stats_before
from predict import predict_race, simulate_race

MIN_FIELD_SIZE = 3
MAX_FIELD_SIZE = 10  # real 100m finals are 3-10 lanes; bigger "finals" in the
                      # raw data are mislabeled full-meet result dumps


def get_real_finals(df):
    """Finals with a plausible field size, one row per race."""
    finals = df[df["round"] == "final"]
    sizes = finals.groupby("source_url").size()
    real_ids = sizes[(sizes >= MIN_FIELD_SIZE) & (sizes <= MAX_FIELD_SIZE)].index
    return finals[finals["source_url"].isin(real_ids)]


def evaluate_race(race_df, df, min_races=1):
    """Backtest a single race. Returns None if there's no valid winner to score against."""
    finishers = race_df.dropna(subset=["time"])
    if len(finishers) == 0:
        return None

    date = race_df["date"].iloc[0]
    field = race_df["ATHLETE"].tolist()
    actual_winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]

    stats = compute_stats_before(date, df)

    baseline = predict_race(field, stats)
    baseline_winner = baseline.index[0] if len(baseline) > 0 else None

    win_probs = simulate_race(field, stats, min_races=min_races)
    mc_winner = win_probs.index[0] if len(win_probs) > 0 else None
    prob_assigned = win_probs.get(actual_winner, 0.0)

    return {
        "source_url": race_df["source_url"].iloc[0],
        "date": date,
        "field_size": len(field),
        "actual_winner": actual_winner,
        "winner_had_history": actual_winner in stats.index,
        "baseline_correct": baseline_winner == actual_winner,
        "mc_correct": mc_winner == actual_winner,
        "prob_assigned_to_winner": prob_assigned,
        "chance_accuracy": 1 / len(field),
    }


def run_backtest(df, min_races=1):
    """Evaluate every real final in df. Returns one row per race."""
    real_finals = get_real_finals(df)
    results = []
    for source_url, race_df in real_finals.groupby("source_url"):
        result = evaluate_race(race_df, df, min_races=min_races)
        if result is not None:
            results.append(result)
    return pd.DataFrame(results).sort_values("date").reset_index(drop=True)


def summarize(results):
    """Headline numbers: model accuracy vs. chance, plus calibration."""
    n = len(results)
    return pd.Series({
        "races_evaluated": n,
        "baseline_top1_accuracy": results["baseline_correct"].mean(),
        "mc_top1_accuracy": results["mc_correct"].mean(),
        "chance_top1_accuracy": results["chance_accuracy"].mean(),
        "avg_prob_assigned_to_winner": results["prob_assigned_to_winner"].mean(),
        "winner_missing_history_rate": (~results["winner_had_history"]).mean(),
    })


if __name__ == "__main__":
    from features import load_clean_data

    df = load_clean_data()
    results = run_backtest(df)
    results.to_csv("backtest_results.csv", index=False)

    print("=== All races ===")
    print(summarize(results))
    print()

    print("=== Excluding cold starts (winner had zero prior history) ===")
    print(summarize(results[results["winner_had_history"]]))
    print()

    print("=== 2016+ only (denser data coverage) ===")
    recent = results[results["date"] >= "2016-01-01"]
    print(summarize(recent))
    print()

    print("=== 2016+, excluding cold starts ===")
    print(summarize(recent[recent["winner_had_history"]]))
    print()

    print("Worst calibrated races (actual winner given lowest predicted probability):")
    print(results.sort_values("prob_assigned_to_winner").head(10)[
        ["date", "actual_winner", "field_size", "winner_had_history", "prob_assigned_to_winner", "mc_correct"]
    ])
