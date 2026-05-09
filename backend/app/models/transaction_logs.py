from uuid import UUID

from sqlalchemy import TEXT, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.includes.models import BaseDBModel, TimestampedModelMixin


class TransactionLog(TimestampedModelMixin, BaseDBModel):
    """Higher-level ledger-style events for monthly summaries."""

    __tablename__ = "transaction_logs"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(String(255))
    paylaod_json: Mapped[str] = mapped_column(TEXT())  # TODO: Convert to JSON field

    def __repr__(self) -> str:
        return f"TransactionLog(id={self.id!r})"
