"""Pydantic models for downloadable / scheduled SaaS summaries (optional endpoints)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: int | None
    summary: str | None
    created_at: datetime | None = None


class TransactionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    summary: str
    payload_json: str | None = None
    created_at: datetime | None = None


class LogsReportResponse(BaseModel):
    activity: list[ActivityLogOut]
    transactions: list[TransactionLogOut]


class ReportDayPoint(BaseModel):
    date: str
    revenue: int


class ReportBestsellerRow(BaseModel):
    product: str
    units_sold: int
    revenue: int


class ReportTopCustomer(BaseModel):
    customer_id: int
    name: str
    revenue: int


class ReportLowStockRow(BaseModel):
    name: str
    quantity: int


class ReportCustomerGrowthPoint(BaseModel):
    month: str
    new_customers: int


class ReportMonthlyDispatch(BaseModel):
    """Automated SaaS vendor report email journal entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    report_kind: str
    period_key: str
    sent_at: datetime | None = None


class ReportSummaryResponse(BaseModel):
    range_start: str
    range_end: str
    total_revenue: int
    monthly_revenue: int
    weekly_revenue: int
    yearly_revenue: int
    pending_balance_total: int
    gross_order_value: int
    paid_revenue: int
    partial_revenue: int
    order_count: int
    average_order_value: int
    status_breakdown: dict[str, int]
    revenue_by_day: list[ReportDayPoint]
    bestsellers: list[ReportBestsellerRow]
    top_customers: list[ReportTopCustomer]
    low_stock_items: list[ReportLowStockRow]
    delivery_success_rate: float | None = None
    customer_growth: list[ReportCustomerGrowthPoint]


class MonthlyDispatchListResponse(BaseModel):
    items: list[ReportMonthlyDispatch]
