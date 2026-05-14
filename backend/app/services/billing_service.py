from app.core.utils import aware_datetime_now
from app.models.users import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from fastapi import HTTPException

from app.core.config import settings
from app.models import BillingTransaction, Invoice, Subscription
from app.services.billing import (
    activate_plan_on_user,
    add_billing_history,
    cancel_subscription,
    get_plan,
    mark_payment_failed,
    normalize_plan_id,
    reactivate_subscription,
    sync_subscription_row,
)
from app.services.invoice_service import create_invoice
from app.services.paystack_service import (
    PaystackError,
    generate_reference,
    initialize_transaction,
    verify_transaction,
)


async def _tx_by_reference(
    db: AsyncSession, reference: str
) -> BillingTransaction | None:
    stmt = select(BillingTransaction).where(BillingTransaction.reference == reference)
    return (await db.execute(stmt)).scalar_one_or_none()


async def initialize_subscription_checkout(
    db: AsyncSession, user: User, plan_id: str
) -> BillingTransaction:
    plan = get_plan(normalize_plan_id(plan_id))

    reference = generate_reference(user.id, plan["id"])
    metadata = {
        "user_id": str(user.id),
        "plan_id": plan["id"],
        "crm_billing": True,
    }

    try:
        init_data = initialize_transaction(
            email=user.email,
            amount_ngn=plan["price_ngn"],
            reference=reference,
            metadata=metadata,
            callback_url=settings.PAYSTACK_CALLBACK_URL,
        )
    except PaystackError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    tx = BillingTransaction(
        user_id=user.id,
        plan_id=plan["id"],
        amount=plan["price_ngn"],
        currency="NGN",
        reference=reference,
        paystack_access_code=init_data.get("access_code"),
        paystack_authorization_url=init_data.get("authorization_url"),
        status="initialized",
    )
    db.add(tx)
    add_billing_history(
        db,
        user_id=user.id,
        action="SUBSCRIBE",
        status="INITIALIZED",
        from_plan=user.current_plan or user.subscription_plan,
        to_plan=plan["id"],
        reference=reference,
    )
    await db.commit()
    await db.refresh(tx)
    return tx


async def apply_successful_payment(
    db: AsyncSession,
    *,
    user: User,
    plan_id: str,
    reference: str,
    customer_code: str | None,
    paystack_transaction_id: str | None,
    paid_at: datetime | None = None,
) -> BillingTransaction:
    plan_id = normalize_plan_id(plan_id)
    tx = await _tx_by_reference(db, reference)
    if not tx:
        plan = get_plan(plan_id)
        tx = BillingTransaction(
            user_id=user.id,
            plan_id=plan["id"],
            amount=plan["price_ngn"],
            currency="NGN",
            reference=reference,
            status="success",
            paystack_transaction_id=paystack_transaction_id,
            paid_at=paid_at or datetime.utcnow(),
        )
        db.add(tx)
    else:
        tx.status = "SUCCESS"
        tx.paystack_transaction_id = (
            paystack_transaction_id or tx.paystack_transaction_id
        )
        tx.paid_at = paid_at or tx.paid_at or aware_datetime_now()

    from_plan = user.current_plan or user.subscription_plan
    activate_plan_on_user(
        user, plan_id, reference=reference, customer_code=customer_code
    )
    sub = await sync_subscription_row(db, user)
    sub.status = "ACTIVE"

    await create_invoice(
        db,
        user_id=user.id,
        transaction_id=tx.id,
        plan_id=plan_id,
        amount=tx.amount,
        reference=reference,
        paid=True,
    )
    add_billing_history(
        db,
        user_id=user.id,
        action="renew" if from_plan == plan_id else "upgrade",
        status="success",
        from_plan=from_plan,
        to_plan=plan_id,
        reference=reference,
    )
    await db.commit()
    await db.refresh(tx)
    return tx


async def verify_and_activate_subscription(
    db: AsyncSession, user: User, reference: str
) -> BillingTransaction:
    tx = await _tx_by_reference(db, reference)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Transaction does not belong to this account"
        )

    if tx.status == "SUCCESS":
        return tx

    try:
        payload = verify_transaction(reference)
    except PaystackError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    status = payload.get("status")
    plan_id = normalize_plan_id(
        (payload.get("metadata") or {}).get("plan_id") or tx.plan_id
    )
    customer_code = (payload.get("customer") or {}).get("customer_code")
    paid_at = None
    paid_at_str = payload.get("paid_at")
    if paid_at_str:
        paid_at = datetime.fromisoformat(paid_at_str.replace("Z", "+00:00")).replace(
            tzinfo=None
        )

    if status == "success":
        return await apply_successful_payment(
            db,
            user=user,
            plan_id=plan_id,
            reference=reference,
            customer_code=customer_code,
            paystack_transaction_id=str(payload.get("id") or ""),
            paid_at=paid_at,
        )

    tx.status = "FAILED" if status in {"failed", "reversed"} else "ABANDONED"
    mark_payment_failed(user)
    await sync_subscription_row(db, user)
    add_billing_history(
        db,
        user_id=user.id,
        action="payment_failed",
        status=tx.status,
        from_plan=user.current_plan or user.subscription_plan,
        to_plan=plan_id,
        reference=reference,
    )
    await db.commit()
    return tx


async def cancel_user_subscription(
    db: AsyncSession, user: User, reason: str | None = None
) -> Subscription:
    prev = user.current_plan or user.subscription_plan
    cancel_subscription(user)
    sub = await sync_subscription_row(db, user)
    sub.status = "CANCELLED"
    sub.cancelled_at = aware_datetime_now()
    add_billing_history(
        db,
        user_id=user.id,
        action="CANCEL",
        status="CANCELLED",
        from_plan=prev,
        to_plan=prev,
        reference=user.subscription_reference,
        note=reason,
    )
    await db.commit()
    return sub


async def reactivate_user_subscription(db, user) -> Subscription:
    prev = user.current_plan or user.subscription_plan
    reactivate_subscription(user)
    sub = await sync_subscription_row(db, user)
    sub.status = "ACTIVE"
    add_billing_history(
        db,
        user_id=user.id,
        action="reactivate",
        status="active",
        from_plan=prev,
        to_plan=prev,
        reference=user.subscription_reference,
    )
    await db.commit()
    return sub


async def billing_snapshot(db: AsyncSession, user: User) -> dict:
    stmt = (
        select(BillingTransaction)
        .where(BillingTransaction.user_id == user.id)
        .limit(20)
    )
    transactions = (await db.execute(stmt)).scalars().all()

    stmt = select(Invoice).where(Invoice.user_id == user.id).limit(20)
    invoices = (await db.execute(stmt)).scalars().all()
    return {"transactions": transactions, "invoices": invoices}
