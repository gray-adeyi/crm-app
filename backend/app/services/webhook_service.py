from app.core.utils import aware_datetime_now
import json
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BillingTransaction, PaymentEvent, User
from app.services.billing import (
    add_billing_history,
    mark_payment_failed,
    sync_subscription_row,
)
from app.services.billing_service import apply_successful_payment


async def _already_processed(
    db: AsyncSession, event_type: str, reference: str | None
) -> bool:
    if not reference:
        return False
    stmt = select(
        exists().where(
            PaymentEvent.provider == "PAYATACK",
            PaymentEvent.event_type == event_type,
            PaymentEvent.reference == reference,
            PaymentEvent.status == "PROCESSED",
        )
    )

    return (await db.execute(stmt)).scalar() or False


async def record_event(
    db: AsyncSession,
    *,
    provider: str,
    event_type: str,
    reference: str | None,
    raw_body: str,
    payload: dict,
) -> PaymentEvent:
    row = PaymentEvent(
        provider=provider,
        event_type=event_type,
        reference=reference,
        raw_body=raw_body,
        payload=json.dumps(payload),
        status="received",
    )
    db.add(row)
    await db.flush()
    return row


async def process_paystack_event(
    db: AsyncSession, payload: dict, raw_body: str
) -> PaymentEvent:
    event_type = payload.get("event") or "unknown"
    data = payload.get("data") or {}
    reference = data.get("reference")

    event_row = await record_event(
        db,
        provider="PAYATACK",
        event_type=event_type,
        reference=reference,
        raw_body=raw_body,
        payload=payload,
    )

    if await _already_processed(db, event_type, reference):
        event_row.status = "DUPLICATE"
        event_row.processed_at = aware_datetime_now()
        await db.commit()
        return event_row

    if event_type in {
        "charge.success",
        "subscription.create",
        "invoice.payment_success",
    }:
        metadata = data.get("metadata") or {}
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")
        if not user_id:
            stmt = select(BillingTransaction).where(
                BillingTransaction.reference == reference
            )
            tx = (await db.execute(stmt)).scalar_one_or_none()
            user_id = tx.user_id if tx else None
            plan_id = plan_id or (tx.plan_id if tx else None)

        if user_id and plan_id:
            stmt = select(User).where(User.id == user_id)
            user = (await db.execute(stmt)).scalar_one_or_none()
            if user:
                await apply_successful_payment(
                    db,
                    user=user,
                    plan_id=plan_id,
                    reference=reference or "",
                    customer_code=(data.get("customer") or {}).get("customer_code"),
                    paystack_transaction_id=str(data.get("id") or ""),
                )

    elif event_type in {"charge.failed", "invoice.payment_failed"}:
        tx = (
            db.query(BillingTransaction)
            .filter(BillingTransaction.reference == reference)
            .first()
        )
        if tx:
            tx.status = "failed"
            user = db.query(User).filter(User.id == tx.user_id).first()
            if user:
                mark_payment_failed(user)
                sync_subscription_row(db, user)
                add_billing_history(
                    db,
                    user_id=user.id,
                    action="payment_failed",
                    status="failed",
                    from_plan=user.current_plan or user.subscription_plan,
                    to_plan=user.current_plan or user.subscription_plan,
                    reference=reference,
                )

    elif event_type in {"subscription.disable"}:
        customer = data.get("customer") or {}
        customer_code = customer.get("customer_code")
        if customer_code:
            user = (
                db.query(User)
                .filter(User.paystack_customer_code == customer_code)
                .first()
            )
            if user:
                user.subscription_status = "cancelled"
                sync_subscription_row(db, user)
                add_billing_history(
                    db,
                    user_id=user.id,
                    action="cancel",
                    status="cancelled",
                    from_plan=user.current_plan or user.subscription_plan,
                    to_plan=user.current_plan or user.subscription_plan,
                    reference=reference,
                )

    event_row.status = "processed"
    event_row.processed_at = datetime.utcnow()
    db.commit()
    return event_row
