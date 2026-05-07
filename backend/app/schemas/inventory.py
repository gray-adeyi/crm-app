from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    unit_price: int = Field(default=0, ge=0)
    quantity_in_stock: int = Field(default=0, ge=0)
    reorder_threshold: int = Field(default=0, ge=0)
    image: str | None = Field(default=None, max_length=2048)


class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    unit_price: int = Field(default=0, ge=0)
    reorder_threshold: int = Field(default=0, ge=0)
    image: str | None = Field(default=None, max_length=2048)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str | None = None
    category: str | None = None
    description: str | None = None
    unit_price: int
    quantity_in_stock: int
    reorder_threshold: int
    peak_quantity: int | None = 0
    is_low_stock: bool | None = False
    image: str | None = None
    user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RestockRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=1000000)
    reason: str | None = Field(default=None, max_length=255)


class InventoryAnalyticsResponse(BaseModel):
    total_inventory_value: int
    low_stock_items: int
    out_of_stock_items: int
