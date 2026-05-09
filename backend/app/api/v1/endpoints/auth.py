import asyncio
import logging
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import AsyncDBSession
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.core.utils import aware_datetime_now
from app.models import User
from app.schemas.auth import (
    ResendOtpRequest,
    SignupResponse,
    TokenResponse,
    UserCreate,
    VendorSignupRequest,
    VerifyEmailRequest,
)
from app.services.email_service import send_email
from app.services.email_templates import build_verification_otp_email_html
from app.services.email_verification_service import (
    issue_email_verification_token,
    verify_email_otp,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def _send_otp_email_async(
    *, otp_plain: str, to_email: str, company_name: str | None
) -> None:
    html = build_verification_otp_email_html(
        company_name=company_name,
        email=to_email,
        otp_code=otp_plain,
        expires_minutes=settings.OTP_EXPIRE_MINUTES,
        support_email=settings.PUBLIC_SUPPORT_EMAIL,
        app_url=settings.PUBLIC_APP_URL.rstrip("/"),
    )
    asyncio.run(
        send_email(
            subject="Verify your Vendora email",
            to_email=to_email,
            html=html,
        )
    )


async def _welcome_task(user_id: UUID) -> None:
    try:
        from app.services.welcome_email import send_vendor_welcome_email

        await send_vendor_welcome_email(user_id)
    except Exception:
        logger.exception("Welcome email failed user_id=%s", user_id)


@router.post("/signup", response_model=SignupResponse)
async def signup(
    user: VendorSignupRequest, db: AsyncDBSession, background_tasks: BackgroundTasks
):
    hashed = hash_password(user.password)
    trial_start = aware_datetime_now()
    trial_end = trial_start + timedelta(days=30)
    new_user = User(
        email=str(user.email).lower().strip(),
        password=hashed,
        role="admin",
        subscription_plan="starter",
        current_plan="starter",
        subscription_status="trial",
        billing_cycle="monthly",
        trial_started_at=trial_start,
        trial_ends_at=trial_end,
        trial_end_date=trial_end,
        currency="NGN",
        onboarding_completed=False,
        business_name=user.company_name.strip(),
        email_verified=False,
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    await db.refresh(new_user)

    try:
        otp_plain = await issue_email_verification_token(
            db, user_id=new_user.id, email=new_user.email, force_new=True
        )
    except HTTPException as exc:
        logger.warning("OTP issue failed for signup: %s", exc.detail)
        raise

    background_tasks.add_task(
        _send_otp_email_async,
        otp_plain=otp_plain,
        to_email=new_user.email,
        company_name=new_user.business_name,
    )

    return SignupResponse(
        verification_required=True,
        email=new_user.email,
        message="We sent a verification code to your inbox.",
    )


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    payload: VerifyEmailRequest, db: AsyncDBSession, background_tasks: BackgroundTasks
):
    user = await verify_email_otp(db, email=str(payload.email), otp_plain=payload.otp)
    background_tasks.add_task(_welcome_task, user.id)
    token_str = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token_str, token_type="bearer")


@router.post("/resend-verification")
async def resend_verification(
    payload: ResendOtpRequest, db: AsyncDBSession, background_tasks: BackgroundTasks
):
    email = str(payload.email).lower().strip()
    stmt = select(User).where(User.email == email)
    db_user = (await db.execute(stmt)).scalar_one_or_none()
    if not db_user:
        return {"message": "If that email is registered, we sent a code."}
    if db_user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified.")

    try:
        otp_plain = await issue_email_verification_token(
            db, user_id=db_user.id, email=db_user.email, force_new=False
        )
    except HTTPException:
        raise

    background_tasks.add_task(
        _send_otp_email_async,
        otp_plain=otp_plain,
        to_email=db_user.email,
        company_name=db_user.business_name,
    )

    return {"message": "Verification code sent."}


@router.post("/login", response_model=TokenResponse)
async def login(user: UserCreate, db: AsyncDBSession):
    email = user.email.lower().strip()
    stmt = select(User).where(User.email == email)
    db_user = (await db.execute(stmt)).scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not getattr(db_user, "email_verified", True):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Verify your email address to access Vendora.",
                "email": db_user.email,
            },
        )
    token_str = create_access_token({"user_id": db_user.id})
    return TokenResponse(access_token=token_str, token_type="bearer")
