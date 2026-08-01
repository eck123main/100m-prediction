"""
Backtest the model against real finals: for each final, rebuild every
athlete's stats using only data known before that race (via
compute_stats_before), predict the field, and compare to what actually
happened. Every race is genuinely leak-free — no result is ever used to
predict itself.
"""

import numpy as np
import pandas as pd

from features import compute_stats_before, get_real_races
from predict import predict_race, simulate_race, elo_win_probs, blend_win_probs

MIN_FIELD_SIZE = 3
MAX_FIELD_SIZE = 10  # real 100m finals are 3-10 lanes; bigger "finals" in the
                      # raw data are mislabeled full-meet result dumps

ELO_WEIGHTS_TO_COMPARE = [0.3, 0.5, 0.7]


def get_real_finals(df):
    """Finals with a plausible field size, one row per race."""
    return get_real_races(df[df["round"] == "final"])


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
    top_pick_prob = win_probs.iloc[0] if len(win_probs) > 0 else np.nan
    prob_assigned = win_probs.get(actual_winner, 0.0)
    if actual_winner in win_probs.index:
        winner_rank = win_probs.index.get_loc(actual_winner) + 1  # win_probs is sorted descending
    else:
        winner_rank = np.nan

    elo_probs = elo_win_probs(field, stats)
    elo_winner = elo_probs.index[0] if len(elo_probs) > 0 else None

    result = {
        "source_url": race_df["source_url"].iloc[0],
        "date": date,
        "field_size": len(field),
        "n_scored": len(win_probs),
        "actual_winner": actual_winner,
        "winner_had_history": actual_winner in stats.index,
        "baseline_correct": baseline_winner == actual_winner,
        "mc_correct": mc_winner == actual_winner,
        "top_pick": mc_winner,
        "top_pick_prob": top_pick_prob,
        "winner_rank": winner_rank,
        "prob_assigned_to_winner": prob_assigned,
        "elo_correct": elo_winner == actual_winner,
        "elo_prob_assigned_to_winner": elo_probs.get(actual_winner, 0.0),
        "chance_accuracy": 1 / len(field),
    }

    for w in ELO_WEIGHTS_TO_COMPARE:
        blended = blend_win_probs(win_probs, elo_probs, elo_weight=w)
        blend_winner = blended.index[0] if len(blended) > 0 else None
        result[f"blend{int(w*100)}_correct"] = blend_winner == actual_winner
        result[f"blend{int(w*100)}_prob_assigned_to_winner"] = blended.get(actual_winner, 0.0)

    return result


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
    out = {
        "races_evaluated": n,
        "baseline_top1_accuracy": results["baseline_correct"].mean(),
        "mc_top1_accuracy": results["mc_correct"].mean(),
        "elo_top1_accuracy": results["elo_correct"].mean(),
        "chance_top1_accuracy": results["chance_accuracy"].mean(),
        "avg_prob_assigned_to_winner": results["prob_assigned_to_winner"].mean(),
        "avg_elo_prob_assigned_to_winner": results["elo_prob_assigned_to_winner"].mean(),
        "winner_missing_history_rate": (~results["winner_had_history"]).mean(),
    }
    for w in ELO_WEIGHTS_TO_COMPARE:
        out[f"blend{int(w*100)}_top1_accuracy"] = results[f"blend{int(w*100)}_correct"].mean()
    return pd.Series(out)


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
    print()

    warm = results[results["winner_had_history"]]
    misses = warm[~warm["mc_correct"]]
    hits = warm[warm["mc_correct"]]

    print("=== Miss-pattern breakdown (excluding cold starts) ===")
    print(f"Total misses: {len(misses)} / {len(warm)}")
    print()
    print("Where did the actual winner rank in the model's own probabilities, when missed?")
    print(misses["winner_rank"].value_counts().sort_index())
    print()
    print(f"Actual winner ranked in model's top 2: {(misses['winner_rank'] <= 2).mean():.1%} of misses")
    print(f"Actual winner ranked in model's top 3: {(misses['winner_rank'] <= 3).mean():.1%} of misses")
    print()
    print("Model's own confidence in its top pick — hits vs misses:")
    print(f"  hits:   mean top_pick_prob = {hits['top_pick_prob'].mean():.3f}, median = {hits['top_pick_prob'].median():.3f}")
    print(f"  misses: mean top_pick_prob = {misses['top_pick_prob'].mean():.3f}, median = {misses['top_pick_prob'].median():.3f}")
    print()
    print("Confidently-wrong misses (top_pick_prob >= 0.40 but still wrong):")
    confident_wrong = misses[misses["top_pick_prob"] >= 0.40]
    print(confident_wrong[["date", "actual_winner", "top_pick", "top_pick_prob", "field_size"]].to_string())
    print()
    print("Calibration check — bucket by top_pick_prob, see actual hit rate per bucket:")
    warm = warm.copy()
    warm["prob_bucket"] = pd.cut(warm["top_pick_prob"], bins=[0, 0.2, 0.3, 0.4, 0.5, 1.0])
    print(warm.groupby("prob_bucket", observed=True)["mc_correct"].agg(["mean", "count"]))
    print()

    print("=== Does adding Elo (head-to-head) fix the confidently-wrong MC misses? ===")
    for w in ELO_WEIGHTS_TO_COMPARE:
        col = f"blend{int(w*100)}_correct"
        n_fixed = confident_wrong[col].sum()
        print(f"  elo_weight={w}: fixed {n_fixed} / {len(confident_wrong)} confidently-wrong MC misses")
