"""
Does a field-relative form prior help? (predict.simulate_race `prior`.)

Without a prior, an athlete with no usable history gets 0% and every
cold-start winner costs the log-loss floor (-ln 0.001 = 6.9); 13% of 2024+
finals are cold starts. The prior simulates those athletes as "field median
+ offset, spread sd" and can also shrink sparse athletes' form toward it.

Backtests every final with each config below, picks the best by log-loss on
finals before 2022 and confirms on 2022+ with a paired bootstrap against no
prior (the project's tuning rule). If the pick is better on train and the
confirm CI isn't worse, set predict.FORM_PRIOR to it and re-run backtest.py.

    py -3.14 tune_prior.py
"""

import pandas as pd

from backtest import TUNE_SPLIT_DATE, get_real_finals
from evaluation import multiclass_brier, paired_bootstrap_ci, winner_log_loss
from features import RACE_KEYS, compute_stats_before, load_clean_data
from predict import blend_win_probs, elo_win_probs, prior_unknown_elo, simulate_race

CONFIGS = {"off": None}
for offset in [0.0, 0.1, 0.2, 0.3]:
    CONFIGS[f"o{offset}"] = {"offset": offset, "sd": 0.15, "races": 0.0}
for offset in [0.1, 0.2]:
    for races in [0.5, 1.0, 2.0]:
        CONFIGS[f"o{offset}_k{races}"] = {"offset": offset, "sd": 0.15, "races": races}


def score_configs(race, df, configs=CONFIGS, elo_weight=0.1):
    """One row of per-config scores for one final (None if nobody finished)."""
    finishers = race.dropna(subset=["time"])
    if finishers.empty:
        return None
    date, field = race["date"].iloc[0], race["ATHLETE"].tolist()
    winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]
    stats = compute_stats_before(date, df)
    # Cold start = the winner has no usable time (not in the table, or only
    # DNFs/DQs on record), i.e. the case the prior is for.
    cold = winner not in stats.index or pd.isna(stats.at[winner, "weighted_avg_time"])
    row = {"date": date, "cold_start": cold}
    elo_cache = {}
    for name, prior in configs.items():
        # Same Elo handling as predict_race_full: with a prior, athletes with
        # no history get BASE_ELO on the Elo side instead of nothing.
        unknown_elo = prior_unknown_elo(prior)
        if unknown_elo not in elo_cache:
            elo_cache[unknown_elo] = elo_win_probs(field, stats, unknown_elo=unknown_elo)
        # exact integration, not Monte Carlo: no sampling noise between configs
        p = blend_win_probs(simulate_race(field, stats, prior=prior, method="exact"),
                            elo_cache[unknown_elo], elo_weight=elo_weight)
        row[f"ll_{name}"] = winner_log_loss(p, winner)
        row[f"brier_{name}"] = multiclass_brier(p, field, winner)
        row[f"top1_{name}"] = len(p) > 0 and p.index[0] == winner
    return row


def main():
    df = load_clean_data()
    groups = list(get_real_finals(df).groupby(RACE_KEYS))
    rows = []
    for i, (_, race) in enumerate(groups, start=1):
        row = score_configs(race, df)
        if row is not None:
            rows.append(row)
        if i % 250 == 0:
            print(f"  {i}/{len(groups)} finals", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv("tune_prior_results.csv", index=False)

    train, test = res[res["date"] < TUNE_SPLIT_DATE], res[res["date"] >= TUNE_SPLIT_DATE]
    for label, part in [("train (pre-2022)", train), ("confirm (2022+)", test),
                        ("2022+ cold starts only", test[test["cold_start"]])]:
        print(f"\n{label}: {len(part)} finals")
        for name in CONFIGS:
            print(f"  {name:<12} log-loss {part[f'll_{name}'].mean():.4f}   "
                  f"brier {part[f'brier_{name}'].mean():.4f}   top-1 {part[f'top1_{name}'].mean():.1%}")

    best = min(CONFIGS, key=lambda n: train[f"ll_{n}"].mean())
    print(f"\nBest on train: {best} = {CONFIGS[best]}")
    for metric in ["ll", "brier"]:
        mean, lo, hi = paired_bootstrap_ci(test[f"{metric}_{best}"], test[f"{metric}_off"])
        print(f"  2022+ {metric} change vs off: {mean:+.4f} (95% CI {lo:+.4f} to {hi:+.4f})")


if __name__ == "__main__":
    main()
