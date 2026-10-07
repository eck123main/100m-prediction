"""
Does indoor 60m form help? Backtests every final from 2023 on with the
converted 60m results weighted 0 / 0.5 / 1 in form history, tunes on
2023-24 and confirms on 2025-26 (paired bootstrap on log-loss).

    py -3.14 tune_indoor.py
"""

import numpy as np
import pandas as pd

from backtest import EPS, get_real_finals
from features import RACE_KEYS, compute_stats_before, load_clean_data
from predict import blend_win_probs, elo_win_probs, simulate_race

WEIGHTS = [0.0, 0.5, 1.0]
START, SPLIT = "2023-01-01", "2025-01-01"


def main():
    df = load_clean_data()
    print(f"60m->100m ratio: {df.attrs['indoor_60m_ratio']:.4f}, "
          f"{len(df.attrs['indoor_60m'])} indoor rows")
    finals = get_real_finals(df)
    finals = finals[finals["date"] >= START]
    rows = []
    groups = list(finals.groupby(RACE_KEYS))
    for i, (_, race) in enumerate(groups, start=1):
        finishers = race.dropna(subset=["time"])
        if finishers.empty:
            continue
        date, field = race["date"].iloc[0], race["ATHLETE"].tolist()
        winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]
        row = {"date": date}
        for w in WEIGHTS:
            stats = compute_stats_before(date, df, indoor_weight=w)
            np.random.seed(0)
            p = blend_win_probs(simulate_race(field, stats), elo_win_probs(field, stats), elo_weight=0.1)
            row[f"ll_{w}"] = -np.log(max(p.get(winner, 0.0), EPS))
            row[f"top1_{w}"] = len(p) > 0 and p.index[0] == winner
        rows.append(row)
        if i % 250 == 0:
            print(f"  {i}/{len(groups)} finals", flush=True)
    res = pd.DataFrame(rows)

    for name, part in [("tune 2023-24", res[res["date"] < SPLIT]), ("confirm 2025-26", res[res["date"] >= SPLIT])]:
        print(f"\n{name} ({len(part)} finals)")
        for w in WEIGHTS:
            print(f"  weight {w}: log-loss {part[f'll_{w}'].mean():.4f}, top-1 {part[f'top1_{w}'].mean():.1%}")
    tune = res[res["date"] < SPLIT]
    best = min(WEIGHTS, key=lambda w: tune[f"ll_{w}"].mean())
    test = res[res["date"] >= SPLIT]
    diff = (test[f"ll_{best}"] - test["ll_0.0"]).to_numpy()
    rng = np.random.default_rng(0)
    boot = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
    print(f"\nBest on tune: {best}. Confirm-set log-loss change vs 0: {diff.mean():+.4f} "
          f"(95% CI {np.percentile(boot, 2.5):+.4f} to {np.percentile(boot, 97.5):+.4f})")


if __name__ == "__main__":
    main()
