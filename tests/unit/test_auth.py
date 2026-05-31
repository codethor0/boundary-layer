"""Authentication unit tests."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from apps.api import config
from apps.api.auth import (
    AuthError,
    build_auth_context,
    build_auth_context_from_token,
    decode_unverified_jwt_for_tests,
    local_lab_auth_context,
    parse_authorization_header,
    require_auth_context,
    require_role,
    resolve_request_tenant,
    validate_jwt_claims,
)
from tests.helpers.auth_tenancy import make_oidc_test_token, production_saas_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_parse_authorization_header():
    assert parse_authorization_header("Bearer token-value") == "token-value"
    assert parse_authorization_header("Basic abc") is None
    assert parse_authorization_header(None) is None


def test_local_lab_auth_context_is_anonymous():
    ctx = local_lab_auth_context()
    assert ctx.is_anonymous is True
    assert ctx.tenant_id == "local-lab"


def test_build_auth_context_from_valid_claims():
    settings = production_saas_settings()
    claims = {
        "sub": "user-1",
        "iss": settings.oidc_issuer_url,
        "aud": settings.oidc_audience,
        "https://boundarylayer.dev/tenant_id": "tenant-a",
        "https://boundarylayer.dev/roles": ["lab_runner"],
    }
    ctx = build_auth_context(claims, settings)
    assert ctx.subject == "user-1"
    assert ctx.tenant_id == "tenant-a"
    assert ctx.roles == ("lab_runner",)


def test_build_auth_context_missing_tenant_raises():
    settings = production_saas_settings()
    claims = {
        "sub": "user-1",
        "iss": settings.oidc_issuer_url,
        "aud": settings.oidc_audience,
    }
    with pytest.raises(AuthError, match="missing tenant"):
        build_auth_context(claims, settings)


def test_validate_jwt_claims_rejects_issuer_mismatch():
    settings = production_saas_settings()
    with pytest.raises(AuthError, match="issuer mismatch"):
        validate_jwt_claims({"iss": "https://wrong.example.com"}, settings)


def test_build_auth_context_from_token_with_oidc_test():
    settings = production_saas_settings()
    token = make_oidc_test_token(settings.secret_key)
    ctx = build_auth_context_from_token(token, settings)
    assert ctx.subject == "user-123"
    assert ctx.tenant_id == "tenant-a"


def test_build_auth_context_from_expired_token_rejected():
    settings = production_saas_settings()
    token = make_oidc_test_token(settings.secret_key, expired=True)
    with pytest.raises(AuthError):
        build_auth_context_from_token(token, settings)


def test_decode_unverified_jwt_for_tests():
    token = make_oidc_test_token("secret-key-for-unverified-decode-test-32")
    claims = decode_unverified_jwt_for_tests(token)
    assert claims["sub"] == "user-123"


def test_require_auth_context_rejects_anonymous():
    with pytest.raises(HTTPException) as exc:
        require_auth_context(local_lab_auth_context())
    assert exc.value.status_code == 401


def test_require_role_allows_platform_admin():
    ctx = build_auth_context(
        {
            "sub": "admin",
            "iss": "https://issuer.example.com",
            "aud": "boundary-layer-api",
            "https://boundarylayer.dev/tenant_id": "tenant-a",
            "https://boundarylayer.dev/roles": ["platform_admin"],
        },
        production_saas_settings(),
    )
    require_role(ctx, "tenant_admin")


def test_require_role_denies_missing_role():
    ctx = build_auth_context(
        {
            "sub": "viewer",
            "iss": "https://issuer.example.com",
            "aud": "boundary-layer-api",
            "https://boundarylayer.dev/tenant_id": "tenant-a",
            "https://boundarylayer.dev/roles": ["observer"],
        },
        production_saas_settings(),
    )
    with pytest.raises(HTTPException) as exc:
        require_role(ctx, "tenant_admin")
    assert exc.value.status_code == 403


def test_resolve_request_tenant_allows_local_lab_defaults():
    settings = config.Settings.model_validate({"boundary_layer_profile": "local-lab"})
    tenant = resolve_request_tenant(settings, local_lab_auth_context(), "tenant-b")
    assert tenant == "tenant-b"


def test_resolve_request_tenant_denies_cross_tenant_in_production_saas():
    settings = production_saas_settings()
    ctx = build_auth_context(
        {
            "sub": "user-1",
            "iss": settings.oidc_issuer_url,
            "aud": settings.oidc_audience,
            "https://boundarylayer.dev/tenant_id": "tenant-a",
            "https://boundarylayer.dev/roles": ["lab_runner"],
        },
        settings,
    )
    with patch("apps.api.tenancy.record_tenant_access_denied") as mock_denied:
        with pytest.raises(HTTPException) as exc:
            resolve_request_tenant(settings, ctx, "tenant-b")
        assert exc.value.status_code == 403
        mock_denied.assert_called_once()


def test_resolve_request_tenant_allows_admin_override():
    settings = production_saas_settings()
    ctx = build_auth_context(
        {
            "sub": "admin",
            "iss": settings.oidc_issuer_url,
            "aud": settings.oidc_audience,
            "https://boundarylayer.dev/tenant_id": "tenant-a",
            "https://boundarylayer.dev/roles": ["platform_admin"],
        },
        settings,
    )
    tenant = resolve_request_tenant(settings, ctx, "tenant-b")
    assert tenant == "tenant-b"


def test_local_lab_does_not_require_oidc_fields(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    settings = config.Settings()
    assert settings.boundary_layer_profile == "local-lab"
    assert settings.oidc_issuer_url == ""
