"""
One-off discovery tool (not part of the regular collect_data.py pipeline):
probe numeric IDs near the known DIAMOND_LEAGUE_HUB_URLS clusters to find
2022-2026 Diamond League meetings that weren't manually collected yet.

Bounded — only probes small ranges around/within existing known clusters,
not open-ended. Run with: python probe_hub_ids.py
"""

import re

from links import DIAMOND_LEAGUE_HUB_URLS
from scraper import fetch, scrape_hub_race

MARGIN = 10
GAP_THRESHOLD = 15  # ids further apart than this are treated as separate clusters

BASE_URL = "https://worldathletics.org/competitions/diamond-league/calendar-results/{id}/result"


def known_ids():
    ids = set()
    for url in DIAMOND_LEAGUE_HUB_URLS:
        m = re.search(r"calendar-results/(\d+)/result", url)
        if m:
            ids.add(int(m.group(1)))
    return ids


def cluster_ranges(ids):
    ids = sorted(ids)
    clusters = []
    start = prev = ids[0]
    for i in ids[1:]:
        if i - prev > GAP_THRESHOLD:
            clusters.append((start, prev))
            start = i
        prev = i
    clusters.append((start, prev))
    return clusters


def main():
    ids = known_ids()
    print(f"Known hub meeting IDs: {len(ids)}")
    clusters = cluster_ranges(ids)
    print(f"Grouped into {len(clusters)} clusters")

    candidates = set()
    for lo, hi in clusters:
        for cand in range(lo - MARGIN, hi + MARGIN + 1):
            if cand not in ids:
                candidates.add(cand)
    candidates = sorted(candidates)
    print(f"Probing {len(candidates)} candidate IDs not already in links.py\n")

    found = []
    for cand in candidates:
        url = BASE_URL.format(id=cand)
        try:
            df = scrape_hub_race(url)
            print(f"NEW MEETING FOUND ({len(df)} rows): {url}")
            found.append(url)
        except Exception as e:
            msg = str(e)
            if "404" in msg or "Client Error" in msg:
                pass  # not a real meeting ID at all, stay quiet
            else:
                # a real meeting page exists, just no elite Diamond Discipline
                # Men's 100m there — not useful to us, stay quiet too
                pass

    print(f"\n=== Done. {len(found)} new usable meetings found ===")
    for url in found:
        print(url)


if __name__ == "__main__":
    main()
