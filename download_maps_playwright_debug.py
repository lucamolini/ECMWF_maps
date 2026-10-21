from datetime import datetime, timezone

BASE_URL = (
    "https://charts.ecmwf.int/products/efi2web_tp"
    "?area=Europe&base_time={base}&day={day}&quantile=99"
)

ADDITIONAL_LINKS = (
    "https://www.stormdom.com/",
    "https://meteoalarm.org/en/live/?t=day0&h=3,10,12,13",
    "https://meteoalarm.org/en/live/?t=day1&h=3,10,12,13",
    "https://www.estofex.org/",
)


def main() -> None:
    """Scrive su stdout i link da inserire direttamente nel corpo della mail."""
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    ecmwf_links = [
        BASE_URL.format(base=base_time, day=day)
        for day in (1, 2, 3)
    ]
    print("\n".join((*ecmwf_links, *ADDITIONAL_LINKS)))


if __name__ == "__main__":
    main()
