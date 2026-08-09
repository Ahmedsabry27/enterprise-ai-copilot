from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.database.models.audit import AuditLog
from app.tool_sdk.errors import redact


def _safe(value: Any) -> dict | None:
    if value is None:
        return None
    safe = redact(value)
    if isinstance(safe, dict):
        return safe
    return {"value": safe}


def append_audit_event(
    db: Session,
    *,
    tenant_id: str,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    correlation_id: str | None = None,
    before: Any = None,
    after: Any = None,
    metadata: Any = None,
) -> AuditLog:
    """Append a sanitized event without committing the caller's transaction."""
    now = datetime.now(UTC)
    event = AuditLog(
        tenant_id=tenant_id,
        user_id=actor_id,
        event_type=action,
        entity=target_type,
        entity_id=target_id,
        timestamp=now,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        correlation_id=correlation_id,
        before_summary=_safe(before),
        after_summary=_safe(after),
        metadata_json=_safe(metadata),
        created_at=now,
    )
    db.add(event)
    return event
