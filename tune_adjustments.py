"""
Do the time adjustments help? (features.ROUND_OFFSETS_TWO_WAY, WIND_QUADRATIC.)

Both change adj_time when the data is loaded, so they can't be tuned per
race the way tune_spread.py tunes sd_scale: this loads the data once per
combination, prints the fitted round offsets and wind terms, and backtests
every final with exact integration (no Monte Carlo noise).

  two_way   — round offsets fitted jointly with athlete ability (two-way
              fixed effects) instead of the one-pass within-athlete average,
              which shrinks them toward 0 when round mixes differ.
  quadratic — wind correction b*w + c*w^2 (headwind costs more than the same
              tailwind gains; Mureika, arXiv physics/0006057) instead of b*w.

Same rule as the other tuners: adopt a setting only if it wins on finals
before 2022 and the 2022+ paired bootstrap CI against the current setting
isn't worse. Then set the constant in features.py and re-run backtest.py.
For the wind term, also check that the fitted c is positive.

    py -3.14 tune_adjustments.py
"""

import itertools

import pandas as pd

import features
from backtest import DEFAULT_ELO_WEIGHT, TUNE_SPLIT_DATE, get_real_finals
from evaluation import paired_bootstrap_ci, winner_log_loss
from features import RACE_KEYS, compute_stats_before, load_clean_data
from predict import FORM_PRIOR, blend_win_probs, elo_win_probs, prior_unknown_elo, simulate_race


def score_finals(df, prior=FORM_PRIOR, elo_weight=DEFAULT_ELO_WEIGHT):
    """One row per final: RACE_KEYS, date and the winner's log-loss."""
    rows = []
    for keys, race in get_real_finals(df).groupby(RACE_KEYS):
        finishers = race.dropna(subset=["time"])
        if finishers.empty:
            continue
        date, field = race["date"].iloc[0], race["ATHLETE"].tolist()
        winner = finishers.loc[finishers["time"].idxmin(), "ATHLETE"]
        stats = compute_stats_before(date, df)
        p = blend_win_probs(simulate_race(field, stats, prior=prior, method="exact"),
                            elo_win_probs(field, stats, unknown_elo=prior_unknown_elo(prior)),
                            elo_weight=elo_weight)
        rows.append(dict(zip(RACE_KEYS, keys), date=date, ll=winner_log_loss(p, winner)))
    return pd.DataFrame(rows)


def main():
    current = (features.ROUND_OFFSETS_TWO_WAY, features.WIND_QUADRATIC)
    scores = {}
    for two_way, quad in itertools.product([False, True], repeat=2):
        features.ROUND_OFFSETS_TWO_WAY, features.WIND_QUADRATIC = two_way, quad
        df = load_clean_data()
        offsets = {k: round(v, 4) for k, v in df.attrs["round_offsets"].items()}
        print(f"two_way={two_way} quadratic={quad}: wind b={df.attrs['wind_coefficient']:+.4f} "
              f"c={df.attrs['wind_quadratic']:+.5f}  round offsets {offsets}", flush=True)
        scores[(two_way, quad)] = score_finals(df).set_index(RACE_KEYS)
    features.ROUND_OFFSETS_TWO_WAY, features.WIND_QUADRATIC = current

    base = scores[current]
    print(f"\nlog-loss by setting (current = two_way={current[0]}, quadratic={current[1]}):")
    for cfg, res in scores.items():
        both = base[["date", "ll"]].join(res[["ll"]], rsuffix="_new", how="inner")
        line = f"  two_way={cfg[0]!s:<5} quadratic={cfg[1]!s:<5}"
        for label, part in [("pre-2022", both[both["date"] < TUNE_SPLIT_DATE]),
                            ("2022+", both[both["date"] >= TUNE_SPLIT_DATE])]:
            line += f"  {label} {part['ll_new'].mean():.4f} ({len(part)})"
        test = both[both["date"] >= TUNE_SPLIT_DATE]
        if cfg != current and len(test):
            mean, lo, hi = paired_bootstrap_ci(test["ll_new"], test["ll"])
            line += f"  2022+ vs current {mean:+.4f} [{lo:+.4f}, {hi:+.4f}]"
        print(line)


if __name__ == "__main__":
    main()
