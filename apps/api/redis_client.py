"""Shared Redis client for production API features."""

from __future__ import annotations

import os

import redis


def get_redis_client() -> redis.Redis:
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    db = int(os.environ.get("REDIS_DB", "0"))
    password = os.environ.get("REDIS_PASSWORD") or None
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
