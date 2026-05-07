import os
from functools import lru_cache


class Settings:
    """Centralized configuration (env-first, PostgreSQL-ready DATABASE_URL)."""

    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "15"))
    OTP_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "8"))
    PUBLIC_SUPPORT_EMAIL: str = os.getenv("PUBLIC_SUPPORT_EMAIL", "support@vendora.app")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-change-me-use-env-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    FRONTEND_ORIGINS: tuple[str, ...] = tuple(
        o.strip()
        for o in os.getenv(
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173,http://localhost:4173",
        ).split(",")
        if o.strip()
    )

    PUBLIC_APP_URL: str = os.getenv("PUBLIC_APP_URL", "http://localhost:5173")

    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_WEBHOOK_SECRET: str = os.getenv("PAYSTACK_WEBHOOK_SECRET", "")
    PAYSTACK_BASE_URL: str = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
    PAYSTACK_CALLBACK_URL: str = os.getenv("PAYSTACK_CALLBACK_URL", "http://localhost:5173/billing/success")
    BILLING_RETURN_URL: str = os.getenv("BILLING_RETURN_URL", "http://localhost:5173/billing")
    BILLING_GRACE_DAYS: int = int(os.getenv("BILLING_GRACE_DAYS", "3"))
    FLUTTERWAVE_SECRET_HASH: str = os.getenv("FLUTTERWAVE_SECRET_HASH", "")

    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TERMII_API_KEY: str = os.getenv("TERMII_API_KEY", "")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "") or os.getenv("EMAIL_FROM", "noreply@example.com")
    # Back-compat for earlier env naming
    EMAIL_FROM: str = SMTP_FROM

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM: str = os.getenv("RESEND_FROM", "") or os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    MAILGUN_API_KEY: str = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN: str = os.getenv("MAILGUN_DOMAIN", "")
    MAILGUN_API_BASE: str = os.getenv("MAILGUN_API_BASE", "https://api.mailgun.net")
    MAILGUN_FROM: str = os.getenv("MAILGUN_FROM", "") or os.getenv("EMAIL_FROM", "")

    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "") or os.getenv("EMAIL_FROM", "noreply@example.com")
    SENDGRID_FROM_NAME: str = os.getenv("SENDGRID_FROM_NAME", "Vendora")


@lru_cache
def get_settings() -> Settings:
    return Settings()
