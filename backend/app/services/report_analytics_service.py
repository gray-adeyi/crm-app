"""Aggregated reports for the Reports dashboard (filterable by date range & status)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Customer, Order, Product


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip()[:10])
    except ValueError:
        return None


def window_bounds(
    *, date_from: str | None, date_to: str | None
) -> tuple[datetime, datetime]:
    end_d = _parse_date(date_to) or date.today()
    start_d = _parse_date(date_from) or (end_d - timedelta(days=365))
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    start_dt = datetime(start_d.year, start_d.month, start_d.day)
    end_exclusive = datetime(end_d.year, end_d.month, end_d.day) + timedelta(days=1)
    return start_dt, end_exclusive


def build_report_summary(
    db: Session,
    *,
    user_id: int,
    date_from: str | None,
    date_to: str | None,
    order_statuses: list[str] | None,
    payment_statuses: list[str] | None,
    customer_id: int | None,
) -> dict[str, Any]:
    start_dt, end_exclusive = window_bounds(date_from=date_from, date_to=date_to)

    q = db.query(Order).filter(
        Order.user_id == user_id,
        Order.created_at.isnot(None),
        Order.created_at >= start_dt,
        Order.created_at < end_exclusive,
    )
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)

    if order_statuses:
        st_list = {
            (s or "").strip().lower() for s in order_statuses if (s or "").strip()
        }
        if st_list:
            q = q.filter(Order.status.in_(list(st_list)))

    rows = q.all()

    def pay_bucket(o: Order) -> str:
        st = (o.status or "").lower()
        if st == "cancelled":
            return "cancelled"
        tb = int(o.price or 0)
        ap = int(o.amount_paid or 0)
        if ap <= 0:
            return "unpaid"
        if ap < tb:
            return "partial"
        return "paid"

    if payment_statuses:
        ps = {(s or "").strip().lower() for s in payment_statuses if (s or "").strip()}
        if ps:
            rows = [o for o in rows if pay_bucket(o) in ps]

    total_revenue = sum(int(o.amount_paid or 0) for o in rows)
    gross = sum(int(o.price or 0) for o in rows)
    pending_balance = sum(int(o.balance or 0) for o in rows)

    now = date.today()
    week_start = now - timedelta(days=now.weekday())
    month_start = date(now.year, now.month, 1)
    year_start = date(now.year, 1, 1)

    def in_range_row(o: Order, a: date, b: date) -> bool:
        if not o.created_at:
            return False
        d = o.created_at.date()
        return a <= d <= b

    monthly_revenue = sum(
        int(o.amount_paid or 0) for o in rows if in_range_row(o, month_start, now)
    )
    weekly_revenue = sum(
        int(o.amount_paid or 0) for o in rows if in_range_row(o, week_start, now)
    )
    yearly_revenue = sum(
        int(o.amount_paid or 0) for o in rows if in_range_row(o, year_start, now)
    )

    paid_rev = sum(int(o.amount_paid or 0) for o in rows if pay_bucket(o) == "paid")
    partial_rev = sum(
        int(o.amount_paid or 0) for o in rows if pay_bucket(o) == "partial"
    )

    order_count = len(rows)
    aov = int(total_revenue / order_count) if order_count else 0

    # daily series for charts (max 90 points)
    by_day: dict[str, int] = defaultdict(int)
    for o in rows:
        if o.created_at:
            by_day[o.created_at.date().isoformat()] += int(o.amount_paid or 0)
    day_keys = sorted(by_day.keys())[-90:]
    revenue_by_day = [{"date": k, "revenue": by_day[k]} for k in day_keys]

    status_counts: dict[str, int] = defaultdict(int)
    for o in rows:
        status_counts[(o.status or "unknown").lower()] += 1

    # best sellers
    prod_qty: dict[str, int] = defaultdict(int)
    prod_rev: dict[str, int] = defaultdict(int)
    for o in rows:
        name = (o.product or "").strip() or "Unknown"
        prod_qty[name] += int(o.quantity or 1)
        prod_rev[name] += int(o.amount_paid or 0)
    bestsellers = sorted(
        [
            {"product": n, "units_sold": prod_qty[n], "revenue": prod_rev[n]}
            for n in prod_qty
        ],
        key=lambda x: x["units_sold"],
        reverse=True,
    )[:8]

    # top customers by revenue (need customer names)
    cust_rev: dict[int, int] = defaultdict(int)
    for o in rows:
        if o.customer_id:
            cust_rev[int(o.customer_id)] += int(o.amount_paid or 0)
    top_ids = sorted(cust_rev.keys(), key=lambda i: cust_rev[i], reverse=True)[:8]
    id_to_name: dict[int, str] = {}
    if top_ids:
        crows = (
            db.query(Customer.id, Customer.name)
            .filter(Customer.user_id == user_id, Customer.id.in_(top_ids))
            .all()
        )
        id_to_name = {int(cid): nm for cid, nm in crows}
    top_customers = [
        {
            "customer_id": cid,
            "name": id_to_name.get(cid, f"#{cid}"),
            "revenue": cust_rev[cid],
        }
        for cid in top_ids
    ]

    lows = (
        db.query(Product.name, Product.quantity_in_stock, Product.is_low_stock)
        .filter(Product.user_id == user_id)
        .filter(Product.is_low_stock == True)  # noqa: E712
        .limit(12)
        .all()
    )
    low_stock_items = [{"name": n, "quantity": int(q or 0)} for n, q, _ in lows]

    delivery_rows = [
        o
        for o in rows
        if (getattr(o, "fulfillment_type", None) or "delivery").lower() == "delivery"
    ]
    deliv_completed = sum(
        1 for o in delivery_rows if (o.status or "").lower() in {"delivered", "paid"}
    )
    delivery_success_rate = (
        round(100.0 * deliv_completed / len(delivery_rows), 1)
        if delivery_rows
        else None
    )

    growth_series = []
    for i in range(5, -1, -1):
        ref_m = now.month - i
        ref_y = now.year
        while ref_m <= 0:
            ref_m += 12
            ref_y -= 1
        label = date(ref_y, ref_m, 1).strftime("%Y-%m")
        start_m = datetime(ref_y, ref_m, 1)
        nm = ref_m + 1
        ny = ref_y
        if nm > 12:
            nm = 1
            ny += 1
        end_m = datetime(ny, nm, 1)
        cnt = int(
            db.query(func.count(Customer.id))
            .filter(
                Customer.user_id == user_id,
                Customer.created_at.isnot(None),
                Customer.created_at >= start_m,
                Customer.created_at < end_m,
            )
            .scalar()
            or 0
        )
        growth_series.append({"month": label, "new_customers": cnt})

    return {
        "range_start": start_dt.date().isoformat(),
        "range_end": (end_exclusive - timedelta(days=1)).date().isoformat(),
        "total_revenue": total_revenue,
        "monthly_revenue": monthly_revenue,
        "weekly_revenue": weekly_revenue,
        "yearly_revenue": yearly_revenue,
        "pending_balance_total": pending_balance,
        "gross_order_value": gross,
        "paid_revenue": paid_rev,
        "partial_revenue": partial_rev,
        "order_count": order_count,
        "average_order_value": aov,
        "status_breakdown": dict(status_counts),
        "revenue_by_day": revenue_by_day,
        "bestsellers": bestsellers,
        "top_customers": top_customers,
        "low_stock_items": low_stock_items,
        "delivery_success_rate": delivery_success_rate,
        "customer_growth": growth_series,
    }
