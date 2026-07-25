"""
Run this file directly to (re)build 100m_races_dataset.csv from scratch:
    python collect_data.py
"""

import pandas as pd
from scraper import scrape_race, get_mens_100m_url, get_diamond_league_meeting_links, generate_round_variants

CSV_PATH = "100m_races_dataset.csv"

CHAMPIONSHIP_URLS = [
    "https://worldathletics.org/results/olympic-games/2024/the-xxxiii-olympic-games-7153115/men/100-metres/final/result",
    "https://worldathletics.org/results/world-athletics-championships/2023/world-athletics-championships-budapest-2023-7138987/men/100-metres/final/result",
    "https://worldathletics.org/results/olympic-games/2021/the-xxxii-olympic-games-7132391/men/100-metres/final/result",
    "https://worldathletics.org/competitions/world-athletics-championships/world-athletics-championships-oregon-2022-7137279/results/men/100-metres/final/result",
    "https://worldathletics.org/results/world-athletics-championships/2019/iaaf-world-athletics-championships-doha-2019-7125365/men/100-metres/final/result",
    "https://worldathletics.org/results/world-athletics-championships/2017/iaaf-world-championships-london-2017-7093740/men/100-metres/final/result",
    "https://worldathletics.org/results/iaaf-world-championships-in-athletics/2015/15th-iaaf-world-championships-7078726/men/100-metres/final/result",
    "https://worldathletics.org/results/world-athletics-championships/2013/14th-iaaf-world-championships-7003368/men/100-metres/final/result",
    "https://worldathletics.org/results/olympic-games/2012/the-xxx-olympic-games-6999193/men/100-metres/final/result",
    "https://worldathletics.org/results/world-athletics-championships/2011/13th-iaaf-world-championships-in-athletics-7003367/men/100-metres/final/result",
]


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

    print("\n=== Discovering Diamond League meeting URLs ===")
    meeting_links = get_diamond_league_meeting_links()
    print(f"Found {len(meeting_links)} meeting links")

    dl_race_urls = []
    for meeting_url in meeting_links:
        try:
            race_url = get_mens_100m_url(meeting_url)
            if race_url:
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