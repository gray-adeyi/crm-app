import logging
from datetime import datetime, timedelta
from datetime import time as dt_time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import get_db_session_ctx
from app.core.utils import aware_datetime_now
from app.models import Notification, Order, User
from app.services.email_service import send_email
from app.services.email_templates import build_order_created_email_html
from app.services.monthly_vendor_jobs import enqueue_monthly_vendor_jobs
from app.services.notification_prefs import is_email_enabled

logger = logging.getLogger(__name__)


def start_reminder_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(
        _run_delivery_reminders,
        "interval",
        minutes=5,
        id="delivery-reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        enqueue_monthly_vendor_jobs,
        "cron",
        day=1,
        hour=8,
        minute=10,
        id="monthly-vendor-reports",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Reminder scheduler started")
    return scheduler


def _delivery_dt(order: Order) -> datetime | None:
    if not order.delivery_date:
        return None
    t = order.delivery_time or dt_time(9, 0)
    return datetime.combine(order.delivery_date, t)


def _parse_tokens(status: str | None) -> set[str]:
    if not status or status == "pending":
        return set()
    return {t.strip() for t in status.split("|") if t.strip()}


def _format_tokens(tokens: set[str]) -> str:
    return "|".join(sorted(tokens)) if tokens else "pending"


async def _run_delivery_reminders() -> None:
    async with get_db_session_ctx() as db:
        try:
            now = aware_datetime_now()
            stmt = (
                select(Order)
                .where(Order.delivery_date.isnot(None), Order.status != "delivered")
                .options(joinedload(Order.customer))
                .order_by(Order.id.asc())
            )
            rows: list[Order] = (await db.execute(stmt)).scalar_all()
            for order in rows:
                ft = getattr(order, "fulfillment_type", None) or "delivery"
                if str(ft).lower() != "delivery":
                    continue

                dt = _delivery_dt(order)
                if not dt:
                    continue

                # only remind for upcoming/overdue within a sane window
                if dt < now - timedelta(days=7):
                    continue

                tokens = _parse_tokens(order.reminder_status)
                delta = dt - now

                secs = delta.total_seconds()
                should_24h = "24h" not in tokens and (22 * 3600) <= secs <= (26 * 3600)
                same_day = (
                    "same_day" not in tokens
                    and order.delivery_date == now.date()
                    and now < dt
                    and 6 <= now.hour <= 11
                )
                overdue = (
                    now > dt
                    and (now - dt) <= timedelta(days=2)
                    and "overdue" not in tokens
                )

                tag = None
                if should_24h:
                    tag = "24h"
                elif same_day:
                    tag = "same_day"
                elif overdue:
                    tag = "overdue"

                if not tag:
                    continue

                user = db.query(User).filter(User.id == order.user_id).first()
                if not user or not user.email:
                    continue
                if not is_email_enabled(user, "order_reminders"):
                    continue

                customer_name = order.customer.name if order.customer else "Customer"
                if tag == "24h":
                    subject = "Delivery reminder — 24 hours"
                    headline = "Delivery reminder — arriving in ~24 hours"
                elif tag == "same_day":
                    subject = "Delivery reminder — today"
                    headline = "Delivery reminder — scheduled today"
                else:
                    subject = "Delivery follow-up — overdue"
                    headline = "Delivery reminder — overdue"

                html = build_order_created_email_html(
                    business_name=user.business_name,
                    customer_name=customer_name,
                    product_name=order.product,
                    quantity=int(order.quantity or 1),
                    amount_paid=int(order.amount_paid or 0),
                    balance=int(order.balance or 0),
                    delivery_date=order.delivery_date,
                    delivery_time=order.delivery_time,
                    order_status=order.status,
                    fulfillment_type="delivery",
                    delivery_address=getattr(order, "delivery_address", None),
                    payment_label=(
                        "Paid in full"
                        if str(order.status or "").lower() in {"paid"}
                        else (
                            "Partially paid"
                            if str(order.status or "").lower() == "partial"
                            else "Unpaid"
                        )
                    ),
                    headline=headline,
                )

                try:
                    await send_email(subject=subject, to_email=user.email, html=html)
                except Exception:
                    logger.exception(
                        "Failed reminder send (order_id=%s tag=%s)", order.id, tag
                    )
                    continue

                tokens.add(tag)
                order.reminder_sent = True
                order.reminder_status = _format_tokens(tokens)

                db.add(
                    Notification(
                        user_id=user.id,
                        type="order_reminder",
                        severity="warning"
                        if tag in {"same_day", "overdue"}
                        else "info",
                        title=(
                            "Delivery overdue"
                            if tag == "overdue"
                            else "Upcoming delivery reminder"
                        ),
                        body=f"{customer_name} • {order.product} • {tag} reminder",
                        related_order_id=order.id,
                    )
                )
                await db.commit()
        finally:
            await db.close()
