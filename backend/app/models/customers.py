from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class Customer(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(15))
    instagram_handle: Mapped[str] = mapped_column(String(255))

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="customers")
    orders = relationship("Order", back_populates="customer")

    def __repr__(self) -> str:
        return f"Customer(id={self.id!r})"
