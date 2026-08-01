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
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7135817/result",  # Kamila Skolimowska Memorial 2019 (Chorzow)
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7138878/result",  # Janusz Kusocinski Memorial 2020 (Chorzow)
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7144851/result",  # Grande Premio Brasil Caixa de Atletismo 2020
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7175595/result",  # 68th ORLEN Janusz Kusocinski Memorial 2022
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7189809/result",  # USATF NYC Grand Prix 2023
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7147650/result",  # 62nd Ostrava Golden Spike 2023
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7201053/result",  # Kip Keino Classic 2024
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7210334/result",  # Jamaica Athletics Invitational Meet 2024
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7205386/result",  # 70th ORLEN Janusz Kusocinski Memorial 2024
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7216820/result",  # Seiko Golden Grand Prix 2025 Tokyo
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7216821/result",  # Kip Keino Classic 2025
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7223459/result",  # Grande Premio Brasil de Atletismo 2025
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7233226/result",  # Kip Keino Classic 2026
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7230225/result",  # Paavo Nurmi Games 2026
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7231211/result",  # FBK Games 2026
    "https://worldathletics.org/competitions/world-athletics-continental-tour/calendar-results/7214030/result",  # Gyulai Istvan Memorial 2026
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
]

# Known gaps not yet found (not confirmed absent from worldathletics.org, just not
# located via search in the time budgeted): RSA 2018-2020/2026; Kenya 2018-2022/2026;
# Botswana 2018-2020/2022/2024; France 2019/2020; Japan 2019-2022/2024/2026. A
# follow-up search pass targeting these specific gap-years would likely find more.