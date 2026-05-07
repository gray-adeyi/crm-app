from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Backward-compatible login credential shape."""

    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=6, max_length=256)


class VendorSignupRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=32)

    @field_validator("otp")
    @classmethod
    def _digits(cls, value: str) -> str:
        cleaned = "".join(ch for ch in str(value) if ch.isdigit())
        if len(cleaned) < 6:
            raise ValueError("Enter the six-digit verification code.")
        return cleaned[:8]


class ResendOtpRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignupResponse(BaseModel):
    verification_required: bool = True
    email: str
    message: str = "Verification code sent."
