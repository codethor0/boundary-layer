"""Secret manager abstraction for Production SaaS."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Protocol

from apps.api.config import Settings

logger = logging.getLogger("boundary_layer.api.secrets")

SUPPORTED_SECRET_MANAGER_PROVIDERS = frozenset(
    {"aws", "gcp", "azure", "doppler", "vault"}
)

SDK_NOT_INSTALLED_MESSAGE = (
    "Provider SDK not installed. Install optional dependency "
    "or use the local test backend."
)


class SecretError(Exception):
    """Secret lookup failure."""

    def __init__(self, message: str, code: str = "secret_error"):
        super().__init__(message)
        self.message = message
        self.code = code


def redact(value: str, visible: int = 4) -> str:
    cleaned = value.strip()
    if not cleaned:
        return "<empty>"
    if len(cleaned) <= visible:
        return "*" * len(cleaned)
    return f"{cleaned[:visible]}{'*' * (len(cleaned) - visible)}"


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> str:
        """Return a secret value by name."""

    def get_json_secret(self, name: str) -> dict[str, Any]:
        """Return a JSON object secret."""

    def refresh_secret(self, name: str) -> str:
        """Refresh and return a secret value."""


class _CachedSecretProvider:
    def __init__(self, cache_ttl_seconds: int) -> None:
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, str]] = {}

    def _cache_get(self, name: str) -> str | None:
        entry = self._cache.get(name)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self._cache.pop(name, None)
            return None
        return value

    def _cache_set(self, name: str, value: str) -> None:
        self._cache[name] = (time.monotonic() + self._cache_ttl_seconds, value)


class EnvironmentSecretProvider(_CachedSecretProvider):
    """Read secrets from environment variables for local-lab and tests."""

    def __init__(self, cache_ttl_seconds: int = 0) -> None:
        super().__init__(cache_ttl_seconds)

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        env_name = name.strip().upper()
        value = os.environ.get(env_name, "").strip()
        if not value:
            raise SecretError(f"Missing secret: {env_name}", "secret_not_found")
        logger.info(
            "Loaded secret %s from environment (value=%s)",
            env_name,
            redact(value),
        )
        if self._cache_ttl_seconds > 0:
            self._cache_set(name, value)
        return value

    def get_json_secret(self, name: str) -> dict[str, Any]:
        raw = self.get_secret(name)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretError(
                f"Secret {name.strip()} is not valid JSON",
                "secret_invalid_json",
            ) from exc
        if not isinstance(parsed, dict):
            raise SecretError(
                f"Secret {name.strip()} must decode to a JSON object",
                "secret_invalid_json",
            )
        return parsed

    def refresh_secret(self, name: str) -> str:
        self._cache.pop(name.strip().upper(), None)
        return self.get_secret(name)


class _CloudSecretProviderBase(_CachedSecretProvider):
    provider_name: str = "cloud"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings.secret_cache_ttl_seconds)
        self._settings = settings

    def _secret_path(self, name: str) -> str:
        base = self._settings.secret_manager_project_or_path.strip().rstrip("/")
        secret_name = name.strip()
        if not base:
            return secret_name
        return f"{base}/{secret_name}"

    def get_json_secret(self, name: str) -> dict[str, Any]:
        raw = self.get_secret(name)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_invalid_json",
            ) from exc
        if not isinstance(parsed, dict):
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_invalid_json",
            )
        return parsed

    def refresh_secret(self, name: str) -> str:
        self._cache.pop(name, None)
        return self.get_secret(name)


class AwsSecretsManagerProvider(_CloudSecretProviderBase):
    provider_name = "aws"

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        try:
            import boto3
        except ImportError as exc:
            raise SecretError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        client = boto3.client("secretsmanager")
        secret_id = self._secret_path(name)
        try:
            response = client.get_secret_value(SecretId=secret_id)
        except Exception as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            ) from exc
        value = str(response.get("SecretString", "")).strip()
        if not value:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            )
        logger.info(
            "Loaded secret %s via aws secrets manager (value=%s)",
            name.strip(),
            redact(value),
        )
        self._cache_set(name, value)
        return value


class GcpSecretManagerProvider(_CloudSecretProviderBase):
    provider_name = "gcp"

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        try:
            from google.cloud import secretmanager
        except ImportError as exc:
            raise SecretError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        client = secretmanager.SecretManagerServiceClient()
        secret_name = self._secret_path(name)
        try:
            response = client.access_secret_version(name=secret_name)
        except Exception as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            ) from exc
        value = response.payload.data.decode("utf-8").strip()
        if not value:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            )
        logger.info(
            "Loaded secret %s via gcp secret manager (value=%s)",
            name.strip(),
            redact(value),
        )
        self._cache_set(name, value)
        return value


class AzureKeyVaultProvider(_CloudSecretProviderBase):
    provider_name = "azure"

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
        except ImportError as exc:
            raise SecretError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        vault_url = self._settings.secret_manager_project_or_path.strip()
        if not vault_url.startswith("https://"):
            raise SecretError(
                "SECRET_MANAGER_PROJECT_OR_PATH must be an Azure Key Vault URL",
                "secret_manager_config_invalid",
            )
        client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
        try:
            secret = client.get_secret(name.strip())
        except Exception as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            ) from exc
        value = str(secret.value or "").strip()
        if not value:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            )
        logger.info(
            "Loaded secret %s via azure key vault (value=%s)",
            name.strip(),
            redact(value),
        )
        self._cache_set(name, value)
        return value


class VaultSecretProvider(_CloudSecretProviderBase):
    provider_name = "vault"

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        try:
            import hvac
        except ImportError as exc:
            raise SecretError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        address = os.environ.get("VAULT_ADDR", "").strip()
        token = os.environ.get("VAULT_TOKEN", "").strip()
        if not address or not token:
            raise SecretError(
                "VAULT_ADDR and VAULT_TOKEN are required for vault provider",
                "secret_manager_config_invalid",
            )
        client = hvac.Client(url=address, token=token)
        secret_path = self._secret_path(name)
        try:
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        except Exception as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            ) from exc
        data = response.get("data", {}).get("data", {})
        value = str(data.get("value", "")).strip()
        if not value:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            )
        logger.info(
            "Loaded secret %s via vault (value=%s)",
            name.strip(),
            redact(value),
        )
        self._cache_set(name, value)
        return value


class DopplerSecretProvider(_CloudSecretProviderBase):
    provider_name = "doppler"

    def get_secret(self, name: str) -> str:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        token = os.environ.get("DOPPLER_TOKEN", "").strip()
        if not token:
            raise SecretError(
                "DOPPLER_TOKEN is required for doppler provider",
                "secret_manager_config_invalid",
            )
        try:
            import httpx
        except ImportError as exc:
            raise SecretError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        project = self._settings.secret_manager_project_or_path.strip()
        url = f"https://api.doppler.com/v3/configs/config/secrets/download?format=json&project={project}"
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            ) from exc
        value = str(payload.get(name.strip(), "")).strip()
        if not value:
            raise SecretError(
                f"Secret lookup failed for {name.strip()}",
                "secret_not_found",
            )
        logger.info(
            "Loaded secret %s via doppler (value=%s)",
            name.strip(),
            redact(value),
        )
        self._cache_set(name, value)
        return value


class DisabledProductionSecretProvider:
    """Fail closed when production-saas lacks a configured secret manager adapter."""

    def __init__(self, provider: str) -> None:
        self._provider = provider

    def _fail(self, name: str) -> None:
        logger.warning(
            "Secret lookup blocked for %s via unconfigured provider %s",
            name,
            self._provider,
        )
        raise SecretError(
            f"Secret manager adapter for {self._provider} is not configured",
            "secret_manager_not_configured",
        )

    def get_secret(self, name: str) -> str:
        self._fail(name)
        raise AssertionError("unreachable")

    def get_json_secret(self, name: str) -> dict[str, Any]:
        self._fail(name)
        raise AssertionError("unreachable")

    def refresh_secret(self, name: str) -> str:
        self._fail(name)
        raise AssertionError("unreachable")


_PROVIDER_CLASSES = {
    "aws": AwsSecretsManagerProvider,
    "gcp": GcpSecretManagerProvider,
    "azure": AzureKeyVaultProvider,
    "vault": VaultSecretProvider,
    "doppler": DopplerSecretProvider,
}


def _environment_provider(settings: Settings) -> EnvironmentSecretProvider:
    ttl = settings.secret_cache_ttl_seconds
    return EnvironmentSecretProvider(cache_ttl_seconds=ttl)


def build_secret_provider(settings: Settings) -> SecretProvider:
    if settings.is_local_lab:
        return _environment_provider(settings)
    if settings.allow_env_secret_provider:
        return _environment_provider(settings)
    if not settings.is_production_saas:
        return _environment_provider(settings)
    provider = settings.secret_manager_provider.strip().lower()
    if provider not in SUPPORTED_SECRET_MANAGER_PROVIDERS:
        raise SecretError(
            "SECRET_MANAGER_PROVIDER is not configured for production-saas",
            "secret_manager_missing",
        )
    provider_cls = _PROVIDER_CLASSES.get(provider)
    if provider_cls is None:
        return DisabledProductionSecretProvider(provider)
    return provider_cls(settings)
