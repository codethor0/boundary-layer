"""TLS connection helper tests."""

from apps.api.db import postgres_connect_kwargs
from apps.api.redis_client import redis_connect_kwargs


def test_postgres_connect_kwargs_default_sslmode(monkeypatch):
    monkeypatch.delenv("POSTGRES_SSLMODE", raising=False)
    monkeypatch.delenv("POSTGRES_SSL_ROOT_CERT", raising=False)
    kwargs = postgres_connect_kwargs()
    assert kwargs["sslmode"] == "prefer"
    assert "sslrootcert" not in kwargs


def test_postgres_connect_kwargs_require_with_root_cert(monkeypatch):
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_SSL_ROOT_CERT", "/app/tls/ca.crt")
    kwargs = postgres_connect_kwargs()
    assert kwargs["sslmode"] == "require"
    assert kwargs["sslrootcert"] == "/app/tls/ca.crt"


def test_redis_connect_kwargs_plain_by_default(monkeypatch):
    monkeypatch.delenv("REDIS_TLS_ENABLED", raising=False)
    kwargs = redis_connect_kwargs()
    assert "ssl" not in kwargs


def test_redis_connect_kwargs_tls_enabled(monkeypatch):
    monkeypatch.setenv("REDIS_TLS_ENABLED", "true")
    monkeypatch.setenv("REDIS_SSL_CA_CERT", "/app/tls/ca.crt")
    kwargs = redis_connect_kwargs()
    assert kwargs["ssl"] is True
    assert kwargs["ssl_ca_certs"] == "/app/tls/ca.crt"
