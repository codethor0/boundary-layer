"""Production SaaS API auth integration tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api import config
from apps.api.config import get_settings
from apps.api.main import app
from tests.helpers.auth_tenancy import (
    make_oidc_test_token,
    production_saas_env,
    production_saas_settings,
)


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
    app.dependency_overrides.clear()


@pytest.fixture
def production_saas_client(monkeypatch):
    env = production_saas_env()
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    config.get_settings.cache_clear()
    settings = production_saas_settings()
    settings = settings.model_copy(update={"rate_limit_enabled": False})
    app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr("apps.api.config.get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.security.get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.middleware.get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.main.get_settings", lambda: settings)
    return TestClient(app), settings


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_get_labs_unauthenticated_still_works_in_local_lab(
    _mock_membership,
    _mock_audit,
    monkeypatch,
):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    config.get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/labs")
    assert response.status_code == 200


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_get_labs_unauthenticated_rejected_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, _settings = production_saas_client
    response = client.get("/labs")
    assert response.status_code == 401


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_post_lab_unauthenticated_rejected_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, _settings = production_saas_client
    response = client.post("/labs/redis/run", json={"mode": "hardened"})
    assert response.status_code == 401


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_post_lab_with_valid_token_accepted_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, settings = production_saas_client
    token = make_oidc_test_token(settings.secret_key)
    response = client.post(
        "/labs/redis/run",
        json={"mode": "hardened"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_get_labs_with_valid_token_accepted_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, settings = production_saas_client
    token = make_oidc_test_token(settings.secret_key)
    response = client.get("/labs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


@patch("apps.api.tenancy.record_tenant_access_denied")
@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_cross_tenant_prompt_cache_request_denied_in_production_saas(
    _mock_membership,
    _mock_audit,
    _mock_denied,
    production_saas_client,
):
    client, settings = production_saas_client
    token = make_oidc_test_token(settings.secret_key, tenant_id="tenant-a")
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={
            "mode": "hardened",
            "tenant_a": "tenant-b",
            "tenant_b": "tenant-b",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_invalid_token_rejected_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, _settings = production_saas_client
    response = client.get("/labs", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
