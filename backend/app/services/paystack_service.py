import uuid

import httpx

from app.core.config import get_settings


class PaystackError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError("PAYSTACK_SECRET_KEY is not configured")
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def _url(path: str) -> str:
    settings = get_settings()
    return f"{settings.PAYSTACK_BASE_URL.rstrip('/')}{path}"


def generate_reference(user_id: int, plan_id: str) -> str:
    return f"crm_{plan_id}_{user_id}_{uuid.uuid4().hex[:14]}"


def initialize_transaction(*, email: str, amount_ngn: int, reference: str, metadata: dict, callback_url: str | None = None) -> dict:
    payload = {
        "email": email,
        "amount": int(amount_ngn) * 100,
        "reference": reference,
        "metadata": metadata,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    with httpx.Client(timeout=30) as client:
        res = client.post(_url("/transaction/initialize"), headers=_headers(), json=payload)
    data = res.json()
    if res.status_code >= 400 or not data.get("status"):
        raise PaystackError(data.get("message") or f"Paystack initialize failed ({res.status_code})")
    return data["data"]


def verify_transaction(reference: str) -> dict:
    with httpx.Client(timeout=30) as client:
        res = client.get(_url(f"/transaction/verify/{reference}"), headers=_headers())
    data = res.json()
    if res.status_code >= 400 or not data.get("status"):
        raise PaystackError(data.get("message") or f"Paystack verify failed ({res.status_code})")
    return data["data"]


def disable_subscription(subscription_code: str, email_token: str) -> dict:
    payload = {"code": subscription_code, "token": email_token}
    with httpx.Client(timeout=30) as client:
        res = client.post(_url("/subscription/disable"), headers=_headers(), json=payload)
    data = res.json()
    if res.status_code >= 400 or not data.get("status"):
        raise PaystackError(data.get("message") or f"Paystack disable failed ({res.status_code})")
    return data.get("data") or {}
