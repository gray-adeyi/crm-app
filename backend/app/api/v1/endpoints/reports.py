from fastapi import APIRouter, Query
from sqlalchemy import desc

from app.api.deps import DbSession, SaasUser
from app.models.entities import TransactionLog, UserActivityLog, VendorReportDispatch
from app.schemas.reports import (
    ActivityLogOut,
    LogsReportResponse,
    MonthlyDispatchListResponse,
    ReportMonthlyDispatch,
    ReportSummaryResponse,
    TransactionLogOut,
)
from app.services.rbac import assert_permission
from app.services.report_analytics_service import build_report_summary

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/logs", response_model=LogsReportResponse)
def vendor_logs(db: DbSession, user: SaasUser, limit: int = Query(default=250, ge=1, le=1000)):
    assert_permission(user, "analytics:read")
    acts = (
        db.query(UserActivityLog)
        .filter(UserActivityLog.user_id == user.id)
        .order_by(desc(UserActivityLog.id))
        .limit(limit)
        .all()
    )
    txs = (
        db.query(TransactionLog)
        .filter(TransactionLog.user_id == user.id)
        .order_by(desc(TransactionLog.id))
        .limit(limit)
        .all()
    )
    return LogsReportResponse(
        activity=[ActivityLogOut.model_validate(r) for r in acts],
        transactions=[TransactionLogOut.model_validate(r) for r in txs],
    )


@router.get("/summary", response_model=ReportSummaryResponse)
def reports_summary(
    db: DbSession,
    user: SaasUser,
    date_from: str | None = Query(default=None, max_length=32),
    date_to: str | None = Query(default=None, max_length=32),
    order_status: list[str] | None = Query(default=None),
    payment_status: list[str] | None = Query(default=None),
    customer_id: int | None = Query(default=None, ge=1),
):
    assert_permission(user, "analytics:read")
    summary = build_report_summary(
        db,
        user_id=user.id,
        date_from=date_from,
        date_to=date_to,
        order_statuses=order_status,
        payment_statuses=payment_status,
        customer_id=customer_id,
    )
    return ReportSummaryResponse.model_validate(summary)


@router.get("/monthly-dispatches", response_model=MonthlyDispatchListResponse)
def monthly_dispatches(db: DbSession, user: SaasUser):
    assert_permission(user, "analytics:read")
    rows = (
        db.query(VendorReportDispatch)
        .filter(VendorReportDispatch.user_id == user.id)
        .order_by(desc(VendorReportDispatch.id))
        .limit(48)
        .all()
    )
    return MonthlyDispatchListResponse(items=[ReportMonthlyDispatch.model_validate(r) for r in rows])
