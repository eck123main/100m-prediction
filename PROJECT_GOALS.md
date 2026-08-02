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

The feature pipeline (recency-weighted + wind-adjusted + round-adjusted
time, reliability-gated Monte Carlo, head-to-head Elo, blended prediction)
is built and validated: ~42-47% top-1 accuracy on real finals vs. ~12%
chance-level. A command-line tool exists to actually run a prediction on a
real upcoming field. See `README.md` for the technical details and
`session_context.txt` for a full recap of what's been done.

## Open ambitions (not yet built)

- Automatically pulling an upcoming race's start list, instead of typing
  the field in by hand.
- Reducing the "cold start" gap — ~9% of real winners had zero prior race
  history in the dataset, which is unpredictable by construction until more
  data is collected.
- ~~Root-causing the scraper bug that occasionally grabs the wrong
  row/column from a results page~~ — investigated: not a scraper bug. The
  implausible marks (e.g. 45.12s) are genuinely published as-is on
  worldathletics.org itself; still filtered to NaN downstream in
  `features.py` since they're not real sprint times.
- Fixing multi-heat "final" URL mislabeling at the source, rather than
  working around it with a field-size filter.
