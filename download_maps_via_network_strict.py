
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os, time, sys


BASE_URL = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def main():
    # base_time = giorno di esecuzione alle 00 UTC, formato yyyymmdd0000
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    print(f"[info] base_time atteso = {base_time}")
    days = [1, 2, 3]
    ensure_dir("maps/map_day1.png")

    any_saved = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})

        for day in days:
            url = BASE_URL.format(base=base_time, day=day)
            out_png = f"maps/map_day{day}.png"
            out_html = f"maps/map_day{day}.html"
            captured = {"buf": None, "url": None, "size": 0}

            def on_response(resp):
                try:
                    ctype = (resp.headers or {}).get("content-type", "").lower()
                    u = resp.url
                    # Accetta solo PNG "grandi" che contengano il base_time corretto nell'URL
                    if base_time in u and ("image/png" in ctype or u.lower().endswith(".png") or ".png?" in u.lower()):
                        body = resp.body()
                        size = len(body) if body else 0
                        if size > captured["size"] and size >= 50_000:
                            captured.update({"buf": body, "url": u, "size": size})
                            print(f"[net] PNG candidato (match base_time): {u} ({size/1024:.1f} KB)")
                    elif ("image/png" in ctype or u.lower().endswith(".png") or ".png?" in u.lower()) and base_time not in u:
                        # Logga PNG scartati perché NON contengono il base_time richiesto
                        print(f"[skip] PNG scartato (base_time diverso): {u}")
                except Exception as e:
                    print(f"[warn] on_response error: {e}")

            page.on("response", on_response)

            try:
                print(f"[step] Day {day}: goto {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                # Salva HTML per audit/debug
                with open(out_html, "w", encoding="utf-8") as f:
                    f.write(page.content())

                # Attendi attività di rete e render
                page.wait_for_timeout(7000)

                if captured["buf"]:
                    with open(out_png, "wb") as f:
                        f.write(captured["buf"])
                    print(f"[ok] PNG salvato (base_time OK): {out_png} (src={captured['url']})")
                    any_saved += 1
                else:
                    # Nessun PNG con il base_time atteso: fallisci esplicitamente e NON fare fallback a screenshot
                    print(f"[fail] Nessun PNG con base_time={base_time} trovato per day {day}.")
                    # lascia un file-diario per evidenziare l'errore
                    with open(f"maps/map_day{day}.ERR.txt", "w") as f:
                        f.write(f"PNG non trovato per base_time={base_time} (day {day}). Vedi HTML.")
            except PlaywrightTimeoutError:
                print(f"[err] Timeout nel caricamento per day {day}.")
            finally:
                page.remove_listener("response", on_response)

        browser.close()

    # Esci con errore se almeno una delle tre non è stata scaricata correttamente
    if any_saved != len(days):
        print(f"[exit] Alcune immagini non rispettano base_time={base_time}. Salvate: {any_saved}/{len(days)}")
        sys.exit(1)
    else:
        print("[done] Tutte le immagini hanno il base_time corretto.")
        sys.exit(0)

if __name__ == "__main__":
    main()
