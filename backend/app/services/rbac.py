from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException, status

from app.models import User

PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset(
        {
            "orders:read",
            "orders:write",
            "orders:delete",
            "customers:read",
            "customers:write",
            "customers:delete",
            "inventory:read",
            "inventory:write",
            "inventory:delete",
            "notifications:read",
            "notifications:write",
            "analytics:read",
            "billing:manage",
            "settings:write",
        }
    ),
    "staff": frozenset(
        {
            "orders:read",
            "orders:write",
            "orders:delete",
            "customers:read",
            "customers:write",
            "customers:delete",
            "inventory:read",
            "inventory:write",
            "notifications:read",
            "analytics:read",
        }
    ),
    "viewer": frozenset(
        {
            "orders:read",
            "customers:read",
            "analytics:read",
            "inventory:read",
            "notifications:read",
        }
    ),
}


def user_permissions(user: User) -> frozenset[str]:
    return PERMISSIONS.get((user.role or "staff").lower(), PERMISSIONS["viewer"])


def assert_permission(user: User, permission: str) -> None:
    if permission not in user_permissions(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


@dataclass
class PermissionGuard:
    """Callable dependency factory."""

    permission: str

    def __call__(self, user: User) -> User:
        assert_permission(user, self.permission)
        return user


def require_permission(permission: str) -> Callable[[User], User]:
    return PermissionGuard(permission)
