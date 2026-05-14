from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AsyncDBSession, CurrentUser
from app.models import BillingTransaction, User
from app.schemas.billing import (
    BillingMeResponse,
    CancelSubscriptionRequest,
    SubscribeInitializeRequest,
    SubscribeInitializeResponse,
    VerifyTransactionRequest,
)
from app.services.billing import SUBSCRIPTION_PLANS, normalize_plan_id
from app.services.billing_service import (
    billing_snapshot,
    cancel_user_subscription,
    initialize_subscription_checkout,
    reactivate_user_subscription,
    verify_and_activate_subscription,
)
from app.services.plan_entitlements import (
    effective_max_customers,
    trial_unlocks_entitlements,
)

router = APIRouter(tags=["billing"])


def _billing_me_response(user: User) -> BillingMeResponse:
    effective = normalize_plan_id(
        user.current_plan or user.subscription_plan or "STARTER"
    )
    mc = effective_max_customers(user)
    limits = {
        "max_customers": mc,
        "trial_all_features": trial_unlocks_entitlements(user),
    }
    return BillingMeResponse(
        plan_id=effective or "STARTER",
        status=user.subscription_status or "inactive",
        billing_cycle=user.billing_cycle or "monthly",
        renewal_date=user.renewal_date or user.subscription_ends_at,
        trial_end_date=user.trial_end_date,
        grace_until=user.subscription_grace_until,
        paystack_customer_code=user.paystack_customer_code,
        limits=limits,
        transactions=[],
        invoices=[],
    )


@router.get("/billing/plans")
def list_plans():
    return {"plans": list(SUBSCRIPTION_PLANS.values())}


@router.get("/billing/me", response_model=BillingMeResponse)
async def billing_me(user: CurrentUser, db: AsyncDBSession):
    base = _billing_me_response(user)
    snap = await billing_snapshot(db, user)
    base.transactions = [
        {
            "reference": t.reference,
            "plan_id": t.plan_id,
            "amount": t.amount,
            "currency": t.currency,
            "status": t.status,
            "paid_at": t.paid_at,
            "created_at": t.created_at,
        }
        for t in snap["transactions"]
    ]
    base.invoices = [
        {
            "invoice_number": i.invoice_number,
            "plan_id": i.plan_id,
            "amount": i.amount,
            "currency": i.currency,
            "status": i.status,
            "issued_at": i.issued_at,
            "reference": i.reference,
        }
        for i in snap["invoices"]
    ]
    return base


@router.post(
    "/billing/subscribe/initialize", response_model=SubscribeInitializeResponse
)
async def subscribe_initialize(
    body: SubscribeInitializeRequest, db: AsyncDBSession, user: CurrentUser
):
    plan_id = normalize_plan_id(body.plan_id.strip())
    if plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    tx = await initialize_subscription_checkout(db, user, plan_id)
    return SubscribeInitializeResponse(
        authorization_url=tx.paystack_authorization_url or "",
        access_code=tx.paystack_access_code or "",
        reference=tx.reference,
    )


@router.post("/billing/subscribe/verify", response_model=BillingMeResponse)
async def subscribe_verify(
    body: VerifyTransactionRequest, db: AsyncDBSession, user: CurrentUser
):
    await verify_and_activate_subscription(db, user, body.reference.strip())
    await db.refresh(user)
    return billing_me(user, db)


@router.post("/billing/cancel", response_model=BillingMeResponse)
async def cancel_billing(
    body: CancelSubscriptionRequest, db: AsyncDBSession, user: CurrentUser
):
    await cancel_user_subscription(db, user, body.reason)
    await db.refresh(user)
    return billing_me(user, db)


@router.post("/billing/reactivate", response_model=BillingMeResponse)
async def reactivate_billing(db: AsyncDBSession, user: CurrentUser):
    await reactivate_user_subscription(db, user)
    await db.refresh(user)
    return billing_me(user, db)


@router.get("/billing/transactions")
async def billing_transactions(db: AsyncDBSession, user: CurrentUser):
    stmt = select(BillingTransaction).where(BillingTransaction.user_id == user.id)
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "reference": r.reference,
                "plan_id": r.plan_id,
                "amount": r.amount,
                "currency": r.currency,
                "status": r.status,
                "paid_at": r.paid_at,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }
