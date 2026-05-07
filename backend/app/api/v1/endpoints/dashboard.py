from fastapi import APIRouter

from app.api.deps import DbSession, SaasUser
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import build_dashboard
from app.services.rbac import assert_permission

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: DbSession, user: SaasUser):
    assert_permission(user, "analytics:read")
    return build_dashboard(db, user)
