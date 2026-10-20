from datetime import datetime, timezone
from pathlib import Path

BASE_URL = (
    "https://charts.ecmwf.int/products/efi2web_tp"
    "?area=Europe&base_time={base}&day={day}&quantile=99"
)

OUTPUT_FILE = Path("ecmwf_links.txt")

ADDITIONAL_LINKS = [
    "https://www.stormdom.com/",
    "https://meteoalarm.org/en/live/?t=day0",
    "https://meteoalarm.org/en/live/?t=day1",
    "https://www.estofex.org/",
]

def main() -> None:
    """Prepara il corpo della mail, senza scrivere file."""
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    links = [BASE_URL.format(base=base_time, day=day) for day in (1, 2, 3)]

 OUTPUT_FILE.write_text("\n".join(links) + "\n", encoding="utf-8")
    
    return (
        "Link ECMWF (giorno 1):\n"
        + "\n".join(links)
        + "\n\nAltri link di monitoraggio meteo:\n"
        + "\n".join(ADDITIONAL_LINKS)
        + "\n"
    )


if __name__ == "__main__":
    main()
