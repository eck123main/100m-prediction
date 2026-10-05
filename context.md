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
  rebuild, a doc update). Don't let uncommitted work pile up. Use small,
  focused commits with conventional prefixes (`feat:`, `fix:`, `chore:`,
  `docs:`), and push to `origin/main` so progress is saved off-machine.
- Commit a dataset rebuild separately from code changes, so a bad
  rescrape can be reverted on its own.
- Update this file at the end of each session, and commit it.

## Status as of 2026-10-05 (end of session)

- Dataset: 9,861 rows, through 2026-09-23. Dense 2012-2026 plus every round
  of every World Championships/Olympics back to 1983.
- Backtest: 295 real finals, **51.2% top-1** (53.9% excl. cold starts) vs
  ~12% chance. Cold-start winners down to 5.1%. Default `elo_weight` 0.1.
- Everything committed and pushed.

### Suggested next steps

1. ~~Elo from heats is noisy~~ — tested (see 2026-10-05 follow-up below):
   down-weighting heats/semis or changing K makes no measurable difference
   at elo_weight=0.1. Not worth more tuning; bigger gains are elsewhere.
2. **Verify hub start lists live.** `predict.py --startlist URL` is built;
   the championship format is verified, but the pre-race hub-page
   `startList` shape is unobserved (WA clears it once results post). Try it
   on the first 2027 Diamond League meeting and adjust
   `scraper._hub_start_list_names` if it fails.
4. ~~Per-race dates for multi-day meetings~~ — done (see below).

## Python environment — important

- This machine has multiple Python installs. The default `python`/`py` on
  PATH is Python 3.8 with pandas 2.0.3 — **too old**, code uses
  `include_groups=` (pandas >=2.2) and will crash.
- Use `py -3.14` (pandas 2.3.3 confirmed working) or `py -3.11` (pandas
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

Predicts men's 100m race win probabilities from ~6,795 scraped
worldathletics.org race results (2016–2026 dense coverage, scattered
championship finals back to 1983).

## File map

| File | Purpose |
|---|---|
| `100m_races_dataset.csv` | The scraped dataset (ATHLETE, COUNTRY, time, record_flag, Reaction Time, wind, date, venue, meet_name, source_url, round) |
| `scraper.py` / `links.py` / `collect_data.py` / `probe_hub_ids.py` | Scraping infra (worldathletics.org) |
| `features.py` | Raw race rows → leak-free athlete stats |
| `predict.py` | Turns stats into predictions; also a CLI (see Quick Start) |
| `backtest.py` | Leak-free backtest harness against real finals |
| `README.md` | Full technical docs |
| `PROJECT_GOALS.md` | Project vision/ambitions |
| `pred.ipynb` | Original exploratory notebook (superseded by the `.py` modules, kept for history) |

## Quick start — predict a real race

```
py -3.14 predict.py "Noah Lyles" "Kishane Thompson" "Fred Kerley" "Akani Simbine"
```

Prints win probabilities plus `weighted_avg_time`, `finish_rate`,
`races_used`, `elo` per athlete. Name matching is case-insensitive; anyone
the model has no usable data for is listed separately, not silently
dropped.

---

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
  pick, the actual winner). Hub pages fall back to results entrants after
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
