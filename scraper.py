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


def scrape_race(url):
    """Scrape a single World Athletics results page into a clean DataFrame."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    tables = pd.read_html(StringIO(resp.text))
    results_table = max(tables, key=len)

    # Normalize column names across inconsistent page formats
    results_table.columns = [str(c).strip() for c in results_table.columns]
    rename_map = {"Mark": "MARK", "Athlete": "ATHLETE", "Unnamed: 2": "COUNTRY"}
    results_table = results_table.rename(columns=rename_map)

    results_table[["time", "record_flag"]] = results_table["MARK"].apply(
        lambda m: pd.Series(clean_mark(m))
    )

    soup = BeautifulSoup(resp.text, "html.parser")

    # wind
    heading = soup.find(string=lambda s: s and "Wind" in s)
    wind = None
    if heading:
        match = re.search(r"Wind\s*([+-]?\d+\.\d+)", heading)
        if match:
            wind = float(match.group(1))

    # date — from EventDate meta tag
    date = None
    for meta in soup.find_all("meta"):
        if meta.get("name") == "EventDate" or meta.get("property") == "EventDate":
            date = meta.get("content")
            break

    # venue + meet name
    desc_tag = soup.find("meta", attrs={"property": "og:description"})
    venue = None
    if desc_tag and desc_tag.get("content"):
        venue_match = re.search(r"in\s+([A-Za-z\s]+)$", desc_tag["content"].strip())
        if venue_match:
            venue = venue_match.group(1).strip()

    title_tag = soup.find("meta", attrs={"property": "og:title"})
    meet_name = title_tag["content"].strip() if title_tag and title_tag.get("content") else None

    # round (final/semi-final/heats) — extracted from the URL path
    round_type = "final"
    if "/semi-final/" in url:
        round_type = "semi-final"
    elif "/heats/" in url:
        round_type = "heats"

    results_table["wind"] = wind
    results_table["date"] = date
    results_table["venue"] = venue
    results_table["meet_name"] = meet_name
    results_table["source_url"] = url
    results_table["round"] = round_type

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


def get_diamond_league_meeting_links():
    """Scrape the Diamond League meetings index page for all meeting URLs."""
    resp = requests.get("https://worldathletics.org/results/diamond-league-meetings",
                         headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=True)

    meeting_links = [
        a["href"] for a in links
        if a["href"].startswith("/results/diamond-league-meetings/")
    ]
    meeting_links = ["https://worldathletics.org" + link for link in meeting_links]
    meeting_links = list(dict.fromkeys(meeting_links))  # dedupe, preserve order

    return meeting_links


def generate_round_variants(final_url):
    """Given a /final/ URL, generate its /semi-final/ and /heats/ equivalents."""
    variants = []
    if "/final/" in final_url:
        variants.append(final_url.replace("/final/", "/semi-final/"))
        variants.append(final_url.replace("/final/", "/heats/"))
    return variants