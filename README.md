# 100m Prediction

Predicts men's 100m race outcomes from historical World Athletics results
(dense 2012-2026 coverage, plus championship finals back to 1983). ~8,160
result rows scraped from worldathletics.org, through September 2026.

## Quick start: predict an upcoming race

```
py -3.14 predict.py "Noah Lyles" "Kishane Thompson" "Fred Kerley" "Akani Simbine"
```

Prints each athlete's win probability plus the numbers behind it (recency-
weighted time, finish rate, race count, Elo rating). Names are matched
case-insensitively; anyone the model has no usable data for is listed
separately at the bottom rather than silently dropped.

**Requires pandas >= 2.2** (for `include_groups`). The default `python`/`py`
on this machine is 3.8 with pandas 2.0.3, which will crash — use `py -3.14`
(or another interpreter with a current pandas) explicitly, as above.

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
   (~15-20 min).

## Validated accuracy

Backtested leak-free against real finals (see `backtest.py` for the exact
methodology):

| | Top-1 accuracy | vs. chance |
|---|---|---|
| All real finals (295) | 47.1% | 12.4% |
| Excluding cold-start winners* (268) | 51.9% | 12.2% |
| 2016+ finals (235) | 43.8% | 12.5% |

\* cold start = the actual winner had zero prior races in the dataset —
unpredictable in principle, not a model failure.

~40-45% top-1 accuracy for 8-person world-class sprint finals is the
realistic range for this kind of data — these races are decided by
hundredths of a second and real day-of factors (reaction time, tactical
racing, nerves) that aren't in this dataset. Treat the output as *win
probabilities to weigh*, not a confident single prediction — roughly half of
the model's misses had the actual winner ranked in its own top 2.

## Known limitations

- **Cold start**: ~9% of race winners have zero prior history in the
  dataset (debutants, or the first race of an early era) — unpredictable by
  construction.
- **No start times/splits/lane data** — only finishing time, wind, round,
  reaction time (where published), and record flags.
- A handful of rows have physically impossible times (e.g. 45.12s). Verified
  against the live worldathletics.org source — these are genuinely published
  there as-is (likely a DNF/injury/fall coded as a numeric mark instead of a
  DNF flag), not a scraper parsing bug. Filtered to NaN in `features.py`.
- No automated way to fetch an upcoming race's start list — the field has
  to be typed in by hand (see Quick start above).
- Multi-day championships: every round of a hub-format meeting carries the
  meeting's start date, so heats/semis of the same meeting aren't used to
  predict its final (conservative, not a leak).
