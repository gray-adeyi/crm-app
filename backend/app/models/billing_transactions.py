from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class BillingTransactionStatuses(StrEnum):
    INITIALIZED = "INITIALIZED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class BillingTransaction(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "billing_transactions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[str] = mapped_column(String(64))
    amount: Mapped[int] = mapped_column(Integer())
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    reference: Mapped[str] = mapped_column(String(64), unique=True)
    paystack_access_code: Mapped[str | None] = mapped_column(String(64))
    paystack_authorization_url: Mapped[str | None] = mapped_column(String(255))
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[BillingTransactionStatuses] = mapped_column(
        ENUM(BillingTransactionStatuses)
    )
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    user = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"BillingTransaction(id={self.id!r})"
