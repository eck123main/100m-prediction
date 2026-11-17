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

## Round 4 — 2026-11-18 (labelled "round 3" by the session prompt)

### Decision: no new model code this round

Python was blocked a fourth time: `py -3.14 -m pytest tests` was auto-denied.
Three rounds of untested code are waiting, along with three default-off knobs
and three tuners. The knobs interact, and none has been fitted. Adding a
fourth untested knob would add risk and give you more to run, without making
the model any better until someone runs it. So I chose not to add more model
code, and spent the round on review and cleanup. **Nothing in the model
changed.**

### What I did

1. **Reviewed round 3's code by reading it.** This covered
   `form_uncertainty_sd`, its use in `simulate_race`, the new
   `days_since_last` column in `features.compute_stats_before`, and
   `tune_uncertainty.py`. I found no bugs. I also worked through the round-3
   test expectations by hand:
   - formula cases: √2·sd, the weight floor giving √11·sd, the drift-only year;
   - the sparse underdog's win chance rises from about 4% to about 18%, still below 50%;
   - in `test_score_uncertainty_row`, the favourite "Sparse" is widened, so the winner "Fast" gains.

   All of these should pass, though I couldn't run them to confirm.
2. **Cleaned up `context.md` → START HERE** (commit a175791). It had grown
   into overlapping notes from each round. It now has one table (knob →
   tuner → what it does), the order to run things in, and the rule for
   adopting a knob.

### Research

- Elite sprinters have two performance peaks a season: around the first week
  of July and the fourth week of August, the second matching major
  championships ([arXiv 1401.7474](https://arxiv.org/pdf/1401.7474)).
  Within-season trajectories vary a lot from one season to the next
  ([arXiv 2405.17214v2](https://arxiv.org/abs/2405.17214v2)). Both suggest a
  season-phase term: a championship final in August may be faster than the
  athlete's recency-weighted May/June form. This should be fitted within
  athletes, the same way the wind coefficient was, as an offset by week of
  the season.

### Ideas for next time (in priority order)

1. **Let `py` run.** For example, add `"Bash(py -3.14:*)"` and
   `"PowerShell(py -3.14 *)"` to `permissions.allow` in
   `.claude/settings.json`, or run the commands in START HERE yourself. I
   didn't change the permission settings: that's your call. Until one of
   these happens, more overnight rounds can't improve accuracy, only add
   untested code.
2. When Python runs: tests, then `tune_prior` → `tune_spread` →
   `tune_uncertainty` → `backtest`, then re-tune `elo_weight`.
3. **Speed up tuning.** All three tuners call `compute_stats_before` once per
   final. A shared per-final stats cache (e.g. a pickle keyed by date) would
   make re-tuning and joint tuning of the knobs cheap.
4. **Season-phase offset** (see the research above): a within-athlete
   regression of adjusted time on week of season, added to `adj_time` like
   the round offsets.
5. Still open: a meeting-level prior offset, Glicko-style inactivity on the
   Elo side, and `tune_indoor.py`.

## Round 5 — 2026-11-18 (labelled "round 4" by the session prompt)

### Still nothing was run

Python was blocked a fifth time: `py -3.14 -m pytest tests` was auto-denied,
and so was even `wc -l`. Only file tools and single git commands worked.
Instead of adding another tuning knob, I read the older core code
(`features.py`, which no earlier overnight round had reviewed) for bugs, and
found one.

### What I changed, and why

1. **Elo bug: same-day rounds were replayed in arbitrary order** (commits
   efea2e3, 19efc7c). **This changes default output slightly.**
   - Dates have no time of day (`04/08/2024 00:00:00`), and a championship's
     semis and final share a date. For example, Paris 2024's semis and final
     are both on 04/08/2024 in the CSV. `compute_elo_history` sorted on date
     alone with pandas' default unstable quicksort, so a final could be
     replayed *before* its semi. `compute_elo_before` then took `.last()`
     after another unstable sort, so the rating it returned for a later race
     could be the post-semi one, missing the final's update entirely. This
     hits exactly the championship finals that matter most.
   - The fix: a new `features.ROUND_ORDER` (heats → quarter-final →
     semi-final → final; unknown rounds go in the middle). The replay sorts
     on (date, round) with a stable sort, and the lookup sorts stably, so
     `.last()` is the most recent update.
   - Test: `test_elo_same_day_rounds_replayed_semi_then_final`. Athlete X
     loses the semi and then wins the final. The final rows are listed first,
     and the test also runs with the rows reversed. X's rating must dip and
     then rise above 1500, and the lookup must return the post-final value.
     I checked the numbers by hand: 1500 → 1488 → about 1500.5.
2. **`backtest.SAME_DAY_EARLIER_ROUNDS`** (commit 4e374b9). Default False,
   so the backtest output is unchanged.
   - The problem: the backtest builds a final's stats from races strictly
     before its date, so it never sees that day's semis. Live predictions
     (`compute_all_time_stats`, cutoff = last date + 1 day) *do* see them.
     So the backtest under-rates the model in exactly the situation users
     care about: predicting a championship final after the semis are run.
     A semi run hours earlier is also the freshest form signal there is.
   - The fix: `features.known_before(df, cutoff, before_round)`. Given the
     target race's round, it also admits rows from the same date whose round
     comes earlier. Same-day rows with an unknown round stay out, and the
     final itself can never get in. `compute_stats_before` and
     `compute_reliability_before` take `before_round`. Elo still uses
     strictly-earlier races. `evaluate_race` and `run_backtest` take
     `same_day=`.
   - `backtest.py` now ends with a paired-bootstrap log-loss comparison of
     the setting against its opposite, overall and on the races that changed.
   - Test: `test_same_day_earlier_rounds`. With the setting on, a same-day
     semi is counted (races, starts, `days_since_last = 0`, faster form). A
     heats race doesn't see it, an unknown round means off, and
     `evaluate_race` works both ways.
   - **Recommendation:** turn it on unless the comparison shows clear harm.
     It's a fidelity fix to the evaluation more than a model change.

### Research

- Wind is not linear: drag goes with (v − w)², so a headwind costs more
  time than the same tailwind gains. About 0.10 s for +2.0 m/s for men
  ([Mureika, back-of-the-envelope wind/altitude correction](https://arxiv.org/pdf/physics/0006057);
  [quasi-physical 100 m model](https://arxiv.org/pdf/physics/0007042);
  [Linthorne, wind measurement accuracy](https://www.scribd.com/document/520728995/WindAccuracy-Linthorne)).
  Our within-athlete fit is a single linear slope.
- Championship scheduling (semis and final on the same evening) is why the
  same-day handling matters. In our CSV, the Paris 2024 semi rows and final
  rows carry the same date.

### Ideas for next time

1. **Let `py` run** (see round 4). Everything since round 1 is untested.
2. Then run: tests (now 36 cases), `tune_prior` → `tune_spread` →
   `tune_uncertainty` → `backtest.py`. Read the same-day comparison at the
   end, and turn `SAME_DAY_EARLIER_ROUNDS` on if it's not worse. Also compare
   the backtest headline numbers with the old `backtest_results.csv` to see
   what the Elo fix did.
3. Pass `before_round` through the three tuners too, if same-day goes on.
   For now they call `compute_stats_before` directly, with it off.
4. **Asymmetric wind:** fit `time ~ a·w + b·w·|w|` within athlete, in place
   of the single slope. Adopt it only if `b` is clearly non-zero and the
   backtest agrees.
5. Same-day info for Elo: let the semi's Elo update count for the final.
   Elo history would need a round column, or `compute_elo_before` would need
   a round-aware cutoff.
6. Still open: the stats cache for tuners, the season-phase offset, a
   meeting-level prior offset, and `tune_indoor.py`.

## Round 6 — 2026-11-18 (labelled "round 5" by the session prompt)

### Still nothing was run

Python was blocked a sixth time: `py -3.14 -m pytest tests` was auto-denied.
Everything below was checked by reading and by hand calculation only.
**Default output is unchanged** (both new knobs are off).

### What I changed, and why

1. **Round offsets fitted as two-way fixed effects** (commit da6d368,
   `features.ROUND_OFFSETS_TWO_WAY`, default False).
   - The problem: `estimate_round_offsets` demeans each athlete's times and
     then averages by round. That is not a fixed-effects fit when athletes'
     round mixes differ. A finalist's mean is mostly finals, and a weaker
     athlete's mostly heats, so each athlete's own mean absorbs part of the
     round gap and the offset shrinks toward 0. The docstring claimed it
     wasn't confounded, but it was.
   - The fix: `_two_way_round_effects` fits athlete + round jointly by
     alternating projections (backfitting). This is the standard iterative
     estimator for models with two sets of fixed effects
     ([Guimarães & Portugal 2010, Stata Journal](https://repec.iza.org/dp3935.pdf)).
     It converges to the exact OLS solution.
   - Test: `test_round_offsets_two_way_removes_mix_bias`. Athlete A runs 9
     heats + 1 final, B runs 1 heat + 9 finals, and heats are exactly 0.20 s
     slower. The old method gives 0.072 (hand-computed), the new one 0.20.
     With balanced round mixes, both give 0.20.
   - Why it matters: heats (with easing-off) are a big share of rows, so an
     under-corrected heats offset makes heat-heavy athletes look slower than
     they are in every form estimate.
2. **Quadratic (asymmetric) wind correction** (commit e4ea8e0,
   `features.WIND_QUADRATIC`, default False; round 5's idea 4).
   - `estimate_wind_quadratic` fits time = athlete + b·w + c·w² within
     athlete (a 2×2 normal-equations solve on demeaned w and w²).
   - Why w² and not w·|w|: expanding Mureika's correction
     t₀ = t_w[1.028 − 0.028(1 − w·t_w/100)²] at t≈10 s gives
     t_w ≈ t₀ − 0.056w + 0.0028w². That is about −0.10 s at +2 m/s and
     +0.12 s at −2 m/s
     ([Mureika, arXiv physics/0006057](https://arxiv.org/pdf/physics/0006057)).
   - Tests: `test_wind_quadratic_recovers_asymmetric_wind` checks exact
     recovery of b = −0.056 and c = 0.0028. A second test checks that the
     knob is off by default and that c ≈ 0 on the linear synthetic data.
3. **`tune_adjustments.py`** (commit bbd93a5). Both knobs change `adj_time`
   at load time, so the per-race tuners can't compare them. This script
   loads the data for all four combinations and prints the fitted wind
   terms and round offsets. It scores every final by exact-integration
   log-loss, split pre-2022 / 2022+, and gives the paired-bootstrap CI
   against the current setting.

I also re-read `predict.py` (`simulate_race`, the exact integrator, the
blend and the prior) and round 5's `known_before` changes, and found no bugs.

### Research

- Two-way fixed effects by alternating projections:
  [Guimarães & Portugal (2010)](https://novaresearch.unl.pt/en/publications/a-simple-feasible-procedure-to-fit-models-with-high-dimensional-f/),
  [working-paper PDF](https://www.bportugal.pt/sites/default/files/anexos/papers/wp200909.pdf).
- Wind physics: Mureika's correction formula (linked above), expanded to
  the w² form used here.

### Ideas for next time

1. **Let `py` run** (see round 4). Six rounds of code are still unrun.
2. Run order: tests (40 cases), then **`tune_adjustments.py` first** (it
   changes `adj_time`, which everything else builds on), then
   `tune_prior` → `tune_spread` → `tune_uncertainty` → `backtest.py`.
3. Fit wind, round and athlete in one backfitting loop (wind is currently
   fitted on raw times, ignoring round). Do this only if round offsets turn
   out to matter.
4. Season-phase offset: add week of season as another fixed-effect factor
   in the same `_two_way_round_effects` loop. It is now nearly free to add.
5. Still open: Elo same-day updates, the stats cache for tuners, a
   meeting-level prior offset, and `tune_indoor.py`.
