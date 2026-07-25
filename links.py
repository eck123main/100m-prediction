"""
Central store of all race URLs. Add new ones here, then run
collect_data.py to scrape and merge them into the dataset.
"""

CHAMPIONSHIP_URLS = [
    "https://worldathletics.org/results/olympic-games/2024/the-xxxiii-olympic-games-7153115/men/100-metres/final/result",  # Paris 2024
    "https://worldathletics.org/results/world-athletics-championships/2023/world-athletics-championships-budapest-2023-7138987/men/100-metres/final/result",  # Budapest 2023
    "https://worldathletics.org/results/olympic-games/2021/the-xxxii-olympic-games-7132391/men/100-metres/final/result",  # Tokyo 2020(21)
    "https://worldathletics.org/competitions/world-athletics-championships/world-athletics-championships-oregon-2022-7137279/results/men/100-metres/final/result",  # Oregon 2022
    "https://worldathletics.org/results/world-athletics-championships/2019/iaaf-world-athletics-championships-doha-2019-7125365/men/100-metres/final/result",  # Doha 2019
    "https://worldathletics.org/results/world-athletics-championships/2017/iaaf-world-championships-london-2017-7093740/men/100-metres/final/result",  # London 2017
    "https://worldathletics.org/results/iaaf-world-championships-in-athletics/2015/15th-iaaf-world-championships-7078726/men/100-metres/final/result",  # Beijing 2015
    "https://worldathletics.org/results/world-athletics-championships/2013/14th-iaaf-world-championships-7003368/men/100-metres/final/result",  # Moscow 2013
    "https://worldathletics.org/results/olympic-games/2012/the-xxx-olympic-games-6999193/men/100-metres/final/result",  # London 2012
    "https://worldathletics.org/results/world-athletics-championships/2011/13th-iaaf-world-championships-in-athletics-7003367/men/100-metres/final/result",  # Daegu 2011

    # Add new championship/Olympic URLs below this line:
]

# Diamond League URLs are discovered automatically by scraper.get_diamond_league_meeting_links()
# and don't need to be listed here manually. But if you find one that isn't
# auto-discoverable (e.g. from a year the index page doesn't expose), add it here:
MANUAL_DIAMOND_LEAGUE_URLS = [
    # e.g. "https://worldathletics.org/results/diamond-league-meetings/2022/.../men/100-metres/final/result",
]