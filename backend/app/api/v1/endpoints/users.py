from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.deps import AsyncDBSession, CurrentUser
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.user import (
    EmailChangeRequest,
    MeResponse,
    OnboardingUpdate,
    PasswordChangeRequest,
    UserProfileUpdate,
)
from app.services.notification_prefs import serialize_prefs

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=MeResponse)
def me(user: CurrentUser):
    return MeResponse.model_validate(user)


@router.patch("/users/me", response_model=MeResponse)
async def update_profile(
    payload: UserProfileUpdate, db: AsyncDBSession, user: CurrentUser
):
    if payload.business_name is not None:
        user.business_name = payload.business_name.strip() or None
    if payload.currency is not None:
        user.currency = payload.currency.strip().upper()
    if payload.logo_url is not None:
        user.logo_url = payload.logo_url.strip() or None
    if payload.business_phone is not None:
        user.business_phone = payload.business_phone.strip() or None
    if payload.business_address is not None:
        user.business_address = payload.business_address.strip() or None
    if payload.notification_preferences is not None:
        user.notification_preferences = serialize_prefs(
            payload.notification_preferences
        )

    db.commit()
    db.refresh(user)
    return MeResponse.model_validate(user)


@router.post("/users/me/onboarding", response_model=MeResponse)
async def complete_onboarding(
    payload: OnboardingUpdate, db: AsyncDBSession, user: CurrentUser
):
    user.business_name = payload.business_name.strip()
    user.currency = payload.currency.strip().upper()
    user.logo_url = payload.logo_url.strip() if payload.logo_url else None
    user.onboarding_completed = payload.onboarding_completed
    db.commit()
    db.refresh(user)
    return MeResponse.model_validate(user)


@router.post("/users/me/password", response_model=MeResponse)
async def change_password(
    payload: PasswordChangeRequest, db: AsyncDBSession, user: CurrentUser
):
    if not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return MeResponse.model_validate(user)


@router.post("/users/me/email", response_model=MeResponse)
async def change_email(
    payload: EmailChangeRequest, db: AsyncDBSession, user: CurrentUser
):
    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    new_email = str(payload.new_email).lower().strip()
    if new_email == user.email:
        raise HTTPException(status_code=400, detail="You are already using this email")
    exists = db.query(User).filter(User.email == new_email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email is already registered")
    user.email = new_email
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email is already registered")
    return MeResponse.model_validate(user)


@router.get("/users/me/preview")
def whoami(user: CurrentUser):
    return {"user_id": user.id, "email": user.email}
