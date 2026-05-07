from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.entities import User
from app.services import plan_entitlements
from app.services.notification_prefs import prefs_dict, serialize_prefs


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: int
    email: str
    role: str
    subscription_plan: str
    current_plan: str | None = None
    subscription_status: str
    subscription_ends_at: datetime | None = None
    billing_cycle: str | None = None
    renewal_date: datetime | None = None
    trial_end_date: datetime | None = None
    trial_started_at: datetime | None = None
    trial_ends_at: datetime | None = None
    subscription_reference: str | None = None
    paystack_customer_code: str | None = None
    business_name: str | None = None
    business_phone: str | None = None
    business_address: str | None = None
    currency: str
    logo_url: str | None = None
    onboarding_completed: bool
    notification_preferences: dict[str, Any] = Field(default_factory=dict)
    is_trial_active: bool = False
    needs_subscription_upgrade: bool = False
    analytics_full: bool = True
    can_bulk_export: bool = True
    email_verified: bool = True

    @model_validator(mode="before")
    @classmethod
    def _from_user(cls, data: Any):
        if isinstance(data, User):
            return {
                "id": data.id,
                "email": data.email,
                "role": data.role,
                "subscription_plan": data.subscription_plan,
                "current_plan": data.current_plan,
                "subscription_status": data.subscription_status,
                "subscription_ends_at": data.subscription_ends_at,
                "billing_cycle": data.billing_cycle,
                "renewal_date": data.renewal_date,
                "trial_end_date": data.trial_end_date,
                "trial_started_at": data.trial_started_at,
                "trial_ends_at": data.trial_ends_at or data.trial_end_date,
                "subscription_reference": data.subscription_reference,
                "paystack_customer_code": data.paystack_customer_code,
                "business_name": data.business_name,
                "business_phone": data.business_phone,
                "business_address": data.business_address,
                "currency": data.currency,
                "logo_url": data.logo_url,
                "onboarding_completed": bool(data.onboarding_completed),
                "notification_preferences": prefs_dict(data),
                "is_trial_active": bool(data.is_trial_active),
                "needs_subscription_upgrade": bool(data.needs_subscription_upgrade),
                "analytics_full": plan_entitlements.has_full_dashboard_analytics(data),
                "can_bulk_export": plan_entitlements.can_bulk_export(data),
                "email_verified": bool(getattr(data, "email_verified", True)),
            }
        return data


class UserProfileUpdate(BaseModel):
    business_name: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, max_length=8)
    logo_url: str | None = Field(default=None, max_length=512)
    business_phone: str | None = Field(default=None, max_length=64)
    business_address: str | None = Field(default=None, max_length=2000)
    notification_preferences: dict[str, Any] | None = Field(default=None)


class OnboardingUpdate(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="NGN", max_length=8)
    logo_url: str | None = Field(default=None, max_length=512)
    onboarding_completed: bool = True


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    password: str = Field(..., min_length=1)
