"""Authentication and authorization helpers for BoundaryLayer API."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from apps.api.auth import (
    AuthContext,
    AuthError,
    build_auth_context_from_token,
    local_lab_auth_context,
    parse_authorization_header,
    require_role,
)
from apps.api.config import Settings, get_settings
from apps.api.tenancy import record_auth_audit_event, require_active_membership


def _extract_bearer_token(authorization: str | None) -> str | None:
    return parse_authorization_header(authorization)


def _extract_api_key(
    authorization: str | None,
    x_api_key: str | None,
) -> str | None:
    bearer = _extract_bearer_token(authorization)
    if bearer:
        return bearer
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    return None


def get_request_auth_context(request: Request) -> AuthContext | None:
    context = getattr(request.state, "auth_context", None)
    if isinstance(context, AuthContext):
        return context
    return None


def attach_auth_context(request: Request, auth_context: AuthContext) -> None:
    request.state.auth_context = auth_context


def verify_metrics_access(
    authorization: Annotated[str | None, Header()] = None,
    x_metrics_token: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.metrics_auth_required:
        return

    provided = _extract_bearer_token(authorization)
    if not provided and x_metrics_token:
        provided = x_metrics_token.strip()
    expected = settings.metrics_token.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing metrics credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _verify_production_saas_access(
    request: Request,
    authorization: str | None,
    settings: Settings,
) -> AuthContext:
    token = parse_authorization_header(authorization)
    if not token:
        record_auth_audit_event(
            settings,
            action="auth_missing_token",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_context = build_auth_context_from_token(token, settings)
        require_active_membership(
            auth_context.tenant_id,
            auth_context.subject,
            settings,
        )
        require_role(auth_context, "lab_runner", "tenant_admin", "platform_admin")
    except AuthError as exc:
        record_auth_audit_event(
            settings,
            action="auth_invalid_token",
            result="denied",
            metadata={"error": exc.message, "code": exc.code},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            record_auth_audit_event(
                settings,
                action="auth_cross_tenant_denied",
                result="denied",
                metadata={"detail": str(exc.detail)},
            )
        raise

    record_auth_audit_event(
        settings,
        action="auth_allowed",
        result="allowed",
        tenant_id=auth_context.tenant_id,
        actor_subject=auth_context.subject,
    )
    attach_auth_context(request, auth_context)
    return auth_context


def verify_api_access(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.is_production_saas:
        _verify_production_saas_access(request, authorization, settings)
        return

    if not settings.auth_enabled:
        attach_auth_context(request, local_lab_auth_context())
        return

    provided = _extract_api_key(authorization, x_api_key)
    expected = settings.api_key.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    attach_auth_context(
        request,
        AuthContext(
            subject="api-key-client",
            email=None,
            tenant_id="production-like",
            roles=("lab_runner",),
            scopes=(),
            issuer=None,
            audience=None,
            raw_claims={},
        ),
    )


def enforce_vulnerable_allowed(mode: str, settings: Settings) -> None:
    if mode != "vulnerable":
        return
    if settings.allow_vulnerable:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vulnerable lab mode is disabled in this environment",
    )
