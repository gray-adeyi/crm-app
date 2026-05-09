from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.includes.models import BaseDBModel


class VendorReportDispatch(BaseDBModel):
    """Idempotent tracking for automated report emails."""

    __tablename__ = "vendor_report_dispatches"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    report_kind: Mapped[str] = mapped_column(String(20))
    period_key: Mapped[str] = mapped_column(String(20))

    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"VendorReportDispatch(id={self.id!r})"
