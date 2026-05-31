"""Production SaaS tenant isolation and cross-tenant denial tests."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.api import config
from apps.api.auth import build_auth_context
from apps.api.config import get_settings
from apps.api.main import app
from apps.api.request_context import resolve_lab_request_context
from apps.api.tenancy import (
    assert_tenant_scope,
    build_tenant_redis_key,
    normalize_lab_tenant_id,
    require_same_tenant_or_admin,
)
from tests.helpers.auth_tenancy import (
    make_oidc_test_token,
    make_request,
    production_saas_env,
    production_saas_settings,
)

LAB_RUN_PATHS = [
    "/labs/tool-router/run",
    "/labs/redis/run",
    "/labs/authz/run",
    "/labs/file-upload/run",
    "/labs/governance/run",
    "/labs/postgres-write-storm/run",
    "/labs/circuit-breaker/run",
    "/labs/sse-exhaustion/run",
    "/labs/prompt-cache-isolation/run",
]


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


def _auth_headers(
    settings,
    tenant_id: str = "tenant-a",
    roles: list[str] | None = None,
):
    token = make_oidc_test_token(
        settings.secret_key,
        tenant_id=tenant_id,
        roles=roles or ["lab_runner"],
    )
    return {"Authorization": f"Bearer {token}"}


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
@pytest.mark.parametrize("path", LAB_RUN_PATHS)
def test_lab_run_requires_auth_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
    path,
):
    client, _settings = production_saas_client
    payload = {"mode": "hardened"}
    if path.endswith("file-upload/run"):
        payload = {"mode": "hardened", "file_type": "pdf"}
    elif path.endswith("postgres-write-storm/run"):
        payload = {"mode": "hardened", "requested_writes": 10}
    elif path.endswith("circuit-breaker/run"):
        payload = {"mode": "hardened", "requested_work_units": 10}
    elif path.endswith("sse-exhaustion/run"):
        payload = {"mode": "hardened", "requested_streams": 10}
    elif path.endswith("prompt-cache-isolation/run"):
        payload = {"mode": "hardened"}
    response = client.post(path, json=payload)
    assert response.status_code == 401


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_get_labs_requires_auth_in_production_saas(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, _settings = production_saas_client
    assert client.get("/labs").status_code == 401


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
@pytest.mark.parametrize("path", LAB_RUN_PATHS)
def test_lab_run_with_valid_token_accepted(
    _mock_membership,
    _mock_audit,
    production_saas_client,
    path,
):
    client, settings = production_saas_client
    payload = {"mode": "hardened"}
    if path.endswith("file-upload/run"):
        payload = {"mode": "hardened", "file_type": "pdf"}
    elif path.endswith("postgres-write-storm/run"):
        payload = {"mode": "hardened", "requested_writes": 10}
    elif path.endswith("circuit-breaker/run"):
        payload = {"mode": "hardened", "requested_work_units": 10}
    elif path.endswith("sse-exhaustion/run"):
        payload = {"mode": "hardened", "requested_streams": 10}
    elif path.endswith("prompt-cache-isolation/run"):
        payload = {"mode": "hardened"}
    response = client.post(path, json=payload, headers=_auth_headers(settings))
    assert response.status_code == 200


@patch("apps.api.tenancy.record_tenant_access_denied")
@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_tenant_override_denied_for_non_admin(
    _mock_membership,
    _mock_audit,
    mock_denied,
    production_saas_client,
):
    client, settings = production_saas_client
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "hardened", "tenant_a": "tenant-b"},
        headers=_auth_headers(settings, tenant_id="tenant-a"),
    )
    assert response.status_code == 403
    mock_denied.assert_called_once()


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_admin_tenant_override_allowed(
    _mock_membership,
    _mock_audit,
    production_saas_client,
):
    client, settings = production_saas_client
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "hardened", "tenant_a": "tenant-b"},
        headers=_auth_headers(settings, tenant_id="tenant-a", roles=["platform_admin"]),
    )
    assert response.status_code == 200


def test_build_tenant_redis_key_differs_by_tenant():
    key_a = build_tenant_redis_key("tenant-a", "redis", "session:abc")
    key_b = build_tenant_redis_key("tenant-b", "redis", "session:abc")
    assert key_a != key_b
    assert "boundary_layer:tenant:tenant-a:lab:redis:" in key_a
    assert "boundary_layer:tenant:tenant-b:lab:redis:" in key_b


def test_normalize_lab_tenant_id_defaults_to_local_lab():
    assert normalize_lab_tenant_id(None) == "local-lab"
    assert normalize_lab_tenant_id("  tenant-x  ") == "tenant-x"


def test_assert_tenant_scope_requires_tenant_in_production_saas():
    settings = production_saas_settings()
    with pytest.raises(ValueError, match="tenant_id is required"):
        assert_tenant_scope(None, settings)


def test_assert_tenant_scope_returns_normalized_tenant():
    settings = production_saas_settings()
    assert assert_tenant_scope("tenant-a", settings) == "tenant-a"


def test_require_same_tenant_or_admin_allows_admin():
    settings = production_saas_settings()
    admin = build_auth_context(
        {
            "sub": "admin",
            "iss": settings.oidc_issuer_url,
            "aud": settings.oidc_audience,
            "https://boundarylayer.dev/tenant_id": "tenant-a",
            "https://boundarylayer.dev/roles": ["platform_admin"],
        },
        settings,
    )
    require_same_tenant_or_admin(settings, admin, "tenant-b")


def test_require_same_tenant_or_admin_denies_cross_tenant():
    from fastapi import HTTPException

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
    with pytest.raises(HTTPException) as exc:
        require_same_tenant_or_admin(settings, ctx, "tenant-b")
    assert exc.value.status_code == 403


def test_resolve_lab_request_context_local_lab_uses_local_lab_tenant(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    config.get_settings.cache_clear()
    request = make_request()
    ctx = resolve_lab_request_context(request)
    assert ctx.is_local_lab is True
    assert ctx.tenant_id == "local-lab"


def test_resolve_lab_request_context_production_saas_uses_auth_tenant(monkeypatch):
    env = production_saas_env()
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    config.get_settings.cache_clear()
    settings = production_saas_settings()
    token = make_oidc_test_token(settings.secret_key, tenant_id="tenant-z")
    request = make_request(authorization=f"Bearer {token}")
    with patch("apps.api.request_context.get_request_auth_context") as mock_ctx:
        mock_ctx.return_value = build_auth_context(
            {
                "sub": "user-z",
                "iss": settings.oidc_issuer_url,
                "aud": settings.oidc_audience,
                "https://boundarylayer.dev/tenant_id": "tenant-z",
                "https://boundarylayer.dev/roles": ["lab_runner"],
            },
            settings,
        )
        ctx = resolve_lab_request_context(request, settings)
    assert ctx.is_production_saas is True
    assert ctx.tenant_id == "tenant-z"


@patch("apps.api.tenancy.insert_audit_event", return_value="audit-1")
@patch("apps.api.metrics.record_audit_event_metric")
@patch("apps.api.metrics.record_auth_decision")
@patch("apps.api.metrics.record_tenant_access_denied_metric")
def test_record_tenant_access_denied_writes_audit(
    mock_metric,
    mock_auth_decision,
    mock_audit_metric,
    mock_insert,
):
    from apps.api.tenancy import record_tenant_access_denied

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
    record_tenant_access_denied(
        settings,
        reason="tenant_override_denied",
        auth_context=ctx,
        requested_tenant_id="tenant-b",
    )
    mock_insert.assert_called_once()
    mock_metric.assert_called_once()
    metadata = mock_insert.call_args.kwargs["metadata"]
    assert metadata["requested_tenant_id"] == "tenant-b"
    assert "token" not in str(metadata).lower()


@patch("apps.api.db.get_connection")
def test_count_write_storm_events_filters_by_tenant(mock_get_connection):
    from apps.api import db

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (7,)

    count = db.count_write_storm_events("tenant-a")

    assert count == 7
    sql = mock_cursor.execute.call_args[0][0]
    assert "tenant_id = %s" in sql


@patch("apps.api.db.get_connection")
def test_insert_write_storm_events_stores_tenant_id(mock_get_connection):
    from apps.api import db

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    db.insert_write_storm_events(2, "batch-1", "tenant-b")

    rows = mock_cursor.executemany.call_args[0][1]
    assert all(row[1] == "tenant-b" for row in rows)


@patch("apps.api.db.get_connection")
def test_verify_prompt_tenant_rejects_cross_tenant_prompt(mock_get_connection):
    from apps.api import db

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("tenant-b",)

    with pytest.raises(ValueError, match="Cross-tenant prompt access denied"):
        db.count_orphan_records(db.governance_prompt_id("tenant-a"), "tenant-a")


def test_prompt_cache_tenant_scoped_redis_keys():
    from labs.prompt_cache_isolation import tenant_cache_key

    legacy = tenant_cache_key("tenant-a", "prefix", tenant_scoped_redis=False)
    scoped = tenant_cache_key("tenant-a", "prefix", tenant_scoped_redis=True)
    assert scoped != legacy
    assert "boundary_layer:tenant:tenant-a:lab:prompt_cache:" in scoped


@patch("apps.api.security.record_auth_audit_event")
@patch("apps.api.security.require_active_membership", return_value={"status": "active"})
def test_local_lab_endpoints_remain_unauthenticated(
    _mock_membership,
    _mock_audit,
    monkeypatch,
):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    config.get_settings.cache_clear()
    client = TestClient(app)
    assert client.get("/labs").status_code == 200
    response = client.post("/labs/redis/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert "lab" in response.json()


@patch("apps.api.metrics.record_auth_decision")
@patch("apps.api.metrics.record_audit_event_metric")
def test_auth_audit_metrics_recorded(mock_audit_metric, mock_auth_decision):
    from apps.api.tenancy import record_auth_audit_event

    settings = production_saas_settings()
    with patch("apps.api.tenancy.insert_audit_event", return_value="audit-1"):
        record_auth_audit_event(
            settings,
            action="auth_allowed",
            result="allowed",
            tenant_id="tenant-a",
            actor_subject="user-1",
        )
    mock_audit_metric.assert_called_once_with("auth_allowed", "allowed")
    mock_auth_decision.assert_called_once_with("allowed", "authenticated")
