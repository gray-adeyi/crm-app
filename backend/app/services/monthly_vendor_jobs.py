"""Background batch jobs that email monthly summaries to every vendor inbox."""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session_ctx
from app.models import (
    Customer,
    Order,
    Product,
    TransactionLog,
    User,
    UserActivityLog,
    VendorReportDispatch,
)
from app.services.email_service import send_email
from app.services.email_templates import (
    build_activity_digest_email_html,
    build_saas_monthly_report_html,
)
from app.services.notification_prefs import is_email_enabled
from app.services.report_pdf import monthly_report_pdf_bytes

logger = logging.getLogger(__name__)


def previous_month(reference: date) -> tuple[date, date]:
    y, m = reference.year, reference.month
    if m == 1:
        y -= 1
        m = 12
    else:
        m -= 1
    start = date(y, m, 1)
    last = monthrange(y, m)[1]
    end = date(y, m, last)
    return start, end


def period_key(reference: date) -> str:
    start, _ = previous_month(reference)
    return start.strftime("%Y-%m")


def monthly_metrics(
    db, user_id: int, *, start_d: date, end_d: date, user_row: User
) -> dict:
    start_dt = datetime(start_d.year, start_d.month, start_d.day)
    end_exclusive = datetime(end_d.year, end_d.month, end_d.day) + timedelta(days=1)

    revenue_month = int(
        db.query(func.coalesce(func.sum(Order.amount_paid), 0))
        .filter(
            Order.user_id == user_id,
            Order.created_at.isnot(None),
            Order.created_at >= start_dt,
            Order.created_at < end_exclusive,
        )
        .scalar()
        or 0,
    )

    gross_month = int(
        db.query(func.coalesce(func.sum(Order.price), 0))
        .filter(
            Order.user_id == user_id,
            Order.created_at.isnot(None),
            Order.created_at >= start_dt,
            Order.created_at < end_exclusive,
        )
        .scalar()
        or 0
    )

    pending_balance = int(
        db.query(func.coalesce(func.sum(Order.balance), 0))
        .filter(Order.user_id == user_id)
        .scalar()
        or 0
    )

    def cnt_orders(where_status: str | None = None):
        q = db.query(func.count(Order.id)).filter(Order.user_id == user_id)
        q = q.filter(Order.created_at.isnot(None))
        q = q.filter(Order.created_at >= start_dt, Order.created_at < end_exclusive)
        if where_status:
            q = q.filter(Order.status == where_status)
        return int(q.scalar() or 0)

    total_customers = int(
        db.query(func.count(Customer.id)).filter(Customer.user_id == user_id).scalar()
        or 0
    )

    low_stock = (
        db.query(func.count(Product.id))
        .filter(Product.user_id == user_id, Product.is_low_stock == True)  # noqa: E712
        .scalar()
        or 0
    )

    bestsellers = (
        db.query(Order.product, func.sum(Order.quantity).label("sold"))
        .filter(
            Order.user_id == user_id,
            Order.created_at.isnot(None),
            Order.created_at >= start_dt,
            Order.created_at < end_exclusive,
        )
        .group_by(Order.product)
        .order_by(func.sum(Order.quantity).desc())
        .limit(5)
        .all()
    )

    lows = (
        db.query(Product.name, Product.quantity_in_stock)
        .filter(
            Product.user_id == user_id,
            Product.quantity_in_stock > 0,
            Product.is_low_stock == True,
        )  # noqa: E712
        .limit(10)
        .all()
    )

    return {
        "revenue_month": revenue_month,
        "orders_month": cnt_orders(None),
        "orders_paid": cnt_orders("paid"),
        "orders_partial": cnt_orders("partial"),
        "orders_pending": cnt_orders("pending"),
        "orders_cancelled": cnt_orders("cancelled"),
        "pending_balance": pending_balance,
        "total_customers": total_customers,
        "gross_sales_month": int(gross_month),
        "low_stock": int(low_stock),
        "subscription_status": user_row.subscription_status or "inactive",
        "plan": user_row.current_plan or user_row.subscription_plan or "starter",
        "bestsellers": list(bestsellers),
        "low_stock_rows": [{"name": n, "qty": int(q)} for n, q in lows],
        "trial_active": getattr(user_row, "is_trial_active", False),
    }


async def _already_sent(
    db: AsyncSession, *, user_id: int, period: str, kind: str
) -> bool:
    stmt = select(VendorReportDispatch).where(
        VendorReportDispatch.user_id == user_id,
        VendorReportDispatch.period_key == period,
        VendorReportDispatch.report_kind == kind,
    )
    return (await db.execute(stmt)).scalar_one_or_none() is None


def _mark_sent(db, *, user_id: int, period: str, kind: str) -> None:
    db.add(VendorReportDispatch(user_id=user_id, report_kind=kind, period_key=period))


def digest_logs(
    db, user_id: int, *, start_dt: datetime, end_dt: datetime
) -> tuple[list, list]:
    acts = (
        db.query(UserActivityLog)
        .filter(
            UserActivityLog.user_id == user_id,
            UserActivityLog.created_at >= start_dt,
            UserActivityLog.created_at < end_dt,
        )
        .order_by(UserActivityLog.id.desc())
        .limit(200)
        .all()
    )
    txs = (
        db.query(TransactionLog)
        .filter(
            TransactionLog.user_id == user_id,
            TransactionLog.created_at >= start_dt,
            TransactionLog.created_at < end_dt,
        )
        .order_by(TransactionLog.id.desc())
        .limit(200)
        .all()
    )
    return acts, txs


async def run_monthly_vendor_jobs(*, anchor: date | None = None) -> None:
    """
    Executes at the beginning of each month — generates reports for the
    previous calendar month.
    """
    ref = anchor or date.today()
    prev_start, prev_end = previous_month(ref)
    pkey = period_key(ref)

    logger.info("Running monthly vendor jobs for period=%s", pkey)
    async with get_db_session_ctx() as db:
        try:
            users = db.query(User).order_by(User.id.asc()).all()
            start_dt = datetime(prev_start.year, prev_start.month, prev_start.day)
            end_exclusive = datetime(
                prev_end.year, prev_end.month, prev_end.day
            ) + timedelta(days=1)

            for u in users:
                if not u.email:
                    continue
                metrics = monthly_metrics(
                    db, u.id, start_d=prev_start, end_d=prev_end, user_row=u
                )

                if is_email_enabled(u, "monthly_report") and not (
                    await _already_sent(
                        db, user_id=u.id, period=pkey, kind="monthly_business"
                    )
                ):
                    label = prev_start.strftime("%B %Y")
                    html = build_saas_monthly_report_html(
                        user=u, metrics=metrics, month_label=label
                    )
                    pdf = monthly_report_pdf_bytes(
                        business_name=u.business_name or "Your business",
                        period_label=label,
                        metrics=metrics,
                    )
                    attachments = [
                        {
                            "filename": f"vendora-report-{pkey}.pdf",
                            "content": pdf,
                            "content_type": "application/pdf",
                        }
                    ]
                    try:
                        await send_email(
                            subject=f"Your monthly business insights — {label}",
                            to_email=u.email,
                            html=html,
                            attachments=attachments,
                        )
                        _mark_sent(
                            db, user_id=u.id, period=pkey, kind="monthly_business"
                        )
                        await db.commit()
                    except Exception:
                        await db.rollback()
                        logger.exception(
                            "Monthly business mail failed user_id=%s", u.id
                        )

                if is_email_enabled(u, "activity_summary") and not (
                    await _already_sent(
                        db, user_id=u.id, period=pkey, kind="activity_summary"
                    )
                ):
                    acts, txs = digest_logs(
                        db, u.id, start_dt=start_dt, end_dt=end_exclusive
                    )
                    label = prev_start.strftime("%B %Y")
                    html = build_activity_digest_email_html(
                        user=u, acts=acts, txs=txs, month_label=label
                    )
                    try:
                        await send_email(
                            subject=f"Vendor activity recap — {label}",
                            to_email=u.email,
                            html=html,
                        )
                        _mark_sent(
                            db, user_id=u.id, period=pkey, kind="activity_summary"
                        )
                        await db.commit()
                    except Exception:
                        await db.rollback()
                        logger.exception("Activity digest mail failed user_id=%s", u.id)
        finally:
            await db.close()


async def enqueue_monthly_vendor_jobs() -> None:
    """Thin wrapper invoked by APScheduler inside the API process."""

    try:
        await run_monthly_vendor_jobs()
    except Exception:
        logger.exception("Monthly vendor batch failed")
