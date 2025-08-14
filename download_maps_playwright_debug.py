
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os, sys, time, traceback

BASE_URL = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"

def log(msg): print(msg, flush=True)

def main():
    # Calcola base_time in UTC -> yyyymmdd0000
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    log(f"[info] base_time={base_time} (UTC)")

    days = [1, 2, 3]
    urls = [BASE_URL.format(base=base_time, day=d) for d in days]

    os.makedirs("maps", exist_ok=True)

    ok = 0
    with sync_playwright() as p:
        # headless è True di default
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        # Abilita log console della pagina (utile per debug)
        page.on("console", lambda m: log(f"[page.console] {m.type.upper()}: {m.text}"))
        for day, url in zip(days, urls):
            out_path = f"maps/map_day{day}.png"
            html_dump = f"maps/map_day{day}.html"
            try:
                log(f"[step] Day {day}: goto {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                # Salva HTML per debug (anche quando va bene aiuta)
                with open(html_dump, "w", encoding="utf-8") as f:
                    f.write(page.content())
                # Attendi elementi grafici
                try:
                    page.wait_for_selector("canvas, svg", timeout=40_000)
                except PlaywrightTimeoutError:
                    log("[warn] canvas/svg non trovati entro 40s; continuo e provo screenshot comunque.")
                # piccola attesa per render finale
                page.wait_for_timeout(3000)
                page.screenshot(path=out_path, full_page=True)
                log(f"[ok] salvato {out_path}")
                ok += 1
            except Exception as e:
                log(f"[err] day {day} failed: {e}")
                traceback.print_exc()
            finally:
                # Sempre prova a salvare uno screenshot "di emergenza"
                if not os.path.exists(out_path):
                    try:
                        page.screenshot(path=out_path, full_page=True)
                        log(f"[info] screenshot di emergenza salvato in {out_path}")
                    except Exception as _:
                        pass
        browser.close()

    # Exit code: 0 se almeno 1 screenshot è riuscito, 1 altrimenti
    if ok == 0:
        log("[fail] nessuno screenshot riuscito. Esco con codice 1.")
        sys.exit(1)
    else:
        log(f"[done] screenshot riusciti: {ok}/3")
        sys.exit(0)

if __name__ == "__main__":
    main()
