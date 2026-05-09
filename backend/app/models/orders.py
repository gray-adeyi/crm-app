from datetime import datetime
from uuid import UUID

from sqlalchemy import BOOLEAN, TEXT, TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class Order(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "orders"

    product: Mapped[str] = mapped_column(String(100))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer(), default=1)
    price: Mapped[int] = mapped_column(Integer())
    amount_paid: Mapped[int] = mapped_column(Integer(), default=0)
    balance: Mapped[int] = mapped_column(Integer(), default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # TODO: Find all the possible statuses
    delivery_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    delivery_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )  # TODO: Remove this `delivery_date` is sufficient
    delivery_notes: Mapped[str] = mapped_column(TEXT())
    delivery_address: Mapped[str] = mapped_column(TEXT())
    fulfillment_type: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # TODO: Find all the possible variants
    reminder_sent: Mapped[bool] = mapped_column(BOOLEAN(), default=False)
    reminder_status: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # TODO: Find all the possible variants
    stock_deducted: Mapped[bool] = mapped_column(BOOLEAN(), default=False)
    notes: Mapped[str] = mapped_column(TEXT())
    payment_method: Mapped[str] = mapped_column(String(20))
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    customer = relationship("Customer", back_populates="orders")
    user = relationship("User", back_populates="orders")
    product_rel = relationship("Product", back_populates="orders")

    @property
    def total_price(self) -> int:
        return int(self.price or 0)

    def __repr__(self) -> str:
        return f"Order(id={self.id!r})"
