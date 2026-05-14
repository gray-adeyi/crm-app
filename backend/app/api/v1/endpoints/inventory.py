from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import AsyncDBSession, SaasUser
from app.models import InventoryMovement, Product
from app.schemas.inventory import (
    InventoryAnalyticsResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    RestockRequest,
)
from app.services.activity_logging import log_transaction_event, log_user_activity
from app.services.inventory_alerts import refresh_product_stock_flags
from app.services.rbac import assert_permission

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def _get_owned_product_or_404(db, product_id: UUID, user_id: UUID) -> Product:
    stmt = select(Product).where(Product.id == product_id, Product.user_id == user_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return row


@router.post("", response_model=ProductResponse)
async def create_product(payload: ProductCreate, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "inventory:write")

    qty = int(payload.quantity_in_stock or 0)
    row = Product(
        name=payload.name.strip(),
        sku=(payload.sku.strip() if payload.sku else None),
        category=(payload.category.strip() if payload.category else None),
        description=(payload.description.strip() if payload.description else None),
        unit_price=int(payload.unit_price or 0),
        quantity_in_stock=qty,
        reorder_threshold=int(payload.reorder_threshold or 0),
        peak_quantity=qty,
        image=(payload.image.strip() if payload.image else None),
        user_id=user.id,
    )
    refresh_product_stock_flags(row)
    db.add(row)
    await db.flush()
    log_user_activity(
        db,
        user_id=user.id,
        action="create_product",
        entity_type="product",
        entity_id=row.id,
        summary=f"Product {row.name}",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="inventory",
        summary=f"Product #{row.id} created",
        payload={"product_id": row.id},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: AsyncDBSession,
    user: SaasUser,
    search: str | None = Query(default=None, max_length=128),
    category: str | None = Query(default=None, max_length=64),
):
    assert_permission(user, "inventory:read")

    stmt = select(Product).where(Product.user_id == user.id)
    if search:
        s = f"%{search.strip()}%"
        stmt = stmt.where(Product.name.ilike(s) | Product.sku.ilike(s))
    if category:
        stmt = stmt.where(Product.category == category.strip())

    return (await db.execute(stmt)).scalars().all()


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, payload: ProductUpdate, db: AsyncDBSession, user: SaasUser
):
    assert_permission(user, "inventory:write")

    row = await _get_owned_product_or_404(db, product_id, user.id)
    row.name = payload.name.strip()
    row.sku = payload.sku.strip() if payload.sku else None
    row.category = payload.category.strip() if payload.category else None
    row.description = payload.description.strip() if payload.description else None
    row.unit_price = int(payload.unit_price or 0)
    row.reorder_threshold = int(payload.reorder_threshold or 0)
    row.image = payload.image.strip() if payload.image else None
    refresh_product_stock_flags(row)
    log_user_activity(
        db,
        user_id=user.id,
        action="update_product",
        entity_type="product",
        entity_id=row.id,
        summary=f"Product #{row.id} updated",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="inventory",
        summary=f"Product #{row.id} updated",
        payload={"product_id": row.id},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "inventory:delete")
    stmt = select(Product).where(Product.id == product_id, Product.user_id == user.id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    pid = row.id
    log_user_activity(
        db,
        user_id=user.id,
        action="delete_product",
        entity_type="product",
        entity_id=pid,
        summary=f"Product #{pid} deleted",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="inventory",
        summary=f"Product #{pid} deleted",
        payload={"product_id": pid},
    )
    await db.delete(row)
    await db.commit()


@router.post("/{product_id}/restock", response_model=ProductResponse)
async def restock_product(
    product_id: UUID, payload: RestockRequest, db: AsyncDBSession, user: SaasUser
):
    assert_permission(user, "inventory:write")
    row = await _get_owned_product_or_404(db, product_id, user.id)

    row.quantity_in_stock = int(row.quantity_in_stock or 0) + int(payload.quantity)
    refresh_product_stock_flags(row)
    db.add(
        InventoryMovement(
            product_id=row.id,
            user_id=user.id,
            kind="restock",
            delta_quantity=int(payload.quantity),
            reason=(payload.reason.strip() if payload.reason else "Restock"),
        )
    )
    log_user_activity(
        db,
        user_id=user.id,
        action="restock_product",
        entity_type="product",
        entity_id=row.id,
        summary=f"Product #{row.id} restocked +{payload.quantity}",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="inventory",
        summary=f"Product #{row.id} restocked +{payload.quantity}",
        payload={"product_id": row.id},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/analytics", response_model=InventoryAnalyticsResponse)
async def inventory_analytics(db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "inventory:read")
    stmt = select(
        func.coalesce(func.sum(Product.unit_price * Product.quantity_in_stock), 0)
    ).where(Product.user_id == user.id)

    total_value = (await db.execute(stmt)).scalar_one_or_none() or 0

    stmt = select(func.count(Product.id)).where(
        Product.user_id == user.id, Product.quantity_in_stock <= 0
    )
    out_of_stock = (await db.execute(stmt)).scalar_one_or_none() or 0

    stmt = select().where(
        Product.user_id == user.id,
        Product.quantity_in_stock > 0,
        or_(
            Product.is_low_stock == True,
            (Product.reorder_threshold > 0)
            & (Product.quantity_in_stock <= Product.reorder_threshold),
        ),
    )
    low_stock = (await db.execute(stmt)).scalar_one_or_none() or 0
    return InventoryAnalyticsResponse(
        total_inventory_value=total_value,
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
    )
