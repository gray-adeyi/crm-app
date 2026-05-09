from datetime import datetime

from sqlalchemy import TEXT, TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column

from app.includes.models import BaseDBModel, TimestampedModelMixin


class PaymentEvent(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "payment_events"

    provider: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str | None] = mapped_column(String(100))
    reference: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))  # TODO: Find all possible variants
    processed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    payload: Mapped[str] = mapped_column(TEXT())
    raw_body: Mapped[str] = mapped_column(TEXT())

    def __repr__(self) -> str:
        return f"PaymentEvent(id={self.id!r})"
