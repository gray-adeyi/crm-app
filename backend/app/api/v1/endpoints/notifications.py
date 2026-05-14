from fastapi import APIRouter, HTTPException, status
from sqlalchemy import false, select, func, update

from app.api.deps import AsyncDBSession, SaasUser
from app.models import Notification
from app.schemas.notification import NotificationMarkReadRequest, NotificationResponse
from app.services.rbac import assert_permission

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: AsyncDBSession, user: SaasUser, unread_only: bool = False, limit: int = 300
):
    assert_permission(user, "notifications:read")
    limit = max(10, min(int(limit), 500))
    stmt = select(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == false())
    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    return [NotificationResponse.model_validate(r) for r in rows]


@router.get("/counts")
async def notification_counts(db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "notifications:read")
    stmt = select(func.count(Notification.id)).where(Notification.user_id == user.id)
    total = (await db.execute(stmt)).scalar()
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user.id, Notification.is_read == False
    )
    unread = (await db.execute(stmt)).scalar()
    return {"total": total, "unread": unread}


@router.post("/mark-read")
async def mark_read(
    payload: NotificationMarkReadRequest, db: AsyncDBSession, user: SaasUser
):
    assert_permission(user, "notifications:write")
    if not payload.ids:
        return {"message": "No ids"}
    stmt = (
        update(Notification)
        .where(Notification.user_id == user.id, Notification.id.in_(payload.ids))
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "OK"}


@router.post("/mark-all-read")
async def mark_all_read(db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "notifications:write")
    stmt = (
        update(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == false)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "OK"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: int, db: AsyncDBSession, user: SaasUser):
    assert_permission(user, "notifications:write")
    stmt = select(Notification).where(
        Notification.id == notification_id, Notification.user_id == user.id
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.delete(row)
    await db.commit()
