from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import Notification


def _derive_category(typ: str) -> str:
    t = (typ or "").lower()
    mapping = {
        "low_stock": "inventory",
        "order_reminder": "deliveries",
        "billing_notice": "billing",
        "payment_notice": "payments",
        "subscription": "billing",
        "system": "system",
        "customer": "customers",
        "payment": "payments",
        "billing": "billing",
    }
    return mapping.get(t, "system")


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: int
    type: str
    title: str
    body: str | None = None
    severity: str
    is_read: bool
    related_order_id: int | None = None
    related_product_id: int | None = None
    created_at: datetime | None = None

    category: str = "system"
    notification_channel_in_app: bool = True
    notification_channel_email: bool = False
    action_label: str | None = None
    action_route: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_notification(cls, data):
        if not isinstance(data, Notification):
            return data
        cat = _derive_category(data.type or "")
        action_route = None
        action_label = None
        if data.related_order_id:
            action_route = "/orders"
            action_label = "Open orders"
        elif data.related_product_id:
            action_route = "/inventory"
            action_label = "View inventory"

        email_push = cat in {"billing"} or ("payment" in (data.title or "").lower())

        return {
            "id": data.id,
            "type": data.type,
            "title": data.title,
            "body": data.body,
            "severity": data.severity,
            "is_read": bool(data.is_read),
            "related_order_id": data.related_order_id,
            "related_product_id": data.related_product_id,
            "created_at": data.created_at,
            "category": cat,
            "notification_channel_in_app": True,
            "notification_channel_email": bool(email_push),
            "action_label": action_label,
            "action_route": action_route,
        }


class NotificationMarkReadRequest(BaseModel):
    ids: list[int] = Field(default_factory=list, max_length=200)
