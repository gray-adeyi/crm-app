from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseDBModel(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )


class TimestampedModelMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )
