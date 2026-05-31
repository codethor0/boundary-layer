"""Tenant, membership, and audit helpers for Production SaaS."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, status

from apps.api.auth import LOCAL_LAB_TENANT_ID, AuthContext
from apps.api.config import Settings
from apps.api.db import get_connection

logger = logging.getLogger("boundary_layer.api.tenancy")

TENANT_REDIS_PREFIX = "boundary_layer:tenant"

TENANCY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  subject TEXT NOT NULL UNIQUE,
  email TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_memberships (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS tenant_memberships_tenant_user_idx
  ON tenant_memberships (tenant_id, user_id);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  actor_subject TEXT,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  result TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_events_tenant_created_idx
  ON audit_events (tenant_id, created_at DESC);
"""


class TenancyError(Exception):
    """Tenancy persistence failure."""


def init_tenancy_schema() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TENANCY_SCHEMA_SQL)


def upsert_tenant(tenant_id: str, name: str, status: str = "active") -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tenants (id, name, status)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name, status = EXCLUDED.status
                """,
                (tenant_id, name, status),
            )


def upsert_user(user_id: str, subject: str, email: str | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, subject, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (subject) DO UPDATE
                SET email = EXCLUDED.email
                """,
                (user_id, subject, email),
            )


def upsert_membership(
    membership_id: str,
    tenant_id: str,
    user_id: str,
    role: str,
    status: str = "active",
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tenant_memberships (id, tenant_id, user_id, role, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET role = EXCLUDED.role, status = EXCLUDED.status
                """,
                (membership_id, tenant_id, user_id, role, status),
            )


def get_user_id_by_subject(subject: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM users WHERE subject = %s
                """,
                (subject,),
            )
            row = cur.fetchone()
    return row[0] if row else None


def get_membership(tenant_id: str, subject: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tm.id, tm.tenant_id, tm.user_id, tm.role, tm.status
                FROM tenant_memberships tm
                JOIN users u ON u.id = tm.user_id
                WHERE tm.tenant_id = %s AND u.subject = %s
                """,
                (tenant_id, subject),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "tenant_id": row[1],
        "user_id": row[2],
        "role": row[3],
        "status": row[4],
    }


def require_active_membership(
    tenant_id: str,
    subject: str,
    settings: Settings,
) -> dict[str, Any]:
    if not settings.is_production_saas:
        return {}
    try:
        membership = get_membership(tenant_id, subject)
    except Exception as exc:
        logger.exception("membership lookup failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant membership service unavailable",
        ) from exc
    if membership is None or membership.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active tenant membership required",
        )
    return membership


def insert_audit_event(
    action: str,
    result: str,
    tenant_id: str | None = None,
    actor_subject: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    event_id = f"audit-{uuid.uuid4().hex}"
    metadata_json = json.dumps(metadata or {})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_events (
                  id, tenant_id, actor_subject, action, resource_type,
                  resource_id, result, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    event_id,
                    tenant_id,
                    actor_subject,
                    action,
                    resource_type,
                    resource_id,
                    result,
                    metadata_json,
                ),
            )
    return event_id


def list_audit_events_for_tenant(
    tenant_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, actor_subject, action, resource_type,
                       resource_id, result, metadata, created_at
                FROM audit_events
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (tenant_id, limit),
            )
            rows = cur.fetchall()
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                "id": row[0],
                "tenant_id": row[1],
                "actor_subject": row[2],
                "action": row[3],
                "resource_type": row[4],
                "resource_id": row[5],
                "result": row[6],
                "metadata": row[7],
                "created_at": row[8].isoformat(),
            }
        )
    return events


def build_tenant_redis_key(tenant_id: str, lab_name: str, key: str) -> str:
    """Build a tenant-scoped Redis key for production SaaS isolation."""
    normalized_tenant = normalize_lab_tenant_id(tenant_id)
    normalized_lab = lab_name.strip().replace(":", "_")
    normalized_key = key.strip().lstrip(":")
    return (
        f"{TENANT_REDIS_PREFIX}:{normalized_tenant}:lab:"
        f"{normalized_lab}:{normalized_key}"
    )


def normalize_lab_tenant_id(tenant_id: str | None) -> str:
    if tenant_id and tenant_id.strip():
        return tenant_id.strip()
    return LOCAL_LAB_TENANT_ID


def assert_tenant_scope(tenant_id: str | None, settings: Settings) -> str:
    normalized = normalize_lab_tenant_id(tenant_id)
    if settings.is_production_saas and not tenant_id:
        raise ValueError("tenant_id is required in production-saas database paths")
    return normalized


def require_same_tenant_or_admin(
    settings: Settings,
    auth_context: AuthContext,
    target_tenant_id: str,
) -> None:
    target = normalize_lab_tenant_id(target_tenant_id)
    if auth_context.is_platform_admin():
        return
    if auth_context.tenant_id != target:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )


def record_tenant_access_denied(
    settings: Settings,
    reason: str,
    auth_context: AuthContext | None = None,
    requested_tenant_id: str | None = None,
) -> None:
    from apps.api.metrics import (
        record_auth_decision,
        record_tenant_access_denied_metric,
    )

    record_tenant_access_denied_metric(reason)
    record_auth_decision("denied", reason)
    record_auth_audit_event(
        settings,
        action="auth_cross_tenant_denied",
        result="denied",
        tenant_id=auth_context.tenant_id if auth_context else None,
        actor_subject=auth_context.subject if auth_context else None,
        metadata={
            "reason": reason,
            "requested_tenant_id": requested_tenant_id,
        },
    )


def record_auth_audit_event(
    settings: Settings,
    action: str,
    result: str,
    tenant_id: str | None = None,
    actor_subject: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    if not settings.audit_log_enabled:
        return None
    if not settings.is_production_saas:
        return None
    try:
        event_id = insert_audit_event(
            action=action,
            result=result,
            tenant_id=tenant_id,
            actor_subject=actor_subject,
            resource_type="auth",
            metadata=metadata,
        )
        from apps.api.metrics import record_audit_event_metric, record_auth_decision

        record_audit_event_metric(action, result)
        if action == "auth_allowed":
            record_auth_decision("allowed", "authenticated")
        elif action.startswith("auth_"):
            record_auth_decision("denied", action.removeprefix("auth_"))
        return event_id
    except Exception:
        logger.exception("audit event insert failed for action=%s", action)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit logging unavailable",
        )
