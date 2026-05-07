from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    role = Column(String, default="admin", nullable=False)
    subscription_plan = Column(String, default="starter", nullable=False)
    subscription_status = Column(String, default="inactive", nullable=False)
    subscription_ends_at = Column(DateTime, nullable=True)
    current_plan = Column(String, default="starter", nullable=False)
    billing_cycle = Column(String, default="monthly", nullable=False)
    renewal_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    trial_started_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_reference = Column(String, nullable=True)
    paystack_customer_code = Column(String, nullable=True)
    subscription_grace_until = Column(DateTime, nullable=True)

    business_name = Column(String, nullable=True)
    business_phone = Column(String, nullable=True)
    business_address = Column(Text, nullable=True)
    currency = Column(String, default="NGN", nullable=False)
    logo_url = Column(String, nullable=True)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    notification_preferences = Column(Text, nullable=True)

    email_verified = Column(Boolean, default=False, nullable=False)

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
        if self.subscription_grace_until and datetime.utcnow() <= self.subscription_grace_until:
            return False
        return True


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    instagram_handle = Column(String)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="customers")
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    product = Column(String)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Integer)

    amount_paid = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    status = Column(String, default="pending")

    delivery_date = Column(Date, nullable=True)
    delivery_time = Column(Time, nullable=True)
    delivery_notes = Column(Text, nullable=True)
    delivery_address = Column(Text, nullable=True)
    fulfillment_type = Column(String, default="delivery", nullable=False)
    reminder_sent = Column(Boolean, default=False, nullable=False)
    reminder_status = Column(String, default="pending", nullable=False)

    stock_deducted = Column(Boolean, default=False, nullable=False)

    notes = Column(Text, nullable=True)
    payment_method = Column(String, nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    customer = relationship("Customer", back_populates="orders")
    user = relationship("User", back_populates="orders")
    product_rel = relationship("Product", back_populates="orders")

    @property
    def total_price(self) -> int:
        return int(self.price or 0)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    unit_price = Column(Integer, default=0, nullable=False)
    quantity_in_stock = Column(Integer, default=0, nullable=False)
    reorder_threshold = Column(Integer, default=0, nullable=False)
    peak_quantity = Column(Integer, default=0, nullable=False)
    is_low_stock = Column(Boolean, default=False, nullable=False)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    user = relationship("User")
    orders = relationship("Order", back_populates="product_rel")
    movements = relationship("InventoryMovement", back_populates="product")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # restock|sale|adjustment
    delta_quantity = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    product = relationship("Product", back_populates="movements")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    type = Column(String, nullable=False)  # order_reminder|low_stock|system
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    severity = Column(String, default="info", nullable=False)  # info|warning|critical
    is_read = Column(Boolean, default=False, nullable=False)

    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    related_product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    user = relationship("User")

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    user = relationship("User", back_populates="verification_tokens")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    event_type = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    status = Column(String, default="received", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    payload = Column(Text, nullable=True)
    raw_body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, nullable=False)
    status = Column(String, default="inactive", nullable=False)  # active|inactive|trial|cancelled|overdue|failed
    billing_cycle = Column(String, default="monthly", nullable=False)
    renewal_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    paystack_subscription_code = Column(String, nullable=True)
    paystack_customer_code = Column(String, nullable=True)
    subscription_reference = Column(String, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="subscriptions")


class BillingTransaction(Base):
    __tablename__ = "billing_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default="NGN", nullable=False)
    reference = Column(String, unique=True, index=True, nullable=False)
    paystack_access_code = Column(String, nullable=True)
    paystack_authorization_url = Column(String, nullable=True)
    paystack_transaction_id = Column(String, nullable=True)
    status = Column(String, default="initialized", nullable=False)  # initialized|success|failed|abandoned
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    user = relationship("User", back_populates="transactions")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("billing_transactions.id"), nullable=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    plan_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default="NGN", nullable=False)
    reference = Column(String, nullable=True)
    status = Column(String, default="issued", nullable=False)
    issued_at = Column(DateTime, server_default=func.now(), nullable=True)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="invoices")


class BillingHistory(Base):
    __tablename__ = "billing_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # subscribe|upgrade|downgrade|cancel|renew|reactivate|payment_failed
    from_plan = Column(String, nullable=True)
    to_plan = Column(String, nullable=True)
    status = Column(String, nullable=False)
    reference = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)


class UserActivityLog(Base):
    """Audit trail for user-facing CRUD actions (orders, customers, inventory, etc.)."""

    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    summary = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)


class TransactionLog(Base):
    """Higher-level ledger-style events for monthly summaries."""

    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)


class VendorReportDispatch(Base):
    """Idempotent tracking for automated report emails."""

    __tablename__ = "vendor_report_dispatch"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_kind = Column(String, nullable=False)
    period_key = Column(String, nullable=False, index=True)
    sent_at = Column(DateTime, server_default=func.now(), nullable=True)
