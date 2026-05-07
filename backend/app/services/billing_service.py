from datetime import datetime

from fastapi import HTTPException

from app.core.config import get_settings
from app.models.entities import BillingTransaction, Invoice, Subscription
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
from app.services.paystack_service import PaystackError, generate_reference, initialize_transaction, verify_transaction


def _tx_by_reference(db, reference: str) -> BillingTransaction | None:
    return db.query(BillingTransaction).filter(BillingTransaction.reference == reference).first()


def initialize_subscription_checkout(db, user, plan_id: str) -> BillingTransaction:
    plan = get_plan(normalize_plan_id(plan_id))
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan selected")

    reference = generate_reference(user.id, plan["id"])
    settings = get_settings()
    metadata = {
        "user_id": user.id,
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
        action="subscribe",
        status="initialized",
        from_plan=user.current_plan or user.subscription_plan,
        to_plan=plan["id"],
        reference=reference,
    )
    db.commit()
    db.refresh(tx)
    return tx


def apply_successful_payment(db, *, user, plan_id: str, reference: str, customer_code: str | None, paystack_transaction_id: str | None, paid_at: datetime | None = None) -> BillingTransaction:
    plan_id = normalize_plan_id(plan_id)
    tx = _tx_by_reference(db, reference)
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
        tx.status = "success"
        tx.paystack_transaction_id = paystack_transaction_id or tx.paystack_transaction_id
        tx.paid_at = paid_at or tx.paid_at or datetime.utcnow()

    from_plan = user.current_plan or user.subscription_plan
    activate_plan_on_user(user, plan_id, reference=reference, customer_code=customer_code)
    sub = sync_subscription_row(db, user)
    sub.status = "active"

    create_invoice(
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
    db.commit()
    db.refresh(tx)
    return tx


def verify_and_activate_subscription(db, user, reference: str) -> BillingTransaction:
    tx = _tx_by_reference(db, reference)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.user_id != user.id:
        raise HTTPException(status_code=403, detail="Transaction does not belong to this account")

    if tx.status == "success":
        return tx

    try:
        payload = verify_transaction(reference)
    except PaystackError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    status = payload.get("status")
    plan_id = normalize_plan_id((payload.get("metadata") or {}).get("plan_id") or tx.plan_id)
    customer_code = (payload.get("customer") or {}).get("customer_code")
    paid_at = None
    paid_at_str = payload.get("paid_at")
    if paid_at_str:
        paid_at = datetime.fromisoformat(paid_at_str.replace("Z", "+00:00")).replace(tzinfo=None)

    if status == "success":
        return apply_successful_payment(
            db,
            user=user,
            plan_id=plan_id,
            reference=reference,
            customer_code=customer_code,
            paystack_transaction_id=str(payload.get("id") or ""),
            paid_at=paid_at,
        )

    tx.status = "failed" if status in {"failed", "reversed"} else "abandoned"
    mark_payment_failed(user)
    sync_subscription_row(db, user)
    add_billing_history(
        db,
        user_id=user.id,
        action="payment_failed",
        status=tx.status,
        from_plan=user.current_plan or user.subscription_plan,
        to_plan=plan_id,
        reference=reference,
    )
    db.commit()
    return tx


def cancel_user_subscription(db, user, reason: str | None = None) -> Subscription:
    prev = user.current_plan or user.subscription_plan
    cancel_subscription(user)
    sub = sync_subscription_row(db, user)
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    add_billing_history(
        db,
        user_id=user.id,
        action="cancel",
        status="cancelled",
        from_plan=prev,
        to_plan=prev,
        reference=user.subscription_reference,
        note=reason,
    )
    db.commit()
    return sub


def reactivate_user_subscription(db, user) -> Subscription:
    prev = user.current_plan or user.subscription_plan
    reactivate_subscription(user)
    sub = sync_subscription_row(db, user)
    sub.status = "active"
    add_billing_history(
        db,
        user_id=user.id,
        action="reactivate",
        status="active",
        from_plan=prev,
        to_plan=prev,
        reference=user.subscription_reference,
    )
    db.commit()
    return sub


def billing_snapshot(db, user) -> dict:
    transactions = (
        db.query(BillingTransaction)
        .filter(BillingTransaction.user_id == user.id)
        .order_by(BillingTransaction.id.desc())
        .limit(20)
        .all()
    )
    invoices = (
        db.query(Invoice)
        .filter(Invoice.user_id == user.id)
        .order_by(Invoice.id.desc())
        .limit(20)
        .all()
    )
    return {"transactions": transactions, "invoices": invoices}
