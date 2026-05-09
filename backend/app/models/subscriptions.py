from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class SubscriptionStatuses(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TRIAL = "TRIAL"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"
    FAILED = "FAILED"


class Subscription(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "subscriptions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[SubscriptionStatuses] = mapped_column(ENUM(SubscriptionStatuses))
    billing_cycle: Mapped[str] = mapped_column(
        String(50)
    )  # TODO: Find all enum variants
    renewal_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    trial_end_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    paystack_subscription_code: Mapped[str] = mapped_column(String(20))
    paystack_customer_code: Mapped[str] = mapped_column(String(20))
    subscription_reference: Mapped[str] = mapped_column(String(64))
    cancelled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"Subscription(id={self.id!r})"
