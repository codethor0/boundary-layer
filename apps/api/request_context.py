"""Request-scoped lab context for BoundaryLayer."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from apps.api.auth import LOCAL_LAB_TENANT_ID, AuthContext, local_lab_auth_context
from apps.api.config import Settings, get_settings
from apps.api.security import get_request_auth_context


@dataclass(frozen=True)
class LabRequestContext:
    profile: str
    tenant_id: str
    auth_context: AuthContext
    is_local_lab: bool
    is_production_saas: bool
    is_admin: bool


def resolve_lab_request_context(
    http_request: Request,
    settings: Settings | None = None,
) -> LabRequestContext:
    current = settings or get_settings()
    auth_context = get_request_auth_context(http_request) or local_lab_auth_context()

    if current.is_production_saas:
        if auth_context.is_anonymous:
            raise ValueError("Authenticated tenant context required in production-saas")
        tenant_id = auth_context.tenant_id
    elif current.is_local_lab:
        tenant_id = LOCAL_LAB_TENANT_ID
    else:
        tenant_id = (
            auth_context.tenant_id
            if auth_context.tenant_id and not auth_context.is_anonymous
            else "production-like"
        )

    return LabRequestContext(
        profile=current.boundary_layer_profile,
        tenant_id=tenant_id,
        auth_context=auth_context,
        is_local_lab=current.is_local_lab,
        is_production_saas=current.is_production_saas,
        is_admin=auth_context.is_platform_admin(),
    )
