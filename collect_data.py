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
    meeting_links = []
    for year in range(2016, 2022):
        year_links = get_diamond_league_meeting_links(year=year)
        print(f"  {year}: {len(year_links)} meetings")
        meeting_links.extend(year_links)
    meeting_links = list(dict.fromkeys(meeting_links))
    print(f"Total unique meetings: {len(meeting_links)}")


    dl_race_urls = list(MANUAL_DIAMOND_LEAGUE_URLS)
    for meeting_url in meeting_links:
        try:
            race_url = get_mens_100m_url(meeting_url)
            if race_url and race_url not in dl_race_urls:
                dl_race_urls.append(race_url)
        except Exception as e:
            print(f"FAILED meeting lookup: {meeting_url} — {e}")

    print(f"\n=== Scraping {len(dl_race_urls)} Diamond League finals ===")
    dl_df = scrape_url_list(dl_race_urls)

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