from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SubscribeInitializeRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=32)


class SubscribeInitializeResponse(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class VerifyTransactionRequest(BaseModel):
    reference: str = Field(..., min_length=6, max_length=128)


class CancelSubscriptionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class BillingTransactionItem(BaseModel):
    reference: str
    plan_id: str
    amount: int
    currency: str
    status: str
    paid_at: datetime | None
    created_at: datetime | None


class InvoiceItem(BaseModel):
    invoice_number: str
    plan_id: str
    amount: int
    currency: str
    status: str
    issued_at: datetime | None
    reference: str | None


class BillingMeResponse(BaseModel):
    plan_id: str
    status: str
    billing_cycle: str
    renewal_date: datetime | None
    trial_end_date: datetime | None
    grace_until: datetime | None
    paystack_customer_code: str | None
    limits: dict[str, Any]
    transactions: list[BillingTransactionItem]
    invoices: list[InvoiceItem]
