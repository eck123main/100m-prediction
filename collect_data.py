"""
Run this file directly to (re)build 100m_races_dataset.csv from scratch:
    python collect_data.py

Or, to only scrape links.py URLs that aren't in the CSV yet (fast, and never
touches existing rows — use this after adding new meetings to links.py):
    python collect_data.py --new-only
"""

import sys

import pandas as pd
from scraper import (
    scrape_race, scrape_hub_race, get_mens_100m_url,
    get_diamond_league_meeting_links, generate_round_variants,
    normalize_meet_name
)
from links import (
    CHAMPIONSHIP_URLS, DIAMOND_LEAGUE_HUB_URLS, MANUAL_DIAMOND_LEAGUE_URLS,
    CONTINENTAL_TOUR_URLS, CONTINENTAL_TOUR_HUB_URLS, OTHER_HUB_URLS
)

CSV_PATH = "100m_races_dataset.csv"


def scrape_url_list(urls, scrape_fn=scrape_race):
    """Scrape a list of URLs with the given scrape function, printing progress.
    Returns a combined DataFrame."""
    all_races = []
    for i, u in enumerate(urls, start=1):
        # flush so progress shows up even when output goes to a file
        try:
            race = scrape_fn(u)
            all_races.append(race)
            print(f"[{i}/{len(urls)}] OK ({len(race)} rows): {u}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(urls)}] FAILED: {u}", flush=True)
            print(f"   error: {e}", flush=True)
    if not all_races:
        return pd.DataFrame()
    return pd.concat(all_races, ignore_index=True)


def main():
    print("=== Scraping championships/Olympics (all rounds, hub format) ===")
    championship_df = scrape_url_list(CHAMPIONSHIP_URLS, scrape_fn=scrape_hub_race)

    print("\n=== Scraping Continental Tour Gold / World Challenge finals ===")
    continental_tour_df = scrape_url_list(CONTINENTAL_TOUR_URLS)

    print("\n=== Discovering Diamond League meeting URLs (2016-2021) ===")
    meetings = []
    for year in range(2016, 2022):
        try:
            year_meetings = get_diamond_league_meeting_links(year=year)
            print(f"  {year}: {len(year_meetings)} meetings")
            meetings.extend(year_meetings)
        except Exception as e:
            # worldathletics.org's year-filtered index currently 404s (site-side
            # change, unrelated to this scraper) — skip rather than crash the
            # whole run; existing rows for prior years stay untouched below.
            print(f"  {year}: FAILED — {e}")
    meetings = list(dict(meetings).items())  # dedupe by URL
    print(f"Total unique meetings: {len(meetings)}")

    dl_race_urls_with_venue = []
    for meeting_url, venue in meetings:
        try:
            race_url = get_mens_100m_url(meeting_url)
            if race_url:
                dl_race_urls_with_venue.append((race_url, venue))
        except Exception as e:
            print(f"FAILED meeting lookup: {meeting_url} — {e}")

    print(f"\n=== Scraping {len(dl_race_urls_with_venue)} Diamond League finals (2016-2021) ===")
    all_races = []
    for u, venue in dl_race_urls_with_venue:
        try:
            race = scrape_race(u, known_venue=venue)
            all_races.append(race)
            print(f"OK ({len(race)} rows): {u}")
        except Exception as e:
            print(f"FAILED: {u}")
            print(f"   error: {e}")
    dl_df = pd.concat(all_races, ignore_index=True) if all_races else pd.DataFrame()

    print("\n=== Expanding to semi-finals/heats ===")
    dl_race_urls_only = [u for u, venue in dl_race_urls_with_venue]
    all_final_urls = dl_race_urls_only + CONTINENTAL_TOUR_URLS
    expanded_urls = []
    for url in all_final_urls:
        expanded_urls.extend(generate_round_variants(url))
    print(f"Generated {len(expanded_urls)} semi-final/heats URLs to try")
    rounds_df = scrape_url_list(expanded_urls, scrape_fn=scrape_race)

    print(f"\n=== Scraping {len(DIAMOND_LEAGUE_HUB_URLS)} hub-format Diamond League races (2022-2026) ===")
    hub_df = scrape_url_list(DIAMOND_LEAGUE_HUB_URLS, scrape_fn=scrape_hub_race)

    print(f"\n=== Scraping {len(MANUAL_DIAMOND_LEAGUE_URLS)} manually added Diamond League races ===")
    manual_df = scrape_url_list(MANUAL_DIAMOND_LEAGUE_URLS, scrape_fn=scrape_race)

    print(f"\n=== Scraping {len(OTHER_HUB_URLS)} other hub-format races (national championships, etc.) ===")
    other_hub_df = scrape_url_list(OTHER_HUB_URLS, scrape_fn=scrape_hub_race)

    print(f"\n=== Scraping {len(CONTINENTAL_TOUR_HUB_URLS)} hub-format Continental Tour races ===")
    ct_hub_df = scrape_url_list(CONTINENTAL_TOUR_HUB_URLS, scrape_fn=scrape_hub_race)

    print("\n=== Merging and saving ===")
    try:
        existing = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        existing = pd.DataFrame()

    if not existing.empty and "meet_name" in existing.columns:
        existing["meet_name"] = existing["meet_name"].apply(
            lambda n: normalize_meet_name(n) if pd.notna(n) else n
        )

    new_parts = [championship_df, continental_tour_df, dl_df, rounds_df,
                 hub_df, manual_df, other_hub_df, ct_hub_df]
    new_parts = [p for p in new_parts if not p.empty]

    # Replace old rows only for URLs successfully re-scraped this run, so a
    # stale scrape gets replaced rather than duplicated. A URL that failed
    # this time (server error, timeout) keeps its existing rows — it used to
    # be dropped too, so one transient failure could delete data.
    rescraped_urls = set()
    for p in new_parts:
        rescraped_urls |= set(p["source_url"])
    if not existing.empty and "source_url" in existing.columns:
        existing = existing[~existing["source_url"].isin(rescraped_urls)]

    # Skip empty frames: concatenating them is deprecated in pandas
    # (FutureWarning about empty/all-NA entries).
    combined = pd.concat(
        [p for p in [existing] + new_parts if not p.empty], ignore_index=True
    )
    combined = combined.drop_duplicates()
    combined.to_csv(CSV_PATH, index=False)
    print(f"Saved {len(combined)} total rows to {CSV_PATH}")


def main_new_only():
    """Scrape only the links.py URLs with no rows in the CSV yet, and append.

    Unlike main(), existing rows are never dropped, so a transient fetch
    failure can't delete previously-scraped data. Skips Diamond League index
    discovery and old-style round-variant expansion (both only apply to
    historical meetings already in the dataset)."""
    existing = pd.read_csv(CSV_PATH)
    have = set(existing["source_url"].dropna())

    def new(urls):
        return [u for u in urls if u not in have]

    flat_urls = new(CONTINENTAL_TOUR_URLS + MANUAL_DIAMOND_LEAGUE_URLS)
    hub_urls = new(CHAMPIONSHIP_URLS + DIAMOND_LEAGUE_HUB_URLS + OTHER_HUB_URLS
                   + CONTINENTAL_TOUR_HUB_URLS)
    print(f"=== {len(flat_urls)} new flat-format URLs, {len(hub_urls)} new hub-format URLs ===")
    flat_df = scrape_url_list(flat_urls, scrape_fn=scrape_race)
    rounds_df = scrape_url_list(
        [v for u in flat_urls for v in generate_round_variants(u)], scrape_fn=scrape_race
    )
    hub_df = scrape_url_list(hub_urls, scrape_fn=scrape_hub_race)

    parts = [p for p in [flat_df, rounds_df, hub_df] if not p.empty]
    if not parts:
        print("Nothing new scraped; CSV unchanged.")
        return
    new_rows = pd.concat(parts, ignore_index=True)
    combined = pd.concat([existing, new_rows], ignore_index=True).drop_duplicates()
    combined.to_csv(CSV_PATH, index=False)
    print(f"Added {len(combined) - len(existing)} rows; saved {len(combined)} total rows to {CSV_PATH}")


if __name__ == "__main__":
    if "--new-only" in sys.argv:
        main_new_only()
    else:
        main()