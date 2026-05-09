from sqlalchemy import BOOLEAN, String, TIMESTAMP, TEXT
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.includes.models import BaseDBModel, TimestampedModelMixin


class User(TimestampedModelMixin, BaseDBModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(
        String(20), default="ADMIN"
    )  # TODO: Find all posible variants
    subscription_plan: Mapped[str] = mapped_column(
        String(20), default="STARTER"
    )  # TODO: Find all posible variants
    subscription_status: Mapped[str] = mapped_column(
        String(20), default="INACTIVE"
    )  # TODO: Find all posible variants
    subscription_ends_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    current_plan: Mapped[str] = mapped_column(
        String(20), default="STARTER"
    )  # TODO: Find all posible variants
    billing_cycle: Mapped[str] = mapped_column(
        String(20), default="MONTLY"
    )  # TODO: Find all posible variants
    renewal_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    trial_end_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    trial_started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    subscription_reference: Mapped[str | None] = mapped_column(String(64))
    paystack_customer_code: Mapped[str | None] = mapped_column(String(64))
    subscription_grace_until: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    business_name: Mapped[str | None] = mapped_column(String(100))
    business_phone: Mapped[str | None] = mapped_column(String(15))
    business_address: Mapped[str | None] = mapped_column(TEXT())
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    logo_url: Mapped[str | None] = mapped_column(String(255))
    notification_preferences: Mapped[str] = mapped_column(TEXT())

    onboarding_completed: Mapped[bool] = mapped_column(BOOLEAN(), default=False)
    email_verified: Mapped[bool] = mapped_column(BOOLEAN(), default=False)

    customers = relationship("Customer", back_populates="user")
    orders = relationship("Order", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    transactions = relationship("BillingTransaction", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user")

    @property
    def is_trial_active(self) -> bool:
        status = (self.subscription_status or "").lower()
        if status != "trial":
            return False
        end = self.trial_ends_at or self.trial_end_date
        if not end:
            return False
        return datetime.utcnow() <= end

    @property
    def needs_subscription_upgrade(self) -> bool:
        if (self.subscription_status or "").lower() == "active":
            return False
        if self.is_trial_active:
            return False
        if (
            self.subscription_grace_until
            and datetime.utcnow() <= self.subscription_grace_until
        ):
            return False
        return True

    def __repr__(self) -> str:
        return f"User(id={self.id!r})"
