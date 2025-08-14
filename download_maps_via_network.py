
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os, time

# Salva come maps/map_day{n}.png l'immagine PNG catturata dai network requests della pagina.
# Se non si trova alcun PNG, fa fallback ad uno screenshot full-page.

BASE_URL = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def main():
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    print(f"[info] base_time={base_time}")
    days = [1, 2, 3]
    ensure_dir("maps/map_day1.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        for day in days:
            url = BASE_URL.format(base=base_time, day=day)
            out_png = f"maps/map_day{day}.png"
            out_html = f"maps/map_day{day}.html"
            found_png = False
            print(f"[step] Navigo: {url}")

            # intercetta tutte le response e salva la prima PNG 'grande' che troviamo
            captured = {"buf": None, "url": None, "ctype": None, "size": 0}

            def on_response(resp):
                try:
                    ctype = (resp.headers or {}).get("content-type", "").lower()
                    url_l = resp.url.lower()
                    if "image/png" in ctype or url_l.endswith(".png") or ".png?" in url_l:
                        # escludi pixel/icone minuscole: usa soglia 50 KB
                        body = resp.body()
                        size = len(body) if body else 0
                        if size > captured["size"] and size >= 50_000:
                            captured.update({"buf": body, "url": resp.url, "ctype": ctype, "size": size})
                            print(f"[net] PNG candidato: {resp.url} ({size/1024:.1f} KB)")
                except Exception as e:
                    print(f"[warn] on_response error: {e}")

            page.on("response", on_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                # salva HTML per debug
                with open(out_html, "w", encoding="utf-8") as f:
                    f.write(page.content())

                # attendi attività di rete e render
                page.wait_for_timeout(6000)

                if captured["buf"]:
                    with open(out_png, "wb") as f:
                        f.write(captured["buf"])
                    print(f"[ok] PNG salvato da network: {out_png} (src={captured['url']})")
                    found_png = True
                else:
                    print("[warn] Nessun PNG trovato tra le risposte di rete; faccio fallback a screenshot.")
                    page.screenshot(path=out_png, full_page=True)
                    print(f"[ok] Screenshot salvato: {out_png}")

            except PlaywrightTimeoutError:
                print("[err] Timeout nel caricamento pagina, salvo screenshot di emergenza.")
                page.screenshot(path=out_png, full_page=True)
            except Exception as e:
                print(f"[err] Errore durante l'elaborazione del day {day}: {e}")
                # tenta almeno uno screenshot
                try:
                    page.screenshot(path=out_png, full_page=True)
                except Exception:
                    pass

            # rimuovi listener per il prossimo ciclo
            page.remove_listener("response", on_response)

        browser.close()
    print("[done] Completato. Controlla la cartella 'maps/'.")

if __name__ == "__main__":
    main()
