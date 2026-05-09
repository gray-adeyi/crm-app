"""Per-user notification channel toggles stored as JSON on `User.notification_preferences`."""

from __future__ import annotations

import json

_DEFAULT = {
    "email_order_reminders": True,
    "email_low_stock": True,
    "email_monthly_report": True,
    "email_activity_summary": True,
    "email_billing": True,
}


def prefs_dict(user) -> dict:
    raw = getattr(user, "notification_preferences", None)
    if not raw:
        return dict(_DEFAULT)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            merged = dict(_DEFAULT)
            merged.update({str(k): v for k, v in data.items()})
            return merged
    except json.JSONDecodeError:
        pass
    return dict(_DEFAULT)


def is_email_enabled(user, topic: str) -> bool:
    """
    Topics: order_reminders | low_stock | monthly_report | activity_summary | billing
    Maps to camelCase email_* keys in stored JSON.
    """
    mapping = {
        "order_reminders": "email_order_reminders",
        "low_stock": "email_low_stock",
        "monthly_report": "email_monthly_report",
        "activity_summary": "email_activity_summary",
        "billing": "email_billing",
    }
    key = mapping.get(topic)
    if not key:
        return True
    data = prefs_dict(user)
    return bool(data.get(key, True))


def serialize_prefs(data: dict) -> str:
    return json.dumps({str(k): v for k, v in data.items()})
