
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os, sys

# Filtra i PNG dalle response di rete accettando SOLO quelli che contengono
# "/streaming/YYYYMMDD-" (data UTC odierna) nell'URL. Ignora l'orario (-HHMM).
BASE_URL = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def main():
    today = datetime.now(timezone.utc).strftime("%Y%m%d")  # es. 20250814
    print(f"[info] data UTC per filtro streaming: {today}")
    # mantiene anche base_time nel formato 'yyyymmdd0000' per la pagina (come nell'URL che usi)
    base_time_for_page = today + "0000"

    days = [1, 2, 3]
    ensure_dir("maps/map_day1.png")

    saved = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})

        for day in days:
            url = BASE_URL.format(base=base_time_for_page, day=day)
            out_png = f"maps/map_day{day}.png"
            out_html = f"maps/map_day{day}.html"
            best = {"buf": None, "url": None, "size": 0}

            def on_response(resp):
                try:
                    ctype = (resp.headers or {}).get("content-type", "").lower()
                    u = resp.url
                    # Accetta solo PNG con path /streaming/YYYYMMDD-*
                    if f"/streaming/{today}-" in u and ("image/png" in ctype or u.lower().endswith(".png") or ".png?" in u.lower()):
                        body = resp.body()
                        size = len(body) if body else 0
                        # Scarta icone minuscole: soglia >= 50 KB
                        if size >= 50_000 and size > best["size"]:
                            best.update({"buf": body, "url": u, "size": size})
                            print(f"[net] PNG candidato: {u} ({size/1024:.1f} KB)")
                except Exception as e:
                    print(f"[warn] on_response error: {e}")

            page.on("response", on_response)

            try:
                print(f"[step] Day {day}: goto {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                # Salva HTML per audit/debug
                with open(out_html, "w", encoding="utf-8") as f:
                    f.write(page.content())
                # Attendi attività di rete/render
                page.wait_for_timeout(7000)

                if best["buf"]:
                    with open(out_png, "wb") as f:
                        f.write(best["buf"])
                    print(f"[ok] PNG salvato: {out_png} (src={best['url']})")
                    saved += 1
                else:
                    print(f"[fail] Nessun PNG /streaming/{today}-* trovato per day {day}.")
                    with open(f"maps/map_day{day}.ERR.txt", "w") as f:
                        f.write(f"PNG non trovato con filtro /streaming/{today}- per day {day}. Vedi HTML.")
            except PlaywrightTimeoutError:
                print(f"[err] Timeout nel caricamento per day {day}.")
            finally:
                page.remove_listener("response", on_response)

        browser.close()

    if saved != len(days):
        print(f"[exit] Immagini salvate {saved}/{len(days)} non tutte trovate con la data odierna.")
        sys.exit(1)
    print("[done] Tutte le immagini corrispondono alla data odierna (streaming/YYYYMMDD-).")
    sys.exit(0)

if __name__ == "__main__":
    main()
