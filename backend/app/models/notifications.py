from enum import StrEnum

from sqlalchemy import BOOLEAN, TEXT, UUID, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class NotificationTypes(StrEnum):
    ORDER_REMINDER = "ORDER_REMINDER"
    LOW_STOCK = "LOW_STOCK"
    SYSTEM = "SYSTEM"


class NotificationSeverities(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Notification(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "notifications"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationTypes] = mapped_column(ENUM(NotificationTypes))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(TEXT())
    severity: Mapped[NotificationSeverities] = mapped_column(
        ENUM(NotificationSeverities)
    )
    is_read: Mapped[bool] = mapped_column(BOOLEAN(), default=False)

    related_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id"))
    related_product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))

    user = relationship("User")

    def __repr__(self) -> str:
        return f"Notification(id={self.id!r})"
