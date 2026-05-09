"""Trial + paid subscription guards for SaaS route protection."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


def utc_now_naive() -> datetime:
    return datetime.utcnow()


def effective_trial_end(user) -> datetime | None:
    return getattr(user, "trial_ends_at", None) or getattr(user, "trial_end_date", None)


def is_trial_effective_now(user, *, now: datetime | None = None) -> bool:
    if (user.subscription_status or "").lower() != "trial":
        return False
    end = effective_trial_end(user)
    if not end:
        return False
    ref = now or utc_now_naive()
    return ref <= end


def is_subscription_active_now(user, *, now: datetime | None = None) -> bool:
    return (user.subscription_status or "").lower() == "active"


def finalize_expired_trial(db, user) -> bool:
    """
    Mutates user row if trial just expired.
    Returns True if state changed (caller should commit if needed).
    """
    ref = utc_now_naive()
    status_s = (user.subscription_status or "").lower()
    if status_s != "trial":
        return False
    end = effective_trial_end(user)
    if end and ref > end:
        user.subscription_status = "trial_expired"
        return True
    return False


async def ensure_saas_access(db: AsyncSession, user: User) -> None:
    """
    Raises HTTPException when the tenant should not reach premium app surfaces.
    Allows: active subscriptions, active trials, and explicit billing grace periods.
    """
    changed = finalize_expired_trial(db, user)
    if changed:
        await db.commit()
        await db.refresh(user)

    ref = utc_now_naive()
    raw_status = (user.subscription_status or "inactive").lower()

    grace = user.subscription_grace_until
    if grace and ref <= grace:
        return

    if raw_status == "active":
        return

    if raw_status == "trial":
        end = effective_trial_end(user)
        if end and ref <= end:
            return

    detail = {
        "code": "SUBSCRIPTION_REQUIRED",
        "message": "Choose a subscription plan to continue using Vendora.",
    }
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
