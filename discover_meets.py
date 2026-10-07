"""
Find meetings we're missing by looking at where athletes actually raced.

For every athlete in the dataset who ran 10.30 or faster since START_DATE,
read their World Athletics 100m results for the given seasons and collect
each competition we don't already have. Prints the new meetings as hub URLs
(ready to paste into links.py) and saves them to a CSV.

    py -3.14 discover_meets.py                     # current season
    py -3.14 discover_meets.py --years 2024 2025   # earlier seasons
    py -3.14 discover_meets.py --indoor-60m --years 2025 2026   # indoor 60m meets

Earlier seasons come from the same data API the athlete profile page uses
when you switch year; its public key is read from the site's own config.
"""

import argparse
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from bs4 import BeautifulSoup

from links import (CHAMPIONSHIP_URLS, CONTINENTAL_TOUR_HUB_URLS, DIAMOND_LEAGUE_HUB_URLS, INDOOR_60M_URLS,
                   OTHER_HUB_URLS)
from scraper import fetch

CSV_PATH = "100m_races_dataset.csv"
START_DATE = "2024-01-01"
MAX_TIME = 10.30
HUB_URL = "https://worldathletics.org/competition/calendar-results/results/{}?eventId={}"
OUT_PATH = "discovered_meets.csv"
SLUG_CACHE = "athlete_slugs.json"
# (discipline name in profile results, WA event id for the hub URL). The API's
# "indoor" field is always empty, so the discipline name is what identifies
# the event (men's 60m is almost entirely an indoor event).
EVENTS = {"100m": ("100 Metres", "10229630"), "60m": ("60 Metres", "10229683")}


def page_data(url):
    soup = BeautifulSoup(fetch(url).text, "html.parser")
    return json.loads(soup.find("script", id="__NEXT_DATA__").string)["props"]["pageProps"]


def athlete_slugs(hub_url):
    """Profile slugs of every men's 100m athlete on a hub results page."""
    try:
        data = page_data(hub_url)["calendarEventsResults"]
    except Exception:
        return {}
    slugs = {}
    for section in data["eventTitles"]:
        for event in section["events"]:
            if event.get("event") != "Men's 100 Metres":
                continue
            for race in event.get("races", []):
                for result in race.get("results", []):
                    c = result.get("competitor") or {}
                    if c.get("urlSlug") and c.get("hasProfile"):
                        slugs[c["name"].strip().title()] = c["urlSlug"]
    return slugs


RESULTS_QUERY = """
query GetSingleCompetitorResultsDiscipline($id: Int, $resultsByYearOrderBy: String, $resultsByYear: Int) {
  getSingleCompetitorResultsDiscipline(id: $id, resultsByYear: $resultsByYear,
                                       resultsByYearOrderBy: $resultsByYearOrderBy) {
    resultsByEvent {
      indoor discipline
      results { date competition venue category race place mark wind notLegal competitionId eventId }
    }
  }
}"""


def graphql_config():
    """The site's public GraphQL endpoint and key, read from its JS bundles."""
    html = fetch("https://worldathletics.org/athletes").text
    for src in re.findall(r'src="(/_next/static/[^"]+\.js)"', html):
        js = fetch("https://worldathletics.org" + src).text
        m = re.search(r'graphql:\{endpoint:"([^"]+)",[^}]*apiKey:"([^"]+)"', js)
        if m:
            return m.group(1), m.group(2)
    raise RuntimeError("Couldn't find the GraphQL config on worldathletics.org")


def season_results(slug, year, api, event="100m"):
    """An athlete's results in one event (default outdoor 100m) for one season."""
    discipline, _ = EVENTS[event]
    endpoint, key = api
    athlete_id = int(slug.rsplit("-", 1)[1])
    time.sleep(random.uniform(0.4, 1.0))  # same politeness as scraper.fetch
    try:
        resp = requests.post(endpoint, timeout=20, headers={"x-api-key": key, "User-Agent": "Mozilla/5.0"},
                             json={"query": RESULTS_QUERY, "variables": {
                                 "id": athlete_id, "resultsByYear": year, "resultsByYearOrderBy": "discipline"}})
        events = resp.json()["data"]["getSingleCompetitorResultsDiscipline"]["resultsByEvent"]
    except Exception:
        return []
    return [r for e in events if e.get("discipline") == discipline for r in e["results"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, nargs="+", default=[pd.Timestamp.now().year])
    parser.add_argument("--indoor-60m", action="store_true", help="find indoor 60m meets instead")
    args = parser.parse_args()
    years, event = args.years, ("60m" if args.indoor_60m else "100m")

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    recent = df[df["date"] >= START_DATE]
    fast = set(recent.loc[recent["time"] <= MAX_TIME, "ATHLETE"].str.strip().str.title())
    recent_hubs = [u for u in recent["source_url"].unique() if "calendar-results" in u]

    # Profile links per meeting page are cached, so re-runs only read new pages.
    try:
        cache = json.load(open(SLUG_CACHE, encoding="utf-8"))
    except FileNotFoundError:
        cache = {}
    to_read = [u for u in recent_hubs if u not in cache]
    print(f"{len(fast)} athletes at <= {MAX_TIME}s since {START_DATE}; "
          f"reading {len(to_read)} new meetings for profile links ({len(recent_hubs) - len(to_read)} cached)")
    with ThreadPoolExecutor(4) as ex:
        for i, (u, s) in enumerate(zip(to_read, ex.map(athlete_slugs, to_read)), start=1):
            cache[u] = s
            if i % 100 == 0 or i == len(to_read):  # save as we go so an interrupted run isn't wasted
                json.dump(cache, open(SLUG_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
                print(f"  profile links: {i}/{len(to_read)} meetings read", flush=True)
    slugs = {}
    for u in recent_hubs:
        slugs.update(cache[u])
    targets = sorted({slugs[a] for a in fast if a in slugs})
    print(f"Found profiles for {len(targets)} of them; reading {years} results")

    api = graphql_config()
    jobs = [(slug, year) for slug in targets for year in years]
    with ThreadPoolExecutor(4) as ex:
        results = [r for rs in ex.map(lambda j: season_results(j[0], j[1], api, event), jobs) for r in rs]

    if not results:
        print("No results found for these athletes/seasons.")
        return
    known = set()
    known_urls = (INDOOR_60M_URLS if event == "60m" else
                  CHAMPIONSHIP_URLS + DIAMOND_LEAGUE_HUB_URLS + OTHER_HUB_URLS + CONTINENTAL_TOUR_HUB_URLS)
    for u in known_urls:
        known |= set(re.findall(r"(\d{7})", u))
    meets = (pd.DataFrame(results)
             .groupby("competitionId")
             .agg(competition=("competition", "first"), date=("date", "first"),
                  category=("category", "first"), athletes=("mark", "size"))
             .reset_index())
    meets = meets[~meets["competitionId"].isin(known)].sort_values("athletes", ascending=False)
    meets["url"] = meets["competitionId"].map(lambda cid: HUB_URL.format(cid, EVENTS[event][1]))
    meets.to_csv(OUT_PATH, index=False)
    print(f"\n{len(meets)} meetings not in links.py (saved to {OUT_PATH}):")
    print(meets[["date", "category", "athletes", "competition"]].head(40).to_string(index=False))


if __name__ == "__main__":
    main()
