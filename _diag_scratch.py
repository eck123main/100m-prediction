import sys
sys.path.insert(0, r"D:\athleticsprediction")
from io import StringIO
import pandas as pd
from scraper import fetch, _drop_non_sprint_marks, clean_mark, _check_plausible_sprint_times

url = "https://worldathletics.org/results/world-continental-tour-gold/2020/paavo-nurmi-games-2020-6888/men/100-metres/final/result"

resp = fetch(url)
tables = pd.read_html(StringIO(resp.text))
print(f"Found {len(tables)} tables on the page\n")
for i, t in enumerate(tables):
    print(f"--- table {i}: shape={t.shape} columns={list(t.columns)}")
    if len(t) <= 15:
        print(t.to_string())
    print()

picked = max(tables, key=len)
print("\n=== PICKED (max by len) ===")
print(f"shape={picked.shape}")
print(picked.to_string())
