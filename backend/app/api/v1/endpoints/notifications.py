from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, false

from app.api.deps import DbSession, SaasUser
from app.models.entities import Notification
from app.schemas.notification import NotificationMarkReadRequest, NotificationResponse
from app.services.rbac import assert_permission

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(db: DbSession, user: SaasUser, unread_only: bool = False, limit: int = 300):
    assert_permission(user, "notifications:read")
    limit = max(10, min(int(limit), 500))
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read == false())
    rows = (
        q.order_by(desc(Notification.id))
        .limit(limit)
        .all()
    )
    return [NotificationResponse.model_validate(r) for r in rows]


@router.get("/counts")
def notification_counts(db: DbSession, user: SaasUser):
    assert_permission(user, "notifications:read")
    total = db.query(Notification).filter(Notification.user_id == user.id).count()
    unread = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == false()).count()
    return {"total": total, "unread": unread}


@router.post("/mark-read")
def mark_read(payload: NotificationMarkReadRequest, db: DbSession, user: SaasUser):
    assert_permission(user, "notifications:write")
    if not payload.ids:
        return {"message": "No ids"}
    (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.id.in_(payload.ids))
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return {"message": "OK"}


@router.post("/mark-all-read")
def mark_all_read(db: DbSession, user: SaasUser):
    assert_permission(user, "notifications:write")
    (
        db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == false()).update(
            {Notification.is_read: True}, synchronize_session=False
        )
    )
    db.commit()
    return {"message": "OK"}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: DbSession, user: SaasUser):
    assert_permission(user, "notifications:write")
    row = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
