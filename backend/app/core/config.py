from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS]

    OTP_EXPIRE_MINUTES: int = Field(15)
    OTP_RESEND_COOLDOWN_SECONDS: int = Field(60)
    OTP_MAX_ATTEMPTS: int = Field(8)
    PUBLIC_SUPPORT_EMAIL: str = Field("support@vendora.app")

    JWT_SECRET_KEY: str = Field("dev-change-me-use-env-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(1440)

    PUBLIC_APP_URL: str = Field("http://localhost:5173")

    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    PAYSTACK_WEBHOOK_SECRET: str
    PAYSTACK_BASE_URL: str = Field("https://api.paystack.co")
    PAYSTACK_CALLBACK_URL: str = Field("http://localhost:5173/billing/success")

    BILLING_GRACE_DAYS: int = Field(3)
    FLUTTERWAVE_SECRET_HASH: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TERMII_API_KEY: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    # Back-compat for earlier env naming
    EMAIL_FROM: str

    RESEND_API_KEY: str
    RESEND_FROM: str = Field("onboarding@resend.dev")

    MAILGUN_API_KEY: str
    MAILGUN_DOMAIN: str
    MAILGUN_API_BASE: str = Field("https://api.mailgun.net")
    MAILGUN_FROM: str

    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    SENDGRID_FROM_NAME: str = Field("Vendora")

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    TIMEZONE: str = "Africa/Lagos"


settings = Settings()  # type: ignore
