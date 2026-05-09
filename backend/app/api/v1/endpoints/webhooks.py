import hashlib
import hmac
import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import AsyncDBSession
from app.core.config import settings
from app.services.webhook_service import process_paystack_event

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/paystack")
async def paystack_webhook(
    request: Request,
    db: AsyncDBSession,
    x_paystack_signature: str | None = Header(None),
):
    body = await request.body()
    raw = body.decode("utf-8", errors="replace")
    signing_secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET_KEY
    if signing_secret and x_paystack_signature:
        digest = hmac.new(
            signing_secret.encode("utf-8"), body, hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(digest, x_paystack_signature):
            raise HTTPException(status_code=400, detail="Invalid Paystack signature")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    row = process_paystack_event(db, payload, raw)
    return {"received": True, "event_id": row.id, "status": row.status}


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(
    request: Request,
    db: AsyncDBSession,
    verif_hash: str | None = Header(None, alias="verif-hash"),
):
    body = await request.body()
    raw = body.decode("utf-8", errors="replace")
    if (
        settings.FLUTTERWAVE_SECRET_HASH
        and verif_hash != settings.FLUTTERWAVE_SECRET_HASH
    ):
        raise HTTPException(status_code=400, detail="Invalid Flutterwave hash")

    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}
    reference = (payload.get("data") or {}).get("tx_ref")
    from app.models import PaymentEvent

    db.add(
        PaymentEvent(
            provider="flutterwave",
            event_type=payload.get("event"),
            reference=reference,
            payload=raw,
            raw_body=raw,
            status="received",
        )
    )
    await db.commit()
    return {"received": True}
