from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from app.api.deps import DbSession, SaasUser
from app.models.entities import Customer
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.activity_logging import log_transaction_event, log_user_activity
from app.services.plan_entitlements import effective_max_customers
from app.services.rbac import assert_permission

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_owned_customer_or_404(db, customer_id: int, user_id: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == user_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: DbSession, user: SaasUser):
    assert_permission(user, "customers:write")

    max_c = effective_max_customers(user)
    if max_c is not None:
        cnt = db.query(func.count(Customer.id)).filter(Customer.user_id == user.id).scalar() or 0
        if int(cnt) >= int(max_c):
            raise HTTPException(
                status_code=403,
                detail="Customer limit reached for your plan. Upgrade to add more customers.",
            )

    instagram = customer.instagram_handle.strip() if customer.instagram_handle else None
    row = Customer(
        name=customer.name.strip(),
        phone=customer.phone.strip(),
        instagram_handle=instagram,
        user_id=user.id,
    )
    db.add(row)
    db.flush()
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
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[CustomerResponse])
def get_customers(db: DbSession, user: SaasUser):
    assert_permission(user, "customers:read")
    return db.query(Customer).filter(Customer.user_id == user.id).order_by(Customer.id.asc()).all()


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer: CustomerCreate, db: DbSession, user: SaasUser):
    assert_permission(user, "customers:write")
    existing = _get_owned_customer_or_404(db, customer_id, user.id)
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
    db.commit()
    db.refresh(existing)
    return existing


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: DbSession, user: SaasUser):
    assert_permission(user, "customers:delete")
    existing = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == user.id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")
    cid = existing.id
    log_user_activity(db, user_id=user.id, action="delete_customer", entity_type="customer", entity_id=cid, summary=f"Customer #{cid} deleted")
    log_transaction_event(db, user_id=user.id, category="customer", summary=f"Customer #{cid} deleted", payload={"customer_id": cid})
    db.delete(existing)
    db.commit()
    return {"message": "Deleted"}
