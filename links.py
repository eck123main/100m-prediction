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
# in browser. Each page contains ALL events for that meeting, including
# Men's 100m. Always use the generic competition/calendar-results/results/{id}
# form: the competitions/diamond-league/calendar-results/{id}/result form of
# the same page sometimes omits sections (see scraper.scrape_hub_race).
# Note: scrape_hub_race() automatically skips any meeting with no Men's
# 100m section (e.g. field-events-only days), so duplicates/misses here
# just fail cleanly rather than breaking anything.
DIAMOND_LEAGUE_HUB_URLS = [
    "https://worldathletics.org/competition/calendar-results/results/7214016?eventId=10229630",  # Shaoxing/Keqiao 2026
    "https://worldathletics.org/competition/calendar-results/results/7214017?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214018?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214019?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214020?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214021?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214022?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214023?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214024?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7214025?eventId=10229630",

    "https://worldathletics.org/competition/calendar-results/results/7199682?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7199683?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7199684?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7199685?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7199686?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7199680?eventId=10229630",

    "https://worldathletics.org/competition/calendar-results/results/7203938?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203939?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203940?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203941?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203943?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203944?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7203816?eventId=10229630",

    "https://worldathletics.org/competition/calendar-results/results/7174050?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174051?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174052?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174053?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174054?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174056?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174057?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174058?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174059?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174060?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174061?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174062?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174063?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7174658?eventId=10229630",

    "https://worldathletics.org/competition/calendar-results/results/7202834?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7172922?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7172925?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7172926?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7172927?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7172928?eventId=10229630",

    "https://worldathletics.org/competition/calendar-results/results/7155407?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7155467?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7154214?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7154215?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7154216?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7154217?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7154228?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7147636?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7147656?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7190105?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153961?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153964?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153965?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153966?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153967?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153968?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153970?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153972?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153974?eventId=10229630",
    "https://worldathletics.org/competition/calendar-results/results/7153975?eventId=10229630",

    # Found via calendar-results discovery (competitionGroupId=627) — gaps versus the list above:
    "https://worldathletics.org/competition/calendar-results/results/7153971?eventId=10229630",  # Herculis Monaco 2022
    "https://worldathletics.org/competition/calendar-results/results/7174055?eventId=10229630",  # Prefontaine Classic 2024
    "https://worldathletics.org/competition/calendar-results/results/7203937?eventId=10229630",  # Bauhaus-Galan 2025
    "https://worldathletics.org/competition/calendar-results/results/7203942?eventId=10229630",  # Herculis Monaco 2025
    "https://worldathletics.org/competition/calendar-results/results/7214015?eventId=10229630",  # Doha Meeting 2026
    "https://worldathletics.org/competition/calendar-results/results/7214026?eventId=10229630",  # Silesia Memorial 2026
    "https://worldathletics.org/competition/calendar-results/results/7214029?eventId=10229630",  # Memorial van Damme (DL Final) 2026
    # Lausanne (7214027) and Zurich (7214028) 2026 had no Diamond Discipline men's 100m.

    # 2012-2015 meetings, from the calendar-results listing (competitionGroupId=627).
    # Fills the gap between the old-style 2016+ pages and championship-only coverage.
    "https://worldathletics.org/competition/calendar-results/results/7033722?eventId=10229630",  # Doha IAAF Diamond League Meeting (2012-05-11)
    "https://worldathletics.org/competition/calendar-results/results/7033723?eventId=10229630",  # Shanghai Samsung Diamond League (2012-05-19)
    "https://worldathletics.org/competition/calendar-results/results/7033724?eventId=10229630",  # Roma Golden Gala (2012-05-31)
    "https://worldathletics.org/competition/calendar-results/results/7033725?eventId=10229630",  # Eugene Prefontaine Classic (2012-06-01)
    "https://worldathletics.org/competition/calendar-results/results/7033726?eventId=10229630",  # Oslo ExxonMobil Bislett Games (2012-06-07)
    "https://worldathletics.org/competition/calendar-results/results/7033727?eventId=10229630",  # New York adidas Grand Prix (2012-06-09)
    "https://worldathletics.org/competition/calendar-results/results/7033728?eventId=10229630",  # Paris Meeting AREVA (2012-07-06)
    "https://worldathletics.org/competition/calendar-results/results/7033729?eventId=10229630",  # Crystal Palace Aviva London Grand Prix (2012-07-13)
    "https://worldathletics.org/competition/calendar-results/results/7033730?eventId=10229630",  # Monaco Herculis (2012-07-20)
    "https://worldathletics.org/competition/calendar-results/results/7033731?eventId=10229630",  # Stockholm DN Galan (2012-08-17)
    "https://worldathletics.org/competition/calendar-results/results/7033732?eventId=10229630",  # Athletissima Lausanne (2012-08-23)
    "https://worldathletics.org/competition/calendar-results/results/7033733?eventId=10229630",  # Birmingham Aviva Grand Prix (2012-08-26)
    "https://worldathletics.org/competition/calendar-results/results/7033734?eventId=10229630",  # Weltklasse Zürich (2012-08-29)
    "https://worldathletics.org/competition/calendar-results/results/7033735?eventId=10229630",  # Bruxelles Memorial Van Damme (2012-09-07)
    "https://worldathletics.org/competition/calendar-results/results/7049151?eventId=10229630",  # Doha IAAF Diamond League Meeting (2013-05-10)
    "https://worldathletics.org/competition/calendar-results/results/7049149?eventId=10229630",  # Shanghai IAAF Diamond League Meeting (2013-05-18)
    "https://worldathletics.org/competition/calendar-results/results/7049152?eventId=10229630",  # New York adidas Grand Prix (2013-05-25)
    "https://worldathletics.org/competition/calendar-results/results/7049155?eventId=10229630",  # Eugene Prefontaine Classic (2013-05-31)
    "https://worldathletics.org/competition/calendar-results/results/7049136?eventId=10229630",  # Roma Golden Gala (2013-06-06)
    "https://worldathletics.org/competition/calendar-results/results/7049154?eventId=10229630",  # Oslo ExxonMobil Bislett Games (2013-06-13)
    "https://worldathletics.org/competition/calendar-results/results/7049140?eventId=10229630",  # Birmingham Sainsbury's Grand Prix (2013-06-30)
    "https://worldathletics.org/competition/calendar-results/results/7049139?eventId=10229630",  # Athletissima Lausanne (2013-07-04)
    "https://worldathletics.org/competition/calendar-results/results/7049153?eventId=10229630",  # Paris Meeting AREVA (2013-07-06)
    "https://worldathletics.org/competition/calendar-results/results/7049145?eventId=10229630",  # Monaco Herculis (2013-07-19)
    "https://worldathletics.org/competition/calendar-results/results/7049137?eventId=10229630",  # London Sainsbury's Anniversary Games (2013-07-26)
    "https://worldathletics.org/competition/calendar-results/results/7049138?eventId=10229630",  # Stockholm DN Galan (2013-08-22)
    "https://worldathletics.org/competition/calendar-results/results/7049156?eventId=10229630",  # Weltklasse Zürich (2013-08-28)
    "https://worldathletics.org/competition/calendar-results/results/7049141?eventId=10229630",  # Bruxelles Memorial Van Damme (2013-09-06)
    "https://worldathletics.org/competition/calendar-results/results/7065889?eventId=10229630",  # Doha IAAF Diamond League (2014-05-09)
    "https://worldathletics.org/competition/calendar-results/results/7065890?eventId=10229630",  # Shanghai Golden Grand Prix (2014-05-18)
    "https://worldathletics.org/competition/calendar-results/results/7065891?eventId=10229630",  # Eugene Prefontaine Classic (2014-05-30)
    "https://worldathletics.org/competition/calendar-results/results/7065892?eventId=10229630",  # Roma Golden Gala - Pietro Mennea (2014-06-05)
    "https://worldathletics.org/competition/calendar-results/results/7065893?eventId=10229630",  # Oslo ExxonMobil Bislett Games (2014-06-11)
    "https://worldathletics.org/competition/calendar-results/results/7065894?eventId=10229630",  # New York adidas Grand Prix (2014-06-14)
    "https://worldathletics.org/competition/calendar-results/results/7065895?eventId=10229630",  # Athletissima Lausanne (2014-07-03)
    "https://worldathletics.org/competition/calendar-results/results/7065896?eventId=10229630",  # Paris Meeting AREVA (2014-07-05)
    "https://worldathletics.org/competition/calendar-results/results/7065897?eventId=10229630",  # Glasgow British Athletics Grand Prix (2014-07-11)
    "https://worldathletics.org/competition/calendar-results/results/7065898?eventId=10229630",  # Monaco Herculis (2014-07-18)
    "https://worldathletics.org/competition/calendar-results/results/7065899?eventId=10229630",  # Stockholm DN Galan (2014-08-21)
    "https://worldathletics.org/competition/calendar-results/results/7065900?eventId=10229630",  # Birmingham British Athletics Grand Prix (2014-08-24)
    "https://worldathletics.org/competition/calendar-results/results/7065901?eventId=10229630",  # Weltklasse Zürich (2014-08-28)
    "https://worldathletics.org/competition/calendar-results/results/7065902?eventId=10229630",  # Bruxelles Memorial Van Damme (2014-09-05)
    "https://worldathletics.org/competition/calendar-results/results/7078661?eventId=10229630",  # Doha IAAF Diamond League (2015-05-15)
    "https://worldathletics.org/competition/calendar-results/results/7078665?eventId=10229630",  # Shanghai Golden Grand Prix (2015-05-17)
    "https://worldathletics.org/competition/calendar-results/results/7078660?eventId=10229630",  # Eugene Prefontaine Classic (2015-05-29)
    "https://worldathletics.org/competition/calendar-results/results/7078659?eventId=10229630",  # Roma Golden Gala - Pietro Mennea (2015-06-04)
    "https://worldathletics.org/competition/calendar-results/results/7078666?eventId=10229630",  # Birmingham British Athletics Grand Prix (2015-06-07)
    "https://worldathletics.org/competition/calendar-results/results/7078658?eventId=10229630",  # Oslo ExxonMobil Bislett Games (2015-06-11)
    "https://worldathletics.org/competition/calendar-results/results/7078657?eventId=10229630",  # New York adidas Grand Prix (2015-06-13)
    "https://worldathletics.org/competition/calendar-results/results/7078655?eventId=10229630",  # Paris Meeting AREVA (2015-07-04)
    "https://worldathletics.org/competition/calendar-results/results/7078656?eventId=10229630",  # Athletissima Lausanne (2015-07-09)
    "https://worldathletics.org/competition/calendar-results/results/7078654?eventId=10229630",  # Monaco Herculis (2015-07-17)
    "https://worldathletics.org/competition/calendar-results/results/7078662?eventId=10229630",  # London Sainsbury's Anniversary Games (2015-07-24)
    "https://worldathletics.org/competition/calendar-results/results/7078653?eventId=10229630",  # Stockholm BAUHAUS Athletics (2015-07-29)
    "https://worldathletics.org/competition/calendar-results/results/7078663?eventId=10229630",  # Weltklasse Zürich (2015-09-02)
    "https://worldathletics.org/competition/calendar-results/results/7078664?eventId=10229630",  # Bruxelles Memorial Van Damme (2015-09-11)

    # Add more here as you find them — one per meeting
]


# Diamond League URLs are discovered automatically by scraper.get_diamond_league_meeting_links()
# and don't need to be listed here manually. But if you find one that isn't
# auto-discoverable (e.g. from a year the index page doesn't expose), add it here:
MANUAL_DIAMOND_LEAGUE_URLS = [
    # e.g. "https://worldathletics.org/results/diamond-league-meetings/2022/.../men/100-metres/final/result",
]

# World Athletics Continental Tour Gold meetings (called "IAAF World Challenge"
# pre-2020) — the tier just below Diamond League. Same URL shape as
# CHAMPIONSHIP_URLS above (a direct /men/100-metres/final/result page), so
# these are scraped with scrape_race(), not scrape_hub_race(). Roughly 2016-2021
# meetings use this flat-page format; the site never generated one for most
# 2022+ meetings (see CONTINENTAL_TOUR_HUB_URLS below for those). 2017 has no
# coverage — its legacy low-numbered IDs 404 on the current site, same class of
# gap as the 1996 Atlanta Olympics note in CHAMPIONSHIP_URLS above.
CONTINENTAL_TOUR_URLS = [
    # --- 2016 ---
    "https://worldathletics.org/results/world-continental-tour-gold/2016/2016-iaaf-world-challenge-beijing-7093325/men/100-metres/final/result",  # IAAF World Challenge Beijing 2016

    # --- 2018 ---
    "https://worldathletics.org/results/world-continental-tour-gold/2018/osaka-golden-grand-prix-2018-7118677/men/100-metres/final/result",  # Osaka Golden Grand Prix 2018
    "https://worldathletics.org/results/world-continental-tour-gold/2018/golden-spike-ostrava-2018-7119787/men/100-metres/final/result",  # Golden Spike Ostrava 2018
    "https://worldathletics.org/results/world-continental-tour-gold/2018/berlin-istaf-2018-7121758/men/100-metres/final/result",  # ISTAF Berlin 2018

    # --- 2019 ---
    "https://worldathletics.org/results/world-continental-tour-gold/2019/seiko-golden-grand-prix-osaka-2019-7130738/men/100-metres/final/result",  # Seiko Golden Grand Prix (Osaka) 2019
    "https://worldathletics.org/results/world-continental-tour-gold/2019/paavo-nurmi-games-2019-7131691/men/100-metres/final/result",  # Paavo Nurmi Games 2019
    "https://worldathletics.org/results/world-continental-tour-gold/2019/golden-spike-ostrava-2019-7131694/men/100-metres/final/result",  # Golden Spike Ostrava 2019
    "https://worldathletics.org/results/world-continental-tour-gold/2019/istaf-berlin-2019-7135123/men/100-metres/final/result",  # ISTAF Berlin 2019

    # --- 2020 ---
    "https://worldathletics.org/results/world-continental-tour-gold/2020/paavo-nurmi-games-2020-6888/men/100-metres/final/result",  # Paavo Nurmi Games 2020
    "https://worldathletics.org/results/world-continental-tour-gold/2020/gyulai-istvan-memorial-2020-6891/men/100-metres/final/result",  # Gyulai Istvan Memorial 2020
    "https://worldathletics.org/results/world-continental-tour-gold/2020/seiko-golden-grand-prix-2020-tokyo-6893/men/100-metres/final/result",  # Seiko Golden Grand Prix 2020 Tokyo
    "https://worldathletics.org/results/world-continental-tour-gold/2020/70th-hanzekovic-memorial-6889/men/100-metres/final/result",  # 70th Hanzekovic Memorial 2020 (Zagreb)

    # --- 2021 ---
    "https://worldathletics.org/results/world-continental-tour-gold/2021/usatf-grand-prix-eugene-7477/men/100-metres/final/result",  # USATF Grand Prix, Eugene 2021 (NOT Prefontaine Classic)
    "https://worldathletics.org/results/world-continental-tour-gold/2021/ready-steady-tokyo-athletics-7246/men/100-metres/final/result",  # READY STEADY TOKYO - Athletics 2021
    "https://worldathletics.org/results/world-continental-tour-gold/2021/usatf-golden-games-7478/men/100-metres/final/result",  # USATF Golden Games 2021
    "https://worldathletics.org/results/world-continental-tour-gold/2021/60th-ostrava-golden-spike-7030/men/100-metres/final/result",  # 60th Ostrava Golden Spike 2021
    "https://worldathletics.org/results/world-continental-tour-gold/2021/paavo-nurmi-games-7048/men/100-metres/final/result",  # Paavo Nurmi Games 2021
    "https://worldathletics.org/results/world-continental-tour-gold/2021/memorial-borisa-hanzekovica-7059/men/100-metres/final/result",  # Memorial Borisa Hanzekovica 2021
    "https://worldathletics.org/results/world-continental-tour-gold/2021/kip-keino-classic-7040/men/100-metres/final/result",  # Kip Keino Classic 2021
]

# Hub-format Continental Tour meetings (mostly 2022-2026, plus a couple of
# 2019-2020 ones the flat page never covered) — scraped with scrape_hub_race()
# same as DIAMOND_LEAGUE_HUB_URLS, since the flat /final/result page 404s for
# these (the site only generated the JSON hub page for them).
CONTINENTAL_TOUR_HUB_URLS = [
    "https://worldathletics.org/competition/calendar-results/results/7135817?eventId=10229630",  # Kamila Skolimowska Memorial 2019 (Chorzow)
    "https://worldathletics.org/competition/calendar-results/results/7138878?eventId=10229630",  # Janusz Kusocinski Memorial 2020 (Chorzow)
    "https://worldathletics.org/competition/calendar-results/results/7144851?eventId=10229630",  # Grande Premio Brasil Caixa de Atletismo 2020
    "https://worldathletics.org/competition/calendar-results/results/7175595?eventId=10229630",  # 68th ORLEN Janusz Kusocinski Memorial 2022
    "https://worldathletics.org/competition/calendar-results/results/7189809?eventId=10229630",  # USATF NYC Grand Prix 2023
    "https://worldathletics.org/competition/calendar-results/results/7147650?eventId=10229630",  # 62nd Ostrava Golden Spike 2023
    "https://worldathletics.org/competition/calendar-results/results/7201053?eventId=10229630",  # Kip Keino Classic 2024
    "https://worldathletics.org/competition/calendar-results/results/7210334?eventId=10229630",  # Jamaica Athletics Invitational Meet 2024
    "https://worldathletics.org/competition/calendar-results/results/7205386?eventId=10229630",  # 70th ORLEN Janusz Kusocinski Memorial 2024
    "https://worldathletics.org/competition/calendar-results/results/7216820?eventId=10229630",  # Seiko Golden Grand Prix 2025 Tokyo
    "https://worldathletics.org/competition/calendar-results/results/7216821?eventId=10229630",  # Kip Keino Classic 2025
    "https://worldathletics.org/competition/calendar-results/results/7223459?eventId=10229630",  # Grande Premio Brasil de Atletismo 2025
    "https://worldathletics.org/competition/calendar-results/results/7233226?eventId=10229630",  # Kip Keino Classic 2026
    "https://worldathletics.org/competition/calendar-results/results/7230225?eventId=10229630",  # Paavo Nurmi Games 2026
    "https://worldathletics.org/competition/calendar-results/results/7231211?eventId=10229630",  # FBK Games 2026
    "https://worldathletics.org/competition/calendar-results/results/7214030?eventId=10229630",  # Gyulai Istvan Memorial 2026

    # Aug-Sep 2026, found via the calendar-results listing (competitionGroupId=3773).
    # Not listed (no elite men's 100m on the page): Monaco Athletics Festival,
    # Stumptown Twilight, Golden Sand, Tyczka na Molo, Aosta, Goteborg, Cheb,
    # Dinamo Zrinjevac, ATHLOS London, Yogibo Challenge Cup.
    "https://worldathletics.org/competition/calendar-results/results/7235002?eventId=10229630",  # IFAM Oordegem 2026
    "https://worldathletics.org/competition/calendar-results/results/7235369?eventId=10229630",  # Espoo Motonet GP 2026
    "https://worldathletics.org/competition/calendar-results/results/7235041?eventId=10229630",  # Atleticky Mitink Rieter 2026
    "https://worldathletics.org/competition/calendar-results/results/7237534?eventId=10229630",  # Felix Sanchez Classic 2026
    "https://worldathletics.org/competition/calendar-results/results/7238146?eventId=10229630",  # Silver CT Bhubaneswar 2026
    "https://worldathletics.org/competition/calendar-results/results/7235055?eventId=10229630",  # Wieslaw Maniak Memorial 2026
    "https://worldathletics.org/competition/calendar-results/results/7234838?eventId=10229630",  # GalAthletics Bellinzona 2026
    "https://worldathletics.org/competition/calendar-results/results/7234714?eventId=10229630",  # ISTAF Berlin 2026
    "https://worldathletics.org/competition/calendar-results/results/7234691?eventId=10229630",  # Grand Prix Brescia 2026
    "https://worldathletics.org/competition/calendar-results/results/7235056?eventId=10229630",  # Ludwichowski Memorial 2026
    "https://worldathletics.org/competition/calendar-results/results/7235074?eventId=10229630",  # Serbia Athletics Meeting 2026
    "https://worldathletics.org/competition/calendar-results/results/7234124?eventId=10229630",  # Oman Athletics Grand Prix 2026
    "https://worldathletics.org/competition/calendar-results/results/7234845?eventId=10229630",  # Palio Citta della Quercia 2026
    "https://worldathletics.org/competition/calendar-results/results/7245567?eventId=10229630",  # CT Challenger Pedro Galvez Velarde 2026 (Lima)
    "https://worldathletics.org/competition/calendar-results/results/7245568?eventId=10229630",  # CT Challenger Maria Letts Colmenares 2026 (Lima)
    "https://worldathletics.org/competition/calendar-results/results/7235127?eventId=10229630",  # 72nd ORLEN Janusz Kusocinski Memorial 2026
]

# National championships with pro/Olympic-level 100m fields (USATF Outdoor
# Championships, Jamaican Championships, British Athletics Championships,
# etc.). These use the generic hub-page format (any worldathletics.org
# competition, not just Diamond League), so they're scraped with
# scrape_hub_race() same as DIAMOND_LEAGUE_HUB_URLS.
#
# Found via worldathletics.org's own calendar-results search backend:
# competition/calendar-results?regionType=country&regionId={id}&competitionGroupId=3731
# (competitionGroupId 3731 = "National Senior Outdoor Championships"). Every ID
# below was independently re-verified by fetching the hub page and checking its
# embedded __NEXT_DATA__ JSON. The trailing ?eventId=10229630 (site-wide ID for
# "Men's 100 Metres") is appended because a couple of pages (both U.S. Olympic
# Trials editions) otherwise omit/misfile the event out of the primary tier.
#
# Known gaps (confirmed absent, not guessed): 2016/2017 aren't in this backend
# for USA/GB/Jamaica at all; 2020 USA/Jamaica were COVID-canceled; Canada
# 2020-2022 not found in the index.
OTHER_HUB_URLS = [
    # --- USATF Outdoor Championships / U.S. Olympic Trials (USA) ---
    "https://worldathletics.org/competition/calendar-results/results/7120163?eventId=10229630",  # Des Moines USA Championships 2018
    "https://worldathletics.org/competition/calendar-results/results/7133932?eventId=10229630",  # USA Championships 2019
    "https://worldathletics.org/competition/calendar-results/results/7163119?eventId=10229630",  # U.S. Olympic Trials 2021
    "https://worldathletics.org/competition/calendar-results/results/7183837?eventId=10229630",  # Toyota USATF Outdoor Championships 2022
    "https://worldathletics.org/competition/calendar-results/results/7201597?eventId=10229630",  # USA Championships 2023
    "https://worldathletics.org/competition/calendar-results/results/7209387?eventId=10229630",  # U.S. Olympic Team Trials 2024
    "https://worldathletics.org/competition/calendar-results/results/7222826?eventId=10229630",  # USA Championships 2025
    "https://worldathletics.org/competition/calendar-results/results/7243123?eventId=10229630",  # USA Championships 2026

    # --- British Athletics Championships / UK Championships (GB) ---
    "https://worldathletics.org/competition/calendar-results/results/7120496?eventId=10229630",  # British Championships 2018 (Birmingham)
    "https://worldathletics.org/competition/calendar-results/results/7134841?eventId=10229630",  # British Championships 2019
    "https://worldathletics.org/competition/calendar-results/results/7154252?eventId=10229630",  # British Championships 2020
    "https://worldathletics.org/competition/calendar-results/results/7168522?eventId=10229630",  # British Championships 2021
    "https://worldathletics.org/competition/calendar-results/results/7184306?eventId=10229630",  # Muller UK Athletics Championships 2022
    "https://worldathletics.org/competition/calendar-results/results/7201469?eventId=10229630",  # UK Championships 2023
    "https://worldathletics.org/competition/calendar-results/results/7213161?eventId=10229630",  # UK Championships 2024
    "https://worldathletics.org/competition/calendar-results/results/7229689?eventId=10229630",  # UK Championships 2025
    "https://worldathletics.org/competition/calendar-results/results/7243090?eventId=10229630",  # Novuna UK Athletics Championships 2026

    # --- Jamaican Championships ---
    "https://worldathletics.org/competition/calendar-results/results/7120196?eventId=10229630",  # Jamaican Championships 2018
    "https://worldathletics.org/competition/calendar-results/results/7132662?eventId=10229630",  # Jamaican Championships 2019
    "https://worldathletics.org/competition/calendar-results/results/7168599?eventId=10229630",  # Jamaican Championships 2021
    "https://worldathletics.org/competition/calendar-results/results/7186707?eventId=10229630",  # Jamaican Championships 2022
    "https://worldathletics.org/competition/calendar-results/results/7196499?eventId=10229630",  # Jamaican Championships 2023
    "https://worldathletics.org/competition/calendar-results/results/7211616?eventId=10229630",  # Jamaican Championships 2024
    "https://worldathletics.org/competition/calendar-results/results/7226886?eventId=10229630",  # Jamaican Championships 2025
    "https://worldathletics.org/competition/calendar-results/results/7239107?eventId=10229630",  # Jamaican Championships 2026

    # --- Italian Championships (bonus) ---
    "https://worldathletics.org/competition/calendar-results/results/7122096?eventId=10229630",  # Italian Championships 2018
    "https://worldathletics.org/competition/calendar-results/results/7134000?eventId=10229630",  # Italian Championships 2019
    "https://worldathletics.org/competition/calendar-results/results/7153998?eventId=10229630",  # Italian Championships 2020
    "https://worldathletics.org/competition/calendar-results/results/7168653?eventId=10229630",  # Italian Championships 2021
    "https://worldathletics.org/competition/calendar-results/results/7186733?eventId=10229630",  # Italian Championships 2022
    "https://worldathletics.org/competition/calendar-results/results/7199655?eventId=10229630",  # Italian Championships 2023
    "https://worldathletics.org/competition/calendar-results/results/7209929?eventId=10229630",  # Italian Championships 2024
    "https://worldathletics.org/competition/calendar-results/results/7226755?eventId=10229630",  # Italian Championships 2025
    "https://worldathletics.org/competition/calendar-results/results/7239956?eventId=10229630",  # Italian Championships 2026

    # --- Canadian Championships (bonus) ---
    "https://worldathletics.org/competition/calendar-results/results/7120563?eventId=10229630",  # Canadian Championships 2018
    "https://worldathletics.org/competition/calendar-results/results/7133978?eventId=10229630",  # Canadian Championships 2019
    "https://worldathletics.org/competition/calendar-results/results/7193208?eventId=10229630",  # Canadian Championships 2023
    "https://worldathletics.org/competition/calendar-results/results/7207284?eventId=10229630",  # Canadian Championships 2024
    "https://worldathletics.org/competition/calendar-results/results/7222681?eventId=10229630",  # Canadian Championships 2025
    "https://worldathletics.org/competition/calendar-results/results/7237652?eventId=10229630",  # Canadian Championships 2026

    # --- South African Championships (RSA) --- home country of Akani Simbine
    "https://worldathletics.org/competition/calendar-results/results/7164150?eventId=10229630",  # South African Championships 2021 (Pretoria)
    "https://worldathletics.org/competition/calendar-results/results/7181890?eventId=10229630",  # South African Championships 2022 (Cape Town)
    "https://worldathletics.org/competition/calendar-results/results/7194901?eventId=10229630",  # South African Championships 2023 (Potchefstroom)
    "https://worldathletics.org/competition/calendar-results/results/7207314?eventId=10229630",  # South African Championships 2024 (Pietermaritzburg)
    "https://worldathletics.org/competition/calendar-results/results/7219516?eventId=10229630",  # South African Championships 2025 (Potchefstroom)

    # --- Kenyan Championships (KEN) --- home country of Ferdinand Omanyala
    "https://worldathletics.org/competition/calendar-results/results/7194286?eventId=10229630",  # Kenyan Championships 2023 (Nairobi)
    "https://worldathletics.org/competition/calendar-results/results/7208088?eventId=10229630",  # Kenyan Championships 2024 (Nairobi)
    "https://worldathletics.org/competition/calendar-results/results/7217332?eventId=10229630",  # Kenyan Championships 2025 (Nairobi)

    # --- Botswana Championships (BOT) --- home country of Letsile Tebogo
    "https://worldathletics.org/competition/calendar-results/results/7166343?eventId=10229630",  # Botswana Championships 2021 (Gaborone)
    "https://worldathletics.org/competition/calendar-results/results/7195408?eventId=10229630",  # Botswana Championships 2023 (Gaborone)
    "https://worldathletics.org/competition/calendar-results/results/7216999?eventId=10229630",  # Botswana Championships 2025 (Gaborone)
    "https://worldathletics.org/competition/calendar-results/results/7241518?eventId=10229630",  # Botswana Championships 2026 (Gaborone)

    # --- French Championships (FRA) --- home country of Jimmy Vicaut
    "https://worldathletics.org/competition/calendar-results/results/7120754?eventId=10229630",  # French Championships 2018 (Albi)
    "https://worldathletics.org/competition/calendar-results/results/7168687?eventId=10229630",  # French Championships 2021 (Angers)
    "https://worldathletics.org/competition/calendar-results/results/7186790?eventId=10229630",  # French Championships 2022 (Caen)
    "https://worldathletics.org/competition/calendar-results/results/7199349?eventId=10229630",  # French Championships 2023 (Albi)
    "https://worldathletics.org/competition/calendar-results/results/7205979?eventId=10229630",  # French Championships 2024 (Angers)
    "https://worldathletics.org/competition/calendar-results/results/7226084?eventId=10229630",  # French Championships 2025 (Talence)
    "https://worldathletics.org/competition/calendar-results/results/7236362?eventId=10229630",  # French Championships 2026 (Albi)

    # --- Japanese Championships (JPN) --- home country of Yoshihide Kiryu / Abdul Hakim Sani Brown
    "https://worldathletics.org/competition/calendar-results/results/7120237?eventId=10229630",  # Japan Championships 2018 (Yamaguchi)
    "https://worldathletics.org/competition/calendar-results/results/7194465?eventId=10229630",  # Japanese Championships 2023 (Osaka)
    "https://worldathletics.org/competition/calendar-results/results/7224447?eventId=10229630",  # Japanese Championships 2025 (Tokyo)

    # --- 2026 major/area championships & games (Jul-Sep), via calendar-results listing ---
    "https://worldathletics.org/competition/calendar-results/results/7187518?eventId=10229630",  # Commonwealth Games 2026 (Glasgow)
    "https://worldathletics.org/competition/calendar-results/results/7192415?eventId=10229630",  # European Championships 2026 (Birmingham)
    "https://worldathletics.org/competition/calendar-results/results/7212925?eventId=10229630",  # World Athletics Ultimate Championship 2026 (Budapest)
    "https://worldathletics.org/competition/calendar-results/results/7176091?eventId=10229630",  # Asian Games 2026 (Nagoya)
    "https://worldathletics.org/competition/calendar-results/results/7233796?eventId=10229630",  # CAC Games 2026 (Santo Domingo)
    "https://worldathletics.org/competition/calendar-results/results/7233421?eventId=10229630",  # Mediterranean Games 2026 (Taranto)
    "https://worldathletics.org/competition/calendar-results/results/7246486?eventId=10229630",  # South American Games 2026 (Santa Fe)
    "https://worldathletics.org/competition/calendar-results/results/7235652?eventId=10229630",  # Central Asian Open Championships 2026 (Tashkent)
    "https://worldathletics.org/competition/calendar-results/results/7237754?eventId=10229630",  # Finnkampen 2026 (Helsinki)

    # --- other 2026 national championships (Aug-Sep) ---
    "https://worldathletics.org/competition/calendar-results/results/7243221?eventId=10229630",  # Chinese Championships 2026 (Quzhou)
    "https://worldathletics.org/competition/calendar-results/results/7244895?eventId=10229630",  # Argentinian Championships 2026 (Rosario)
    "https://worldathletics.org/competition/calendar-results/results/7246255?eventId=10229630",  # Iranian Championships 2026 (Shiraz)
    "https://worldathletics.org/competition/calendar-results/results/7245331?eventId=10229630",  # Sri Lankan Championships 2026 (Diyagama)
    "https://worldathletics.org/competition/calendar-results/results/7245433?eventId=10229630",  # Bolivian Championships 2026 (Cochabamba)
]

# Known gaps not yet found (not confirmed absent from worldathletics.org, just not
# located via search in the time budgeted): RSA 2018-2020/2026; Kenya 2018-2022/2026;
# Botswana 2018-2020/2022/2024; France 2019/2020; Japan 2019-2022/2024/2026. A
# follow-up search pass targeting these specific gap-years would likely find more.