from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.models.entities import BillingHistory, Subscription

SUBSCRIPTION_PLANS: dict[str, dict[str, Any]] = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_ngn": 15000,
        "interval": "monthly",
        "max_customers": 50,
        "features": ["Up to 50 customers", "Basic tracking", "Limited analytics dashboard"],
        "gates": {"inventory_writes": True, "advanced_exports": False, "multi_user": False},
    },
    "growth": {
        "id": "growth",
        "name": "Growth",
        "price_ngn": 50000,
        "interval": "monthly",
        "max_customers": None,
        "features": ["Unlimited customers", "Payment tracking", "Analytics", "Inventory system"],
        "gates": {"inventory_writes": True, "advanced_exports": False, "multi_user": False},
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_ngn": 100000,
        "interval": "monthly",
        "max_customers": None,
        "features": ["Multi-user access", "Advanced analytics", "Automated receipts", "Priority support", "Advanced exports"],
        "gates": {"inventory_writes": True, "advanced_exports": True, "multi_user": True},
    },
}

PLAN_ALIASES: dict[str, str] = {"pro": "enterprise"}


def normalize_plan_id(plan_id: str | None) -> str:
    raw = (plan_id or "starter").strip().lower()
    return PLAN_ALIASES.get(raw, raw)


def plan_max_customers(plan_id: str) -> int | None:
    nid = normalize_plan_id(plan_id)
    plan = SUBSCRIPTION_PLANS.get(nid, SUBSCRIPTION_PLANS["starter"])
    return plan.get("max_customers")


def get_plan(plan_id: str) -> dict[str, Any]:
    nid = normalize_plan_id(plan_id)
    return SUBSCRIPTION_PLANS.get(nid, SUBSCRIPTION_PLANS["starter"])


def plan_feature_gates(plan_id: str) -> dict[str, bool]:
    return dict(get_plan(plan_id).get("gates") or {})


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def next_renewal_date(from_date: datetime | None = None) -> datetime:
    base = from_date or _now()
    return base + timedelta(days=30)


def activate_plan_on_user(user, plan_id: str, *, reference: str | None = None, customer_code: str | None = None) -> None:
    nid = normalize_plan_id(plan_id)
    if nid not in SUBSCRIPTION_PLANS:
        nid = "starter"
    user.subscription_plan = nid
    user.current_plan = nid
    user.subscription_status = "active"
    user.subscription_ends_at = next_renewal_date()
    user.renewal_date = user.subscription_ends_at
    user.billing_cycle = "monthly"
    user.trial_end_date = None
    user.trial_ends_at = None
    user.trial_started_at = None
    if reference:
        user.subscription_reference = reference
    if customer_code:
        user.paystack_customer_code = customer_code
    user.subscription_grace_until = None


def sync_subscription_row(db, user) -> Subscription:
    row = db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.id.desc()).first()
    if not row:
        row = Subscription(user_id=user.id, plan_id=user.current_plan or user.subscription_plan, status=user.subscription_status)
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
    settings = get_settings()
    now = _now()
    user.subscription_status = "overdue"
    user.subscription_grace_until = now + timedelta(days=settings.BILLING_GRACE_DAYS)


def cancel_subscription(user) -> None:
    user.subscription_status = "cancelled"
    user.subscription_grace_until = None


def reactivate_subscription(user) -> None:
    user.subscription_status = "active"
    user.subscription_grace_until = None
    if not user.renewal_date or user.renewal_date < _now():
        user.renewal_date = next_renewal_date()
        user.subscription_ends_at = user.renewal_date


def add_billing_history(db, *, user_id: int, action: str, status: str, from_plan: str | None, to_plan: str | None, reference: str | None, note: str | None = None) -> BillingHistory:
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
