"""JWKS client unit tests."""

from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.api.jwks import (
    HttpJwksClient,
    InMemoryJwksClient,
    JwksError,
    build_jwks_client,
    extract_token_kid,
    validate_jwt_algorithm,
)


def _rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def test_in_memory_jwks_cache_hit():
    _, public_pem = _rsa_keypair()
    client = InMemoryJwksClient(keys_by_kid={"kid-1": public_pem}, cache_ttl_seconds=60)
    first = client.get_signing_key("kid-1")
    second = client.get_signing_key("kid-1")
    assert first == second


def test_in_memory_jwks_missing_kid_rejected():
    client = InMemoryJwksClient(keys_by_kid={})
    with pytest.raises(JwksError, match="missing kid"):
        client.get_signing_key(None)


def test_in_memory_jwks_unknown_kid_rejected():
    client = InMemoryJwksClient(keys_by_kid={})
    with pytest.raises(JwksError, match="Unknown key id"):
        client.get_signing_key("missing")


def test_in_memory_jwks_refresh_clears_cache():
    _, public_pem = _rsa_keypair()
    client = InMemoryJwksClient(keys_by_kid={"kid-1": public_pem})
    client.get_signing_key("kid-1")
    client.refresh()
    assert client._cache == {}


def test_validate_jwt_algorithm_rejects_none():
    with pytest.raises(JwksError, match="none"):
        validate_jwt_algorithm("none", ["RS256"])


def test_validate_jwt_algorithm_rejects_unsupported():
    with pytest.raises(JwksError, match="Unsupported"):
        validate_jwt_algorithm("HS512", ["RS256"])


def test_extract_token_kid_from_signed_token():
    private_pem, _ = _rsa_keypair()
    token = jwt.encode(
        {"sub": "user-1"},
        private_pem,
        algorithm="RS256",
        headers={"kid": "kid-1"},
    )
    header, kid = extract_token_kid(token)
    assert header["alg"] == "RS256"
    assert kid == "kid-1"


@patch("apps.api.jwks.urlopen")
def test_http_jwks_fetch_failure(mock_urlopen):
    mock_urlopen.side_effect = OSError("network down")
    client = HttpJwksClient(
        jwks_url="https://issuer.example.com/.well-known/jwks.json",
        timeout_seconds=1.0,
    )
    with pytest.raises(JwksError, match="fetch failed"):
        client.refresh()


def test_build_jwks_client_requires_url_without_test_keys():
    with pytest.raises(JwksError, match="not configured"):
        build_jwks_client(jwks_url="")


def test_build_jwks_client_returns_in_memory_for_tests():
    _, public_pem = _rsa_keypair()
    client = build_jwks_client(test_keys_by_kid={"kid-1": public_pem})
    assert isinstance(client, InMemoryJwksClient)
