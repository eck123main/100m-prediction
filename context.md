# 100m Prediction — Project Context

Paste this into a new conversation to resume work on this project.

## Project location

- Windows path: `D:\athleticsprediction`
- WSL path: `/mnt/d/athleticsprediction`
- GitHub: https://github.com/eck123main/100m-prediction (branch: `main`)
- Everything below is committed and pushed as of commit `629ee63`.

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
