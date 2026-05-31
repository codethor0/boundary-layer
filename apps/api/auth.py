"""Authentication and JWT validation for BoundaryLayer production SaaS."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import HTTPException, status

from apps.api.config import Settings

logger = logging.getLogger("boundary_layer.api.auth")

LOCAL_LAB_TENANT_ID = "local-lab"
PLATFORM_ADMIN_ROLE = "platform_admin"
DEFAULT_TENANT_CLAIM = "https://boundarylayer.dev/tenant_id"
DEFAULT_ROLES_CLAIM = "https://boundarylayer.dev/roles"
DEFAULT_SUBJECT_CLAIM = "sub"


class AuthError(Exception):
    """Authentication validation failure."""

    def __init__(self, message: str, code: str = "auth_invalid"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class AuthContext:
    """Verified caller identity for a request."""

    subject: str
    email: str | None
    tenant_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    issuer: str | None
    audience: str | None
    raw_claims: dict[str, Any] = field(default_factory=dict)
    is_anonymous: bool = False

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def is_platform_admin(self) -> bool:
        return self.has_role(PLATFORM_ADMIN_ROLE)


def local_lab_auth_context() -> AuthContext:
    """Synthetic identity for unauthenticated local-lab requests."""
    return AuthContext(
        subject="local-lab-anonymous",
        email=None,
        tenant_id=LOCAL_LAB_TENANT_ID,
        roles=("lab_runner",),
        scopes=(),
        issuer=None,
        audience=None,
        raw_claims={},
        is_anonymous=True,
    )


def parse_authorization_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def decode_unverified_jwt_for_tests(token: str) -> dict[str, Any]:
    return jwt.decode(token, options={"verify_signature": False})


def _extract_roles(claims: dict[str, Any], settings: Settings) -> tuple[str, ...]:
    claim_name = settings.oidc_roles_claim.strip() or DEFAULT_ROLES_CLAIM
    value = claims.get(claim_name, claims.get("roles", ()))
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def _extract_tenant_id(claims: dict[str, Any], settings: Settings) -> str | None:
    claim_name = settings.oidc_tenant_claim.strip() or DEFAULT_TENANT_CLAIM
    value = claims.get(claim_name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_subject(claims: dict[str, Any], settings: Settings) -> str | None:
    claim_name = settings.oidc_subject_claim.strip() or DEFAULT_SUBJECT_CLAIM
    value = claims.get(claim_name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_jwt_claims(claims: dict[str, Any], settings: Settings) -> None:
    issuer = settings.oidc_issuer_url.strip()
    audience = settings.oidc_audience.strip()
    if issuer and claims.get("iss") != issuer:
        raise AuthError("issuer mismatch", "auth_invalid_token")
    if audience:
        aud = claims.get("aud")
        if isinstance(aud, list):
            if audience not in aud:
                raise AuthError("audience mismatch", "auth_invalid_token")
        elif aud != audience:
            raise AuthError("audience mismatch", "auth_invalid_token")
    for claim in settings.oidc_required_claims_list:
        if claim not in claims:
            raise AuthError(f"missing required claim: {claim}", "auth_missing_claim")


def build_auth_context(claims: dict[str, Any], settings: Settings) -> AuthContext:
    validate_jwt_claims(claims, settings)
    subject = _extract_subject(claims, settings)
    tenant_id = _extract_tenant_id(claims, settings)
    if not subject:
        raise AuthError("missing subject claim", "auth_missing_subject")
    if not tenant_id:
        raise AuthError("missing tenant claim", "auth_missing_tenant")
    email = claims.get("email")
    if email is not None:
        email = str(email)
    scope_value = claims.get("scope")
    if isinstance(scope_value, str):
        scopes = tuple(part for part in scope_value.split() if part)
    elif isinstance(scope_value, list):
        scopes = tuple(str(part) for part in scope_value)
    else:
        scopes = ()
    audience = claims.get("aud")
    if isinstance(audience, list):
        audience_text = ",".join(str(item) for item in audience)
    elif audience is not None:
        audience_text = str(audience)
    else:
        audience_text = None
    return AuthContext(
        subject=subject,
        email=email,
        tenant_id=tenant_id,
        roles=_extract_roles(claims, settings),
        scopes=scopes,
        issuer=str(claims.get("iss")) if claims.get("iss") else None,
        audience=audience_text,
        raw_claims=claims,
    )


def verify_jwt_token(token: str, settings: Settings) -> dict[str, Any]:
    algorithms = settings.oidc_algorithms_list
    provider = settings.auth_provider.strip().lower()
    issuer = settings.oidc_issuer_url.strip() or None
    audience = settings.oidc_audience.strip() or None

    try:
        if provider == "oidc-test":
            return jwt.decode(
                token,
                settings.secret_key.strip(),
                algorithms=algorithms or ["HS256"],
                audience=audience,
                issuer=issuer,
                options={"require": ["exp", "sub"]},
            )

        if not settings.oidc_jwks_url.strip():
            raise AuthError("JWKS URL not configured", "auth_misconfigured")

        jwk_client = jwt.PyJWKClient(settings.oidc_jwks_url.strip())
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms or ["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "sub"]},
        )
    except AuthError:
        raise
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc), "auth_invalid_token") from exc


def build_auth_context_from_token(token: str, settings: Settings) -> AuthContext:
    claims = verify_jwt_token(token, settings)
    return build_auth_context(claims, settings)


def require_auth_context(auth_context: AuthContext | None) -> AuthContext:
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if auth_context.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_context


def require_role(auth_context: AuthContext, *roles: str) -> None:
    if auth_context.is_platform_admin():
        return
    if not any(auth_context.has_role(role) for role in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role",
        )


def require_tenant_match(auth_context: AuthContext, tenant_id: str) -> None:
    if auth_context.is_platform_admin():
        return
    if auth_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )


def resolve_request_tenant(
    settings: Settings,
    auth_context: AuthContext | None,
    requested_tenant_id: str | None = None,
) -> str:
    if not settings.is_production_saas:
        if requested_tenant_id and requested_tenant_id.strip():
            return requested_tenant_id.strip()
        if auth_context is not None:
            return auth_context.tenant_id
        return LOCAL_LAB_TENANT_ID

    auth_context = require_auth_context(auth_context)
    if requested_tenant_id and requested_tenant_id.strip():
        requested = requested_tenant_id.strip()
        if auth_context.is_platform_admin():
            return requested
        if requested != auth_context.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access denied",
            )
        return requested
    return auth_context.tenant_id
