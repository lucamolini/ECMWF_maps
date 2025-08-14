from datetime import datetime, timezone
import requests
import os

# Calcola base_time in UTC, formato yyyymmddHHMM
base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
print(f"Base time: {base_time}")

# Giorni da scaricare
days = [1, 2, 3]
urls = [
    f"https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base_time}&day={day}&quantile=99"
    for day in days
]

os.makedirs("maps", exist_ok=True)

for day, url in zip(days, urls):
    print(f"Scarico giorno {day}...")
    r = requests.get(url)
    r.raise_for_status()
    filepath = f"maps/map_day{day}.png"
    with open(filepath, "wb") as f:
        f.write(r.content)
    print(f"Salvato {filepath}")

print("Tutte le mappe scaricate.")
