# Project Goals & Ambitions

## What this is

A model that predicts men's 100m sprint race outcomes from real historical
World Athletics results — not a toy exercise, something meant to actually
be used to weigh in on upcoming real races.

## The core ambition

Build something more honest than "whoever has the fastest recent time wins."
That naive approach was explicitly called out early on as the wrong
baseline — a single fastest time doesn't account for:

- **When** that time was run — a PB from 10 years ago shouldn't count the
  same as current form.
- **Wind** — a tailwind-aided time isn't the same as a true time.
- **Round** — athletes often ease off in heats once they've qualified;
  heat times shouldn't be read as their real capability.
- **Reliability** — a fast average time from someone who false-starts or
  DNFs regularly is a false picture; DQ/DNF/DNS history matters.
- **Head-to-head history** — raw solo stats miss "does this specific
  athlete tend to beat that specific rival," which pure time comparison
  can't see.

The goal was always **calibrated win probabilities across a field**, not a
single confident "this person wins" call — sprint finals are decided by
hundredths of a second, false starts, and day-of factors, so honesty about
uncertainty was treated as a feature requirement, not a hedge.

## Standards held throughout

- **Leak-free backtesting** — every prediction, in every backtest, is built
  using only data that existed strictly before that race happened. No
  result is ever allowed to help predict itself.
- **Empirically estimated, not guessed** — the wind coefficient and round
  offsets were fit from this dataset's own data (within-athlete regressions)
  rather than plugging in a remembered physics constant or an assumption.
- **Validate against reality** — every feature added was backtested against
  real finals before being trusted, and results were reported honestly
  (including where the model is weak) rather than optimized to look good.
- **Regular commits** — the repo was kept checkpointed and pushed
  throughout, not left as an uncommitted pile of work.

## Where it stands

As of 2026-10-05: ~57,000 results, a calibrated Monte Carlo + Elo model,
a leak-free backtest (51% top-1 on elite finals vs ~12% chance, roughly level
with the fastest-time rule but with much better probabilities), a live
Streamlit website, start-list fetching, and tooling to log predictions and
compare them to bookmaker odds in the 2027 season. See `context.md` → START
HERE for the current numbers and the next steps.

## Open ambitions (not yet built)

- Automatically pulling an upcoming race's start list, instead of typing
  the field in by hand.
- Reducing the "cold start" gap — ~8% of real winners had zero prior race
  history in the dataset, which is unpredictable by construction until more
  data is collected.
- ~~Root-causing the scraper bug that occasionally grabs the wrong
  row/column from a results page~~ — investigated: the *implausible-time*
  rows (e.g. 45.12s) turned out not to be a scraper bug at all, they're
  genuinely published as-is on worldathletics.org. But a real, much bigger
  scraper bug was found and fixed in the same investigation: `scrape_race()`
  picked one results table per page (`max(tables, key=len)`), and heats/
  semi-final pages render one table *per heat group* — on the tie this
  silently kept only the first heat and discarded the rest (up to 48 of 56
  athletes on one 1987 Worlds heats page). Fixed to concatenate every
  results table on the page; dataset rebuilt 5,356 -> 6,795 rows.
- ~~Fixing multi-heat "final" URL mislabeling at the source~~ — fixed: it
  was actually two bugs — `features.py` was overwriting an already-correct
  `round` column with URL-based guessing (which can't distinguish rounds on
  hub pages, since they share one URL across the whole meeting), and
  `get_real_races`/Elo were grouping by `source_url` alone instead of
  `(source_url, round)`. Mislabeled-as-final groups dropped from 66 down to
  3 residual cases (modest 16-18 person fields, not the previous 76-125).
- Residual, smaller risk left open: on hub pages, individual heat *groups*
  within the same round (e.g. Heat 1 vs Heat 2) all collapse to the same
  `round` value, so if two small heats' combined size lands in the 3-10
  "real race" window, Elo could still credit a made-up head-to-head between
  people who raced in different heats. Not fixed this session — would need
  scrape_hub_race to persist a per-heat-group id, which the current CSV
  schema doesn't have retroactively.
