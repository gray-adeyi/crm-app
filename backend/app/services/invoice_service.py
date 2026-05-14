from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import aware_datetime_now
from app.models import Invoice


def build_invoice_number(user_id: UUID, reference: str) -> str:
    stamp = aware_datetime_now().strftime("%Y%m%d")
    return f"INV-{stamp}-{user_id}-{reference[-6:]}"


async def create_invoice(
    db: AsyncSession,
    *,
    user_id: UUID,
    transaction_id: int | None,
    plan_id: str,
    amount: int,
    reference: str,
    paid: bool,
) -> Invoice:
    stmt = select(Invoice).where(
        Invoice.reference == reference, Invoice.user_id == user_id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
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
        paid_at=aware_datetime_now() if paid else None,
    )
    db.add(row)
    return row
