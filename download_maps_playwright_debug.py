from datetime import datetime, timezone
from pathlib import Path

BASE_URL = (
    "https://charts.ecmwf.int/products/efi2web_tp"
    "?area=Europe&base_time={base}&day={day}&quantile=99"
)


ADDITIONAL_LINKS = [
    "https://www.stormdom.com/",
    "https://meteoalarm.org/en/live/?t=day0",
    "https://meteoalarm.org/en/live/?t=day1",
    "https://www.estofex.org/",
]

def main() -> None:
    """Prepara il corpo della mail, senza scrivere file."""
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    ecmwf_links = [BASE_URL.format(base=base_time, day=day) for day in (1)]
    return (
        "Link ECMWF (giorno 1):\n"
        + "\n".join(ecmwf_links)
        + "\n\nAltri link di monitoraggio meteo:\n"
        + "\n".join(ADDITIONAL_LINKS)
        + "\n"
    )


if __name__ == "__main__":
    main()
