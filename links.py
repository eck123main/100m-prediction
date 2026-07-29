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

    # Added: gaps found by cross-referencing worldathletics.org's calendar-results
    # API (competitionGroupId=6 for Worlds, =5 for Olympics) against the URLs above.
    # Note: the slug text in these URLs is cosmetic — worldathletics.org resolves
    # purely off the trailing numeric ID, confirmed by requesting these same IDs
    # with garbage slugs and getting identical 200 responses.
    "https://worldathletics.org/results/world-athletics-championships/2025/world-athletics-championships-tokyo-2025-7190593/men/100-metres/final/result",  # Tokyo 2025
    "https://worldathletics.org/results/olympic-games/2016/the-xxxi-olympic-games-7093747/men/100-metres/final/result",  # Rio 2016
    "https://worldathletics.org/results/olympic-games/2008/the-xxix-olympic-games-6977748/men/100-metres/final/result",  # Beijing 2008
    "https://worldathletics.org/results/olympic-games/2004/the-xxviii-olympic-games-6913163/men/100-metres/final/result",  # Athens 2004
    "https://worldathletics.org/results/olympic-games/2000/the-xxvii-olympic-games-6951910/men/100-metres/final/result",  # Sydney 2000
    # 1996 Atlanta Olympics: this ID (6961749) 404s on the modern results path —
    # not migrated to this URL scheme. Skipped rather than guessing further.
    "https://worldathletics.org/results/world-athletics-championships/2009/iaaf-world-championships-berlin-2009-6998524/men/100-metres/final/result",  # Berlin 2009
    "https://worldathletics.org/results/world-athletics-championships/2007/iaaf-world-championships-osaka-2007-6903480/men/100-metres/final/result",  # Osaka 2007
    "https://worldathletics.org/results/world-athletics-championships/2005/iaaf-world-championships-helsinki-2005-6937596/men/100-metres/final/result",  # Helsinki 2005
    "https://worldathletics.org/results/world-athletics-championships/2003/iaaf-world-championships-paris-2003-6930156/men/100-metres/final/result",  # Paris/Saint-Denis 2003
    "https://worldathletics.org/results/world-athletics-championships/2001/iaaf-world-championships-edmonton-2001-6947294/men/100-metres/final/result",  # Edmonton 2001
    "https://worldathletics.org/results/world-athletics-championships/1999/iaaf-world-championships-seville-1999-6939522/men/100-metres/final/result",  # Seville 1999
    "https://worldathletics.org/results/world-athletics-championships/1997/iaaf-world-championships-athens-1997-6913256/men/100-metres/final/result",  # Athens 1997
    "https://worldathletics.org/results/world-athletics-championships/1995/iaaf-world-championships-gothenburg-1995-6997728/men/100-metres/final/result",  # Gothenburg 1995
    "https://worldathletics.org/results/world-athletics-championships/1993/iaaf-world-championships-stuttgart-1993-6993598/men/100-metres/final/result",  # Stuttgart 1993
    "https://worldathletics.org/results/world-athletics-championships/1991/iaaf-world-championships-tokyo-1991-6987209/men/100-metres/final/result",  # Tokyo 1991
    "https://worldathletics.org/results/world-athletics-championships/1987/iaaf-world-championships-rome-1987-6986221/men/100-metres/final/result",  # Rome 1987
    "https://worldathletics.org/results/world-athletics-championships/1983/iaaf-world-championships-helsinki-1983-6988504/men/100-metres/final/result",  # Helsinki 1983

    # Add new championship/Olympic URLs below this line:
]

# 2022-2026 Diamond League meetings — found manually by clicking through
# in browser (the "calendar-results/{id}/result" hub format). Each page
# contains ALL events for that meeting, including Men's 100m.
# Note: scrape_hub_race() automatically skips any meeting with no Men's
# 100m section (e.g. field-events-only days), so duplicates/misses here
# just fail cleanly rather than breaking anything.
DIAMOND_LEAGUE_HUB_URLS = [
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214016/result",  # Shaoxing/Keqiao 2026
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214017/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214018/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214019/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214020/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214021/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214022/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214023/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214024/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214025/result",

    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199682/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199683/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199684/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199685/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199686/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7199680/result",

    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203938/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203939/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203940/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203941/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203943/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203944/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203816/result",

    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174050/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174051/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174052/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174053/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174054/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174056/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174057/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174058/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174059/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174060/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174061/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174062/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174063/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174658/result",

    "https://worldathletics.org/competitions/diamond-league/calendar-results/7202834/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7172922/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7172925/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7172926/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7172927/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7172928/result",

    "https://worldathletics.org/competitions/diamond-league/calendar-results/7155407/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7155467/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7154214/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7154215/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7154216/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7154217/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7154228/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7147636/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7147656/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7190105/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153961/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153964/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153965/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153966/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153967/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153968/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153970/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153972/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153974/result",
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153975/result",

    # Found via calendar-results discovery (competitionGroupId=627) — gaps versus the list above:
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7153971/result",  # Herculis Monaco 2022
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7174055/result",  # Prefontaine Classic 2024
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203937/result",  # Bauhaus-Galan 2025
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7203942/result",  # Herculis Monaco 2025
    "https://worldathletics.org/competitions/diamond-league/calendar-results/7214015/result",  # Doha Meeting 2026

    # Add more here as you find them — one per meeting, any year 2022-2026
]


# Diamond League URLs are discovered automatically by scraper.get_diamond_league_meeting_links()
# and don't need to be listed here manually. But if you find one that isn't
# auto-discoverable (e.g. from a year the index page doesn't expose), add it here:
MANUAL_DIAMOND_LEAGUE_URLS = [
    # e.g. "https://worldathletics.org/results/diamond-league-meetings/2022/.../men/100-metres/final/result",
]