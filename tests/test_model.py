"""Unit tests on small synthetic data. Run: py -3.14 -m pytest tests"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import features  # noqa: E402
from evaluation import (EPS, calibration_table, expected_calibration_error,  # noqa: E402
                        multiclass_brier, paired_bootstrap_ci, winner_log_loss)
from predict import blend_win_probs, predict_race_full, simulate_race  # noqa: E402


# ---------------------------------------------------------------- evaluation

def test_winner_log_loss_floor_and_value():
    p = pd.Series({"A": 0.5, "B": 0.5})
    assert winner_log_loss(p, "A") == pytest.approx(np.log(2))
    assert winner_log_loss(p, "Z") == pytest.approx(-np.log(EPS))


def test_multiclass_brier():
    field = ["A", "B", "C"]
    assert multiclass_brier(pd.Series({"A": 1.0}), field, "A") == pytest.approx(0.0)
    assert multiclass_brier(pd.Series({"B": 1.0}), field, "A") == pytest.approx(2.0)
    uniform = pd.Series({a: 1 / 3 for a in field})
    assert multiclass_brier(uniform, field, "A") == pytest.approx((2 / 3) ** 2 + 2 * (1 / 3) ** 2)


def test_calibration_perfect_and_off():
    prob = np.array([0.1] * 10 + [0.6] * 10)
    won = np.array([1] + [0] * 9 + [1] * 6 + [0] * 4)
    assert expected_calibration_error(prob, won) == pytest.approx(0.0)
    t = calibration_table(prob, won)
    assert t["count"].sum() == 20
    assert expected_calibration_error(np.full(10, 0.9), np.zeros(10)) == pytest.approx(0.9)


def test_paired_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(1)
    old = rng.random(200)
    new = old - 0.1
    mean, lo, hi = paired_bootstrap_ci(new, old)
    assert mean == pytest.approx(-0.1)
    assert lo <= mean <= hi


# ---------------------------------------------------------------- simulate_race prior

def make_stats(rows):
    return pd.DataFrame(rows, columns=["ATHLETE", "weighted_avg_time", "races_used", "form_weight",
                                       "consistency", "finish_rate", "elo"]).set_index("ATHLETE")


STATS = make_stats([
    ("Fast", 9.90, 10, 6.0, 0.08, 1.0, 1600),
    ("Mid", 10.00, 10, 6.0, 0.08, 1.0, 1550),
    ("Slow", 10.20, 10, 6.0, 0.08, 1.0, 1450),
    ("Sparse", 9.85, 1, 0.2, 0.10, 1.0, 1500),
])


def test_no_prior_drops_unknown():
    np.random.seed(0)
    p = simulate_race(["Fast", "Mid", "Nobody"], STATS, n_simulations=2000)
    assert "Nobody" not in p.index
    assert p.sum() == pytest.approx(1.0)


def test_prior_gives_unknown_a_probability():
    np.random.seed(0)
    prior = {"offset": 0.1, "sd": 0.15, "races": 0.0}
    p = simulate_race(["Fast", "Mid", "Slow", "Nobody"], STATS, n_simulations=20000, prior=prior)
    assert set(p.index) == {"Fast", "Mid", "Slow", "Nobody"}
    assert p.sum() == pytest.approx(1.0)
    assert 0 < p["Nobody"] < p["Fast"]


def test_prior_shrinks_sparse_athlete_only_much():
    prior_off = {"offset": 0.2, "sd": 0.15, "races": 0.0}
    prior_on = {"offset": 0.2, "sd": 0.15, "races": 2.0}
    field = ["Fast", "Mid", "Sparse"]
    np.random.seed(0)
    p0 = simulate_race(field, STATS, n_simulations=20000, prior=prior_off)
    np.random.seed(0)
    p1 = simulate_race(field, STATS, n_simulations=20000, prior=prior_on)
    # Sparse (0.2 effective races) is pulled far toward median + 0.2s; the
    # established athletes barely move, so they gain.
    assert p1["Sparse"] < p0["Sparse"] - 0.1
    assert p1["Fast"] > p0["Fast"]


def test_prior_with_only_unknowns_is_uniform():
    np.random.seed(0)
    p = simulate_race(["X", "Y"], STATS, n_simulations=20000, prior={"offset": 0.1, "sd": 0.15})
    assert p["X"] == pytest.approx(0.5, abs=0.03)


def test_duplicate_names_counted_once():
    np.random.seed(0)
    p = simulate_race(["Fast", "Fast", "Nobody", "Nobody"], STATS, n_simulations=2000, prior={"offset": 0.1})
    assert len(p) == 2


def test_predict_race_full_prior_none_matches_off():
    np.random.seed(0)
    a = predict_race_full(["Fast", "Mid", "Nobody"], STATS, n_simulations=2000, prior=None)
    assert "Nobody" not in a.index
    assert a.sum() == pytest.approx(1.0)


def test_exact_matches_monte_carlo():
    stats = STATS.copy()
    stats.loc["Slow", "finish_rate"] = 0.8
    field = ["Fast", "Mid", "Slow", "Sparse"]
    np.random.seed(0)
    mc = simulate_race(field, stats, n_simulations=200000)
    ex = simulate_race(field, stats, method="exact")
    assert set(mc.index) == set(ex.index)
    for a in field:
        assert ex[a] == pytest.approx(mc[a], abs=0.01)
    assert ex.sum() == pytest.approx(1.0, abs=1e-3)


def test_exact_two_equal_athletes_and_dnf_mass():
    from predict import exact_win_probs
    p = exact_win_probs([10.0, 10.0], [0.1, 0.1], [1.0, 1.0])
    assert p == pytest.approx([0.5, 0.5], abs=1e-4)
    # Nobody finishes with probability 0.5 * 0.5 -> probabilities sum to 0.75.
    p = exact_win_probs([10.0, 10.0], [0.1, 0.1], [0.5, 0.5])
    assert p.sum() == pytest.approx(0.75, abs=1e-4)


@pytest.mark.parametrize("sd_a,sd_b", [(0.1, 0.1), (0.005, 0.2), (0.3, 0.02)])
def test_exact_two_athletes_matches_closed_form(sd_a, sd_b):
    # P(A beats B) = Phi((mu_b - mu_a) / sqrt(sd_a^2 + sd_b^2)); the uneven
    # spreads check the per-athlete grid points.
    from math import erf, sqrt
    from predict import exact_win_probs
    mu_a, mu_b = 9.95, 10.0
    expected = 0.5 * (1 + erf((mu_b - mu_a) / sqrt(sd_a ** 2 + sd_b ** 2) / sqrt(2)))
    p = exact_win_probs([mu_a, mu_b], [sd_a, sd_b], [1.0, 1.0])
    assert p[0] == pytest.approx(expected, abs=1e-4)
    assert p.sum() == pytest.approx(1.0, abs=1e-4)


def test_sd_scale_flattens_and_default_unchanged():
    field = ["Fast", "Mid", "Slow"]
    base = simulate_race(field, STATS, method="exact")
    same = simulate_race(field, STATS, method="exact", sd_scale=1.0)
    wide = simulate_race(field, STATS, method="exact", sd_scale=2.0)
    tight = simulate_race(field, STATS, method="exact", sd_scale=0.5)
    assert same["Fast"] == pytest.approx(base["Fast"])
    assert tight["Fast"] > base["Fast"] > wide["Fast"]
    assert tight["Slow"] < base["Slow"] < wide["Slow"]


def test_form_uncertainty_sd_formula():
    from predict import form_uncertainty_sd
    sd = np.array([0.1, 0.1, 0.0, 0.1])
    w = np.array([1.0, np.nan, 10.0, 0.0])
    days = np.array([0.0, 0.0, 365.0, np.nan])
    assert form_uncertainty_sd(sd, w, days, None) == pytest.approx(sd)
    out = form_uncertainty_sd(sd, w, days, {"per_race": 1.0, "drift_per_year": 0.1})
    assert out[0] == pytest.approx(0.1 * np.sqrt(2))   # one race: mean as uncertain as a race
    assert out[1] == pytest.approx(0.1)                # unknown weight: no extra
    assert out[2] == pytest.approx(0.1)                # a year off: drift only
    assert out[3] == pytest.approx(0.1 * np.sqrt(11))  # weight floored at 0.1


def test_form_uncertainty_helps_sparse_underdog_only():
    stats = make_stats([("Est", 9.90, 10, 6.0, 0.08, 1.0, 1500),
                        ("New", 10.10, 1, 0.2, 0.08, 1.0, 1500)])
    stats["days_since_last"] = [10.0, 10.0]
    off = simulate_race(["Est", "New"], stats, method="exact", form_uncertainty=None)
    default = simulate_race(["Est", "New"], stats, method="exact")
    on = simulate_race(["Est", "New"], stats, method="exact", form_uncertainty={"per_race": 1.0})
    assert default["New"] == pytest.approx(off["New"])  # FORM_UNCERTAINTY is None by default
    assert off["New"] < on["New"] < 0.5
    assert on.sum() == pytest.approx(1.0, abs=1e-4)
    # works on a stats table without the new columns too
    assert simulate_race(["Fast", "Mid"], STATS, method="exact",
                         form_uncertainty={"drift_per_year": 0.1}).sum() == pytest.approx(1.0, abs=1e-4)


def test_score_scales_row(monkeypatch):
    import tune_spread
    monkeypatch.setattr(tune_spread, "compute_stats_before", lambda date, df: STATS)
    race = pd.DataFrame({"ATHLETE": ["Fast", "Mid", "Slow"], "time": [9.9, 10.0, None],
                         "date": pd.Timestamp("2024-01-01")})
    row = tune_spread.score_scales(race, None, scales=[0.8, 1.0], prior=None)
    assert set(row) == {"date", "ll_0.8", "brier_0.8", "ll_1.0", "brier_1.0"}
    assert row["ll_0.8"] < row["ll_1.0"]  # the favourite won, so sharper scores better


def test_exact_empty_field():
    from predict import exact_win_probs
    assert len(exact_win_probs([], [], [])) == 0


def test_norm_cdf_accuracy():
    from math import erf, sqrt
    from predict import _norm_cdf
    z = np.linspace(-5, 5, 101)
    expected = np.array([0.5 * (1 + erf(v / sqrt(2))) for v in z])
    assert np.max(np.abs(_norm_cdf(z) - expected)) < 1e-6


def test_elo_unknown_excluded_or_base():
    from features import BASE_ELO
    from predict import elo_win_probs, prior_unknown_elo
    p = elo_win_probs(["Fast", "Nobody"], STATS)
    assert list(p.index) == ["Fast"]
    p = elo_win_probs(["Fast", "Nobody", "Nobody"], STATS, unknown_elo=BASE_ELO)
    assert set(p.index) == {"Fast", "Nobody"}
    assert p.sum() == pytest.approx(1.0)
    assert prior_unknown_elo(None) is None
    assert prior_unknown_elo({"offset": 0.1}) == BASE_ELO
    assert prior_unknown_elo({"elo": 1400}) == 1400


def test_predict_race_full_prior_gives_unknown_elo_share():
    # With elo_weight=1 only the Elo side counts: the unknown athlete must
    # still get a share when a prior is on.
    p = predict_race_full(["Fast", "Nobody"], STATS, n_simulations=1000, elo_weight=1.0,
                          prior={"offset": 0.1, "sd": 0.15})
    assert p["Nobody"] > 0


def test_blend_union_and_normalised():
    mc = pd.Series({"A": 0.7, "B": 0.3})
    elo = pd.Series({"A": 0.4, "B": 0.4, "C": 0.2})
    b = blend_win_probs(mc, elo, elo_weight=0.5)
    assert set(b.index) == {"A", "B", "C"}
    assert b.sum() == pytest.approx(1.0)


# ---------------------------------------------------------------- features on a synthetic dataset

def synthetic_csv(tmp_path):
    """Three athletes, ten finals over two years: A ~9.90, B ~10.00, C ~10.10,
    with times shifted by a known 0.05 s per m/s of tailwind."""
    rng = np.random.default_rng(0)
    base = {"Ann A": 9.90, "Ben B": 10.00, "Cal C": 10.10, "Dan D": 10.20}
    rows = []
    for r in range(10):
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=60 * r)
        wind = rng.uniform(-2, 2)
        for name, t in base.items():
            rows.append({"ATHLETE": name, "COUNTRY": "X", "time": round(t - 0.05 * wind + rng.normal(0, 0.01), 2),
                         "record_flag": "", "Reaction Time": np.nan, "wind": round(wind, 1),
                         "date": date.strftime("%d/%m/%Y %H:%M:%S"), "venue": "V", "meet_name": f"M{r}",
                         "source_url": f"u{r}", "round": "final", "heat": 1})
    path = tmp_path / "races.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


@pytest.fixture
def df(tmp_path, monkeypatch):
    empty = pd.DataFrame(columns=["ATHLETE", "date", "adj_time"])
    monkeypatch.setattr(features, "load_indoor_60m", lambda d: (empty, np.nan))
    return features.load_clean_data(synthetic_csv(tmp_path))


def test_wind_coefficient_recovered(df):
    assert df.attrs["wind_coefficient"] == pytest.approx(-0.05, abs=0.01)


def test_stats_are_leak_free_and_ordered(df):
    cutoff = pd.Timestamp("2024-07-01")
    stats = features.compute_stats_before(cutoff, df)
    assert (stats["races_used"] == 4).all()  # finals on days 0, 60, 120, 180 only
    assert stats["form_weight"].between(0, 4).all()
    order = stats["weighted_avg_time"].sort_values().index.tolist()
    assert order == ["Ann A", "Ben B", "Cal C", "Dan D"]


def test_days_since_last(df):
    stats = features.compute_stats_before(pd.Timestamp("2024-07-01"), df)
    # last final before the cutoff is 2024-01-01 + 180 days = 2024-06-29
    assert (stats["days_since_last"] == 2).all()


def test_elo_ranks_consistent_winner_highest(df):
    stats = features.compute_all_time_stats(df)
    assert stats["elo"].idxmax() == "Ann A"
    assert stats["elo"].idxmin() == "Dan D"


def test_prior_end_to_end(df):
    stats = features.compute_all_time_stats(df)
    np.random.seed(0)
    p = predict_race_full(["Ann A", "Ben B", "Newcomer"], stats, n_simulations=5000,
                          prior={"offset": 0.1, "sd": 0.15, "races": 1.0})
    assert p.index[0] == "Ann A"
    assert p["Newcomer"] > 0
    assert p.sum() == pytest.approx(1.0)
