"""
Is the race model's spread right? (predict.simulate_race `sd_scale`.)

simulate_race is a normal race model (Thurstone; Henery 1981 for horse
racing): each athlete's time ~ N(form, consistency). Its win probabilities
are only calibrated if the spread is right, and consistency is fitted to
each athlete's past scatter, not to how often finals produce upsets. This
scales every spread by one factor and checks which factor scores best: >1
flattens the probabilities, <1 sharpens them. It's the "temperature" of the
model, the usual one-parameter recalibration of probabilistic forecasts.

Backtests every final with each scale using exact integration (no Monte
Carlo noise), picks the best by log-loss on finals before 2022, and
confirms on 2022+ with a paired bootstrap against 1.0 (the project's tuning
rule). If the pick wins on train and the 2022+ CI isn't worse, set
predict.SD_SCALE to it and re-run backtest.py. Uses predict.FORM_PRIOR, so
re-run this if the prior changes.

    py -3.14 tune_spread.py
"""

import pandas as pd

from backtest import DEFAULT_ELO_WEIGHT, TUNE_SPLIT_DATE, get_real_finals
from evaluation import expected_calibration_error, multiclass_brier, paired_bootstrap_ci, winner_log_loss
from features import RACE_KEYS, compute_stats_before, load_clean_data
from predict import FORM_PRIOR, blend_win_probs, elo_win_probs, prior_unknown_elo, simulate_race

SCALES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.35, 1.5, 1.75, 2.0]
BASELINE = 1.0


def score_scales(race, df, scales=SCALES, prior=FORM_PRIOR, elo_weight=DEFAULT_ELO_WEIGHT,
                 entrants=None):
    """One row of per-scale scores for one final (None if nobody finished).
    If entrants is a dict, (scale -> list) of (prob, won) per athlete is
    appended for per-entrant calibration."""
    finishers = race.dropna(subset=["time"])
    if finishers.empty:
        return None
    date, field = race["date"].iloc[0], race["ATHLETE"].tolist()
    winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]
    stats = compute_stats_before(date, df)
    elo = elo_win_probs(field, stats, unknown_elo=prior_unknown_elo(prior))
    row = {"date": date}
    for s in scales:
        p = blend_win_probs(simulate_race(field, stats, prior=prior, method="exact", sd_scale=s),
                            elo, elo_weight=elo_weight)
        row[f"ll_{s}"] = winner_log_loss(p, winner)
        row[f"brier_{s}"] = multiclass_brier(p, field, winner)
        if entrants is not None:
            entrants.setdefault(s, []).extend(
                (float(p.get(a, 0.0)), a == winner) for a in dict.fromkeys(field))
    return row


def main():
    df = load_clean_data()
    groups = list(get_real_finals(df).groupby(RACE_KEYS))
    rows, entrants = [], {}
    for i, (_, race) in enumerate(groups, start=1):
        row = score_scales(race, df, entrants=entrants)
        if row is not None:
            rows.append(row)
        if i % 250 == 0:
            print(f"  {i}/{len(groups)} finals", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv("tune_spread_results.csv", index=False)

    train, test = res[res["date"] < TUNE_SPLIT_DATE], res[res["date"] >= TUNE_SPLIT_DATE]
    for label, part in [("train (pre-2022)", train), ("confirm (2022+)", test)]:
        print(f"\n{label}: {len(part)} finals")
        for s in SCALES:
            print(f"  sd x{s:<5} log-loss {part[f'll_{s}'].mean():.4f}   "
                  f"brier {part[f'brier_{s}'].mean():.4f}")

    print("\nPer-entrant ECE, all finals:")
    for s in SCALES:
        prob, won = zip(*entrants[s]) if entrants.get(s) else ((), ())
        print(f"  sd x{s:<5} ECE {expected_calibration_error(prob, won):.4f}")

    best = min(SCALES, key=lambda s: train[f"ll_{s}"].mean())
    print(f"\nBest on train: sd x{best}")
    for metric in ["ll", "brier"]:
        mean, lo, hi = paired_bootstrap_ci(test[f"{metric}_{best}"], test[f"{metric}_{BASELINE}"])
        print(f"  2022+ {metric} change vs x{BASELINE}: {mean:+.4f} (95% CI {lo:+.4f} to {hi:+.4f})")


if __name__ == "__main__":
    main()
