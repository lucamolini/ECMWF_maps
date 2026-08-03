from datetime import datetime, timezone
from pathlib import Path

BASE_URL = (
    "https://charts.ecmwf.int/products/efi2web_tp"
    "?area=Europe&base_time={base}&day={day}&quantile=99"
)
OUTPUT_FILE = Path("ecmwf_links.txt")


def main() -> None:
    """Genera i link ECMWF per i giorni 1, 2 e 3."""
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    links = [BASE_URL.format(base=base_time, day=day) for day in (1, 2, 3)]

    OUTPUT_FILE.write_text("\n".join(links) + "\n", encoding="utf-8")

    print(f"base_time={base_time}")
    print(f"Creato {OUTPUT_FILE} con i tre link ECMWF:")
    print("\n".join(links))


if __name__ == "__main__":
    main()
