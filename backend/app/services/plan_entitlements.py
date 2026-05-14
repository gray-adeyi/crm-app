"""
Plan limits and feature gates (trial overrides for full premium during active trial).
"""

from __future__ import annotations

from app.services.billing import (
    normalize_plan_id,
)
from app.services.billing import (
    plan_max_customers as _plan_max_customers,
)
from app.services.subscription_access import is_trial_effective_now


def trial_unlocks_entitlements(user) -> bool:
    return is_trial_effective_now(user)


def effective_max_customers(user) -> int | None:
    if trial_unlocks_entitlements(user):
        return None
    return _plan_max_customers(user.current_plan or user.subscription_plan or "starter")


def has_full_dashboard_analytics(user) -> bool:
    if trial_unlocks_entitlements(user):
        return True
    plan_id = normalize_plan_id(user.current_plan or user.subscription_plan)
    return plan_id in {"growth", "enterprise"}


def can_bulk_export(user) -> bool:
    """
    Bulk orders/customers exports (Growth+ and Enterprise, plus full trial access)."""
    if trial_unlocks_entitlements(user):
        return True
    plan_id = normalize_plan_id(user.current_plan or user.subscription_plan)
    return plan_id in {"growth", "enterprise"}
