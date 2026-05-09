from datetime import datetime

from sqlalchemy import TIMESTAMP, UUID, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.includes.models import BaseDBModel, TimestampedModelMixin


class EmailVerificationToken(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "email_verification_tokens"

    email: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    otp_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(Integer(), default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    user = relationship("User", back_populates="verification_tokens")

    def __repr__(self) -> str:
        return f"EmailVerificationToken(id={self.id!r})"
