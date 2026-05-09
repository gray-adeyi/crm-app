from datetime import datetime

from app.models import Invoice


def build_invoice_number(user_id: int, reference: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    return f"INV-{stamp}-{user_id}-{reference[-6:]}"


def create_invoice(
    db,
    *,
    user_id: int,
    transaction_id: int | None,
    plan_id: str,
    amount: int,
    reference: str,
    paid: bool,
) -> Invoice:
    existing = (
        db.query(Invoice)
        .filter(Invoice.reference == reference, Invoice.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    row = Invoice(
        user_id=user_id,
        transaction_id=transaction_id,
        invoice_number=build_invoice_number(user_id, reference),
        plan_id=plan_id,
        amount=amount,
        currency="NGN",
        reference=reference,
        status="paid" if paid else "issued",
        paid_at=datetime.utcnow() if paid else None,
    )
    db.add(row)
    return row
