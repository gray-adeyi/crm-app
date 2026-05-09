from enum import StrEnum

from sqlalchemy import UUID, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class IventoryKind(StrEnum):
    RESTOCK = "RESTOCK"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"


class InventoryMovement(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "inventory_movements"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[IventoryKind] = mapped_column(ENUM(IventoryKind))
    delta_quantity: Mapped[int] = mapped_column(Integer())
    reason: Mapped[str | None] = mapped_column(String(255))
    related_order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"))

    product = relationship("Product", back_populates="movements")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"InventoryMovement(id={self.id!r})"
