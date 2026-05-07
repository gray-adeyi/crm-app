from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.entities import User
from app.services.subscription_access import ensure_saas_access


def _get_token_raw(
    authorization: Optional[str] = Header(None),
    token_legacy: Optional[str] = Header(None, alias="token"),
) -> Optional[str]:
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    return token_legacy


def require_user_id(access_token_raw: Annotated[Optional[str], Depends(_get_token_raw)]) -> int:
    if not access_token_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication")
    try:
        payload = decode_token(access_token_raw)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return int(user_id)
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(user_id: Annotated[int, Depends(require_user_id)], db: Annotated[Session, Depends(get_db)]) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user context")
    if not getattr(user, "email_verified", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Verify your email address to continue.",
                "email": user.email,
            },
        )
    return user


DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Depends(require_user_id)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_saas_entitlement(db: Annotated[Session, Depends(get_db)], user: CurrentUser) -> User:
    ensure_saas_access(db, user)
    return user


SaasUser = Annotated[User, Depends(require_saas_entitlement)]
