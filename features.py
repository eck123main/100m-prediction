"""
Turn race-level rows into athlete-level features: cleaning, recency-weighted
average time, consistency, and cutoff-based stats for leak-free backtesting.
"""

import pandas as pd
import numpy as np

# A race's weight halves every ~6 months. Tuned 2026-10-05 over
# {180, 365, 730, 1460, inf} days: 180 had the best log-loss on pre-2022
# finals (1.455 vs 1.479 at 730) and also on 2022+ finals (1.848 vs 1.871),
# though the 2022+ gain is within noise (95% CI -0.072..+0.029).
HALF_LIFE_DAYS = 180

# Spread (see robust_spread). Tuned 2026-10-05 against the old plain std
# over all history: pre-2022 log-loss -0.070 (95% CI -0.127..-0.009),
# 2022+ +0.009 (CI -0.024..+0.044, i.e. no measurable change).
SPREAD_WINDOW_DAYS = 730
SPREAD_PRIOR_RACES = 5

# Indoor 60m results (collect_data.py --indoor-60m) converted to 100m-
# equivalents and blended into form with this weight per race (0 = off).
INDOOR_60M_CSV = "60m_indoor_dataset.csv"
INDOOR_60M_WEIGHT = 0.0

# Men's 100m world record is 9.58s; even a weak heat qualifier at the
# competition levels this scraper covers finishes well under 13s. Times
# outside this band (e.g. one row records 45.12s) were checked against the
# live worldathletics.org source (both the old HTML tables and the newer
# __NEXT_DATA__ JSON) and are genuinely published there as-is — not a
# scraper parsing bug. They're presumably a DNF/injury/fall that World
# Athletics coded as a numeric mark instead of a DNF flag. Treated as NaN
# here either way, since they're not a representative sprint time.
MIN_PLAUSIBLE_TIME = 9.0
MAX_PLAUSIBLE_TIME = 13.0

# One race = one (source_url, round, heat) group. A single real 100m
# heat/semi/final has 3-10 lanes; groups with more rows than that are
# mislabeled multi-heat/full-meet dumps (e.g. rows scraped before the heat
# column existed, which default to heat 1), not one race — pairwise-comparing everyone in one of those would
# credit made-up head-to-head results between people who never actually
# raced each other.
RACE_KEYS = ["source_url", "round", "heat"]
MIN_REAL_RACE_SIZE = 3
MAX_REAL_RACE_SIZE = 10

# The same athlete published under different names across pages/years
# (title-cased form -> canonical form, WA's current spelling). Found by
# matching first name + surname + country; only clear same-person cases.
ATHLETE_ALIASES = {
    "Marvin Bracy": "Marvin Bracy-Williams",
    "Jeff Demps": "Jeffery Demps",
    "Ngoni Makusha": "Ngonidzashe Makusha",
    "Deondre Batson": "Diondre Batson",
}

BASE_ELO = 1500
ELO_K = 24
# Multiplier on ELO_K per round, in case heats (where athletes ease off once
# qualified) should count less. Tested 2026-10-05 on 295 finals: heats at
# 1/0.5/0.25/0, semis at 1/0.75/0.5, and overall K x0.67/x1.5 all gave the
# same blended accuracy (47.1%) and log-loss within 0.002 at elo_weight=0.1,
# so everything stays at 1.0. See context.md.
ELO_ROUND_K = {"final": 1.0, "semi-final": 1.0, "heats": 1.0}


def load_clean_data(csv_path="100m_races_dataset.csv"):
    """Load the dataset and clean names/dates/round so grouping works correctly."""
    df = pd.read_csv(csv_path)
    df["ATHLETE"] = df["ATHLETE"].str.strip().str.title().replace(ATHLETE_ALIASES)
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    # Hand-timed marks ("10.1h") parse to no time. They're neither a usable
    # time (0.1s resolution) nor a non-finish, so drop them rather than let
    # reliability count them as DNFs.
    hand_timed = df["time"].isna() & df["record_flag"].astype(str).str.fullmatch(r"\d+(\.\d+)?h")
    df = df[~hand_timed].copy()

    implausible = (df["time"] < MIN_PLAUSIBLE_TIME) | (df["time"] > MAX_PLAUSIBLE_TIME)
    df.loc[implausible, "time"] = np.nan

    # Fall back to inferring round from the URL only where it's missing.
    # Trust the stored column otherwise: hub pages (calendar-results URLs)
    # share one URL across every round of the meeting, so re-deriving round
    # from the URL for those rows would collapse heats/semis/final into
    # whatever infer_round() defaults to (see MAX_REAL_RACE_SIZE note below
    # for the fallout when this used to run unconditionally).
    def infer_round(url):
        if "/semi-final/" in url:
            return "semi-final"
        elif "/heats/" in url:
            return "heats"
        else:
            return "final"

    missing_round = df["round"].isna() | (df["round"].str.strip() == "")
    df.loc[missing_round, "round"] = df.loc[missing_round, "source_url"].apply(infer_round)

    # Rows without a heat id (scraped before it existed) collapse into heat 1,
    # i.e. the old (source_url, round) grouping — groupby would otherwise
    # silently drop NaN keys.
    if "heat" not in df.columns:
        df["heat"] = 1
    df["heat"] = df["heat"].fillna(1).astype(int)

    coefficient = estimate_wind_coefficient(df)
    df["adj_time"] = df["time"] - coefficient * df["wind"]
    df["adj_time"] = df["adj_time"].fillna(df["time"])
    df.attrs["wind_coefficient"] = coefficient

    round_offsets = estimate_round_offsets(df)
    df["adj_time"] = df["adj_time"] - df["round"].map(round_offsets).fillna(0)
    df.attrs["round_offsets"] = round_offsets

    df.attrs["elo_history"] = compute_elo_history(df)
    df.attrs["indoor_60m"], df.attrs["indoor_60m_ratio"] = load_indoor_60m(df)

    return df


def get_real_races(df):
    """Rows belonging to a single genuine race (plausible field size).
    Keyed on RACE_KEYS, not source_url alone: hub pages (calendar-results
    URLs) share one URL across every round of a meeting, and one round can
    hold several heats, so coarser grouping would conflate separate races
    into one oversized group and exclude even a real, correctly-sized final
    just because it shares a URL with the meeting's other races."""
    sizes = df.groupby(RACE_KEYS)["ATHLETE"].transform("size")
    return df[(sizes >= MIN_REAL_RACE_SIZE) & (sizes <= MAX_REAL_RACE_SIZE)]


def compute_elo_history(df, round_k=None):
    """Replay every real race in chronological order, updating Elo ratings
    via pairwise 'who finished ahead of whom' comparisons — this is the
    head-to-head / field-relative signal, as opposed to each athlete's solo
    average time. A race with n finishers decomposes into every pairwise
    comparison; each athlete's rating change is the average surprise across
    their n-1 comparisons that race, scaled by ELO_K.

    Returns one row per (ATHLETE, date, elo) — the athlete's rating right
    after that race. Look up a leak-free rating as of any cutoff via
    compute_elo_before, which takes the most recent row strictly before it.

    round_k overrides ELO_ROUND_K (per-round multiplier on ELO_K); a round
    with multiplier 0 is skipped entirely."""
    round_k = ELO_ROUND_K if round_k is None else round_k
    races = get_real_races(df).dropna(subset=["time", "date"]).sort_values("date")

    ratings = {}
    rows = []

    for _, race in races.groupby(RACE_KEYS, sort=False):
        race = race.sort_values("time")
        athletes = race["ATHLETE"].tolist()
        if len(athletes) < 2:
            continue
        date = race["date"].iloc[0]
        k = ELO_K * round_k.get(race["round"].iloc[0], 1.0)
        if k == 0:
            continue

        current = {a: ratings.get(a, BASE_ELO) for a in athletes}
        delta = {a: 0.0 for a in athletes}
        n = len(athletes)

        for i in range(n):
            for j in range(i + 1, n):
                faster, slower = athletes[i], athletes[j]
                expected_faster = 1 / (1 + 10 ** ((current[slower] - current[faster]) / 400))
                surprise = 1 - expected_faster  # actual result (faster won) minus expectation
                delta[faster] += surprise
                delta[slower] -= surprise

        for a in athletes:
            ratings[a] = current[a] + k * delta[a] / (n - 1)
            rows.append({"ATHLETE": a, "date": date, "elo": ratings[a]})

    return pd.DataFrame(rows, columns=["ATHLETE", "date", "elo"])


def compute_elo_before(cutoff_date, elo_history):
    """Each athlete's most recent Elo rating from a real race strictly before
    cutoff_date. Athletes with no prior rated race aren't included here —
    callers should default them to BASE_ELO (an unknown quantity, not a weak
    one)."""
    history = elo_history[elo_history["date"] < cutoff_date]
    if len(history) == 0:
        return pd.Series(dtype=float, name="elo")
    return history.sort_values("date").groupby("ATHLETE")["elo"].last()


def estimate_wind_coefficient(df, min_races=3, min_wind_std=0.3):
    """Seconds of time per 1 m/s of wind, estimated as a within-athlete
    fixed-effects regression: compares each athlete only against their own
    times across their own varying wind conditions, so a fast athlete who
    happens to race in windier conditions than a slow athlete doesn't get
    mistaken for a wind effect. Uses the whole dataset regardless of any
    backtest cutoff — this is a shared physical relationship (wind's effect
    on sprint time), not information about who wins a specific future race.

    Only athletes with min_races+ races and real variation in the wind
    they've faced (min_wind_std) contribute, since an athlete who has only
    ever raced in +0.5 conditions can't tell us anything about the slope."""
    valid = df.dropna(subset=["time", "wind"])
    counts = valid.groupby("ATHLETE").size()
    wind_std = valid.groupby("ATHLETE")["wind"].std()
    eligible = counts[(counts >= min_races) & (wind_std.reindex(counts.index).fillna(0) >= min_wind_std)].index
    valid = valid[valid["ATHLETE"].isin(eligible)]

    if len(valid) == 0:
        return 0.0

    dt = valid["time"] - valid.groupby("ATHLETE")["time"].transform("mean")
    dw = valid["wind"] - valid.groupby("ATHLETE")["wind"].transform("mean")

    denom = (dw ** 2).sum()
    if denom == 0:
        return 0.0
    return (dt * dw).sum() / denom


def estimate_round_offsets(df, baseline_round="final", min_races=3):
    """Seconds each round tends to run slower/faster than an athlete's own
    final-round pace, estimated the same fixed-effects way as the wind
    coefficient: only compares an athlete against their own times across
    rounds, so it isn't confounded by weaker athletes appearing in heats
    more often than finals. Only athletes with min_races+ races across 2+
    distinct rounds contribute, since the comparison needs actual variation.

    Returns {round_name: offset_seconds}, where offset is subtracted from
    adj_time to get a 'final-equivalent' estimate — heats typically comes
    out positive since athletes often ease off once they've qualified."""
    valid = df.dropna(subset=["adj_time", "round"])
    counts = valid.groupby("ATHLETE").size()
    rounds_per_athlete = valid.groupby("ATHLETE")["round"].nunique()
    eligible = counts[(counts >= min_races) & (rounds_per_athlete.reindex(counts.index).fillna(0) >= 2)].index
    valid = valid[valid["ATHLETE"].isin(eligible)]

    if len(valid) == 0:
        return {baseline_round: 0.0}

    demeaned = valid["adj_time"] - valid.groupby("ATHLETE")["adj_time"].transform("mean")
    round_effect = demeaned.groupby(valid["round"]).mean()

    baseline = round_effect.get(baseline_round, 0.0)
    return (round_effect - baseline).to_dict()


def compute_reliability_before(cutoff_date, df, prior_strength=8):
    """Per-athlete rate of producing a valid time (i.e. not a DNF/DQ/DNS), using
    only races strictly before cutoff_date. Shrunk toward the field-wide average
    via a Beta prior (worth prior_strength races) so an athlete with only 1-2
    starts doesn't get scored as a false 0% or 100% reliable."""
    history = df[df["date"] < cutoff_date]
    # Slicing propagates df.attrs (which holds elo_history, a DataFrame) onto
    # history and everything derived from it. pandas' own join/concat later
    # compares .attrs for equality to decide what to keep, and comparing two
    # DataFrames with == raises instead of returning a bool — strip attrs
    # here so that comparison never has a DataFrame to choke on.
    history.attrs = {}
    if len(history) == 0:
        return pd.DataFrame(columns=["starts", "finishes", "finish_rate"])

    prior_rate = history["time"].notna().mean()
    alpha0 = prior_rate * prior_strength
    beta0 = (1 - prior_rate) * prior_strength

    g = history.groupby("ATHLETE")["time"]
    starts = g.size()
    finishes = g.count()  # non-NaN times
    return pd.DataFrame({
        "starts": starts,
        "finishes": finishes,
        "finish_rate": (finishes + alpha0) / (starts + alpha0 + beta0),
    })


def robust_spread(valid, cutoff_date, window_days=SPREAD_WINDOW_DAYS, prior_races=SPREAD_PRIOR_RACES):
    """How much an athlete's adjusted times scatter, for the simulation.

    Uses the median absolute deviation (x1.4826 to match a normal sigma) over
    the last window_days only, so one bad old race (an injury, a jog-through
    heat) doesn't inflate it — a plain std over all history made erratic
    athletes look like they had more upside. Shrunk toward the field's typical
    spread by prior_races pseudo-races so a handful of results can't give an
    implausibly tight or wide spread."""
    recent = valid[valid["date"] >= cutoff_date - pd.Timedelta(days=window_days)]
    g = recent.groupby("ATHLETE")["adj_time"]
    mad = (recent["adj_time"] - g.transform("median")).abs().groupby(recent["ATHLETE"]).median() * 1.4826
    n = g.size()
    pooled = np.nanmedian(mad[n >= 3]) if (n >= 3).any() else 0.08
    dof = (n - 1).clip(lower=0)
    return np.sqrt((dof * mad ** 2 + prior_races * pooled ** 2) / (dof + prior_races))


def load_indoor_60m(df, csv_path=INDOOR_60M_CSV):
    """Indoor 60m results as 100m-equivalent times.

    The conversion is one ratio (100m / 60m), the median over athletes who
    ran both in the same calendar year, comparing their median adjusted 100m
    time with their median 60m time. Returns (rows, ratio); rows is empty if
    there's no 60m data yet."""
    empty = pd.DataFrame(columns=["ATHLETE", "date", "adj_time"])
    try:
        indoor = pd.read_csv(csv_path)
    except FileNotFoundError:
        return empty, np.nan
    indoor["ATHLETE"] = indoor["ATHLETE"].str.strip().str.title().replace(ATHLETE_ALIASES)
    indoor["date"] = pd.to_datetime(indoor["date"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    indoor = indoor[indoor["time"].between(6.3, 7.5)].dropna(subset=["date"])

    key = lambda d: [d["ATHLETE"], d["date"].dt.year]
    m60 = indoor.groupby(key(indoor))["time"].median()
    m100 = df.dropna(subset=["adj_time", "date"])
    m100 = m100.groupby(key(m100))["adj_time"].median()
    pairs = pd.concat([m60.rename("t60"), m100.rename("t100")], axis=1, join="inner")
    if len(pairs) < 20:
        return empty, np.nan
    ratio = (pairs["t100"] / pairs["t60"]).median()
    return indoor.assign(adj_time=indoor["time"] * ratio)[["ATHLETE", "date", "adj_time"]], ratio


def compute_stats_before(cutoff_date, df, half_life_days=HALF_LIFE_DAYS, indoor_weight=None):
    """Recency-weighted stats using only races strictly before cutoff_date.
    Prevents leaking a target race's own result into an athlete's 'known form'.
    Vectorized (one groupby, no per-athlete Python) — it runs once per race
    in the backtest."""
    history = df[df["date"] < cutoff_date]
    history.attrs = {}  # see compute_reliability_before for why
    if len(history) == 0:
        return pd.DataFrame(columns=["weighted_avg_time", "races_used", "consistency",
                                      "finish_rate", "starts", "finishes", "elo"])

    valid = history.dropna(subset=["adj_time", "date"])
    form_rows = valid[["ATHLETE", "date", "adj_time"]].assign(mult=1.0)
    indoor_weight = INDOOR_60M_WEIGHT if indoor_weight is None else indoor_weight
    indoor = df.attrs.get("indoor_60m")
    if indoor_weight > 0 and indoor is not None and len(indoor):
        indoor = indoor[indoor["date"] < cutoff_date]
        form_rows = pd.concat([form_rows, indoor.assign(mult=indoor_weight)], ignore_index=True)
    weights = form_rows["mult"] * 0.5 ** ((cutoff_date - form_rows["date"]).dt.days / half_life_days)
    g = form_rows.assign(w=weights, wt=weights * form_rows["adj_time"]).groupby("ATHLETE")
    athletes = pd.Index(sorted(set(history["ATHLETE"].dropna()) | set(form_rows["ATHLETE"])), name="ATHLETE")
    stats = pd.DataFrame({
        "weighted_avg_time": g["wt"].sum() / g["w"].sum(),
        "races_used": g.size().astype(float),
        "consistency": robust_spread(valid, cutoff_date),
    }).reindex(athletes)
    stats["races_used"] = stats["races_used"].fillna(0.0)

    reliability = compute_reliability_before(cutoff_date, df)
    stats = stats.join(reliability[["finish_rate", "starts", "finishes"]])

    elo = compute_elo_before(cutoff_date, df.attrs["elo_history"])
    stats["elo"] = elo.reindex(stats.index).fillna(BASE_ELO)

    return stats


def compute_all_time_stats(df):
    """Recency-weighted stats using every race in the dataset (no cutoff).
    Use this for real predictions on upcoming races, not backtests."""
    reference_date = df["date"].max()
    return compute_stats_before(reference_date + pd.Timedelta(days=1), df)