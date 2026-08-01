"""
Diagnostic script: test different ways of accessing Diamond League meetings
by year, to figure out which years/methods actually work before committing
to a scraping strategy.

Run with: python test_year_access.py
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def get_meeting_years_present(html_text):
    """Given page HTML, find which years actually appear in the meeting links found."""
    soup = BeautifulSoup(html_text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)
             if a["href"].startswith("/results/diamond-league-meetings/")]
    years = set()
    for link in links:
        parts = link.split("/")
        # /results/diamond-league-meetings/2021/weltklasse-zurich-7058
        if len(parts) > 3 and parts[3].isdigit():
            years.add(parts[3])
    return sorted(years), len(links)


def test_url(label, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        years, count = get_meeting_years_present(resp.text)
        print(f"{label}: {count} links, years present: {years}")
        return years
    except Exception as e:
        print(f"{label}: FAILED — {e}")
        return []


def main():
    print("=== Testing base index page (no params) ===")
    test_url("base", "https://worldathletics.org/results/diamond-league-meetings")

    print("\n=== Testing ?year= param for 2016-2024 ===")
    for year in range(2016, 2025):
        test_url(f"?year={year}", f"https://worldathletics.org/results/diamond-league-meetings?year={year}")

    print("\n=== Testing ?page= pagination ===")
    for page in range(1, 5):
        test_url(f"?page={page}", f"https://worldathletics.org/results/diamond-league-meetings?page={page}")

    print("\n=== Testing alternate query param names ===")
    for param in ["Year", "y", "season", "yr"]:
        test_url(f"?{param}=2018", f"https://worldathletics.org/results/diamond-league-meetings?{param}=2018")


if __name__ == "__main__":
    main()