from calendar import monthrange
from datetime import date, datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    BillingTransaction,
    Customer,
    Notification,
    Order,
    Product,
    User,
)
from app.schemas.dashboard import (
    CustomerGrowthPoint,
    DashboardResponse,
    DeliveryDTO,
    MonthlyRevenuePoint,
    RecentOrderDTO,
)
from app.services.plan_entitlements import has_full_dashboard_analytics


def _order_to_delivery_row(o: Order) -> DeliveryDTO:
    ft = getattr(o, "fulfillment_type", None) or "delivery"
    addr = getattr(o, "delivery_address", None)
    return DeliveryDTO(
        id=o.id,
        customer_name=(o.customer.name if o.customer else None),
        product=o.product,
        quantity=int(o.quantity or 1),
        status=o.status,
        fulfillment_type=ft,
        delivery_address=addr,
        delivery_date=(o.delivery_date.isoformat() if o.delivery_date else None),
        delivery_time=(o.delivery_time.strftime("%H:%M") if o.delivery_time else None),
    )


def _month_start(d: date) -> datetime:
    return datetime(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def build_dashboard(db: Session, user: User) -> DashboardResponse:
    user_id = user.id
    total_customers = int(
        db.query(func.count(Customer.id)).filter(Customer.user_id == user_id).scalar()
        or 0
    )
    total_orders = int(
        db.query(func.count(Order.id)).filter(Order.user_id == user_id).scalar() or 0
    )

    total_collected = int(
        db.query(func.coalesce(func.sum(Order.amount_paid), 0))
        .filter(Order.user_id == user_id)
        .scalar()
        or 0
    )
    gross_sales = int(
        db.query(func.coalesce(func.sum(Order.price), 0))
        .filter(Order.user_id == user_id)
        .scalar()
        or 0
    )
    outstanding = int(
        db.query(func.coalesce(func.sum(Order.balance), 0))
        .filter(Order.user_id == user_id)
        .scalar()
        or 0
    )

    today = date.today()
    m_start = _month_start(today)
    next_m = _add_months(today.replace(day=1), 1)
    m_end = datetime(next_m.year, next_m.month, next_m.day)

    monthly_revenue = int(
        db.query(func.coalesce(func.sum(Order.amount_paid), 0))
        .filter(
            Order.user_id == user_id,
            Order.created_at.isnot(None),
            Order.created_at >= m_start,
            Order.created_at < m_end,
        )
        .scalar()
        or 0
    )

    orders_pending = int(
        db.query(func.count(Order.id))
        .filter(Order.user_id == user_id, Order.status == "pending")
        .scalar()
        or 0
    )
    orders_partial = int(
        db.query(func.count(Order.id))
        .filter(Order.user_id == user_id, Order.status == "partial")
        .scalar()
        or 0
    )
    orders_paid = int(
        db.query(func.count(Order.id))
        .filter(Order.user_id == user_id, Order.status == "paid")
        .scalar()
        or 0
    )
    failed_payments = int(
        db.query(func.count(BillingTransaction.id))
        .filter(
            BillingTransaction.user_id == user_id,
            BillingTransaction.status.in_(["failed", "abandoned"]),
        )
        .scalar()
        or 0
    )
    mrr = int(
        db.query(func.coalesce(func.sum(BillingTransaction.amount), 0))
        .filter(
            BillingTransaction.user_id == user_id,
            BillingTransaction.status == "success",
            BillingTransaction.created_at >= m_start,
            BillingTransaction.created_at < m_end,
        )
        .scalar()
        or 0
    )
    active_subscriptions = int(
        db.query(func.count(User.id))
        .filter(User.id == user_id, User.subscription_status.in_(["active", "trial"]))
        .scalar()
        or 0
    )
    cancelled = int(
        db.query(func.count(User.id))
        .filter(User.id == user_id, User.subscription_status == "cancelled")
        .scalar()
        or 0
    )
    base_for_churn = active_subscriptions + cancelled
    churn_rate = float((cancelled / base_for_churn) * 100) if base_for_churn else 0.0

    revenue_by_month: list[MonthlyRevenuePoint] = []
    customer_growth: list[CustomerGrowthPoint] = []

    for i in range(5, -1, -1):
        ref = _add_months(today.replace(day=1), -i)
        start = _month_start(ref)
        nxt = _add_months(ref, 1)
        end = datetime(nxt.year, nxt.month, nxt.day)
        label = ref.strftime("%Y-%m")

        rev = int(
            db.query(func.coalesce(func.sum(Order.amount_paid), 0))
            .filter(
                Order.user_id == user_id,
                Order.created_at.isnot(None),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .scalar()
            or 0
        )
        ocnt = int(
            db.query(func.count(Order.id))
            .filter(
                Order.user_id == user_id,
                Order.created_at.isnot(None),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .scalar()
            or 0
        )
        revenue_by_month.append(
            MonthlyRevenuePoint(month=label, revenue=rev, orders=ocnt)
        )

        ccnt = int(
            db.query(func.count(Customer.id))
            .filter(
                Customer.user_id == user_id,
                Customer.created_at.isnot(None),
                Customer.created_at >= start,
                Customer.created_at < end,
            )
            .scalar()
            or 0
        )
        customer_growth.append(CustomerGrowthPoint(month=label, new_customers=ccnt))

    recent_rows = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(Order.user_id == user_id)
        .order_by(Order.id.desc())
        .limit(5)
        .all()
    )

    recent_orders = [
        RecentOrderDTO(
            id=o.id,
            product=o.product,
            total_price=o.price,
            amount_paid=o.amount_paid,
            balance=o.balance,
            status=o.status,
            customer_id=o.customer_id,
            customer_name=(o.customer.name if o.customer else None),
        )
        for o in recent_rows
    ]

    # deliveries widgets
    today = date.today()
    upcoming_cutoff = today + timedelta(days=7)
    delivery_rows = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(
            Order.user_id == user_id,
            Order.delivery_date.isnot(None),
            func.coalesce(Order.fulfillment_type, "delivery") == "delivery",
        )
        .order_by(Order.delivery_date.asc(), Order.id.desc())
        .limit(200)
        .all()
    )

    upcoming: list[DeliveryDTO] = []
    todays: list[DeliveryDTO] = []
    overdue: list[DeliveryDTO] = []
    for o in delivery_rows:
        dto = _order_to_delivery_row(o)
        if o.delivery_date == today:
            todays.append(dto)
        elif (
            o.delivery_date
            and o.delivery_date < today
            and o.status not in {"delivered", "cancelled"}
        ):
            overdue.append(dto)
        elif o.delivery_date and today <= o.delivery_date <= upcoming_cutoff:
            upcoming.append(dto)

    upcoming = upcoming[:8]
    todays = todays[:8]
    overdue = overdue[:8]

    pickup_rows = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(
            Order.user_id == user_id,
            Order.fulfillment_type == "pickup",
            ~Order.status.in_(["delivered", "cancelled"]),
        )
        .order_by(Order.id.desc())
        .limit(20)
        .all()
    )
    pickups_ready = [_order_to_delivery_row(o) for o in pickup_rows[:8]]

    completed_rows = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(
            Order.user_id == user_id,
            func.coalesce(Order.fulfillment_type, "delivery") == "delivery",
            Order.status == "delivered",
        )
        .order_by(Order.id.desc())
        .limit(12)
        .all()
    )
    deliveries_completed = [_order_to_delivery_row(o) for o in completed_rows]

    unread_notifications = int(
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .scalar()
        or 0
    )

    total_inventory_value = int(
        db.query(
            func.coalesce(func.sum(Product.unit_price * Product.quantity_in_stock), 0)
        )
        .filter(Product.user_id == user_id)
        .scalar()
        or 0
    )
    out_of_stock_items = int(
        db.query(func.count(Product.id))
        .filter(Product.user_id == user_id, Product.quantity_in_stock <= 0)
        .scalar()
        or 0
    )
    low_stock_items = int(
        db.query(func.count(Product.id))
        .filter(
            Product.user_id == user_id,
            Product.quantity_in_stock > 0,
            or_(
                Product.is_low_stock == True,
                (Product.reorder_threshold > 0)
                & (Product.quantity_in_stock <= Product.reorder_threshold),
            ),  # noqa: E712
        )
        .scalar()
        or 0
    )

    analytics_limited = not has_full_dashboard_analytics(user)
    if analytics_limited:
        revenue_by_month = (
            revenue_by_month[-3:] if len(revenue_by_month) > 3 else revenue_by_month
        )
        customer_growth = (
            customer_growth[-3:] if len(customer_growth) > 3 else customer_growth
        )
        mrr = 0
        failed_payments = 0
        churn_rate = 0.0

    return DashboardResponse(
        total_customers=total_customers,
        total_orders=total_orders,
        total_revenue=total_collected,
        gross_sales=gross_sales,
        outstanding_balance=outstanding,
        monthly_revenue=monthly_revenue,
        orders_pending=orders_pending,
        orders_partial=orders_partial,
        orders_paid=orders_paid,
        mrr=mrr,
        active_subscriptions=active_subscriptions,
        failed_payments=failed_payments,
        churn_rate=round(churn_rate, 2),
        revenue_by_month=revenue_by_month,
        customer_growth=customer_growth,
        recent_orders=recent_orders,
        upcoming_deliveries=upcoming,
        todays_deliveries=todays,
        overdue_deliveries=overdue,
        pickups_ready=pickups_ready,
        completed_deliveries=deliveries_completed,
        unread_notifications=unread_notifications,
        total_inventory_value=total_inventory_value,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        analytics_limited=analytics_limited,
    )
