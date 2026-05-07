import asyncio
import logging

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.entities import User
from app.services.email_service import send_email
from app.services.email_templates import build_vendor_welcome_email_html

logger = logging.getLogger(__name__)


def send_vendor_welcome_email(user_id: int) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            return
        url = settings.PUBLIC_APP_URL.rstrip("/") + "/"
        html = build_vendor_welcome_email_html(dashboard_url=url, user_email=user.email)
        asyncio.run(
            send_email(
                subject="Welcome to Vendora 🚀",
                to_email=user.email,
                html=html,
            )
        )
    except Exception:
        logger.exception("Welcome email failed (user_id=%s)", user_id)
    finally:
        db.close()
