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
