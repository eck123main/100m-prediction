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


# Empirical-Bayes prior for athletes with little or no usable history
# (see simulate_race). None = off: unknown athletes get 0% and sparse
# athletes' form is used as-is (the behaviour up to 2026-11). Values to try
# are in tune_prior.py; set this only if it wins there (choose on pre-2022
# finals, confirm on 2022+ with the paired bootstrap).
# Example: {"offset": 0.15, "sd": 0.15, "races": 1.0}
FORM_PRIOR = None


def _norm_cdf(z):
    """Standard normal CDF without scipy (Abramowitz & Stegun 7.1.26 erf,
    max abs error ~1.5e-7)."""
    x = np.abs(z) / np.sqrt(2)
    t = 1 / (1 + 0.3275911 * x)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erf = 1 - poly * np.exp(-x * x)
    return 0.5 * (1 + np.sign(z) * erf)


def exact_win_probs(mu, sd, fr, n_grid=4000, n_local=400):
    """The quantity simulate_race estimates, by numerical integration instead
    of sampling: P(i wins) = fr_i * integral of pdf_i(t) * prod_{j != i}
    (1 - fr_j * cdf_j(t)) dt — athlete i finishes in time t and everyone else
    either doesn't finish or is slower. No Monte Carlo noise (10,000 runs
    leave ~0.5 percentage points of noise on a 30% favourite), so model
    variants can be compared on the same races without seed effects.
    Sums to P(at least one finisher), like the simulation.

    The grid is one even grid over the whole field plus n_local points within
    +-8 sd of each athlete, so an athlete with a much tighter spread than the
    rest still gets enough points under their density."""
    mu, sd, fr = (np.asarray(a, dtype=float) for a in (mu, sd, fr))
    if len(mu) == 0:
        return np.empty(0)
    sd = np.maximum(sd, 1e-3)
    lo, hi = (mu - 8 * sd).min(), (mu + 8 * sd).max()
    local = (mu[:, None] + sd[:, None] * np.linspace(-8, 8, n_local)[None, :]).ravel()
    t = np.unique(np.concatenate([np.linspace(lo, hi, n_grid), local]))
    z = (t[None, :] - mu[:, None]) / sd[:, None]
    pdf = np.exp(-0.5 * z ** 2) / (sd[:, None] * np.sqrt(2 * np.pi))
    survive = 1 - fr[:, None] * _norm_cdf(z)  # j hasn't beaten time t
    out = np.empty(len(mu))
    for i in range(len(mu)):
        others = np.prod(np.delete(survive, i, axis=0), axis=0)
        out[i] = fr[i] * np.trapezoid(pdf[i] * others, t) if hasattr(np, "trapezoid") \
            else fr[i] * np.trapz(pdf[i] * others, t)
    return out


def simulate_race(athlete_names, stats_table, n_simulations=10000, min_races=1, prior=None,
                  method="mc"):
    """Monte Carlo simulate the race: model each athlete as a normal distribution
    (mean = weighted_avg_time, spread = consistency), simulate many times, and
    return win probabilities. min_races filters out athletes with too little
    history to trust (avoids overconfident predictions from sparse data).

    Each simulated run, an athlete first has to actually produce a valid time —
    drawn as a coin flip against their finish_rate — before their time even
    enters that run's comparison. This lets a DQ/DNF-prone athlete's history
    cost them win probability, instead of every simulated race assuming
    everyone finishes clean.

    prior (dict, optional) is a field-relative empirical-Bayes prior, as in
    hierarchical models of athletics performance (e.g. Griffin et al.;
    arXiv 2405.17214) where athletes with few results are pulled toward a
    population level:
      offset — prior mean, in seconds slower than the median form of the
               known athletes in this field (a debutant in a final is
               usually not as fast as the athletes with a record);
      sd     — prior spread (s) for athletes with no usable time;
      races  — pseudo-races of prior weight; each known athlete's form is
               shrunk as (W*form + races*prior) / (W + races), with W their
               recency-weighted race count (form_weight). 0 = no shrinkage.
    With a prior, athletes with no usable history are simulated from it
    instead of being dropped with 0% — without it, every cold-start winner
    costs the maximum log-loss.

    method="exact" integrates the same model numerically (exact_win_probs)
    instead of sampling; n_simulations is then ignored."""
    names = list(dict.fromkeys(athlete_names))
    field = stats_table.loc[stats_table.index.intersection(names)].copy()
    field = field.dropna(subset=["weighted_avg_time"])
    field = field[field["races_used"] >= min_races]

    fallback_std = field["consistency"].mean() if "consistency" in field and field["consistency"].notna().any() else 0.05
    fallback_finish_rate = field["finish_rate"].mean() if "finish_rate" in field and field["finish_rate"].notna().any() else 0.95

    missing = [a for a in names if a not in field.index]
    if missing and prior is None:
        print(f"Warning: excluded (no data or below min_races={min_races}): {set(missing)}")

    if field.empty and (prior is None or not missing):
        return pd.Series(dtype=float)

    mu = field["weighted_avg_time"].to_numpy(dtype=float)
    sd = field["consistency"].fillna(fallback_std).to_numpy(dtype=float)
    fr = field["finish_rate"].fillna(fallback_finish_rate).to_numpy(dtype=float)
    index = field.index

    if prior is not None:
        prior_mu = (np.median(mu) if len(mu) else 0.0) + prior.get("offset", 0.15)
        k = float(prior.get("races", 0.0))
        if k > 0 and len(mu):
            w_col = "form_weight" if "form_weight" in field else "races_used"
            w = field[w_col].fillna(0).to_numpy(dtype=float)
            mu = (w * mu + k * prior_mu) / (w + k)
        if missing:
            mu = np.concatenate([mu, np.full(len(missing), prior_mu)])
            sd = np.concatenate([sd, np.full(len(missing), prior.get("sd", 0.15))])
            fr = np.concatenate([fr, np.full(len(missing), fallback_finish_rate)])
            index = index.append(pd.Index(missing))

    if method == "exact":
        return pd.Series(exact_win_probs(mu, sd, fr), index=index).sort_values(ascending=False)

    # All runs at once: one row per simulated race, one column per athlete.
    finished = np.random.random((n_simulations, len(mu))) <= fr
    times = np.where(finished, np.random.normal(mu, sd, (n_simulations, len(mu))), np.inf)
    someone_finished = finished.any(axis=1)  # everyone DNF-ing is very rare; no winner
    winners = times[someone_finished].argmin(axis=1)
    wins = np.bincount(winners, minlength=len(mu))

    win_probs = pd.Series(wins, index=index) / n_simulations
    return win_probs.sort_values(ascending=False)


def elo_win_probs(athlete_names, stats_table, unknown_elo=None):
    """Win probabilities from head-to-head Elo rating alone (ignores time/
    consistency/reliability entirely) — the Bradley-Terry extension of the
    pairwise Elo formula: p_i proportional to 10^(elo_i/400). An athlete in
    the stats table with no rating history gets BASE_ELO (via
    compute_stats_before). Athletes not in the table at all are excluded,
    unless unknown_elo is given: then they get that rating (predict_race_full
    passes BASE_ELO when the form prior is on, so a debutant isn't left at 0
    on the Elo side while the time side gives them a chance)."""
    names = list(dict.fromkeys(athlete_names))
    elo = stats_table["elo"].reindex(names)
    missing = elo.index[elo.isna()]
    if len(missing) and unknown_elo is None:
        print(f"Warning: no usable data for {set(missing)} — excluded from prediction")
    elo = elo.dropna() if unknown_elo is None else elo.fillna(unknown_elo)

    strength = 10 ** (elo / 400)
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


def predict_race_full(athlete_names, stats_table, n_simulations=10000, min_races=1, elo_weight=0.1,
                      prior="default"):
    """Recommended prediction: blend the time-based Monte Carlo simulation
    with head-to-head Elo. elo_weight=0.1 was chosen in backtest.py by
    log-loss on finals before 2022 over a 0-1 grid, and holds up on 2022+
    finals (2026-10 rebuild: 295 finals, heats now rated as separate races).
    After the all-rounds championship data, 0.0 and 0.1 tie on pre-2022
    log-loss (1.471 vs 1.478) while 0.1 is clearly better on 2022+ (1.869
    vs 1.896), so 0.1 is kept.
    Elo alone is a weaker signal than the time model; a small weight helps
    probability calibration, larger weights hurt it.
    prior defaults to FORM_PRIOR (see simulate_race); pass None to force it off."""
    prior = FORM_PRIOR if isinstance(prior, str) and prior == "default" else prior
    mc_probs = simulate_race(athlete_names, stats_table, n_simulations=n_simulations,
                             min_races=min_races, prior=prior)
    elo_probs = elo_win_probs(athlete_names, stats_table, unknown_elo=prior_unknown_elo(prior))
    return blend_win_probs(mc_probs, elo_probs, elo_weight=elo_weight)


def prior_unknown_elo(prior):
    """Elo rating for athletes with no history: BASE_ELO (where every athlete
    starts) when a form prior is on, None (= exclude them, the old
    behaviour) when it's off. A prior can override it with an "elo" key."""
    if prior is None:
        return None
    from features import BASE_ELO
    return prior.get("elo", BASE_ELO)


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

    # reindex, not .loc: with a FORM_PRIOR, athletes with no history are in probs too
    table = stats.reindex(probs.index)[["weighted_avg_time", "finish_rate", "races_used", "elo"]].copy()
    table.insert(0, "win_prob", probs)

    for rank, (name, row) in enumerate(table.iterrows(), start=1):
        if pd.isna(row["weighted_avg_time"]):
            print(f"  {rank}. {name:<28} {row['win_prob']:>5.1%}   (no usable history: prior only)")
            continue
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
