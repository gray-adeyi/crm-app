from enum import StrEnum
from uuid import UUID

from sqlalchemy import TEXT, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.includes.models import BaseDBModel, TimestampedModelMixin


class BillingActions(StrEnum):
    SUBSCRIBE = "SUBSCRIBE"
    UPGRADE = "UPGRADE"
    DOWNGRADE = "DOWNGRADE"
    CANCEL = "CANCEL"
    RENEW = "RENEW"
    REACTIVATE = "REACTIVATE"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class BillingHistory(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "billing_histories"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[BillingActions] = mapped_column(ENUM(BillingActions))

    from_plan: Mapped[str | None] = mapped_column(String(64))
    to_plan: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(15))  # TODO: Convert status to enum
    reference: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(TEXT())

    def __repr__(self) -> str:
        return f"BillingHistory(id={self.id!r})"
