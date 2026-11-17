"""
Does adding form uncertainty to the spread help? (predict.simulate_race
`form_uncertainty`.)

consistency is an athlete's race-day scatter around their form, but the form
itself is an estimate: from 1-2 recent races it's uncertain, and after a
long layoff it may have drifted. Glicko handles the same two effects for
ratings (rating deviation shrinks with games, grows with inactivity). This
widens each athlete's spread to

    sd^2 * (1 + per_race / form_weight) + drift_per_year^2 * days_since_last / 365

and checks which setting scores best. Unlike tune_spread.py's global scale,
it flattens only the athletes we know little about.

Backtests every final with each config using exact integration (no Monte
Carlo noise), picks the best by log-loss on finals before 2022, and confirms
on 2022+ with a paired bootstrap against off (the project's tuning rule). If
the pick wins on train and the 2022+ CI isn't worse, set
predict.FORM_UNCERTAINTY to it and re-run backtest.py. Uses predict.FORM_PRIOR
and predict.SD_SCALE, so run it after tune_prior.py and tune_spread.py.

    py -3.14 tune_uncertainty.py
"""

import pandas as pd

from backtest import DEFAULT_ELO_WEIGHT, TUNE_SPLIT_DATE, get_real_finals
from evaluation import expected_calibration_error, multiclass_brier, paired_bootstrap_ci, winner_log_loss
from features import RACE_KEYS, compute_stats_before, load_clean_data
from predict import FORM_PRIOR, blend_win_probs, elo_win_probs, prior_unknown_elo, simulate_race

CONFIGS = {"off": None}
for per_race in [0.5, 1.0, 2.0]:
    CONFIGS[f"r{per_race}"] = {"per_race": per_race}
for drift in [0.05, 0.1]:
    CONFIGS[f"d{drift}"] = {"drift_per_year": drift}
    for per_race in [0.5, 1.0]:
        CONFIGS[f"r{per_race}_d{drift}"] = {"per_race": per_race, "drift_per_year": drift}
BASELINE = "off"


def score_configs(race, df, configs=CONFIGS, prior=FORM_PRIOR, elo_weight=DEFAULT_ELO_WEIGHT,
                  entrants=None):
    """One row of per-config scores for one final (None if nobody finished).
    If entrants is a dict, (config -> list) of (prob, won) per athlete is
    appended for per-entrant calibration."""
    finishers = race.dropna(subset=["time"])
    if finishers.empty:
        return None
    date, field = race["date"].iloc[0], race["ATHLETE"].tolist()
    winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]
    stats = compute_stats_before(date, df)
    elo = elo_win_probs(field, stats, unknown_elo=prior_unknown_elo(prior))
    row = {"date": date}
    for name, unc in configs.items():
        p = blend_win_probs(simulate_race(field, stats, prior=prior, method="exact", form_uncertainty=unc),
                            elo, elo_weight=elo_weight)
        row[f"ll_{name}"] = winner_log_loss(p, winner)
        row[f"brier_{name}"] = multiclass_brier(p, field, winner)
        if entrants is not None:
            entrants.setdefault(name, []).extend(
                (float(p.get(a, 0.0)), a == winner) for a in dict.fromkeys(field))
    return row


def main():
    df = load_clean_data()
    groups = list(get_real_finals(df).groupby(RACE_KEYS))
    rows, entrants = [], {}
    for i, (_, race) in enumerate(groups, start=1):
        row = score_configs(race, df, entrants=entrants)
        if row is not None:
            rows.append(row)
        if i % 250 == 0:
            print(f"  {i}/{len(groups)} finals", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv("tune_uncertainty_results.csv", index=False)

    train, test = res[res["date"] < TUNE_SPLIT_DATE], res[res["date"] >= TUNE_SPLIT_DATE]
    for label, part in [("train (pre-2022)", train), ("confirm (2022+)", test)]:
        print(f"\n{label}: {len(part)} finals")
        for name in CONFIGS:
            print(f"  {name:<12} log-loss {part[f'll_{name}'].mean():.4f}   "
                  f"brier {part[f'brier_{name}'].mean():.4f}")

    print("\nPer-entrant ECE, all finals:")
    for name in CONFIGS:
        prob, won = zip(*entrants[name]) if entrants.get(name) else ((), ())
        print(f"  {name:<12} ECE {expected_calibration_error(prob, won):.4f}")

    best = min(CONFIGS, key=lambda n: train[f"ll_{n}"].mean())
    print(f"\nBest on train: {best} = {CONFIGS[best]}")
    for metric in ["ll", "brier"]:
        mean, lo, hi = paired_bootstrap_ci(test[f"{metric}_{best}"], test[f"{metric}_{BASELINE}"])
        print(f"  2022+ {metric} change vs {BASELINE}: {mean:+.4f} (95% CI {lo:+.4f} to {hi:+.4f})")


if __name__ == "__main__":
    main()
