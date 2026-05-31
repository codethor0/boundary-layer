"""Tenancy schema and membership tests."""

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from apps.api import config
from apps.api.tenancy import (
    get_membership,
    init_tenancy_schema,
    insert_audit_event,
    list_audit_events_for_tenant,
    require_active_membership,
    upsert_membership,
    upsert_tenant,
    upsert_user,
)
from tests.helpers.auth_tenancy import production_saas_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def _production_saas_settings():
    return production_saas_settings()


@patch("apps.api.tenancy.get_connection")
def test_init_tenancy_schema_executes_sql(mock_get_connection):
    connection = MagicMock()
    cursor = MagicMock()

    @contextmanager
    def fake_connection():
        yield connection

    connection.cursor.return_value.__enter__.return_value = cursor
    mock_get_connection.side_effect = fake_connection

    init_tenancy_schema()

    cursor.execute.assert_called_once()


@patch("apps.api.tenancy.get_connection")
def test_upsert_tenant_user_membership(mock_get_connection):
    connection = MagicMock()
    cursor = MagicMock()

    @contextmanager
    def fake_connection():
        yield connection

    connection.cursor.return_value.__enter__.return_value = cursor
    mock_get_connection.side_effect = fake_connection

    upsert_tenant("tenant-a", "Tenant A")
    upsert_user("user-1", "subject-1", "user@example.com")
    upsert_membership("membership-1", "tenant-a", "user-1", "lab_runner")

    assert cursor.execute.call_count == 3


@patch("apps.api.tenancy.get_connection")
def test_get_membership_returns_row(mock_get_connection):
    connection = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = (
        "membership-1",
        "tenant-a",
        "user-1",
        "lab_runner",
        "active",
    )

    @contextmanager
    def fake_connection():
        yield connection

    connection.cursor.return_value.__enter__.return_value = cursor
    mock_get_connection.side_effect = fake_connection

    membership = get_membership("tenant-a", "subject-1")
    assert membership is not None
    assert membership["role"] == "lab_runner"


@patch("apps.api.tenancy.get_membership")
def test_require_active_membership_allows_active(mock_get_membership):
    mock_get_membership.return_value = {
        "id": "membership-1",
        "tenant_id": "tenant-a",
        "user_id": "user-1",
        "role": "lab_runner",
        "status": "active",
    }
    settings = _production_saas_settings()
    membership = require_active_membership("tenant-a", "subject-1", settings)
    assert membership["status"] == "active"


@patch("apps.api.tenancy.get_membership")
def test_require_active_membership_denies_missing(mock_get_membership):
    mock_get_membership.return_value = None
    settings = _production_saas_settings()
    with pytest.raises(HTTPException) as exc:
        require_active_membership("tenant-a", "subject-1", settings)
    assert exc.value.status_code == 403


@patch("apps.api.tenancy.get_membership")
def test_require_active_membership_skipped_for_local_lab(mock_get_membership):
    settings = config.Settings()
    result = require_active_membership("tenant-a", "subject-1", settings)
    assert result == {}
    mock_get_membership.assert_not_called()


@patch("apps.api.tenancy.get_connection")
def test_insert_audit_event(mock_get_connection):
    connection = MagicMock()
    cursor = MagicMock()

    @contextmanager
    def fake_connection():
        yield connection

    connection.cursor.return_value.__enter__.return_value = cursor
    mock_get_connection.side_effect = fake_connection

    event_id = insert_audit_event(
        action="auth_allowed",
        result="allowed",
        tenant_id="tenant-a",
        actor_subject="subject-1",
        metadata={"path": "/labs"},
    )
    assert event_id.startswith("audit-")


@patch("apps.api.tenancy.get_connection")
def test_list_audit_events_for_tenant(mock_get_connection):
    connection = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (
            "audit-1",
            "tenant-a",
            "subject-1",
            "auth_allowed",
            "auth",
            None,
            "allowed",
            {"path": "/labs"},
            datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
    ]

    @contextmanager
    def fake_connection():
        yield connection

    connection.cursor.return_value.__enter__.return_value = cursor
    mock_get_connection.side_effect = fake_connection

    events = list_audit_events_for_tenant("tenant-a")
    assert len(events) == 1
    assert events[0]["action"] == "auth_allowed"
