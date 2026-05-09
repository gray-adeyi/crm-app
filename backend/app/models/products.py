from uuid import UUID

from sqlalchemy import BOOLEAN, TEXT, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class Product(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(100))
    sku: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(TEXT())
    unit_price: Mapped[int] = mapped_column(Integer(), default=0)
    quantity_in_stock: Mapped[int] = mapped_column(Integer(), default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer(), default=0)
    peak_quantity: Mapped[int] = mapped_column(Integer(), default=0)
    is_low_stock: Mapped[bool] = mapped_column(BOOLEAN(), default=False)
    image: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User")
    orders = relationship("Order", back_populates="product_rel")
    movements = relationship("InventoryMovement", back_populates="product")

    def __repr__(self) -> str:
        return f"Product(id={self.id!r})"
