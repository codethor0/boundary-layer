"""Shared Redis client for production API features."""

from __future__ import annotations

import os
import ssl

import redis


def redis_connect_kwargs() -> dict[str, object]:
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    db = int(os.environ.get("REDIS_DB", "0"))
    password = os.environ.get("REDIS_PASSWORD") or None
    kwargs: dict[str, object] = {
        "host": host,
        "port": port,
        "db": db,
        "password": password,
        "decode_responses": True,
        "socket_connect_timeout": 2,
        "socket_timeout": 2,
    }
    if os.environ.get("REDIS_TLS_ENABLED", "false").lower() == "true":
        kwargs["ssl"] = True
        kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED
        ca_cert = os.environ.get("REDIS_SSL_CA_CERT", "").strip()
        if ca_cert:
            kwargs["ssl_ca_certs"] = ca_cert
    return kwargs


def get_redis_client() -> redis.Redis:
    return redis.Redis(**redis_connect_kwargs())
