"""Invia via SMTP una mail con i link ECMWF e i siti meteo aggiuntivi.

Configurazione tramite variabili d'ambiente:
  SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD,
  MAIL_FROM (default SMTP_USER), MAIL_TO (indirizzi separati da virgola),
  MAIL_SUBJECT (facoltativo).

Non viene creato alcun file.
"""

from datetime import datetime, timezone
from email.message import EmailMessage
import os
import smtplib

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


def build_email_body() -> str:
    """Prepara il corpo della mail, senza scrivere file."""
    base_time = datetime.now(timezone.utc).strftime("%Y%m%d0000")
    ecmwf_links = [BASE_URL.format(base=base_time, day=day) for day in (1, 2, 3)]
    return (
        "Link ECMWF (giorni 1, 2 e 3):\n"
        + "\n".join(ecmwf_links)
        + "\n\nAltri link di monitoraggio meteo:\n"
        + "\n".join(ADDITIONAL_LINKS)
        + "\n"
    )


def main() -> None:
    """Invia direttamente l'email; non genera file sul disco."""
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("MAIL_FROM") or user
    recipients = [addr.strip() for addr in os.getenv("MAIL_TO", "").split(",") if addr.strip()]

    if not host or not sender or not recipients:
        raise SystemExit(
            "Configurazione incompleta: imposta SMTP_HOST, MAIL_TO e "
            "SMTP_USER oppure MAIL_FROM (piu SMTP_PASSWORD se richiesta)."
        )

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = os.getenv("MAIL_SUBJECT", "Link monitoraggio meteo")
    message.set_content(build_email_body())

    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(message)

    print("Email inviata con tutti i link meteo nel corpo.")


if __name__ == "__main__":
    main()
