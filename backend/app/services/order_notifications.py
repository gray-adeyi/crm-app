import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import get_db_session_ctx
from app.models import Notification, Order, User
from app.services.email_service import send_email
from app.services.email_templates import build_order_created_email_html
from app.services.notification_prefs import is_email_enabled

logger = logging.getLogger(__name__)


async def enqueue_order_created_notifications(order_id: UUID, user_id: UUID) -> None:
    """
    Runs inside FastAPI BackgroundTasks (sync context). We create our own DB session
    and run the async mail sender via asyncio.
    """

    async with get_db_session_ctx() as db:
        try:
            stmt = select(User).where(User.id == user_id)
            user = (await db.execute(stmt)).scalar_one_or_none()
            if not user:
                return

            stmt = (
                select(Order)
                .where(Order.id == order_id, Order.user_id == user_id)
                .options(joinedload(Order.customer))
            )
            order = (await db.execute(stmt)).scalar_one_or_none()
            if not order:
                return

            customer_name = order.customer.name if order.customer else "Customer"
            fulfillment = getattr(order, "fulfillment_type", None) or "delivery"
            if fulfillment.lower() == "pickup":
                subject = "New order — pickup"
            else:
                subject = "New order — delivery"

            window_label = (
                "Pickup"
                if fulfillment.lower() == "pickup"
                else f"Delivery {_delivery_label(order)}"
            )
            db.add(
                Notification(
                    user_id=user_id,
                    type="order_reminder",
                    severity="info",
                    title="New order scheduled",
                    body=(
                        f"{customer_name} • {order.product} • "
                        f"Qty {int(order.quantity or 1)} • {window_label}"
                    ),
                    related_order_id=order.id,
                )
            )
            await db.commit()

            if not is_email_enabled(user, "order_reminders"):
                return

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
                fulfillment_type=fulfillment,
                delivery_address=getattr(order, "delivery_address", None),
                payment_label=_payment_label_from_order(order),
            )

            try:
                await send_email(subject=subject, to_email=user.email, html=html)
                order.reminder_status = "CREATED_EMAIL_SENT"
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "Order email failed (order_id=%s user_id=%s)", order_id, user_id
                )
                try:
                    order.reminder_status = "FAILED"
                    await db.commit()
                except Exception:
                    await db.rollback()
        finally:
            await db.close()


def _payment_label_from_order(order: Order) -> str:
    st = (order.status or "").lower()
    bal = int(order.balance or 0)
    if st == "PAID" or bal <= 0:
        return "Paid in full"
    if st == "PARTIAL":
        return "Partially paid"
    return "Unpaid"


def _delivery_label(order: Order) -> str:
    if not order.delivery_date and not order.delivery_time:
        return "unscheduled"
    if order.delivery_date and order.delivery_time:
        return (
            f"{order.delivery_date.isoformat()} {order.delivery_time.strftime('%H:%M')}"
        )
    if order.delivery_date:
        return order.delivery_date.isoformat()
    return order.delivery_time.strftime("%H:%M")
