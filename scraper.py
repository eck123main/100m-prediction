"""
Core scraping functions: fetch a single race's results, and discover
race URLs automatically from World Athletics' meeting-index pages.
"""

import json
import random
import re
import time
from io import StringIO

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

RESULT_COLUMNS = ["ATHLETE", "COUNTRY", "time", "record_flag", "Reaction Time",
                   "wind", "date", "venue", "meet_name", "source_url", "round", "heat"]


def fetch(url, max_retries=3, backoff_base=1.0, **kwargs):
    """GET a URL with a small polite delay and retry-with-backoff on failure.
    Shared by every scraping function so we don't hammer worldathletics.org
    with hundreds of back-to-back requests."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 15)
    last_exc = None
    for attempt in range(max_retries):
        time.sleep(random.uniform(0.4, 1.0))
        try:
            resp = requests.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            # 4xx client errors (404, etc.) are permanent — retrying the same
            # URL won't ever succeed, so fail fast instead of burning backoff.
            if e.response is not None and 400 <= e.response.status_code < 500:
                raise
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff_base * (2 ** attempt))
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff_base * (2 ** attempt))
    raise last_exc


def normalize_meet_name(name):
    """Collapse whitespace runs (including newlines/tabs from page markup)
    so the same meet doesn't fragment into multiple distinct meet_name values."""
    if not name:
        return name
    return " ".join(str(name).split())


def _drop_non_sprint_marks(results_table):
    """Drop rows whose raw mark looks like a longer-distance time (contains ':',
    e.g. '1:43.68' for an 800m result) before clean_mark() can mis-parse it into
    record_flag. Wrong-table matches on multi-event hub pages produce these."""
    mask = results_table["MARK"].astype(str).str.contains(":", na=False)
    return results_table.loc[~mask].reset_index(drop=True)


def _check_plausible_sprint_times(results_table, low=9.4, high=11.5, min_valid_fraction=0.5):
    """Raise if most parsed times fall outside a plausible men's 100m range —
    a cheap defense-in-depth check against wrong-event contamination (e.g. a
    200m/800m table getting matched instead of the 100m one)."""
    valid_times = results_table["time"].dropna()
    if len(valid_times) == 0:
        return
    in_range = valid_times.between(low, high).mean()
    if in_range < min_valid_fraction:
        raise ValueError(
            f"only {in_range:.0%} of {len(valid_times)} marks fall in a plausible "
            f"100m range [{low}, {high}]s — likely wrong event table"
        )


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
def _rename_result_columns(table):
    """Strip whitespace from a raw pd.read_html table's column labels and
    rename them to this module's schema."""
    table = table.copy()
    table.columns = [str(c).strip() for c in table.columns]
    rename_map = {"Mark": "MARK", "Athlete": "ATHLETE", "Unnamed: 2": "COUNTRY"}
    return table.rename(columns=rename_map)


def scrape_race(url, known_venue=None):
    resp = fetch(url)

    tables = pd.read_html(StringIO(resp.text))
    renamed = [_rename_result_columns(t) for t in tables]
    # A heats/semi-final page renders one table per heat group — all with
    # identical columns/length — not one table for the whole round. Picking
    # a single table (even "the largest", which on a tie is just the first)
    # silently drops every other heat group's athletes. Concatenate every
    # table that looks like a results table instead; a final page always has
    # exactly one such table, so this is a no-op there.
    results_tables = [t for t in renamed if "MARK" in t.columns and "ATHLETE" in t.columns]
    if not results_tables:
        raise ValueError("No results table found on this page")
    # Keep which table (= heat group) each row came from, so downstream code
    # can treat each heat as its own race instead of one giant field.
    results_table = pd.concat(
        [t.assign(heat=i) for i, t in enumerate(results_tables, start=1)], ignore_index=True
    )

    results_table = _drop_non_sprint_marks(results_table)
    results_table[["time", "record_flag"]] = results_table["MARK"].apply(
        lambda m: pd.Series(clean_mark(m))
    )
    _check_plausible_sprint_times(results_table)

    soup = BeautifulSoup(resp.text, "html.parser")

    # One "Wind +0.8" label per heat table, in page order. When the counts
    # line up, give each heat its own wind; otherwise fall back to the first
    # label for every row (all a single-table final page ever has).
    winds = [float(m.group(1)) for s in soup.find_all(string=lambda s: s and "Wind" in s)
             if (m := re.match(r"\s*Wind\s*([+-]?\d+\.\d+)", s))]
    if len(winds) == len(results_tables):
        wind = results_table["heat"].map(dict(enumerate(winds, start=1)))
    else:
        wind = winds[0] if winds else None

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
    meet_name = normalize_meet_name(meet_name) if meet_name else (
        normalize_meet_name(soup.title.string) if soup.title else None
    )

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

    # This page format doesn't always include Reaction Time — add it as
    # empty if missing, so column selection below doesn't crash
    if "Reaction Time" not in results_table.columns:
        results_table["Reaction Time"] = None

    return results_table[RESULT_COLUMNS]

def _map_round_label(race_label):
    """Map a hub-page race label ('Final', 'Heat 1', 'Semi-Final 2',
    'Semifinal - Heat', ...) to the same round vocabulary used elsewhere in
    the dataset. Checks "semi" before "heat": some hub pages label a
    semi-final's individual heat groups as e.g. 'Semifinal - Heat', which
    contains both substrings and must resolve to 'semi-final', not the
    first-round 'heats' bucket. Quarter-finals ('Quarterfinal - Heat') get
    their own round; decathlon races ('Combined - Group', which some
    championship pages list in the same section) return None and are skipped."""
    if not race_label:
        return "final"
    label = race_label.lower()
    if "combined" in label:
        return None  # decathlon 100m ("Combined - Group"), not a 100m race
    if "semi" in label:
        return "semi-final"
    if "quarter" in label:
        return "quarter-final"
    if "heat" in label:
        return "heats"
    return "final"


def _parse_wind(wind_value):
    try:
        return float(wind_value)
    except (TypeError, ValueError):
        return None


# Hub-page section titles that hold an elite men's 100m, in order of
# preference. None = an untitled section, which is how championships and
# Continental Tour meetings label their main event. "Promotional"/
# "Invitational" are non-scoring but elite-field 100m races at Diamond League
# meetings (e.g. Kerley at Silesia 2024). Anything else — "U18/U20/U23
# Events", "National Events", "Regional Races", "Pre-Programme", "Combined
# Events", "Qualifier Prelims", one-off exhibitions like "Karsten vs. Mondo"
# — is deliberately excluded. This used to be a blocklist, which let unseen
# titles (U18/U23 races, the Warholm-Duplantis exhibition) through.
ELITE_HUB_TIERS = ["Diamond Discipline", None, "Promotional Events", "Invitational Events"]


# Plausible winning-to-tail-end times per event, for the wrong-table check.
PLAUSIBLE_RANGE = {"Men's 100 Metres": (9.4, 11.5), "Men's 60 Metres": (6.3, 7.4)}


def scrape_hub_race(url, event_name="Men's 100 Metres"):
    """Scrape a men's 100m result from a World Athletics 'hub' page —
    a calendar-results/{id}(/result) page that embeds every event's results
    for the whole meeting on one page. Used for Diamond League meetings and
    for other meetings (national championships, etc.) that share the same
    underlying page format.

    Rather than parsing the rendered HTML tables (which is ambiguous: a
    single meeting page can have several sections all headed "Men's 100
    Metres" — e.g. a National-tier and a U20-tier field alongside, or
    instead of, the elite one — and naive "next table after this heading"
    logic can walk into a completely different event's table), this reads
    the page's embedded __NEXT_DATA__ JSON directly, which explicitly
    labels each section's tier (e.g. "Diamond Discipline" vs "National
    Events" vs "U20 Events"). Diamond League pages label the elite tier
    "Diamond Discipline"; other meetings (e.g. national championships)
    leave it untitled (eventTitle None) instead. See ELITE_HUB_TIERS.

    Prefer the generic competition/calendar-results/results/{id} URL: the
    competitions/diamond-league/... variant of the same page sometimes omits
    sections (e.g. Zurich 2022/2025 and Lausanne 2025 Diamond Discipline
    100m finals are only on the generic one).
    """
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag is None or not script_tag.string:
        raise ValueError("No __NEXT_DATA__ JSON found on this page")

    data = json.loads(script_tag.string)
    calendar_results = data["props"]["pageProps"]["calendarEventsResults"]
    competition = calendar_results["competition"]

    # A meeting can have a "Diamond Discipline" section that doesn't include
    # the men's 100m that year, alongside a Promotional one that does — so
    # pick the most-preferred tier that actually contains the event.
    sections_with_100m = [
        et for et in calendar_results["eventTitles"]
        if any(e.get("event") == event_name for e in et.get("events", []))
    ]
    main_section = next(
        (et for tier in ELITE_HUB_TIERS for et in sections_with_100m
         if et.get("eventTitle") == tier),
        None,
    )
    if main_section is None:
        raise ValueError(f"No elite-tier section with {event_name} on this page")

    event = next(
        (e for e in main_section["events"] if e.get("event") == event_name),
        None,
    )
    if event is None:
        raise ValueError(f"{event_name} is not an elite-tier event at this meeting")

    venue = competition.get("venue")
    meet_name = normalize_meet_name(competition.get("name"))
    start_date = competition.get("startDate")  # ISO "YYYY-MM-DD", or None

    rows = []
    heats_seen = {}
    for race in event.get("races", []):
        round_label = _map_round_label(race.get("race"))
        if round_label is None:
            continue
        wind = _parse_wind(race.get("wind"))
        # Each race carries its own date — on multi-day championships the
        # heats are days before the final, so they can inform its prediction.
        race_date = race.get("date") or start_date
        date_str = pd.to_datetime(race_date).strftime("%d/%m/%Y %H:%M:%S") if race_date else None
        # Several races can share a round label (Heat 1/Heat 2, or an A and B
        # "Final") — number them so each is kept as its own race downstream.
        heats_seen[round_label] = heats_seen.get(round_label, 0) + 1
        for result in race.get("results", []):
            competitor = result.get("competitor") or {}
            rows.append({
                "ATHLETE": competitor.get("name"),
                "COUNTRY": result.get("nationality"),
                "MARK": result.get("mark"),
                "Reaction Time": None,  # not present in this page format
                "wind": wind,
                "date": date_str,
                "venue": venue,
                "meet_name": meet_name,
                "source_url": url,
                "round": round_label,
                "heat": heats_seen[round_label],
            })

    results_table = pd.DataFrame(rows)
    if results_table.empty or "MARK" not in results_table.columns:
        raise ValueError(f"{event_name} section has no results")

    results_table = _drop_non_sprint_marks(results_table)
    results_table[["time", "record_flag"]] = results_table["MARK"].apply(
        lambda m: pd.Series(clean_mark(m))
    )
    _check_plausible_sprint_times(results_table, *PLAUSIBLE_RANGE.get(event_name, (9.4, 11.5)))

    return results_table[RESULT_COLUMNS]
def get_mens_100m_url(meeting_url):
    """Given a Diamond League meeting page URL, find its men's 100m final result URL."""
    resp = fetch(meeting_url)

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

    resp = fetch(url)

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

def _hub_start_list_names(start_list):
    """Best-effort athlete names from a hub race's startList field. Its
    pre-race shape hasn't been observed yet (WA clears it once results are
    published), so accept the shapes results[] uses and fail loudly
    otherwise rather than guessing."""
    names = []
    for entry in start_list or []:
        if not isinstance(entry, dict):
            continue
        competitor = entry.get("competitor") or {}
        name = competitor.get("name") or entry.get("name") or entry.get("athlete")
        if name:
            names.append(name)
    return names


def fetch_start_list(url):
    """Return the men's 100m field (list of athlete names) for an upcoming race.

    Supports:
    - Old-style championship/meeting pages (.../men/100-metres/<round>/result
      or .../startlist): reads the /startlist table. Verified on Tokyo 2025.
    - Hub pages (competition/calendar-results/results/{id}): reads the elite
      tier's races[].startList, or the entrants in results[] if the race has
      no marks yet. Not yet verified against a live pre-race page.
    For a hub meeting with several races (heats), returns every entrant.
    """
    if "/100-metres/" in url:
        sl_url = re.sub(r"/(result|startlist)/?$", "", url.rstrip("/")) + "/startlist"
        tables = [_rename_result_columns(t) for t in pd.read_html(StringIO(fetch(sl_url).text))]
        tables = [t for t in tables if "ATHLETE" in t.columns]
        if not tables:
            raise ValueError(f"No start list table found at {sl_url}")
        return pd.concat(tables)["ATHLETE"].dropna().astype(str).str.strip().tolist()

    soup = BeautifulSoup(fetch(url).text, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag is None or not script_tag.string:
        raise ValueError("No __NEXT_DATA__ JSON found on this page")
    calendar_results = json.loads(script_tag.string)["props"]["pageProps"]["calendarEventsResults"]
    sections = [et for et in calendar_results["eventTitles"]
                if any(e.get("event") == "Men's 100 Metres" for e in et.get("events", []))]
    section = next((et for tier in ELITE_HUB_TIERS for et in sections
                    if et.get("eventTitle") == tier), None)
    if section is None:
        raise ValueError("No elite-tier men's 100m on this page")
    event = next(e for e in section["events"] if e.get("event") == "Men's 100 Metres")

    names = []
    for race in event.get("races", []):
        names += _hub_start_list_names(race.get("startList"))
        if not race.get("startList"):
            names += _hub_start_list_names(race.get("results"))
    if not names:
        raise ValueError("Men's 100m found but no start list published yet "
                         "(or its format isn't recognized) — pass names manually")
    return list(dict.fromkeys(names))
