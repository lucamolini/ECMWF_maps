
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os, sys, re

BASE_URL = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

VT_REGEX = re.compile(
    r"VT:\s*\w{3}\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+00UTC", re.I
)

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def vt_start_from_text(text: str) -> str | None:
    """
    Cerca una stringa tipo 'VT: Sun 10 Aug 2025 00UTC ...' e restituisce YYYYMMDD
    della data di inizio VT (se trovata). Altrimenti None.
    """
    m = VT_REGEX.search(text)
    if not m:
        return None
    dd, mon, yyyy = int(m.group(1)), m.group(2).title(), int(m.group(3))
    mm = MONTHS.get(mon)
    if not mm:
        return None
    return f"{yyyy:04d}{mm:02d}{dd:02d}"

def main():
    # Data di riferimento UTC (oggi)
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y%m%d")
    base_time_for_page = today_str + "0000"
    print(f"[info] today(UTC)={today_str}, base_time param={base_time_for_page}")
    days = [1, 2, 3]

    ensure_dir("maps/map_day1.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})

        all_ok = True

        for day in days:
            expected_vt_start = (today + timedelta(days=day-1)).strftime("%Y%m%d")
            url = BASE_URL.format(base=base_time_for_page, day=day)
            out_png = f"maps/map_day{day}.png"
            out_html = f"maps/map_day{day}.html"
            out_txt = f"maps/map_day{day}.log.txt"
            ensure_dir(out_png)

            # Cattura PNG da network che contengono /streaming/YYYYMMDD-
            best = {"buf": None, "url": None, "size": 0}
            def on_response(resp):
                try:
                    ctype = (resp.headers or {}).get("content-type", "").lower()
                    u = resp.url
                    if f"/streaming/{today_str}-" in u and ("image/png" in ctype or u.lower().endswith(".png") or ".png?" in u.lower()):
                        body = resp.body()
                        size = len(body) if body else 0
                        if size >= 50_000 and size > best["size"]:
                            best.update({"buf": body, "url": u, "size": size})
                            print(f"[net] PNG candidato: {u} ({size/1024:.1f} KB)")
                except Exception as e:
                    print(f"[warn] on_response error: {e}")

            page.on("response", on_response)

            try:
                print(f"[step] Day {day}: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)

                # Testo pagina (non screenshot) per estrarre VT
                body_text = page.evaluate("document.body.innerText || ''")
                vt_start = vt_start_from_text(body_text)

                # Salva HTML e log per audit
                with open(out_html, "w", encoding="utf-8") as f:
                    f.write(page.content())
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(f"expected_vt_start={expected_vt_start}\n")
                    f.write(f"found_vt_start={vt_start}\n")
                    f.write(f"page_title={page.title()}\n")
                    f.write(f"url={url}\n")

                if not vt_start:
                    print(f"[fail] impossibile leggere VT dal testo pagina per day {day}.")
                    all_ok = False
                elif vt_start != expected_vt_start:
                    print(f"[fail] VT mismatch day {day}: atteso {expected_vt_start}, trovato {vt_start}")
                    all_ok = False
                else:
                    print(f"[ok] VT day {day} corrisponde ({vt_start}).")

                # Attendi un po' di traffico e salva PNG
                page.wait_for_timeout(7000)
                if best["buf"]:
                    with open(out_png, "wb") as f:
                        f.write(best["buf"])
                    print(f"[ok] PNG salvato: {out_png} (src={best['url']})")
                else:
                    print(f"[warn] nessun PNG catturato per day {day}.")

            except TimeoutError:
                print(f"[err] timeout caricando day {day}")
                all_ok = False
            finally:
                page.remove_listener("response", on_response)

        browser.close()

    if not all_ok:
        print("[exit] Almeno un day non ha VT corrispondente al giorno atteso. Failing (opzione A).")
        sys.exit(1)

    print("[done] Tutte le mappe hanno VT coerente con la data attesa.")
    sys.exit(0)

if __name__ == "__main__":
    main()
