from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class Invoice(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "invoices"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("billing_transactions.id")
    )
    invoice_number: Mapped[str] = mapped_column(String(64), index=True)
    plan_id: Mapped[str] = mapped_column(String(64))
    amount: Mapped[int] = mapped_column(Integer())
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    reference: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(15), default="ISSUED"
    )  # TODO: Find all status variants
    issued_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    user = relationship("User", back_populates="invoices")

    def __repr__(self) -> str:
        return f"Invoice(id={self.id!r})"
