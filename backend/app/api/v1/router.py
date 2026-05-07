from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    billing,
    customers,
    dashboard,
    health,
    inventory,
    notifications,
    orders,
    reports,
    users,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(orders.router)
api_router.include_router(inventory.router)
api_router.include_router(notifications.router)
api_router.include_router(dashboard.router)
api_router.include_router(billing.router)
api_router.include_router(reports.router)
api_router.include_router(webhooks.router)
