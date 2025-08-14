from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import time

# Calcola base_time in UTC, formato yyyymmddHHMM -> alle 00:00 UTC del giorno
base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
print(f"[info] Base time: {base_time}")

days = [1, 2, 3]
urls = [
    f\"https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base_time}&day={day}&quantile=99\"
    for day in days
]

os.makedirs("maps", exist_ok=True)

def capture_with_retry(page, url, out_path, retries=3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[info] ({attempt}/{retries}) Navigo: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # attendo che il grafico sia carico – euristica: presenza di <canvas> o <svg>
            try:
                page.wait_for_selector("canvas, svg", timeout=20000)
            except PlaywrightTimeoutError:
                print("[warn] Nessun canvas/svg trovato entro il timeout, continuo comunque.")
            # extra attesa per render finale
            page.wait_for_timeout(3000)
            page.screenshot(path=out_path, full_page=True)
            print(f"[ok] Salvato: {out_path}")
            return
        except Exception as e:
            print(f"[err] Tentativo {attempt} fallito: {e}")
            if attempt == retries:
                raise
            time.sleep(2 * attempt)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    for day, url in zip(days, urls):
        out_path = f"maps/map_day{day}.png"
        capture_with_retry(page, url, out_path)
    browser.close()

print("[done] Screenshot salvati in 'maps/'.")
