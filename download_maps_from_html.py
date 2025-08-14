\
from datetime import datetime, timezone
import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse

BASE_PAGE = "https://charts.ecmwf.int/products/efi2web_tp?area=Europe&base_time={base}&day={day}&quantile=99"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Referer": "https://charts.ecmwf.int/",
    "Connection": "close",
}

IMG_PATTERNS = [
    re.compile(r'https?://[^\s"\']+?\.png(?:\?[^\s"\']*)?', re.I),
    # spesso le immagini possono essere in JSON inline tipo "src":"...png"
    re.compile(r'"src"\s*:\s*"([^"]+?\.png(?:\?[^"]*)?)"', re.I),
]

def find_first_png(html: str, base_url: str) -> str | None:
    # prova varie regex
    for pat in IMG_PATTERNS:
        m = pat.search(html)
        if not m:
            continue
        url = m.group(1) if m.groups() else m.group(0)
        # completa le relative
        if not url.startswith("http"):
            url = urljoin(base_url, url)
        return url
    return None

def is_image_response(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return "image/png" in ctype or resp.content[:8].startswith(b"\x89PNG\r\n\x1a\n")

def download_png(img_url: str, out_path: str, max_redirects: int = 3) -> None:
    session = requests.Session()
    session.headers.update(HEADERS)
    # alcuni server richiedono referer corretto
    parsed = urlparse(img_url)
    session.headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
    # follow con timeout
    r = session.get(img_url, timeout=60, allow_redirects=True)
    r.raise_for_status()
    if not is_image_response(r):
        raise RuntimeError(f"Not a PNG (content-type={r.headers.get('Content-Type')}) from {img_url}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r.content)

def main():
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    print(f"[info] base_time={base_time}")
    days = [1, 2, 3]
    ok = 0
    for day in days:
        page_url = BASE_PAGE.format(base=base_time, day=day)
        print(f"[step] GET page: {page_url}")
        resp = requests.get(page_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        html = resp.text
        # salva html per debug (artifact)
        os.makedirs("maps", exist_ok=True)
        with open(f"maps/map_day{day}.html", "w", encoding="utf-8") as f:
            f.write(html)
        img_url = find_first_png(html, page_url)
        if not img_url:
            print(f"[warn] Nessun URL .png trovato nell'HTML per day {day}")
            continue
        print(f"[info] PNG trovato: {img_url}")
        out_path = f"maps/map_day{day}.png"
        try:
            download_png(img_url, out_path)
            print(f"[ok] Salvato {out_path}")
            ok += 1
        except Exception as e:
            print(f"[err] Download PNG fallito (day {day}): {e}")
    if ok == 0:
        # fallo fallire per far emergere l'errore nei logs della action
        raise SystemExit(1)
    print(f"[done] PNG scaricati: {ok}/{len(days)}")

if __name__ == "__main__":
    main()
