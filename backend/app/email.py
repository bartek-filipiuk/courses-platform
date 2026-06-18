import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)
_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


async def send_magic_link_email(to: str, link: str) -> None:
    """Send the passwordless access link via Brevo. No-op (logged) without a key."""
    if not settings.BREVO_API_KEY:
        logger.warning("BREVO_API_KEY unset — skipping magic-link email to %s", to)
        return
    body = {
        "sender": {"email": settings.BREVO_SENDER_EMAIL, "name": "Devince"},
        "to": [{"email": to}],
        "subject": "Twój dostęp do kursu — link logowania",
        "htmlContent": (
            f"<p>Twój link do wejścia na kurs (ważny 15 minut):</p>"
            f'<p><a href="{link}">{link}</a></p>'
            f"<p>Jeśli wygaśnie — wejdź na /login i wpisz swój e-mail po nowy link.</p>"
        ),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _BREVO_URL,
            headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json"},
            json=body,
        )
    if resp.status_code >= 300:
        raise RuntimeError(f"Brevo {resp.status_code}: {resp.text}")
