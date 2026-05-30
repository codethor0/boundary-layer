"""Tests for PostgreSQL governance database helpers."""

from unittest.mock import MagicMock, patch

import pytest

from apps.api import db


@pytest.fixture(autouse=True)
def postgres_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "false")


def test_postgres_live_enabled_reads_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")
    assert db.postgres_live_enabled() is True


def test_governance_prompt_id_uses_namespace():
    assert db.governance_prompt_id().startswith(db.GOVERNANCE_ID_PREFIX)


@patch("apps.api.db.get_connection")
def test_count_orphan_records_sums_downstream_tables(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [(2,), (1,), (1,), (1,)]

    orphan_count = db.count_orphan_records(db.governance_prompt_id())

    assert orphan_count == 5


@patch("apps.api.db.get_connection")
def test_insert_deletion_audit_writes_record(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    audit_id = db.insert_deletion_audit(db.governance_prompt_id(), "hardened", 0, True)

    assert audit_id.startswith(db.GOVERNANCE_ID_PREFIX)
    assert mock_cursor.execute.called


@patch("apps.api.db.get_connection")
def test_reset_write_storm_events_deletes_lab_rows(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    db.reset_write_storm_events()

    assert mock_cursor.execute.called


@patch("apps.api.db.get_connection")
def test_insert_write_storm_events_uses_namespace(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    inserted = db.insert_write_storm_events(3, "batch-test")

    assert inserted == 3
    assert mock_cursor.executemany.called
    rows = mock_cursor.executemany.call_args[0][1]
    assert all(row[0].startswith(db.WRITE_STORM_ID_PREFIX) for row in rows)
