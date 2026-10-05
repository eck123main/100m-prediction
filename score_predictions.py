"""
Grade logged predictions (from `predict.py --log`) against actual results.

    py -3.14 score_predictions.py [predictions_log.csv]

For each logged race with a URL, fetches the result page and finds the
final's winner. Races not run yet are reported as pending. This is the
live, out-of-sample check — unlike backtest.py, nothing here could have
been tuned on these races.
"""

import sys

import numpy as np
import pandas as pd

from features import ATHLETE_ALIASES
from scraper import scrape_hub_race, scrape_race

LOG_PATH = sys.argv[1] if len(sys.argv) > 1 else "predictions_log.csv"
EPS = 1e-3  # same floor as backtest.py, so log-loss is comparable


def actual_winner(race_url):
    """Winner of the race's final, or None if no result is published yet."""
    if "calendar-results" in race_url:
        results = scrape_hub_race(race_url)
    else:
        results = scrape_race(race_url.rstrip("/").rsplit("/", 1)[0] + "/result")
    final = results[(results["round"] == "final") & (results["heat"] == 1)].dropna(subset=["time"])
    if final.empty:
        return None
    name = final.loc[final["time"].idxmin(), "ATHLETE"].strip().title()
    return ATHLETE_ALIASES.get(name, name)


def main():
    log = pd.read_csv(LOG_PATH)
    rows = []
    for (logged_at, url), pred in log.dropna(subset=["race_url"]).groupby(["logged_at", "race_url"]):
        try:
            winner = actual_winner(url)
        except Exception as e:  # page not up yet, network error, etc.
            winner, err = None, str(e)[:60]
        else:
            err = None
        if winner is None:
            rows.append({"logged_at": logged_at, "race_url": url, "status": "pending", "note": err})
            continue
        probs = pred.set_index("athlete")["win_prob"].sort_values(ascending=False)
        p = probs.get(winner, 0.0)
        rows.append({
            "logged_at": logged_at, "race_url": url, "status": "scored",
            "winner": winner, "top_pick": probs.index[0],
            "correct": probs.index[0] == winner,
            "prob_to_winner": p, "logloss": -np.log(max(p, EPS)),
        })

    report = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(report.drop(columns=["race_url"]).to_string(index=False))
    scored = report[report["status"] == "scored"]
    if len(scored):
        print(f"\nScored {len(scored)} races: top-1 {scored['correct'].mean():.1%}, "
              f"mean log-loss {scored['logloss'].mean():.3f}, "
              f"mean prob to winner {scored['prob_to_winner'].mean():.1%}")
    print(f"Pending: {(report['status'] == 'pending').sum()}")


if __name__ == "__main__":
    main()
