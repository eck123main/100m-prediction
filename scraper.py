"""
Core scraping functions: fetch a single race's results, and discover
race URLs automatically from World Athletics' meeting-index pages.
"""

import requests
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
from io import StringIO

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def clean_mark(mark):
    """Split '9.79 PB' into (9.79, 'PB'), or '9.91' into (9.91, None).
    Non-numeric marks (DNF/DQ/DNS) get NaN time and the code as the flag."""
    if pd.isna(mark):
        return np.nan, None
    parts = str(mark).strip().split()
    try:
        time = float(parts[0])
        flag = parts[1] if len(parts) > 1 else None
    except ValueError:
        time = np.nan
        flag = parts[0]  # e.g. 'DNF', 'DQ', 'DNS'
    return time, flag
def scrape_race(url, known_venue=None):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    tables = pd.read_html(StringIO(resp.text))
    results_table = max(tables, key=len)

    results_table.columns = [str(c).strip() for c in results_table.columns]
    rename_map = {"Mark": "MARK", "Athlete": "ATHLETE", "Unnamed: 2": "COUNTRY"}
    results_table = results_table.rename(columns=rename_map)

    results_table[["time", "record_flag"]] = results_table["MARK"].apply(
        lambda m: pd.Series(clean_mark(m))
    )

    soup = BeautifulSoup(resp.text, "html.parser")

    heading = soup.find(string=lambda s: s and "Wind" in s)
    wind = None
    if heading:
        match = re.search(r"Wind\s*([+-]?\d+\.\d+)", heading)
        if match:
            wind = float(match.group(1))

    date = None
    for meta in soup.find_all("meta"):
        if meta.get("name") == "EventDate" or meta.get("property") == "EventDate":
            date = meta.get("content")
            break

    venue = known_venue
    if not venue:
        desc_tag = soup.find("meta", attrs={"property": "og:description"})
        if desc_tag and desc_tag.get("content"):
            venue_match = re.search(r"in\s+([A-Za-z\s]+)$", desc_tag["content"].strip())
            if venue_match:
                venue = venue_match.group(1).strip()

    title_tag = soup.find("meta", attrs={"property": "og:title"})
    meet_name = title_tag["content"].strip() if title_tag and title_tag.get("content") else None

    round_type = "final"
    if "/semi-final/" in url:
        round_type = "semi-final"
    elif "/heats/" in url:
        round_type = "heats"

    results_table["wind"] = wind
    results_table["date"] = date
    results_table["venue"] = venue
    results_table["meet_name"] = meet_name if meet_name else (soup.title.string if soup.title else None)
    results_table["source_url"] = url
    results_table["round"] = round_type

    # This page format doesn't always include Reaction Time — add it as
    # empty if missing, so column selection below doesn't crash
    if "Reaction Time" not in results_table.columns:
        results_table["Reaction Time"] = None

    return results_table[["ATHLETE", "COUNTRY", "time", "record_flag", "Reaction Time",
                            "wind", "date", "venue", "meet_name", "source_url", "round"]]

def scrape_hub_race(url):
    """Scrape a men's 100m result from a Diamond League 'hub' page —
    a calendar-results/{id}/result page that embeds every event's
    results on one page, rather than linking to separate per-event pages."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the "Men's 100 Metres" heading, then the FIRST table that
    # appears after it (that's this event's results table)
    heading = soup.find(string=lambda s: s and "Men's 100 Metres" in s)
    if not heading:
        raise ValueError("No Men's 100 Metres section found on this page")

    # Walk forward through the page from that heading until we hit a table
    table_tag = heading.find_next("table")
    if table_tag is None:
        raise ValueError("Found 'Men's 100 Metres' heading but no table after it")

    results_table = pd.read_html(StringIO(str(table_tag)))[0]
    results_table.columns = [str(c).strip() for c in results_table.columns]
    rename_map = {"Mark": "MARK", "Athlete": "ATHLETE", "Pos.": "POS"}
    results_table = results_table.rename(columns=rename_map)

    # Country isn't a labeled column here — it's a separate cell before
    # athlete name in this format. Handle gracefully if missing.
    if "COUNTRY" not in results_table.columns:
        results_table["COUNTRY"] = None

    if "MARK" not in results_table.columns:
        raise ValueError("Table found but no MARK column — wrong table matched")

    results_table[["time", "record_flag"]] = results_table["MARK"].apply(
        lambda m: pd.Series(clean_mark(m))
    )

    if "Reaction Time" not in results_table.columns:
        results_table["Reaction Time"] = None

    # Wind — look for text near the "Men's 100 Metres" heading specifically
    wind = None
    wind_text = heading.find_next(string=lambda s: s and "Wind" in s)
    if wind_text:
        match = re.search(r"Wind:\s*([+-]?\d+\.\d+)", wind_text)
        if match:
            wind = float(match.group(1))

    results_table["wind"] = wind
    results_table["date"] = None   # not reliably extractable from this format yet
    results_table["venue"] = None
    results_table["meet_name"] = soup.title.string if soup.title else None
    results_table["source_url"] = url
    results_table["round"] = "final"

    return results_table[["ATHLETE", "COUNTRY", "time", "record_flag", "Reaction Time",
                            "wind", "date", "venue", "meet_name", "source_url", "round"]]
def get_mens_100m_url(meeting_url):
    """Given a Diamond League meeting page URL, find its men's 100m final result URL."""
    resp = requests.get(meeting_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=True)

    event_links = [a["href"] for a in links if "/men/100-metres/final/" in a["href"]]

    if not event_links:
        return None  # this meeting had no men's 100m final

    href = event_links[0].split("#")[0]  # strip the #resultheader fragment
    return "https://worldathletics.org" + href if href.startswith("/") else href


def get_diamond_league_meeting_links(year=None):
    """Scrape the Diamond League meetings index page for meeting URLs and venues.
    Returns a list of (url, venue) tuples."""
    url = "https://worldathletics.org/results/diamond-league-meetings"
    if year:
        url += f"?year={year}"

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr")

    meetings = []
    for row in rows:
        link_tag = row.find("a", href=True)
        if not link_tag or not link_tag["href"].startswith("/results/diamond-league-meetings/"):
            continue
        cells = row.find_all("td")
        venue = cells[1].get_text(strip=True) if len(cells) > 1 else None
        meetings.append(("https://worldathletics.org" + link_tag["href"], venue))

    # dedupe by URL, keep first venue seen
    seen = {}
    for u, v in meetings:
        if u not in seen:
            seen[u] = v
    return list(seen.items())


def generate_round_variants(final_url):
    """Given a /final/ URL, generate its /semi-final/ and /heats/ equivalents."""
    variants = []
    if "/final/" in final_url:
        variants.append(final_url.replace("/final/", "/semi-final/"))
        variants.append(final_url.replace("/final/", "/heats/"))
    return variants