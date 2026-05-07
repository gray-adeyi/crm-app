"""SMS / WhatsApp hooks — wire Twilio, Termii, or Meta when credentials exist."""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_order_status_alert(phone: str, message: str) -> bool:
    settings = get_settings()
    if settings.TERMII_API_KEY:
        logger.info("Termii configured — would send SMS to %s", phone[:4] + "***")
        return True
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        logger.info("Twilio configured — would send SMS to %s", phone[:4] + "***")
        return True
    logger.debug("No SMS provider configured; skipping: %s", message[:80])
    return False


def send_payment_confirmation(phone: str, amount_ngn: int) -> bool:
    return send_order_status_alert(phone, f"Payment received: ₦{amount_ngn:,}")
