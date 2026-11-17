# Overnight report

## Round 1 — 2026-11-18

### Important: nothing was run this round

This session could not execute Python (every `py`/`python` call was denied:
there was no way to approve permission prompts). So **none of the code below
has been run, and the tests have not been run**. All changes were checked by
careful reading only. Git commands worked, so every step is committed.

First thing next session (or for you):

```
py -3.14 -m pip install --user pytest      # if not installed
py -3.14 -m pytest tests                   # new unit tests, a few seconds
py -3.14 tune_prior.py                     # decides FORM_PRIOR (see below)
py -3.14 backtest.py                       # now also prints Brier + calibration
```

No model defaults were changed, so the website and `backtest_results.csv`
behave exactly as before until you set `predict.FORM_PRIOR`.

### What I changed, and why

1. **Optional empirical-Bayes form prior** (`predict.simulate_race(prior=...)`,
   `predict.FORM_PRIOR`, default `None` = off). commit faf1bb6
   - The problem: an athlete with no usable history is dropped, so they get
     0%. When that athlete wins (13% of 2024+ finals, 19.6% of all finals),
     the race scores the log-loss floor −ln(0.001) = 6.9. That's probably
     about 0.9 of the 2.0 log-loss on 2024+ finals.
   - The fix: a prior relative to the field. Unknown athletes are simulated
     as "median form of the known athletes in this race + `offset` seconds,
     spread `sd`". Sparse athletes can also be shrunk toward the same prior
     by `races` pseudo-races, weighted by their recency-weighted race count.
     This is the idea behind the hierarchical Bayesian performance models in
     the research below: pull athletes with few results toward a population
     level.
   - `features.compute_stats_before` gains a `form_weight` column (effective
     number of races after recency weighting) for this.
   - `app.py` and the `predict.py` CLI table now use `reindex`, so they don't
     crash when an athlete without history is in the output.
2. **`tune_prior.py`** (commit 043bf49): backtests every final with 11 prior
   settings (off; offset 0/0.1/0.2/0.3 s; offset 0.1/0.2 with 0.5/1/2
   pseudo-races). It picks the best by log-loss on pre-2022 finals and
   confirms on 2022+ against "off" with a paired bootstrap CI. That is the
   project's existing tuning rule. It reports log-loss, Brier and top-1, plus
   2022+ cold-start races on their own, and writes `tune_prior_results.csv`.
   **If the chosen setting wins on train and the 2022+ CI isn't worse, set
   `FORM_PRIOR` to it, re-run `backtest.py` and commit.** One thing to watch:
   pre-2022 finals have very few cold starts, so train may favour a large
   offset (a weak prior). That choice is conservative but safe.
3. **Exact win probabilities** (`predict.exact_win_probs`,
   `simulate_race(method="exact")`, commit f5cfdd6). This computes the same
   model by numerical integration:
   P(i wins) = fr_i ∫ pdf_i(t) Π_{j≠i} (1 − fr_j·cdf_j(t)) dt.
   It has no Monte Carlo noise (10k runs leave about ±0.5 points on a 30%
   favourite) and is faster. `tune_prior.py` uses it so settings are compared
   without seed noise. The default is still `"mc"`. If the tests pass,
   switching the default to `"exact"` is a reasonable next step.
4. **Better evaluation** (new `evaluation.py`; `backtest.py`,
   `score_predictions.py`):
   - Multi-class **Brier score** per race (column `blend10_brier` in the
     backtest, `brier` / `book_brier` in live scoring). Unlike log-loss, it
     can't be dominated by a few 0%-winner races.
   - **Per-entrant calibration table + ECE**, using every athlete in every
     final instead of only the top pick (about 8× more points). Printed
     separately for pre-2022 and 2022+.
   - A shared `paired_bootstrap_ci`. The live scorer now prints a CI for
     model-minus-bookmaker log-loss.
   - `EPS` now lives in `evaluation.py`, and `backtest.EPS` still works.
5. **First unit tests** (`tests/test_model.py`, 20 tests; commits f360f30,
   f5cfdd6). They cover the scoring rules, the prior (unknown athletes get
   probability, sparse athletes are shrunk, prior None = old behaviour,
   duplicate names), exact vs Monte Carlo agreement, the normal-CDF
   accuracy, and a synthetic dataset through `load_clean_data`. That last
   test checks the wind coefficient is recovered (−0.05 s per m/s), the
   stats are leak-free, and the Elo ordering is right.

### Research

- Hierarchical Bayesian models of elite athletics performance shrink
  athletes with few results toward a population mean, and can say something
  even about athletes with no results in a season. Griffin et al. applied
  this to the 100m:
  [Modelling between- and within-season trajectories in elite athletic performance data (arXiv 2405.17214)](https://arxiv.org/abs/2405.17214);
  [Bayesian GARCH modelling of functional sports data (arXiv 2101.08175)](https://arxiv.org/abs/2101.08175).
  This is the basis for the form prior.
- Choosing a scoring rule: Wheatcroft argues the local log/ignorance score
  beats the Brier score and the RPS for comparing sports forecasters. So
  log-loss stays the selection metric, and Brier/ECE are diagnostics:
  [Evaluating probabilistic forecasts of football matches: the case against the RPS (arXiv 1908.08980)](https://arxiv.org/abs/1908.08980).
- Brier and ECE as complements to accuracy for win probabilities:
  [Rethinking evaluation metrics for probability estimation, esports (arXiv 2309.06248)](https://arxiv.org/abs/2309.06248).
  Calibration testing of published win probabilities:
  [Yeh, Rice & Dubin, NBA real-time forecasts (arXiv 2010.00781)](https://arxiv.org/abs/2010.00781).

### Ideas for next time

- Run the tests and `tune_prior.py`, and adopt `FORM_PRIOR` if it passes.
  This is the most likely log-loss gain available right now.
- Switch `simulate_race` to `method="exact"` by default once the tests pass.
  Then re-tune `elo_weight` on the noise-free numbers.
- Make the prior smarter. Set the offset from data: the debut performance of
  new athletes relative to the field, by meeting level. A debutant in a
  Diamond League final is different from one in an NCAA heat.
- Give the Elo side a prior too. Unknown athletes currently get nothing from
  Elo (they get BASE_ELO only if they're in the stats table).
- Season-phase / trajectory term, as in arXiv 2405.17214: early-season form
  vs peak (month of year, days since the athlete's last race).
- The `tune_indoor.py` run from the previous plan is still outstanding.

## Round 2 — 2026-11-18 (labelled "round 1" by the session prompt)

### Again: nothing was run

Python was blocked again (every `py` call needed an approval nobody could
give). Neither round's code has been executed or tested. I reviewed last
round's code by reading it (`predict.py`, `evaluation.py`, `tune_prior.py`,
the stats code in `features.py`, the tests). I found no definite bugs, so
this round adds small, default-off changes that stay safe if you never run
them. **All defaults are unchanged** (`FORM_PRIOR = None`, `SD_SCALE = 1.0`),
and with them the backtest output is the same as before, including the MC
random draws.

Run in this order:

```
py -3.14 -m pytest tests        # 20 old + 10 new test cases
py -3.14 tune_prior.py          # adopt FORM_PRIOR if it passes
py -3.14 tune_spread.py         # run AFTER setting FORM_PRIOR; adopt SD_SCALE if it passes
py -3.14 backtest.py
```

### What I changed, and why

1. **Accurate exact integration for uneven spreads** (commit df5f2a4).
   `exact_win_probs` used one even grid over the whole field. An athlete with
   a much tighter spread than the others could get too few grid points under
   their density. Now the grid also has 400 points within ±8 sd of each
   athlete, and an empty field returns an empty array. New tests check it
   against the closed form for two athletes,
   P(A beats B) = Φ((μB−μA)/√(σA²+σB²)), with uneven spreads
   (0.005 vs 0.2 s).
2. **Elo side for athletes with no history** (commit 5207733). This was an
   idea from last round. With a form prior on, a debutant got some
   probability from the time model but nothing from the Elo side, so the
   blend still gave them only 90% of a fair share. Now
   `elo_win_probs(unknown_elo=...)` rates them, and `prior_unknown_elo(prior)`
   gives `BASE_ELO` (where every athlete starts) when a prior is on and
   `None` (the old behaviour) when it's off. A prior dict can override this
   with an `"elo"` key. `predict_race_full`, `backtest.py` and
   `tune_prior.py` all use it, so tuning matches production.
   - `tune_prior.py`'s `cold_start` now also counts winners who are in the
     stats table with only DNFs/DQs (no usable time). Before, it counted
     only winners missing from the table, which undercounted the cases the
     prior is meant for.
3. **Spread calibration: `sd_scale` and `tune_spread.py`** (commit e5fd4fa).
   `simulate_race(sd_scale=...)` (default `predict.SD_SCALE = 1.0`)
   multiplies every athlete's race-day spread. This is the one-parameter
   "temperature" recalibration of a normal (Thurstone/Henery) race model:
   >1 flattens the probabilities, <1 sharpens them. `consistency` is fitted
   to each athlete's past scatter, which isn't necessarily the right spread
   for upsets in finals. The previous round's calibration tables are the
   place to check whether the model is overconfident.
   - `tune_spread.py` tries 0.7–2.0 with exact integration (no seed noise),
     picks the best on pre-2022 log-loss, and confirms on 2022+ with the
     paired bootstrap against 1.0. It also prints the per-entrant ECE for
     each scale and writes `tune_spread_results.csv`. It uses the current
     `FORM_PRIOR`, so tune the prior first.
   - Tests: 1.0 matches the default, the probabilities are monotone in the
     scale, and the score columns are right when stats are stubbed.

### Research

- Our simulation is the normal-error ranking model Henery proposed for
  horse races. Later work on win pools found it gives accurate ranking
  probabilities. Luce/Plackett-Luce is the same Thurstone structure with
  double-exponential noise, so switching to Plackett-Luce wouldn't add
  much; calibrating the spread is the lever that's left.
  [Ali, "Probability models on horse-race outcomes"](https://www.stat.berkeley.edu/~aldous/157/Papers/ali.pdf);
  [Parameter estimation for Thurstone choice models (arXiv 1705.00136)](https://arxiv.org/pdf/1705.00136)
  (the Thurstone/Luce equivalence, and why the noise distribution matters
  for inference).
- Time-weighted Plackett-Luce models for race forecasting (Formula 1), a
  possible later alternative to Elo for the head-to-head side:
  [Bayesian Analysis, 2018](https://projecteuclid.org/euclid.ba/1488250819).
- A survey of Bradley–Terry extensions (ties, home effects, dynamic
  ratings): [arXiv 2601.14727](https://arxiv.org/html/2601.14727v1).

### Ideas for next time

- Get Python running (allow `py` in `.claude/settings.json`, or run the four
  commands above yourself). Two rounds of untested code are now waiting, and
  running them is worth more than anything else.
- After `SD_SCALE` and `FORM_PRIOR` are fitted, re-tune `elo_weight` on
  exact probabilities. The three knobs interact.
- Use a per-athlete spread scale by experience (fewer races → wider), as a
  hierarchical alternative to one global scale.
- Replace Elo with a time-weighted Plackett-Luce rating fitted to full
  finishing orders (see the 2018 Bayesian Analysis link). It uses the whole
  order of each race, not just pairwise results.
- Still open from last round: a data-driven prior offset by meeting level,
  a season-phase/layoff term (days since last race), and `tune_indoor.py`.

## Round 3 — 2026-11-18 (labelled "round 2" by the session prompt)

### Still nothing was run

Python was blocked a third time (`py -3.14 -m pytest tests` was auto-denied:
there was no way to approve it). Three rounds of code are now untested. I
re-read last round's code (`predict.py`, `tune_prior.py`, `tune_spread.py`,
`backtest.py`, the stats code in `features.py`) and found no bugs. Since every
extra untested line adds risk, this round makes one focused, default-off
change. **Defaults are unchanged** (`FORM_UNCERTAINTY = None`), and with them
the output is the same as before, including the MC draws.

Run in this order (also noted in `context.md`):

```
py -3.14 -m pytest tests        # now 34 cases
py -3.14 tune_prior.py          # adopt FORM_PRIOR if it passes
py -3.14 tune_spread.py         # adopt SD_SCALE if it passes
py -3.14 tune_uncertainty.py    # adopt FORM_UNCERTAINTY if it passes
py -3.14 backtest.py
```

To stop this happening again, allow `py` for overnight sessions (e.g. a
`Bash(py -3.14:*)` / `PowerShell(py -3.14 *)` rule in `.claude/settings.json`).
I didn't change the permission settings myself.

### What I changed, and why

1. **Glicko-style form uncertainty** (commit 1759347).
   `simulate_race(form_uncertainty=...)`, default `predict.FORM_UNCERTAINTY = None`.
   - The problem: the simulation uses an athlete's form estimate as if it
     were exact and adds only their race-day scatter (`consistency`). An
     athlete with one recent race, or one coming back from a long layoff,
     gets as sharp a distribution as an established athlete who raced last
     week. That makes the model overconfident about exactly the athletes it
     knows least about. The prior's `races` shrinkage moves their *mean*;
     nothing widened their *spread*.
   - The fix: the predictive spread is now
     `sd² · (1 + per_race / W) + drift_per_year² · days_since_last / 365`.
     The first term is the variance of a mean of W races, where W is the
     recency-weighted race count (`form_weight`). The second is a random walk
     in true form since the last race. This is how Glicko's rating deviation
     works: it shrinks as games are played and grows with inactivity. It
     differs from `sd_scale`: it's per athlete, so it can flatten a sparse
     athlete's chances without flattening an established favourite's. This
     was the "per-athlete spread scale by experience" idea from last round.
   - `features.compute_stats_before` gains a `days_since_last` column (days
     from the athlete's last usable time to the cutoff).
   - Tests: the formula (including missing/zero weights), off = default =
     the old output, it helps a sparse underdog without pushing them past
     50%, it works on stats without the new columns, and `days_since_last`
     on the synthetic dataset.
2. **`tune_uncertainty.py`** (commit 718fee9). Tries `per_race` 0.5/1/2,
   `drift_per_year` 0.05/0.1 s, and their combinations, with exact
   integration. It picks the best on pre-2022 log-loss, confirms on 2022+
   with the paired bootstrap against off, prints the per-entrant ECE, and
   writes `tune_uncertainty_results.csv`. It uses the current `FORM_PRIOR`
   and `SD_SCALE`, so tune those first. Tested through `score_configs` with
   stubbed stats.

### Research

- Glicko: rating deviation RD falls after each game and grows during
  inactivity as RD = min(√(RD₀² + c²t), RD_unrated). The same two effects
  apply here: few races and a stale form estimate.
  [Glicko rating system (Wikipedia)](https://en.wikipedia.org/wiki/Glicko_rating_system);
  [Glickman's papers](http://www.glicko.net/glicko.html).
- The Bayesian predictive for a normal mean with known scatter σ after n
  observations has variance σ²(1 + 1/n). `per_race = 1` is that textbook
  case. Larger values allow for recency weighting and model error. Same
  hierarchical-shrinkage reasoning as round 1
  ([arXiv 2405.17214](https://arxiv.org/abs/2405.17214)).

### Ideas for next time

- Run everything above. This is still worth far more than more code.
- If `FORM_UNCERTAINTY` with drift helps, try the same drift on the Elo side
  (a Glicko-style rating: inactive athletes' ratings pulled toward BASE_ELO,
  or a Glicko-2 implementation in place of Elo).
- Re-tune `elo_weight` once prior, spread and uncertainty are fixed.
- Still open: a meeting-level prior offset, a season-phase term, and
  `tune_indoor.py`.
