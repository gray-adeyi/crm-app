from uuid import UUID
from datetime import datetime, timedelta
from typing import Literal, TypedDict, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import aware_datetime_now
from app.models import BillingHistory, Subscription
from app.models.users import User

SubscriptionPlanIds = Literal["STARTER", "GROWTH", "ENTERPRICE"]


class GatesSettings(TypedDict):
    inventory_writes: bool
    advanced_exports: bool
    multi_user: bool


class SubscriptionPlan(TypedDict):
    id: SubscriptionPlanIds
    name: str
    price_ngn: int
    interval: str
    max_customers: int
    features: list[str]
    gates: GatesSettings


SUBSCRIPTION_PLANS: dict[SubscriptionPlanIds, SubscriptionPlan] = {
    "STARTER": SubscriptionPlan(
        **{
            "id": "starter",
            "name": "Starter",
            "price_ngn": 15000,
            "interval": "MONTHLY",
            "max_customers": 50,
            "features": [
                "Up to 50 customers",
                "Basic tracking",
                "Limited analytics dashboard",
            ],
            "gates": {
                "inventory_writes": True,
                "advanced_exports": False,
                "multi_user": False,
            },
        }
    ),
    "GROWTH": SubscriptionPlan(
        **{
            "id": "GROWTH",
            "name": "Growth",
            "price_ngn": 50000,
            "interval": "MONTHLY",
            "max_customers": None,
            "features": [
                "Unlimited customers",
                "Payment tracking",
                "Analytics",
                "Inventory system",
            ],
            "gates": {
                "inventory_writes": True,
                "advanced_exports": False,
                "multi_user": False,
            },
        }
    ),
    "ENTERPRICE": SubscriptionPlan(
        **{
            "id": "ENTERPRICE",
            "name": "Enterprise",
            "price_ngn": 100000,
            "interval": "monthly",
            "max_customers": None,
            "features": [
                "Multi-user access",
                "Advanced analytics",
                "Automated receipts",
                "Priority support",
                "Advanced exports",
            ],
            "gates": {
                "inventory_writes": True,
                "advanced_exports": True,
                "multi_user": True,
            },
        }
    ),
}


PLAN_ALIASES: dict[str, SubscriptionPlanIds] = {"PRO": "ENTERPRICE"}


def normalize_plan_id(plan_id: str | None) -> SubscriptionPlanIds | None:
    raw = (plan_id or "STARTER").strip().upper()
    return PLAN_ALIASES.get(raw)


def plan_max_customers(plan_id: str) -> int | None:
    nid = normalize_plan_id(plan_id)
    plan = SUBSCRIPTION_PLANS.get(nid or "STARTER")
    plan = cast(SubscriptionPlan, plan)
    return plan.get("max_customers")


def get_plan(plan_id: str) -> SubscriptionPlan:
    nid = normalize_plan_id(plan_id)
    return cast(SubscriptionPlan, SUBSCRIPTION_PLANS.get(nid or "STARTER"))


def plan_feature_gates(plan_id: str) -> GatesSettings:
    return get_plan(plan_id).get("gates")


def next_renewal_date(from_date: datetime | None = None) -> datetime:
    base = from_date or aware_datetime_now()
    return base + timedelta(days=30)


def activate_plan_on_user(
    user,
    plan_id: str,
    *,
    reference: str | None = None,
    customer_code: str | None = None,
) -> None:
    nid = normalize_plan_id(plan_id)
    if nid not in SUBSCRIPTION_PLANS:
        nid = "STARTER"
    user.subscription_plan = nid
    user.current_plan = nid
    user.subscription_status = "ACTIVE"
    user.subscription_ends_at = next_renewal_date()
    user.renewal_date = user.subscription_ends_at
    user.billing_cycle = "MONTHLY"
    user.trial_end_date = None
    user.trial_ends_at = None
    user.trial_started_at = None
    if reference:
        user.subscription_reference = reference
    if customer_code:
        user.paystack_customer_code = customer_code
    user.subscription_grace_until = None


async def sync_subscription_row(db: AsyncSession, user: User) -> Subscription:
    stmt = select(Subscription).where(Subscription.user_id == user.id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        row = Subscription(
            user_id=user.id,
            plan_id=user.current_plan or user.subscription_plan,
            status=user.subscription_status,
        )
        db.add(row)
    row.plan_id = user.current_plan or user.subscription_plan
    row.status = user.subscription_status
    row.billing_cycle = user.billing_cycle or "monthly"
    row.renewal_date = user.renewal_date
    row.trial_end_date = user.trial_end_date
    row.paystack_customer_code = user.paystack_customer_code
    row.subscription_reference = user.subscription_reference
    return row


def mark_payment_failed(user) -> None:
    now = aware_datetime_now()
    user.subscription_status = "OVERDUE"
    user.subscription_grace_until = now + timedelta(days=settings.BILLING_GRACE_DAYS)


def cancel_subscription(user) -> None:
    user.subscription_status = "CANCELLED"
    user.subscription_grace_until = None


def reactivate_subscription(user) -> None:
    user.subscription_status = "ACTIVE"
    user.subscription_grace_until = None
    if not user.renewal_date or user.renewal_date < aware_datetime_now():
        user.renewal_date = next_renewal_date()
        user.subscription_ends_at = user.renewal_date


def add_billing_history(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str,
    status: str,
    from_plan: str | None,
    to_plan: str | None,
    reference: str | None,
    note: str | None = None,
) -> BillingHistory:
    row = BillingHistory(
        user_id=user_id,
        action=action,
        status=status,
        from_plan=from_plan,
        to_plan=to_plan,
        reference=reference,
        note=note,
    )
    db.add(row)
    return row
