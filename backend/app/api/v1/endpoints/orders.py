from app.models.inventory_movements import InventoryMovement
from app.models.customers import Customer
from sqlalchemy import select
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import AsyncDBSession, SaasUser
from app.models import Order, Product
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.activity_logging import log_transaction_event, log_user_activity
from app.services.order_logic import compute_balance, compute_order_status
from app.services.rbac import assert_permission

router = APIRouter(prefix="/orders", tags=["orders"])


async def _get_owned_customer_or_404(
    db: AsyncDBSession, customer_id: UUID, user_id: UUID
):

    stmt = select(Customer).where(
        Customer.id == customer_id, Customer.user_id == user_id
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _normalize_amounts(total_price: int, amount_paid: int) -> tuple[int, int]:
    if amount_paid < 0:
        raise HTTPException(status_code=400, detail="amount_paid cannot be negative")
    if amount_paid > total_price:
        raise HTTPException(
            status_code=400, detail="amount_paid cannot exceed total_price"
        )
    return int(total_price), int(amount_paid)


async def _get_owned_product_or_404(
    db: AsyncDBSession, product_id: UUID, user_id: UUID
) -> Product:
    stmt = select(Product).filter(Product.id == product_id, Product.user_id == user_id)
    product = (await db.execute(stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _deduct_stock_or_400(
    db: AsyncDBSession, *, product: Product, qty: int, user_id: UUID, order_id: UUID
) -> None:
    if qty <= 0:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")
    if int(product.quantity_in_stock or 0) < int(qty):
        raise HTTPException(
            status_code=400, detail=f"Insufficient stock for {product.name}"
        )
    product.quantity_in_stock = int(product.quantity_in_stock or 0) - int(qty)

    db.add(
        InventoryMovement(
            product_id=product.id,
            user_id=user_id,
            kind="sale",
            delta_quantity=-int(qty),
            reason="Order created",
            related_order_id=order_id,
        )
    )


@router.post("", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: AsyncDBSession,
    user: SaasUser,
    background_tasks: BackgroundTasks,
):
    assert_permission(user, "orders:write")
    await _get_owned_customer_or_404(db, order.customer_id, user.id)

    total_price, amount_paid = _normalize_amounts(order.total_price, order.amount_paid)
    balance = compute_balance(total_price, amount_paid)
    status_val = compute_order_status(total_price, amount_paid, "pending")

    product_name = (order.product.strip() if order.product else None) or ""
    product_id = order.product_id
    product_row = None
    if product_id:
        product_row = await _get_owned_product_or_404(db, product_id, user.id)
        product_name = product_row.name

    ft = (order.fulfillment_type or "delivery").lower()
    delivery_date = order.delivery_date if ft == "delivery" else None
    delivery_time = order.delivery_time if ft == "delivery" else None
    delivery_address = (
        (order.delivery_address.strip() if order.delivery_address else None)
        if ft == "delivery"
        else None
    )

    row = Order(
        product=product_name,
        product_id=product_id,
        quantity=int(order.quantity or 1),
        price=total_price,
        amount_paid=amount_paid,
        balance=balance,
        status=status_val,
        customer_id=order.customer_id,
        user_id=user.id,
        fulfillment_type=ft,
        delivery_date=delivery_date,
        delivery_time=delivery_time,
        delivery_address=delivery_address,
        delivery_notes=(order.delivery_notes.strip() if order.delivery_notes else None)
        if ft == "delivery"
        else None,
        notes=(order.notes.strip() if order.notes else None),
        payment_method=(order.payment_method.strip() if order.payment_method else None),
    )
    try:
        db.add(row)
        await db.flush()  # allocate row.id for movement link
        if product_row and not row.stock_deducted:
            _deduct_stock_or_400(
                db,
                product=product_row,
                qty=row.quantity,
                user_id=user.id,
                order_id=row.id,
            )
            row.stock_deducted = True
            try:
                from app.services.inventory_alerts import refresh_product_stock_flags

                refresh_product_stock_flags(product_row)
            except Exception:
                pass
        log_user_activity(
            db,
            user_id=user.id,
            action="create_order",
            entity_type="order",
            entity_id=row.id,
            summary=f"Order #{row.id} created · {product_name}",
            metadata={"customer_id": order.customer_id, "fulfillment_type": ft},
        )
        log_transaction_event(
            db,
            user_id=user.id,
            category="order",
            summary=f"Order #{row.id} created",
            payload={
                "order_id": row.id,
                "amount_paid": amount_paid,
                "total": total_price,
            },
        )
        await db.commit()
        await db.refresh(row)
    except Exception:
        await db.rollback()
        raise

    # fire-and-forget: email notification + internal notification row
    try:
        from app.services.order_notifications import enqueue_order_created_notifications

        background_tasks.add_task(enqueue_order_created_notifications, row.id, user.id)
    except Exception:
        # never block order creation on email
        ...

    try:
        if product_row:
            from app.services.inventory_alerts import (
                enqueue_low_stock_alert,
                is_low_stock,
            )

            if is_low_stock(product_row):
                background_tasks.add_task(
                    enqueue_low_stock_alert, product_row.id, user.id
                )
    except Exception:
        ...
    return row


@router.get("", response_model=list[OrderResponse])
async def list_orders(db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "orders:read")
    stmt = select(Order).filter(Order.user_id == user.id)
    return (await db.execute(stmt)).scalars().all()


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID, payload: OrderUpdate, db: AsyncDBSession, user: SaasUser
):
    assert_permission(user, "orders:write")
    stmt = select(Order).filter(Order.id == order_id, Order.user_id == user.id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    await _get_owned_customer_or_404(db, payload.customer_id, user.id)

    total_price, amount_paid = _normalize_amounts(
        payload.total_price, payload.amount_paid
    )
    balance = compute_balance(total_price, amount_paid)
    normalized_status = compute_order_status(
        total_price, amount_paid, payload.status.strip().lower()
    )

    new_product_id = payload.product_id
    new_product_name = (payload.product.strip() if payload.product else None) or ""
    product_row = None
    if new_product_id:
        product_row = await _get_owned_product_or_404(db, new_product_id, user.id)
        new_product_name = product_row.name

    # stock adjustment (best-effort)
    if (
        existing.product_id
        and existing.stock_deducted
        and existing.product_id == new_product_id
    ):
        delta_qty = int(payload.quantity) - int(existing.quantity or 1)
        if delta_qty != 0 and product_row:
            if delta_qty > 0:
                _deduct_stock_or_400(
                    db,
                    product=product_row,
                    qty=delta_qty,
                    user_id=user.id,
                    order_id=existing.id,
                )
            else:
                product_row.quantity_in_stock = int(
                    product_row.quantity_in_stock or 0
                ) + abs(int(delta_qty))

                db.add(
                    InventoryMovement(
                        product_id=product_row.id,
                        user_id=user.id,
                        kind="adjustment",
                        delta_quantity=abs(int(delta_qty)),
                        reason="Order quantity reduced",
                        related_order_id=existing.id,
                    )
                )
    elif existing.product_id != new_product_id:
        # changing product on an already-deducted order is complex; block to prevent double-deduction bugs
        if existing.stock_deducted:
            raise HTTPException(
                status_code=400,
                detail="Cannot change product for an order that already affected stock",
            )

    ft = (payload.fulfillment_type or "delivery").lower()
    existing.product = new_product_name
    existing.product_id = new_product_id
    existing.quantity = int(payload.quantity)
    existing.price = total_price
    existing.amount_paid = amount_paid
    existing.balance = balance
    existing.status = normalized_status
    existing.customer_id = payload.customer_id
    existing.fulfillment_type = ft
    existing.delivery_date = payload.delivery_date if ft == "delivery" else None
    existing.delivery_time = payload.delivery_time if ft == "delivery" else None
    existing.delivery_address = (
        (payload.delivery_address.strip() if payload.delivery_address else None)
        if ft == "delivery"
        else None
    )
    existing.delivery_notes = (
        (payload.delivery_notes.strip() if payload.delivery_notes else None)
        if ft == "delivery"
        else None
    )
    existing.notes = payload.notes.strip() if payload.notes else None
    existing.payment_method = (
        payload.payment_method.strip() if payload.payment_method else None
    )

    if product_row:
        try:
            from app.services.inventory_alerts import refresh_product_stock_flags

            refresh_product_stock_flags(product_row)
        except Exception:
            pass

    log_user_activity(
        db,
        user_id=user.id,
        action="update_order",
        entity_type="order",
        entity_id=existing.id,
        summary=f"Order #{existing.id} updated",
        metadata={"status": normalized_status, "fulfillment_type": ft},
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="order",
        summary=f"Order #{existing.id} updated",
        payload={"order_id": existing.id, "status": normalized_status},
    )

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "orders:delete")
    stmt = select(Order).filter(Order.id == order_id, Order.user_id == user.id)

    existing = (await db.execute(stmt)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    oid = existing.id
    log_user_activity(
        db,
        user_id=user.id,
        action="delete_order",
        entity_type="order",
        entity_id=oid,
        summary=f"Order #{oid} deleted",
    )
    log_transaction_event(
        db,
        user_id=user.id,
        category="order",
        summary=f"Order #{oid} deleted",
        payload={"order_id": oid},
    )
    await db.delete(existing)
    await db.commit()
