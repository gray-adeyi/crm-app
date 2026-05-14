"""Append-only activity + transaction logs for dashboards and vendor digests."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionLog, UserActivityLog


def log_user_activity(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    row = UserActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_json=json.dumps(metadata, default=str) if metadata else None,
    )
    db.add(row)


def log_transaction_event(
    db: AsyncSession,
    *,
    user_id: UUID,
    category: str,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> None:
    row = TransactionLog(
        user_id=user_id,
        category=category,
        summary=summary,
        payload_json=json.dumps(payload, default=str) if payload else None,
    )
    db.add(row)
