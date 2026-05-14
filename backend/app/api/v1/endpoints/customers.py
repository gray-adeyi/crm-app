from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import AsyncDBSession, SaasUser
from app.models import Customer
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.activity_logging import log_transaction_event, log_user_activity
from app.services.plan_entitlements import effective_max_customers
from app.services.rbac import assert_permission

router = APIRouter(prefix="/customers", tags=["customers"])


async def _get_owned_customer_or_404(
    db: AsyncDBSession, customer_id: UUID, user_id: UUID
) -> Customer:
    stmt = select(Customer).where(
        Customer.id == customer_id, Customer.user_id == user_id
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "customers:write")

    max_customers = effective_max_customers(user)
    if max_customers is not None:
        stmt = select(func.count(Customer.id)).where(Customer.user_id == user.id)
        count = (await db.execute(stmt)).scalar_one_or_none() or 0
        if int(count) >= int(max_customers):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Customer limit reached for your plan."
                    " Upgrade to add more customers."
                ),
            )

    instagram = customer.instagram_handle.strip() if customer.instagram_handle else None
    row = Customer(
        name=customer.name.strip(),
        phone=customer.phone.strip(),
        instagram_handle=instagram,
        user_id=user.id,
    )
    db.add(row)
    await db.flush()
    log_user_activity(
        db,
        user_id=user.id,
        action="create_customer",
        entity_type="customer",
        entity_id=row.id,
        summary=f"Customer {row.name}",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="customer",
        summary=f"Customer #{row.id} created",
        payload={"customer_id": row.id},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[CustomerResponse])
async def get_customers(db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "customers:read")
    stmt = select(Customer).where(Customer.user_id == user.id)
    return (await db.execute(stmt)).scalars().all()


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID, customer: CustomerCreate, db: AsyncDBSession, user: SaasUser
):
    assert_permission(user, "customers:write")
    existing = await _get_owned_customer_or_404(db, customer_id, user.id)
    instagram = customer.instagram_handle.strip() if customer.instagram_handle else None
    existing.name = customer.name.strip()
    existing.phone = customer.phone.strip()
    existing.instagram_handle = instagram
    log_user_activity(
        db,
        user_id=user.id,
        action="update_customer",
        entity_type="customer",
        entity_id=existing.id,
        summary=f"Customer #{existing.id} updated",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="customer",
        summary=f"Customer #{existing.id} updated",
        payload={"customer_id": existing.id},
    )
    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "customers:delete")
    stmt = select(Customer).where(
        Customer.id == customer_id, Customer.user_id == user.id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")
    cid = existing.id
    log_user_activity(
        db,
        user_id=user.id,
        action="delete_customer",
        entity_type="customer",
        entity_id=cid,
        summary=f"Customer #{cid} deleted",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="customer",
        summary=f"Customer #{cid} deleted",
        payload={"customer_id": cid},
    )
    await db.delete(existing)
    await db.commit()
