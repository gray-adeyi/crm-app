from uuid import UUID

from sqlalchemy import TEXT, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.includes.models import BaseDBModel, TimestampedModelMixin


class UserActivityLog(TimestampedModelMixin, BaseDBModel):
    """Audit trail for user-facing CRUD actions (orders, customers, inventory, etc.)."""

    __tablename__ = "user_activity_logs"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(20))
    entity_type: Mapped[UUID] = mapped_column(Uuid())
    summary: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[str] = mapped_column(TEXT())  # TODO: use json field

    def __repr__(self) -> str:
        return f"UserActivityLog(id={self.id!r})"
