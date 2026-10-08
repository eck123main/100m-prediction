# 100m Prediction — Project Context

Paste this into a new conversation to resume work on this project.

## Project location

- Windows path: `D:\Users\rotem\projects\athleticsprediction` (moved; older
  notes/scripts such as `_diag_scratch.py` still reference `D:\athleticsprediction`)
- WSL path: `/mnt/d/Users/rotem/projects/athleticsprediction`
- GitHub: https://github.com/eck123main/100m-prediction (branch: `main`)
- Everything below is committed and pushed (see git log for the latest).

## Working rule — commit regularly

- **Commit after every meaningful step** (a bug fix, a feature, a dataset
  rebuild, a doc update). Don't let uncommitted work pile up. Keep commit
  messages short and plain, one line (e.g. "add 2026 meets", "fix wind for
  heats") — no long bodies, no Co-Authored-By lines. Push to `origin/main`
  so progress is saved off-machine.
- Commit a dataset rebuild separately from code changes, so a bad
  rescrape can be reverted on its own.
- Update this file at the end of each session, and commit it.

## START HERE — status at end of 2026-10-08 session

**2026-10-07 session (5-task plan, partly done):**
- Done: website Track record tab has an "Elite meets / All finals" toggle
  (elite: 219 finals, ~50% top-1). 60m support in the model is coded but
  off (`features.INDOOR_60M_WEIGHT = 0.0`; `load_indoor_60m` estimates the
  60m->100m ratio from athletes with both in one season, needs >=20 pairs).
- Fixed: 60m discovery found nothing because the WA API's `indoor` field is
  always empty — now filters by discipline name. Discovery is resumable:
  `athlete_slugs.json` (complete, 1,248 meetings) and `athlete_results.json`
  (season lookups, saved every 200; failed lookups not cached) — both
  gitignored, local only.
- **2026-10-08:** indoor 60m done — 1,263 meetings (2023-26) in
  `INDOOR_60M_URLS`, 48,894 rows in `60m_indoor_dataset.csv`; 60m->100m
  ratio 1.552 (6.50 -> 10.09). 2022 season done — 209 meetings added to
  OTHER_HUB_URLS, +6,138 rows (dataset now 87,261). Backtest re-run and
  committed: 2024+ finals 47.3% top-1, log-loss 1.982 (was 2.000), cold
  starts 13.4%; 2022 finals 40.4% top-1 (28.7% cold starts).
- **Only thing left:** `py -3.14 tune_indoor.py` (~20-30 min) decides
  whether 60m form helps (weights 0/0.5/1, tune 2023-24, confirm 2025-26
  with bootstrap CI). It was killed by Claude Code for low system memory
  before printing anything. If a weight > 0 wins and the confirm CI isn't
  worse, set `features.INDOOR_60M_WEIGHT`, re-run `backtest.py`, commit.
  Background jobs here keep getting killed for low memory — close heavy
  apps, or launch Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`.
- **Website link broken (2026-10-08):** the URL below gave "You do not have
  access to this app or it does not exist", even signed in as eck123main
  (the GitHub owner). Next session first: ask the user what "My apps" at
  share.streamlit.io shows. If the app is listed, record its real URL here;
  if not, redeploy (Create app -> repo `eck123main/100m-prediction`, branch
  `main`, file `app.py`) and record the new URL.

**The model works.** Website (Streamlit Community Cloud, from
this repo, branch `main`, file `app.py`):
https://100m-prediction-5zcsyvwkxjrsdfmna4cfej.streamlit.app (currently not
opening — see above; the repo is private; deployed from the user's
eck123main Streamlit account). Pushing to `main` redeploys it automatically.

**Data:** 87,261 rows (`100m_races_dataset.csv`), through 2026-09-23,
plus 48,894 indoor 60m rows (`60m_indoor_dataset.csv`, 2023-26, unused
until tune_indoor.py says it helps). Before 2026-10-08 there were 81,123 rows:
Dense 2012-2026 elite meets, every round of every Worlds/Olympics back to
1983, plus ~1,880 extra 2023-2026 meetings (NCAA, national champs, area
champs, smaller invitationals) found via athlete profiles.

**Model** (features.py + predict.py):
- Form = wind- and round-adjusted times, recency-weighted (half-life 180
  days). Spread = robust MAD over last 730 days, shrunk toward the field
  (`robust_spread`). Reliability = Beta-shrunk finish rate.
- 10,000-run Monte Carlo (vectorized) -> win probabilities, blended 90/10
  with head-to-head Elo (each heat rated as its own race).
- Hand-timed marks dropped; `ATHLETE_ALIASES` merges name variants.

**Backtest** (`py -3.14 backtest.py`, ~5-8 min; writes `backtest_results.csv`,
which is committed so the website loads fast — re-run and commit it after
any model change):
- Original 295 elite finals: **50.8% top-1**, log-loss **1.424**, cold
  start 1.7%. Fastest-adjusted-time rule ~51.5% top-1, so the model's value
  is calibrated probabilities, not more correct picks.
- 2024+ finals (3,033): 47.0% top-1, log-loss 2.000, cold start 13.7%
  (was 22.6% before the 2023 data).
- All 4,654 finals: 45.3% top-1 (56.3% excl. cold starts, 19.6%).
- **Calibration is fine once cold starts are excluded** (elite finals: ~74%
  said -> ~72% won; ~45% -> ~48%). The earlier "overconfident top end" was
  races won by athletes with no history (the model gives them 0%). Tested
  shrinking toward uniform (p' = (1-a)p + a/n): pre-2022 prefers a=0, so
  rejected. The fix for calibration is more data (fewer cold starts).

**Honest standing vs Velocitra** (B2B odds supplier to sportsbooks, built on
the Tilastopaja database): we can't match their breadth; aim is depth on the
men's 100m + a transparent track record. The real benchmark is bookmaker
odds — tooling is ready (`--odds`), needs live 2027 races.

### Next steps (agreed plan, in order)

1. **Indoor 60m** (groundwork done, not yet run):
   - `scraper.scrape_hub_race(url, "Men's 60 Metres")` works (tested on the
     2026 World Indoors, competition 7199326).
   - Run `py -3.14 discover_meets.py --indoor-60m --years 2023 2024 2025 2026`
     -> paste meetings (>=2 results) into `INDOOR_60M_URLS` in `links.py`
     (URLs use eventId=10229683) -> `py -3.14 collect_data.py --indoor-60m`
     -> writes `60m_indoor_dataset.csv`.
   - Then in features.py: estimate a 60m -> 100m conversion from athletes
     who ran both in the same season, add converted 60m results to form
     history with a tuned weight (try 0 / 0.5 / 1; choose on pre-2022 is
     impossible since 60m data starts 2023 — use 2023-24 to tune, 2025-26
     to confirm), excluded from Elo and reliability.
2. **Fewer cold starts**: `discover_meets.py --years 2022` (same flow as
   2023: >=2 results -> bottom of OTHER_HUB_URLS -> `collect_data.py
   --new-only`, now ~30 min with progress output; known-empty URLs are
   skipped via `no_100m_urls.txt`).
3. **Live test in 2027**: before big races
   `py -3.14 predict.py --startlist <url> --log --odds "Name=2.5,..."`,
   commit `predictions_log.csv`; after: `py -3.14 score_predictions.py`.
   Also verifies hub start-list parsing (`scraper._hub_start_list_names`),
   never seen live.
4. Tuning rule used throughout: choose on finals before 2022, confirm on
   2022+ with a paired bootstrap; only adopt if it doesn't hurt 2022+.

### Commands cheat sheet

```
py -3.14 predict.py "Noah Lyles" "Oblique Seville" ...        # predict
py -3.14 predict.py --startlist <WA url> [--before YYYY-MM-DD] [--log] [--odds "..."]
py -3.14 score_predictions.py                                # grade logged predictions
py -3.14 backtest.py                                         # ~5 min
py -3.14 discover_meets.py [--years 2023 2024] [--indoor-60m]  # find missing meetings
py -3.14 collect_data.py --new-only [--retry-failed]         # scrape new links.py URLs
py -3.14 collect_data.py --indoor-60m                        # scrape INDOOR_60M_URLS
py -3.14 -m streamlit run app.py                             # website locally
```

## Python environment — important

- This machine has multiple Python installs. The default `python`/`py` on
  PATH is Python 3.8 with pandas 2.0.3 — **too old**, code uses
  `include_groups=` (pandas >=2.2) and will crash.
- Use `py -3.14` (pandas 2.3.3, streamlit 1.65 installed with
  `pip install --user`; confirmed working) or `py -3.11` (pandas
  2.3.1, also fine). Always run scripts explicitly, e.g.:
  ```
  py -3.14 predict.py "Noah Lyles" "Kishane Thompson"
  py -3.14 backtest.py
  ```
- Also confirmed working under WSL's python3.12 + pandas 2.3.1 (used to
  investigate/fix bugs this session — see below). pandas 3.0.5 (what a
  fresh `pip install pandas` gives you today) used to crash on a `.attrs`
  propagation issue; that's now fixed.
- **If pushing from WSL** and `git push` fails with "could not read
  Username": the repo's `credential.helper=manager` (Windows GCM) isn't on
  WSL's PATH. Workaround (doesn't touch saved git config):
  ```
  git -c credential.helper= -c credential.helper=/mnt/c/PROGRA~1/Git/mingw64/bin/git-credential-manager.exe push origin main
  ```

## What the project does

Predicts men's 100m race win probabilities from World Athletics results
scraped from worldathletics.org (see START HERE for current numbers).

## File map

| File | Purpose |
|---|---|
| `100m_races_dataset.csv` | Dataset: ATHLETE, COUNTRY, time, record_flag, Reaction Time, wind, date (per race), venue, meet_name, source_url, round (heats/quarter-final/semi-final/final), heat |
| `links.py` | Every source URL (CHAMPIONSHIP_URLS, DIAMOND_LEAGUE_HUB_URLS, OTHER_HUB_URLS, CONTINENTAL_TOUR_*) — mostly generic hub URLs `competition/calendar-results/results/{id}?eventId=10229630` |
| `scraper.py` | `scrape_hub_race` (hub JSON, tier allowlist `ELITE_HUB_TIERS`, per-race dates/wind/heat), `scrape_race` (old flat pages), `fetch_start_list` |
| `collect_data.py` | Rebuild (`main`) or add only new URLs (`--new-only`, safe) |
| `discover_meets.py` | Find meetings we lack from athlete profiles / WA GraphQL (`--years`, `--indoor-60m`); caches profile links in `athlete_slugs.json` |
| `no_100m_urls.txt` | links.py URLs with no usable men's 100m (skipped by `--new-only`) |
| `features.py` | Cleaning, wind/round adjustment, robust spread, reliability, Elo, `compute_stats_before` (leak-free) |
| `predict.py` | Monte Carlo + Elo blend; CLI with `--startlist`, `--before`, `--log`, `--odds` |
| `backtest.py` | Leak-free backtest over every real final; Elo weight grid with train/test split |
| `backtest_results.csv` | Saved backtest output (read by the website) |
| `score_predictions.py` | Grades logged live predictions (and bookmaker odds) |
| `app.py` / `requirements.txt` | Streamlit website / deps for Streamlit Cloud |
| `probe_hub_ids.py`, `test_year_access.py`, `pred.ipynb` | Old one-off tools / original notebook |

*(Everything below is the historical session log — numbers in it are as of
that point in time. START HERE above is current.)*

## Session 2026-08-02: bug hunt — "look into the scraping bug and all bugs"

Set up a working Python env in WSL (bootstrapped pip via `get-pip.py`, then
`pip install --user --break-system-packages pandas numpy requests
beautifulsoup4 lxml html5lib`) to actually run and test the code live
against worldathletics.org, rather than just reading it. Found and fixed
six real bugs, all committed and pushed.

### 1. The actual scraper bug (the big one)

`scraper.py`'s `scrape_race()` picked one results table per page via
`max(tables, key=len)`. Heats and semi-final pages render one HTML table
**per heat group**, all with identical row counts (World Athletics pads to
a fixed lane count) — so on that tie, Python's `max()` deterministically
kept only the *first* table and silently discarded every other heat.

Confirmed live: a 1987 Rome Worlds heats page has 7 tables of 8 athletes
each (56 total); only the first 8 were ever scraped. Verified this held
across **every one of the 48** old-style heats/semi-final URLs in the
dataset — every single one was capped at 6–10 rows, consistent with "only
got one heat table," not a real round.

**Fixed**: now concatenates every table on the page that looks like a
results table (has `MARK`+`ATHLETE` columns); verified non-regressive on
single-table pages (finals always have exactly one table).

### 2. Round-label mislabeling

`_map_round_label()` in `scraper.py` checked `"heat" in label` before
`"semi"`, so hub-page labels like `"Semifinal - Heat"` (contains both
substrings) resolved to `"heats"` instead of `"semi-final"`. Fixed the
check order.

### 3. `round` column overwrite in `features.py`

`load_clean_data()` was unconditionally overwriting the already-correct
`round` column with URL-based guessing. That guessing can't distinguish
rounds on hub pages (`calendar-results` URLs), since all rounds of a
meeting share one URL — so it collapsed heats/semis/final into whatever
`infer_round()` defaults to (`"final"`), producing fake giant "finals"
with field sizes up to 125. The stored `round` column was actually 100%
populated (0 nulls across 6,795 rows) — no reason to discard it. Fixed to
only fill genuinely-missing values.

### 4. Elo/real-race grouping bug

`get_real_races()`/`compute_elo_history()` grouped by `source_url` alone
instead of `(source_url, round)` — on hub pages this conflated a real,
correctly-sized final with the meeting's heats/semis sharing the same
URL, so a legitimate 8-person final got excluded from Elo just for
sharing a URL with a 50-person heats round. Confirmed 510 final-round rows
across 64 meetings were being wrongly excluded before this fix.

### 5. pandas 3.x forward-compat crash

`features.py` stashed a DataFrame (`elo_history`) inside `df.attrs`.
pandas propagates `.attrs` through slicing/groupby, and `.join()`/
`.concat()` compare `.attrs` dicts for equality to decide what to keep —
comparing two DataFrames with `==` raises "truth value is ambiguous"
instead of returning a bool, on pandas 3.0+ (reproduced on 3.0.5; did
**not** reproduce on 2.3.1). Fixed by stripping `.attrs` off the `history`
slices in `compute_stats_before`/`compute_reliability_before` before any
groupby/join touches them. This matters because the README's only version
pin is a lower bound (`pandas >= 2.2`) — anyone doing a fresh
`pip install pandas` today gets 3.x and would hit this crash immediately.

### 6. Mis-documented "scraper bug" that wasn't one

Docs were wrong about the implausible-time rows (e.g. 45.12s for
Christophe Lemaitre at Turku 2020). Previously assumed to be a "scraper
mismatch (wrong row/column)." Verified directly against the live
worldathletics.org source (both the raw HTML `data-bind` JSON for
old-style pages, and the embedded `__NEXT_DATA__` JSON for hub pages,
across 4 different examples/years/formats) — these times are genuinely
published there as-is, most likely a DNF/injury/fall that WA coded as a
numeric mark instead of a DNF flag. **Not** a scraper bug. The existing
filter (set to `NaN` in `features.py`) is the correct behavior regardless
of the underlying cause — just corrected the comments/docs that
misattributed it.

### Also

Removed dead `MIN_FIELD_SIZE`/`MAX_FIELD_SIZE` constants in `backtest.py`
(never referenced — actual filtering happens via `features.py`'s
`MIN`/`MAX_REAL_RACE_SIZE` inside `get_real_races`).

## Dataset rebuilt

Ran `python collect_data.py` end-to-end with the fixes applied.
**5,356 → 6,795 rows (+27%)**. Verified zero regressions: every
`source_url` that existed before has the same or more rows after (checked
programmatically, not just spot-checked). `semi-final` round rows went
from 145 to 1,142 (previously mislabeled as `heats`). Mislabeled-as-
`"final"` URL groups with implausible field sizes dropped from 66 down to
3 (and those 3 are modest 16–18 person fields, not the previous 76–125).

## Backtest re-validated

(py3.12/pandas 2.3.1 in WSL, after the rescrape)

- **199 real finals evaluated** (up from the previously-documented 136 —
  the `get_real_races` grouping fix alone surfaced 64 finals that were
  wrongly excluded before, even prior to the rescrape).
- `elo_weight=0.3` now beats 0.5 and 0.7 in **every** slice tested (all
  races, excl. cold starts, 2016+, 2016+ excl. cold starts) — a reversal
  of the previously-documented finding that 0.5 was best, now that Elo has
  much more correct semi-final/heats data feeding it. Updated
  `predict_race_full()`'s default `elo_weight` from 0.5 to 0.3.
- Headline numbers with the new default: **42.7%** top-1 (all 199 real
  finals) / **46.4%** (excl. cold starts, 183 races) vs ~12% chance-level.
  Close to the old headline numbers (42.6%/46.8%) but now on a larger,
  more honest evaluation set built from actually-fixed data.
- Cold-start rate: ~8% of winners had zero prior history (was ~9%).
- Miss pattern held up: actual winner in the model's own top 2 ~49.5% of
  misses, top 3 ~63.6%.

## Known open items / not yet built

- No automated start-list scraping — upcoming race fields must be typed
  in by hand (CLI takes them as command-line args).
- Cold-start gap (~8% of winners had zero history) — inherent to sparse
  early-career/early-era data, not fixable without more data collection.
- **Residual Elo precision gap**: on hub pages, individual heat *groups*
  within the same round (e.g. Heat 1 vs Heat 2) aren't distinguished in
  the stored data — they share the same `round` value. If two small
  heats' combined size lands inside the 3–10 "real race" window used for
  Elo, it could still credit a made-up head-to-head between people who
  actually raced in different heats. Would need `scrape_hub_race` to
  persist a per-heat-group id (a schema change + re-scrape) to fully
  close — not done this session; flagged as a known limitation instead.
- Elo weight (0.3, was 0.5) still only tested against 2 other candidates
  `{0.3, 0.5, 0.7}` on ~199 races — a small sample; more rigorous tuning
  (e.g. train/test split across eras, finer weight grid) wasn't done.
- Minor: `collect_data.py` prints a pandas `FutureWarning` about
  concatenating empty/all-NA columns (e.g. an all-None Reaction Time
  column). Harmless today, will need a fix when pandas actually changes
  this behavior.

## Git / commit history this session

(chronological, all pushed to `origin/main`)

- `docs: correct scraper-bug claim — implausible times are real source data`
- `fix: correct round grouping and pandas 3 compat in features.py`
- `fix: scrape_race dropped every heat but one; fix round mislabeling`
- `chore: rebuild dataset with scraper fixes (5,356 -> 6,795 rows)`
- `chore: remove dead MIN/MAX_FIELD_SIZE constants in backtest.py`
- `fix: update elo_weight default and docs from re-validated backtest`
- `docs: update session context with this session's bug-hunt findings`

---

## Session 2026-10-05: catch-up scrape, scraper fixes, heats as races

### Finding new meetings (reusable method)

`https://worldathletics.org/competition/calendar-results?startDate=...&endDate=...&competitionGroupId=<id>`
embeds results in `__NEXT_DATA__` (`props.pageProps.initialEvents.results`,
each with `id`, `name`, `startDate`, `hasResults`). Useful group ids: 627
Diamond League meeting, 3520 DL Final, 3773 Continental Tour, 3731 national
senior championships, 3660/3771/3757 area champs/games; `rankingCategoryId`
4 (OW) / 5 (GW) / 6 (GL) / 1 (A) catches majors without a group (e.g.
Commonwealth Games). Then scrape each with
`competition/calendar-results/results/{id}?eventId=10229630` — a 500 on that
URL means the meeting has no men's 100m.

### What changed

- **Added Aug-Sep 2026**: Commonwealth Games, European Champs, Ultimate
  Championship, Asian Games, CAC/Mediterranean/South American Games, late
  DL (Silesia, Brussels final), ~16 Continental Tour meetings, some national
  champs. Lausanne/Zurich 2026 had no DL men's 100m.
- **Added 2012-2015 Diamond League** (39 meetings with a men's 100m).
- **Bug: DL-form hub URLs hide sections.** `competitions/diamond-league/
  calendar-results/{id}/result` omitted real DL 100m finals (Zurich
  2022/2025, Lausanne 2025, Silesia 2025, Pre 2022) that the generic
  `competition/calendar-results/results/{id}` URL shows. All hub links
  converted to the generic form.
- **Bug: hub tier fallback was a blocklist** — could pick U18/U23 races or
  the "Karsten vs. Mondo" exhibition. Now an allowlist (`ELITE_HUB_TIERS`).
  Verified no existing rows were contaminated.
- **New `heat` column** (closes the "residual Elo precision gap" open item):
  both scrapers record which race within a round each row came from; races
  are keyed on `RACE_KEYS = (source_url, round, heat)`. Real races usable
  for Elo: 274 -> 1,061. 328/331 URLs re-scraped identically; the other 3
  keep rows with empty heat (treated as heat 1).
- **Oregon 2022 Worlds** rows had no date (page lacks EventDate meta) —
  filled 15/07/2022; the 2022 final was previously an automatic miss.
- **`collect_data.py --new-only`**: incremental mode. Note the full `main()`
  drops existing rows for every attempted URL even if the fetch fails.
- **Backtest**: elo_weight grid 0-1, scored by log-loss, fit on pre-2022
  finals and checked on 2022+; seeded Monte Carlo. Best = 0.1 on both the
  pre-heat and heat-aware data.
- Removed stray `python` file and `_diag_scratch.py`.

### Results (heat-aware, 295 finals)

| Slice | Races | MC top-1 | blend 0.1 | Elo alone | chance |
|---|---|---|---|---|---|
| All | 295 | 47.1% | 47.1% | 34.9% | 12.4% |
| Excl. cold starts | 268 | 51.9% | 51.9% | 38.4% | 12.2% |
| 2016+ | 235 | 43.8% | 43.8% | 32.3% | 12.5% |

Log-loss (lower better): w=0.0 train 1.804 / test 2.082; w=0.1 1.794 /
2.011; w=0.3 1.826 / 1.998. Top-1 barely moves; the small Elo weight mainly
improves calibration.

### Follow-up (same day): Elo round weighting + start lists

- **Elo round weighting**: added `ELO_ROUND_K` (per-round K multiplier) and
  `compute_elo_history(df, round_k=...)`. Experiment over 8 variants on 295
  finals: at elo_weight=0.1, train log-loss 1.792-1.794, test 2.010-2.012,
  top-1 47.1% for all. Standalone Elo top-1 ranged 34.6-37.6% (noise-level
  at 10% weight). Kept all multipliers at 1.0.
- **Start lists**: `scraper.fetch_start_list(url)` +
  `predict.py --startlist URL [--before YYYY-MM-DD]`. Championship
  `/startlist` pages verified (Tokyo 2025 final replay: Thompson 34% top
  pick — he finished 2nd; Oblique Seville won. Corrected: an earlier note
  here wrongly said Thompson won). Hub pages fall back to results entrants after
  the race; pre-race shape untested.

### Follow-up 2: per-race dates, all-rounds championships, data hygiene

- **Per-race dates**: `scrape_hub_race` uses `races[].date`, so heats of a
  multi-day meeting precede its final. Same-day rounds still don't leak
  (stats use strictly-before dates).
- **Championships moved to hub pages**: the flat `/final/result` pages had
  no heats/semis for 2023+ (404) and only one heat for Oregon 2022. Hub
  pages have every round back to 1983 (Paris 2024: 8 -> 153 rows). All 27
  finals verified identical (3 differed only by name spelling). Quarter-
  finals get their own round; decathlon 100m ('Combined - Group', listed in
  the same section on some old championships) is skipped.
- **Per-heat wind** on multi-heat flat pages (was first heat's wind for all).
- **`ATHLETE_ALIASES`** in features.py merges same-person spellings
  (Bracy/Bracy-Williams, Demps, Makusha, Batson); also applied to CLI input.
- **collect_data.py**: full run no longer drops rows for URLs that fail to
  fetch; empty-frame concat FutureWarning fixed.
- Checked and left alone: remaining 6 cross-source "duplicates" are genuine
  (same athlete ran the same time in a heat and the final that day).
- Round offsets now: heats +0.042s, quarter +0.008s, semi +0.009s vs final;
  wind coefficient -0.049 s per m/s.

Backtest (295 finals): MC 51.2% top-1 (was 47.1%), excl. cold starts 53.9%,
2016+ 46.0%. Elo grid log-loss train/test: w=0.0 1.471/1.896, w=0.1
1.478/1.869, w=0.2 1.500/1.870 — 0.1 kept (train tie, better on test).
Backtest now takes ~25-30 min.

### Follow-up 3: speed, tuning, ablations, live-test tooling

- **Backtest 25-30 min -> ~10 s**: vectorized `compute_stats_before`,
  `compute_reliability_before` (identical output to 1e-14) and
  `simulate_race` (one numpy draw for all runs).
- **Tuning** (choose on pre-2022 finals by log-loss, confirm on 2022+,
  paired bootstrap CI): half-life 730 -> 180 days adopted (train 1.479 ->
  1.455, test 1.871 -> 1.848, CI -0.072..+0.029). Rejected: temperature
  calibration T=1.3 (train better, test +0.020 worse), shrinking athlete
  spread toward pooled (worse on both, though it fixes top-end
  overconfidence), recency-weighted spread and spread scaling (train-only
  gains that reversed on test).
- **Ablations** (all within noise on log-loss): wind adjustment is the one
  clearly useful component (top-1 drops ~3-4 points without it);
  reliability gating small consistent gain; round adjustment neutral.
  All kept.
- **Model vs naive baseline**: ~50% vs ~49% top-1 — the extra modelling
  mainly buys probabilities, not more correct picks.
- **Live testing**: `predict.py --log [CSV]` appends the prediction (with
  model commit + data date); `score_predictions.py` grades logged races once
  results are up. Tested on two replays (Tokyo 2025, Brussels 2026).

### Website (2026-10-05)

- `app.py` — Streamlit app: Predict (multiselect or start-list URL), Replay a
  past final (leak-free), Track record (backtest metrics, calibration chart,
  accuracy by year, live prediction log). Run: `py -3.14 -m streamlit run app.py`.
- `requirements.txt` added for Streamlit Community Cloud. Not deployed yet —
  needs the user to sign in at share.streamlit.io with GitHub.
- Streamlit installed for py -3.14 (`pip install --user streamlit`).

### Bookmaker odds, more 2026 data, robust spread (2026-10-05)

- `predict.py --odds "Name=2.5,..."` logs margin-free bookmaker probabilities;
  `score_predictions.py` compares model vs bookmaker log-loss/top-1.
- `discover_meets.py`: reads WA athlete profiles (urlSlug from hub JSON) for
  everyone <=10.30 since 2025 and lists meetings we lack. Found 116 new 2026
  meetings (African/Pan Am/NCAA/Australian champs, Mt SAC, Botswana GP...),
  +4,078 rows -> 13,939. Profiles only server-render the current season;
  earlier years load client-side (not scraped yet).
- Hand-timed marks ("10.1h") are dropped in load_clean_data (were counted as
  DNFs by reliability).
- **Spread**: replaced all-history std with `robust_spread` (MAD over last
  730 days, shrunk toward field median by 5 pseudo-races). Fixes erratic
  athletes getting extra win probability (Leotlela 17.3% -> 2.1% vs a
  similar-form Coleman). Pre-2022 log-loss -0.070 (CI excludes 0), 2022+
  neutral. On the original 295 finals: log-loss 1.649 -> 1.554, top-1 ~50%.
- Backtest set is now 622 finals (21% cold starts from the new small meets).
  Top-end calibration still overconfident (~78% said -> ~64% won).

Next: earlier seasons from athlete profiles (needs WA's client-side API),
indoor 60m as early-season form, then top-end calibration.

### 2024-2025 seasons via WA's data API (2026-10-05)

- Athlete profiles only server-render the current season; older seasons come
  from WA's public GraphQL endpoint (`GetSingleCompetitorResultsDiscipline`,
  id = number at the end of the profile slug). `discover_meets.py --years`
  reads the endpoint + public key from the site's JS config at runtime.
- 426 athletes (<=10.30 since 2024) -> 1,328 missing 2024-25 meetings; kept the
  1,066 with >=2 results from those athletes; 1,035 scraped (+43,170 rows ->
  57,109). Failures: no elite 100m section, 500s, 3 wrong-event tables.
- Backtest now 3,219 finals, ~5 min. Original 295 elite finals: log-loss
  1.554 -> 1.421, top-1 49.8% -> 51.2%, cold start 3.7% -> 1.7%, top-end
  calibration ~77% said -> 67% won (was 64%).
- 21% cold starts across all finals: most new meets are lower level and 2024
  is their first year of data. `discover_meets.py --years 2023` would help.

### Session 2026-10-06

- 2023 season: `discover_meets.py --years 2023` (887 athletes) -> 935 missing
  meetings, kept 740 with >=2 results; 724 scraped (+24,014 rows -> 81,123).
  2024+ finals: cold start 22.6% -> 13.7%, log-loss 2.451 -> 2.000.
- collect_data: progress printed with flush; permanent failures recorded in
  `no_100m_urls.txt` and skipped next time (seeded with 74 from logs).
- discover_meets: profile-link cache (`athlete_slugs.json`), `--indoor-60m`.
- scraper: `scrape_hub_race(url, event_name)` for any event; per-event
  plausible ranges (`PLAUSIBLE_RANGE`).
- Calibration: shrink-toward-uniform rejected (see START HERE); top-end
  overconfidence was cold starts.
