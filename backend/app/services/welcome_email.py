import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_session_ctx
from app.models import User
from app.services.email_service import send_email
from app.services.email_templates import build_vendor_welcome_email_html

logger = logging.getLogger(__name__)


async def send_vendor_welcome_email(user_id: UUID) -> None:
    async with get_db_session_ctx() as db:
        try:
            stmt = select(User).where(User.id == user_id)
            user = (await db.execute(stmt)).scalar_one_or_none()
            if not user or not user.email:
                return
            url = settings.PUBLIC_APP_URL.rstrip("/") + "/"
            html = build_vendor_welcome_email_html(
                dashboard_url=url, user_email=user.email
            )
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
