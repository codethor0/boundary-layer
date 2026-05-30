"""Authentication and authorization helpers for BoundaryLayer API."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from apps.api.config import Settings, get_settings


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


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


def verify_api_access(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.auth_enabled:
        return

    provided = _extract_api_key(authorization, x_api_key)
    expected = settings.api_key.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API credentials",
            headers={"WWW-Authenticate": "Bearer"},
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
