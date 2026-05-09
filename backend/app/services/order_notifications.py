import logging

from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models import Notification, Order, User
from app.services.email_service import send_email
from app.services.email_templates import build_order_created_email_html
from app.services.notification_prefs import is_email_enabled

logger = logging.getLogger(__name__)


def enqueue_order_created_notifications(order_id: int, user_id: int) -> None:
    """
    Runs inside FastAPI BackgroundTasks (sync context). We create our own DB session
    and run the async mail sender via asyncio.
    """
    import asyncio

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        order = (
            db.query(Order)
            .options(joinedload(Order.customer))
            .filter(Order.id == order_id, Order.user_id == user_id)
            .first()
        )
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
                body=f"{customer_name} • {order.product} • Qty {int(order.quantity or 1)} • {window_label}",
                related_order_id=order.id,
            )
        )
        db.commit()

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
            asyncio.run(send_email(subject=subject, to_email=user.email, html=html))
            order.reminder_status = "created_email_sent"
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "Order email failed (order_id=%s user_id=%s)", order_id, user_id
            )
            try:
                order.reminder_status = "failed"
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()


def _payment_label_from_order(order: Order) -> str:
    st = (order.status or "").lower()
    bal = int(order.balance or 0)
    if st == "paid" or bal <= 0:
        return "Paid in full"
    if st == "partial":
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
