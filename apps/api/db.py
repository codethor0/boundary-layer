"""PostgreSQL helpers for BoundaryLayer labs."""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager

GOVERNANCE_ID_PREFIX = "boundary-layer-governance-"
WRITE_STORM_ID_PREFIX = "boundary-layer-write-storm-"
WRITE_STORM_SYNTHETIC_PROMPT_ID = f"{GOVERNANCE_ID_PREFIX}prompt-001"
WRITE_STORM_TENANT_ID = "tenant-a"


def _governance_id_prefix(tenant_id: str) -> str:
    return f"{GOVERNANCE_ID_PREFIX}{tenant_id}:"


def _write_storm_id_prefix(tenant_id: str) -> str:
    return f"{WRITE_STORM_ID_PREFIX}{tenant_id}:"


def _verify_prompt_tenant(prompt_id: str, tenant_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tenant_id FROM prompt_requests WHERE id = %s
                """,
                (prompt_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"Prompt record not found: {prompt_id}")
    if row[0] != tenant_id:
        raise ValueError("Cross-tenant prompt access denied")


POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "boundary_layer")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "boundary_layer")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "boundary_layer_local")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS prompt_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  prompt_text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS prompt_logs (
  id TEXT PRIMARY KEY,
  prompt_request_id TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tool_records (
  id TEXT PRIMARY KEY,
  prompt_request_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS evaluation_queue (
  id TEXT PRIMARY KEY,
  prompt_request_id TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS training_queue (
  id TEXT PRIMARY KEY,
  prompt_request_id TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS deletion_audit (
  id TEXT PRIMARY KEY,
  prompt_request_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  orphan_count INTEGER NOT NULL,
  complete BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS write_storm_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  prompt_request_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS write_storm_events_tenant_created_idx
ON write_storm_events (tenant_id, created_at DESC);
"""


def postgres_live_enabled() -> bool:
    return os.environ.get("BOUNDARY_LAYER_POSTGRES_LIVE", "false").lower() == "true"


def governance_prompt_id(tenant_id: str = WRITE_STORM_TENANT_ID) -> str:
    return f"{_governance_id_prefix(tenant_id)}prompt-001"


def postgres_connect_kwargs() -> dict[str, object]:
    kwargs: dict[str, object] = {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "dbname": POSTGRES_DB,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "connect_timeout": 2,
    }
    sslmode = os.environ.get("POSTGRES_SSLMODE", "prefer").strip()
    if sslmode and sslmode.lower() != "disable":
        kwargs["sslmode"] = sslmode
    root_cert = os.environ.get("POSTGRES_SSL_ROOT_CERT", "").strip()
    if root_cert:
        kwargs["sslrootcert"] = root_cert
    return kwargs


@contextmanager
def get_connection():
    import psycopg2

    conn = psycopg2.connect(**postgres_connect_kwargs())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)


def reset_governance_lab_records(tenant_id: str = WRITE_STORM_TENANT_ID) -> None:
    prefix = _governance_id_prefix(tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM deletion_audit
                WHERE prompt_request_id LIKE %s
                """,
                (f"{prefix}%",),
            )
            for table in (
                "prompt_logs",
                "tool_records",
                "evaluation_queue",
                "training_queue",
            ):
                cur.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE prompt_request_id LIKE %s OR id LIKE %s
                    """,
                    (f"{prefix}%", f"{prefix}%"),
                )
            cur.execute(
                """
                DELETE FROM prompt_requests
                WHERE id LIKE %s AND tenant_id = %s
                """,
                (f"{prefix}%", tenant_id),
            )


def create_prompt_lifecycle_records(tenant_id: str = WRITE_STORM_TENANT_ID) -> str:
    prefix = _governance_id_prefix(tenant_id)
    prompt_id = governance_prompt_id(tenant_id)
    records = {
        "prompt_logs": [
            (f"{prefix}log-200", "Prompt invocation log A"),
            (f"{prefix}log-201", "Prompt invocation log B"),
        ],
        "tool_records": [
            (f"{prefix}tool-300", "summarize_feedback", "Tool output"),
        ],
        "evaluation_queue": [
            (f"{prefix}eval-400", "Queued for offline eval"),
        ],
        "training_queue": [
            (f"{prefix}train-500", "Queued for training pipeline"),
        ],
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO prompt_requests (id, tenant_id, prompt_text)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET deleted_at = NULL, prompt_text = EXCLUDED.prompt_text,
                    tenant_id = EXCLUDED.tenant_id
                """,
                (
                    prompt_id,
                    tenant_id,
                    "Summarize customer feedback for product team.",
                ),
            )
            for record_id, content in records["prompt_logs"]:
                cur.execute(
                    """
                    INSERT INTO prompt_logs (id, prompt_request_id, content)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET deleted_at = NULL, content = EXCLUDED.content
                    """,
                    (record_id, prompt_id, content),
                )
            for record_id, tool_name, content in records["tool_records"]:
                cur.execute(
                    """
                    INSERT INTO tool_records
                    (id, prompt_request_id, tool_name, content)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET deleted_at = NULL, content = EXCLUDED.content
                    """,
                    (record_id, prompt_id, tool_name, content),
                )
            for record_id, content in records["evaluation_queue"]:
                cur.execute(
                    """
                    INSERT INTO evaluation_queue (id, prompt_request_id, content)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET deleted_at = NULL, content = EXCLUDED.content
                    """,
                    (record_id, prompt_id, content),
                )
            for record_id, content in records["training_queue"]:
                cur.execute(
                    """
                    INSERT INTO training_queue (id, prompt_request_id, content)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET deleted_at = NULL, content = EXCLUDED.content
                    """,
                    (record_id, prompt_id, content),
                )
    return prompt_id


def delete_primary_only(prompt_id: str, tenant_id: str = WRITE_STORM_TENANT_ID) -> None:
    _verify_prompt_tenant(prompt_id, tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE prompt_requests
                SET deleted_at = now()
                WHERE id = %s
                """,
                (prompt_id,),
            )


def delete_all_prompt_lifecycle_records(
    prompt_id: str,
    tenant_id: str = WRITE_STORM_TENANT_ID,
) -> None:
    _verify_prompt_tenant(prompt_id, tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table in (
                "prompt_logs",
                "tool_records",
                "evaluation_queue",
                "training_queue",
            ):
                cur.execute(
                    f"""
                    UPDATE {table}
                    SET deleted_at = now()
                    WHERE prompt_request_id = %s AND deleted_at IS NULL
                    """,
                    (prompt_id,),
                )
            cur.execute(
                """
                UPDATE prompt_requests
                SET deleted_at = now()
                WHERE id = %s
                """,
                (prompt_id,),
            )


def count_orphan_records(
    prompt_id: str,
    tenant_id: str = WRITE_STORM_TENANT_ID,
) -> int:
    _verify_prompt_tenant(prompt_id, tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM prompt_logs pl
                JOIN prompt_requests pr ON pr.id = pl.prompt_request_id
                WHERE pl.prompt_request_id = %s
                  AND pr.tenant_id = %s
                  AND pr.deleted_at IS NOT NULL
                  AND pl.deleted_at IS NULL
                """,
                (prompt_id, tenant_id),
            )
            log_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT COUNT(*)
                FROM tool_records tr
                JOIN prompt_requests pr ON pr.id = tr.prompt_request_id
                WHERE tr.prompt_request_id = %s
                  AND pr.tenant_id = %s
                  AND pr.deleted_at IS NOT NULL
                  AND tr.deleted_at IS NULL
                """,
                (prompt_id, tenant_id),
            )
            tool_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT COUNT(*)
                FROM evaluation_queue eq
                JOIN prompt_requests pr ON pr.id = eq.prompt_request_id
                WHERE eq.prompt_request_id = %s
                  AND pr.tenant_id = %s
                  AND pr.deleted_at IS NOT NULL
                  AND eq.deleted_at IS NULL
                """,
                (prompt_id, tenant_id),
            )
            eval_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT COUNT(*)
                FROM training_queue tq
                JOIN prompt_requests pr ON pr.id = tq.prompt_request_id
                WHERE tq.prompt_request_id = %s
                  AND pr.tenant_id = %s
                  AND pr.deleted_at IS NOT NULL
                  AND tq.deleted_at IS NULL
                """,
                (prompt_id, tenant_id),
            )
            train_count = cur.fetchone()[0]
    return log_count + tool_count + eval_count + train_count


def insert_deletion_audit(
    prompt_id: str,
    mode: str,
    orphan_count: int,
    complete: bool,
    tenant_id: str = WRITE_STORM_TENANT_ID,
) -> str:
    _verify_prompt_tenant(prompt_id, tenant_id)
    audit_id = f"{_governance_id_prefix(tenant_id)}audit-{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deletion_audit
                (id, prompt_request_id, mode, orphan_count, complete)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (audit_id, prompt_id, mode, orphan_count, complete),
            )
    return audit_id


def check_postgres_connection() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def reset_write_storm_events(tenant_id: str = WRITE_STORM_TENANT_ID) -> None:
    prefix = _write_storm_id_prefix(tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM write_storm_events
                WHERE tenant_id = %s AND id LIKE %s
                """,
                (tenant_id, f"{prefix}%"),
            )


def insert_write_storm_events(
    count: int,
    batch_id: str,
    tenant_id: str = WRITE_STORM_TENANT_ID,
) -> int:
    if count <= 0:
        return 0

    prefix = _write_storm_id_prefix(tenant_id)
    prompt_id = governance_prompt_id(tenant_id)
    rows = []
    for index in range(count):
        rows.append(
            (
                f"{prefix}{batch_id}-event-{index:05d}",
                tenant_id,
                prompt_id,
                "prompt_log",
                f"synthetic write storm event {index}",
            )
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO write_storm_events
                (id, tenant_id, prompt_request_id, event_type, payload)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                rows,
            )
    return count


def count_write_storm_events(tenant_id: str = WRITE_STORM_TENANT_ID) -> int:
    prefix = _write_storm_id_prefix(tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM write_storm_events
                WHERE tenant_id = %s AND id LIKE %s
                """,
                (tenant_id, f"{prefix}%"),
            )
            return int(cur.fetchone()[0])
