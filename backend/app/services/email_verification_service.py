"""Signup email OTP issuance, cooldown, brute-force exhaustion, hashed storage."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import aware_datetime_now
from app.models import EmailVerificationToken, User


def _otp_digest(otp_plain: str) -> str:
    pepper = (settings.JWT_SECRET_KEY + ":vendora-otp:v1").encode("utf-8")
    body = otp_plain.strip().encode("utf-8")
    return hmac.new(pepper, body, hashlib.sha256).hexdigest()


def _otp_matches(otp_plain: str, stored: str) -> bool:
    return hmac.compare_digest(_otp_digest(otp_plain), stored)


def _norm_email(email: str) -> str:
    return (email or "").lower().strip()


def generate_numeric_otp(digits: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(int(digits)))


async def deactivate_unconsumed_tokens(db: AsyncSession, *, email: str) -> None:
    em = _norm_email(email)
    now = aware_datetime_now()
    stmt = (
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.email == em,
            EmailVerificationToken.consumed_at.is_(None),
        )
        .values(consumed_at=now, synchronize_session=False)
    )
    await db.execute(stmt)


async def latest_any_token(
    db: AsyncSession, *, email: str
) -> EmailVerificationToken | None:
    em = _norm_email(email)
    stmt = (
        select(EmailVerificationToken)
        .where(EmailVerificationToken.email == em)
        .order_by(EmailVerificationToken.id.desc())
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def latest_verifiable_token(
    db: AsyncSession, *, email: str
) -> EmailVerificationToken | None:
    em = _norm_email(email)
    now = aware_datetime_now()
    stmt = (
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.email == em,
            EmailVerificationToken.consumed_at.is_(None),
            EmailVerificationToken.expires_at >= now,
        )
        .order_by(EmailVerificationToken.created_at.desc())
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def issue_email_verification_token(
    db: AsyncSession, *, user_id: UUID, email: str, force_new: bool = False
) -> str:
    now = aware_datetime_now()
    em = _norm_email(email)

    if not force_new:
        cooldown = timedelta(seconds=max(5, settings.OTP_RESEND_COOLDOWN_SECONDS))
        last_any = await latest_any_token(db, email=em)
        if (
            last_any
            and last_any.last_sent_at
            and last_any.last_sent_at + cooldown > now
        ):
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "OTP_COOLDOWN",
                    "message": "Please wait before requesting another code.",
                    "retry_after_sec": settings.OTP_RESEND_COOLDOWN_SECONDS,
                },
            )

    otp_plain = generate_numeric_otp(6)
    await deactivate_unconsumed_tokens(db, email=em)
    expires = now + timedelta(minutes=max(5, settings.OTP_EXPIRE_MINUTES))
    row = EmailVerificationToken(
        email=em,
        user_id=user_id,
        otp_hash=_otp_digest(otp_plain),
        expires_at=expires,
        failed_attempts=0,
        last_sent_at=now,
    )
    db.add(row)
    await db.commit()
    return otp_plain


async def verify_email_otp(db: AsyncSession, *, email: str, otp_plain: str) -> User:
    now = aware_datetime_now()
    em = _norm_email(email)
    row = await latest_verifiable_token(db, email=em)
    if not row:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "OTP_INVALID",
                "message": "No active verification code. Request a new one.",
            },
        )

    if int(row.failed_attempts or 0) >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "OTP_LOCKED",
                "message": "Too many attempts. Request a new code.",
            },
        )

    if not _otp_matches(otp_plain.strip(), row.otp_hash):
        row.failed_attempts = int(row.failed_attempts or 0) + 1
        db.add(row)
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail={"code": "OTP_INVALID", "message": "Incorrect verification code."},
        )

    stmt = select(User).where(User.id == row.user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.email_verified = True
    row.consumed_at = now
    db.add(user)
    db.add(row)
    await db.commit()
    await db.refresh(user)
    return user
