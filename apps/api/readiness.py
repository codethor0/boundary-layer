"""Readiness checks for BoundaryLayer API dependencies."""

from __future__ import annotations

import os

from apps.api.db import get_connection, postgres_live_enabled


def _redis_live_enabled() -> bool:
    return os.environ.get("BOUNDARY_LAYER_REDIS_LIVE", "false").lower() == "true"


def _check_postgres() -> tuple[bool, str]:
    if not postgres_live_enabled():
        return True, "skipped (live mode disabled)"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True, "connected"
    except Exception as exc:
        return False, str(exc)


def _check_redis() -> tuple[bool, str]:
    if not _redis_live_enabled():
        return True, "skipped (live mode disabled)"
    try:
        from labs.redis_state import _get_redis_client

        client = _get_redis_client()
        client.ping()
        return True, "connected"
    except Exception as exc:
        return False, str(exc)


def evaluate_readiness() -> tuple[bool, dict[str, dict[str, str | bool]]]:
    postgres_ok, postgres_detail = _check_postgres()
    redis_ok, redis_detail = _check_redis()
    checks = {
        "postgres": {"ok": postgres_ok, "detail": postgres_detail},
        "redis": {"ok": redis_ok, "detail": redis_detail},
    }
    return postgres_ok and redis_ok, checks
