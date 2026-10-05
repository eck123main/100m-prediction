# 100m Prediction

Predicts men's 100m race outcomes from historical World Athletics results
(dense 2012-2026 coverage, plus every round of every World Championships /
Olympics back to 1983, plus ~1,150 extra 2024-2026 meets). ~57,000 result rows scraped from worldathletics.org, through September 2026.

## Quick start: predict an upcoming race

```
py -3.14 predict.py "Noah Lyles" "Kishane Thompson" "Fred Kerley" "Akani Simbine"
```

Or fetch the field from a worldathletics.org race page, optionally replaying
a past race using only data from before it:

```
py -3.14 predict.py --startlist "<race or meeting URL>" [--before 2025-09-13]
```

Add `--log` to save the prediction to `predictions_log.csv`; after the race,
`py -3.14 score_predictions.py` grades every logged prediction against the
actual result. Add bookmaker decimal odds with
`--odds "Oblique Seville=2.5,Noah Lyles=3.2"` and the scorer compares the
model against the betting market (margin removed) on the same races.

Prints each athlete's win probability plus the numbers behind it (recency-
weighted time, finish rate, race count, Elo rating). Names are matched
case-insensitively; anyone the model has no usable data for is listed
separately at the bottom rather than silently dropped.

**Requires pandas >= 2.2** (for `include_groups`). The default `python`/`py`
on this machine is 3.8 with pandas 2.0.3, which will crash — use `py -3.14`
(or another interpreter with a current pandas) explicitly, as above.

## Website

```
py -3.14 -m pip install -r requirements.txt
py -3.14 -m streamlit run app.py
```

Opens at http://localhost:8501 with three tabs: predict a race (pick athletes
or paste a World Athletics link), replay any past final leak-free, and the
model's track record (accuracy, calibration, live predictions).

To put it online for free: push to GitHub, sign in at share.streamlit.io with
GitHub, click "Create app", pick this repo and `app.py`.

## How it works

1. **`scraper.py` / `links.py` / `collect_data.py`** — scrape race results
   from worldathletics.org into `100m_races_dataset.csv`. After adding new
   meetings to `links.py`, run `py -3.14 collect_data.py --new-only` — it
   scrapes only URLs not yet in the CSV and never drops existing rows.
2. **`features.py`** — turn raw race rows into leak-free, point-in-time
   athlete stats:
   - Wind-adjusts every time via a within-athlete regression coefficient
     (not a guessed physical constant — estimated from this dataset).
   - Round-adjusts heats/semis to a final-equivalent time, since athletes
     often ease off once qualified.
   - Reliability: a Beta-shrunk finish rate (DNF/DQ/DNS history), so a
     handful of races doesn't read as a false 0% or 100%.
   - Elo rating: sequential head-to-head rating from real single-race
     pairwise "who finished ahead of whom" results. A race is one
     `(source_url, round, heat)` group, so each heat is rated separately.
   - `compute_stats_before(cutoff_date, df)` computes all of the above using
     only data strictly before `cutoff_date` — this is what makes backtesting
     honest (no race is ever used to predict itself).
3. **`predict.py`** — turns those stats into a prediction:
   - `predict_race()` — naive baseline, ranks by recency-weighted time alone.
   - `simulate_race()` — Monte Carlo: each athlete is a normal distribution
     (mean = weighted time, spread = consistency), with a finish-rate coin
     flip each simulated run so a DQ-prone athlete can simulate not
     finishing at all.
   - `elo_win_probs()` — win probability from head-to-head Elo alone.
   - `predict_race_full()` — **the recommended entry point.** Blends
     Monte Carlo and Elo at a 90/10 weighting (Monte Carlo/Elo), chosen by
     log-loss on pre-2022 finals over a 0-1 grid and checked on 2022+.
4. **`backtest.py`** — validates all of the above against ~295 real finals
   (filtered to plausible field sizes), and tunes `elo_weight` with an
   out-of-time split. Run `py -3.14 backtest.py` for the full breakdown
   (~5 min).

## Validated accuracy

Backtested leak-free against real finals (see `backtest.py` for the exact
methodology):

| | Top-1 accuracy | vs. chance |
|---|---|---|
| The original 295 elite finals | 51.2% | 12.4% |
| All 3,219 finals (incl. NCAA/national/small meets) | 45.7% | ~15% |
| All finals excluding cold-start winners* (2,530) | 58.0% | ~15% |

Most finals in the backtest are now from the 2024-2026 meets added via athlete
profiles; 21% of their winners have no earlier results (the data starts in
2024 for most lower-level athletes). Simply picking the fastest recent
adjusted time scores about the same top-1; the model's value is in its
probabilities (log-loss 1.421 on the original 295 finals, down from 1.649
before the robust spread and the extra 2024-2026 data).

\* cold start = the actual winner had zero prior races in the dataset —
unpredictable in principle, not a model failure.

~40-45% top-1 accuracy for 8-person world-class sprint finals is the
realistic range for this kind of data — these races are decided by
hundredths of a second and real day-of factors (reaction time, tactical
racing, nerves) that aren't in this dataset. Treat the output as *win
probabilities to weigh*, not a confident single prediction — roughly half of
the model's misses had the actual winner ranked in its own top 2.

## Known limitations

- **Cold start**: ~2% of elite-final winners (21% across all finals incl. small 2024-2026 meets) have zero prior history in the
  dataset (debutants, or the first race of an early era) — unpredictable by
  construction.
- **No start times/splits/lane data** — only finishing time, wind, round,
  reaction time (where published), and record flags.
- A handful of rows have physically impossible times (e.g. 45.12s). Verified
  against the live worldathletics.org source — these are genuinely published
  there as-is (likely a DNF/injury/fall coded as a numeric mark instead of a
  DNF flag), not a scraper parsing bug. Filtered to NaN in `features.py`.
- `--startlist` is verified on championship pages; on Diamond League /
  hub pages the pre-race start-list format hasn't been seen live yet.
- Each race is dated by its own day, so a championship's earlier rounds
  inform its final; same-day rounds (often semis + final) don't.
