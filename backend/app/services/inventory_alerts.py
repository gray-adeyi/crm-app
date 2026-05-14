from uuid import UUID
import logging
import math
from datetime import timedelta

from sqlalchemy import select

from app.core.database import get_db_session_ctx
from app.core.utils import aware_datetime_now
from app.models import Notification, Product, User
from app.services.email_service import send_email
from app.services.email_templates import build_low_stock_email_html
from app.services.notification_prefs import is_email_enabled

logger = logging.getLogger(__name__)


def is_low_stock(product: Product) -> bool:
    remaining = int(product.quantity_in_stock or 0)
    peak = int(getattr(product, "peak_quantity", 0) or 0)
    if peak > 0:
        ten_percent_line = max(1, math.ceil(peak * 0.10))
        if remaining <= ten_percent_line:
            return True
    threshold = int(product.reorder_threshold or 0)
    if remaining <= 0:
        return True
    if threshold > 0 and remaining <= threshold:
        return True
    return threshold == 0 and remaining <= 5


def refresh_product_stock_flags(product: Product) -> None:
    qty = int(product.quantity_in_stock or 0)
    peak = int(getattr(product, "peak_quantity", 0) or 0)
    if qty > peak:
        product.peak_quantity = qty
    product.is_low_stock = bool(is_low_stock(product))


async def enqueue_low_stock_alert(product_id: UUID, user_id: UUID) -> None:
    async with get_db_session_ctx() as db:
        try:
            stmt = select(User).where(User.id == user_id)
            user = (await db.execute(stmt)).scalar_one_or_none()
            stmt = select(Product).where(
                Product.id == product_id, Product.user_id == user_id
            )
            product = (await db.execute(stmt)).scalar_one_or_none()
            if not user or not product:
                return

            if not is_low_stock(product):
                return

            # dedupe: only one low_stock notification per product per 24h
            since = aware_datetime_now() - timedelta(hours=24)
            stmt = select(Notification).where(
                Notification.user_id == user_id,
                Notification.type == "low_stock",
                Notification.related_product_id == product_id,
                Notification.created_at.isnot(None),
                Notification.created_at >= since,
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                return

            remaining = int(product.quantity_in_stock or 0)
            threshold = int(product.reorder_threshold or 0)
            db.add(
                Notification(
                    user_id=user_id,
                    type="low_stock",
                    severity="critical" if remaining <= 0 else "warning",
                    title="Low stock alert",
                    body=f"{product.name} is running low ({remaining} left)",
                    related_product_id=product_id,
                )
            )
            await db.commit()

            if not is_email_enabled(user, "low_stock"):
                return

            peak_val = int(product.peak_quantity or 0)
            restock_tip = max(
                peak_val - remaining if peak_val else 0,
                threshold * 2 if threshold else 0,
                10,
            )

            html = build_low_stock_email_html(
                business_name=user.business_name,
                product_name=product.name,
                remaining=remaining,
                threshold=threshold,
                restock_tip=restock_tip,
                peak_quantity=int(product.peak_quantity or 0),
            )
            try:
                await send_email(
                    subject="Low Stock Alert — Restock Needed",
                    to_email=user.email,
                    html=html,
                )
            except Exception:
                logger.exception(
                    "Low stock email failed (product_id=%s user_id=%s)",
                    product_id,
                    user_id,
                )
        finally:
            await db.close()
