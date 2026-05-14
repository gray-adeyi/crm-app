from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=64)
    instagram_handle: str | None = Field(default=None, max_length=255)


class CustomerResponse(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
