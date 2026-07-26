"""
Run this file directly to (re)build 100m_races_dataset.csv from scratch:
    python collect_data.py
"""

import pandas as pd
from scraper import scrape_race, get_mens_100m_url, get_diamond_league_meeting_links, generate_round_variants
from links import CHAMPIONSHIP_URLS, MANUAL_DIAMOND_LEAGUE_URLS

CSV_PATH = "100m_races_dataset.csv"


def scrape_url_list(urls, label=""):
    """Scrape a list of URLs with scrape_race(), printing progress. Returns a combined DataFrame."""
    all_races = []
    for u in urls:
        try:
            race = scrape_race(u)
            all_races.append(race)
            print(f"OK ({len(race)} rows): {u}")
        except Exception as e:
            print(f"FAILED: {u}")
            print(f"   error: {e}")
    if not all_races:
        return pd.DataFrame()
    return pd.concat(all_races, ignore_index=True)


def main():
    print("=== Scraping championship/Olympic finals ===")
    championship_df = scrape_url_list(CHAMPIONSHIP_URLS)

    print("\n=== Discovering Diamond League meeting URLs (2016-2021) ===")
    meetings = []
    for year in range(2016, 2022):
        year_meetings = get_diamond_league_meeting_links(year=year)
        print(f"  {year}: {len(year_meetings)} meetings")
        meetings.extend(year_meetings)
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

    print(f"\n=== Scraping {len(dl_race_urls_with_venue)} Diamond League finals ===")
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
    all_final_urls = CHAMPIONSHIP_URLS + dl_race_urls
    expanded_urls = []
    for url in all_final_urls:
        expanded_urls.extend(generate_round_variants(url))
    print(f"Generated {len(expanded_urls)} semi-final/heats URLs to try")

    rounds_df = scrape_url_list(expanded_urls)

    print("\n=== Merging and saving ===")
    try:
        existing = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        existing = pd.DataFrame()

    combined = pd.concat([existing, championship_df, dl_df, rounds_df], ignore_index=True)
    combined = combined.drop_duplicates()
    combined.to_csv(CSV_PATH, index=False)
    print(f"Saved {len(combined)} total rows to {CSV_PATH}")


if __name__ == "__main__":
    main()