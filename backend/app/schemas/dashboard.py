from uuid import UUID

from pydantic import BaseModel


class RecentOrderDTO(BaseModel):
    id: UUID
    product: str
    total_price: int
    amount_paid: int
    balance: int
    status: str
    customer_id: int
    customer_name: str | None = None


class MonthlyRevenuePoint(BaseModel):
    month: str
    revenue: int
    orders: int


class CustomerGrowthPoint(BaseModel):
    month: str
    new_customers: int


class DashboardResponse(BaseModel):
    total_customers: int
    total_orders: int
    total_revenue: int
    gross_sales: int
    outstanding_balance: int

    monthly_revenue: int
    orders_pending: int
    orders_partial: int
    orders_paid: int
    mrr: int
    active_subscriptions: int
    failed_payments: int
    churn_rate: float

    revenue_by_month: list[MonthlyRevenuePoint]
    customer_growth: list[CustomerGrowthPoint]
    recent_orders: list[RecentOrderDTO]

    # deliveries / reminders
    upcoming_deliveries: list["DeliveryDTO"] = []
    todays_deliveries: list["DeliveryDTO"] = []
    overdue_deliveries: list["DeliveryDTO"] = []

    pickups_ready: list["DeliveryDTO"] = []
    completed_deliveries: list["DeliveryDTO"] = []

    # notifications + inventory
    unread_notifications: int = 0
    total_inventory_value: int = 0
    low_stock_items: int = 0
    out_of_stock_items: int = 0

    # plan / subscription UX
    analytics_limited: bool = False


class DeliveryDTO(BaseModel):
    id: UUID
    customer_name: str | None = None
    product: str
    quantity: int
    status: str
    fulfillment_type: str | None = "delivery"
    delivery_address: str | None = None
    delivery_date: str | None = None
    delivery_time: str | None = None


DashboardResponse.model_rebuild()
