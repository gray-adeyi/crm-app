from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderCreate(BaseModel):
    product: str | None = Field(default=None, min_length=1, max_length=255)
    product_id: UUID | None = Field(default=None, ge=1)
    quantity: int = Field(default=1, ge=1, le=100000)
    total_price: int = Field(..., ge=0)
    amount_paid: int = Field(default=0, ge=0)
    customer_id: UUID = Field(..., ge=1)
    fulfillment_type: str = Field(default="delivery", max_length=32)
    delivery_date: date | None = None
    delivery_time: time | None = None
    delivery_address: str | None = Field(default=None, max_length=4000)
    delivery_notes: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)
    payment_method: str | None = Field(default=None, max_length=64)

    @model_validator(mode="before")
    @classmethod
    def _legacy_price_key(cls, data):
        if isinstance(data, dict) and "price" in data and "total_price" not in data:
            data = {**data, "total_price": data["price"]}
        return data

    @model_validator(mode="after")
    def _require_product_or_product_id(self):
        if not self.product_id and not (self.product and self.product.strip()):
            raise ValueError("Provide either product_id or product")
        ft = (self.fulfillment_type or "delivery").strip().lower()
        if ft not in {"delivery", "pickup"}:
            raise ValueError("fulfillment_type must be delivery or pickup")
        self.fulfillment_type = ft
        if ft == "delivery":
            if not self.delivery_date or not self.delivery_time:
                raise ValueError(
                    "Delivery date and time are required for delivery orders"
                )
        return self


class OrderUpdate(BaseModel):
    product: str | None = Field(default=None, min_length=1, max_length=255)
    product_id: UUID | None
    quantity: int = Field(..., ge=1, le=100000)
    total_price: int = Field(..., ge=0)
    amount_paid: int = Field(..., ge=0)
    customer_id: UUID
    status: str = Field(..., min_length=1, max_length=32)
    fulfillment_type: str = Field(default="delivery", max_length=32)
    delivery_date: date | None = None
    delivery_time: time | None = None
    delivery_address: str | None = Field(default=None, max_length=4000)
    delivery_notes: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)
    payment_method: str | None = Field(default=None, max_length=64)

    @model_validator(mode="before")
    @classmethod
    def _legacy_price_key(cls, data):
        if isinstance(data, dict) and "price" in data and "total_price" not in data:
            data = {**data, "total_price": data["price"]}
        return data

    @model_validator(mode="after")
    def _require_product_or_product_id(self):
        if not self.product_id and not (self.product and self.product.strip()):
            raise ValueError("Provide either product_id or product")
        ft = (self.fulfillment_type or "delivery").strip().lower()
        if ft not in {"delivery", "pickup"}:
            raise ValueError("fulfillment_type must be delivery or pickup")
        self.fulfillment_type = ft
        if ft == "delivery":
            if not self.delivery_date or not self.delivery_time:
                raise ValueError(
                    "Delivery date and time are required for delivery orders"
                )
        return self


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product: str
    product_id: int | None = None
    quantity: int
    total_price: int
    amount_paid: int
    balance: int
    status: str
    customer_id: UUID
    user_id: UUID
    fulfillment_type: str = "delivery"
    delivery_date: date | None = None
    delivery_time: time | None = None
    delivery_address: str | None = None
    delivery_notes: str | None = None
    reminder_sent: bool | None = None
    reminder_status: str | None = None
    notes: str | None = None
    payment_method: str | None = None
    created_at: datetime | None = None
