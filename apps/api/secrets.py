"""Secret manager abstraction for Production SaaS."""

from __future__ import annotations

import logging
import os
from typing import Protocol

from apps.api.config import Settings

logger = logging.getLogger("boundary_layer.api.secrets")

SUPPORTED_SECRET_MANAGER_PROVIDERS = frozenset(
    {"aws", "gcp", "azure", "doppler", "vault"}
)


class SecretError(Exception):
    """Secret lookup failure."""

    def __init__(self, message: str, code: str = "secret_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> str:
        """Return a secret value by name."""


class EnvironmentSecretProvider:
    """Read secrets from environment variables for local-lab and tests."""

    def get_secret(self, name: str) -> str:
        env_name = name.strip().upper()
        value = os.environ.get(env_name, "").strip()
        if not value:
            raise SecretError(f"Missing secret: {env_name}", "secret_not_found")
        logger.info("Loaded secret %s from environment", env_name)
        return value


class DisabledProductionSecretProvider:
    """Fail closed when production-saas lacks a configured secret manager adapter."""

    def __init__(self, provider: str) -> None:
        self._provider = provider

    def get_secret(self, name: str) -> str:
        logger.warning(
            "Secret lookup blocked for %s via unconfigured provider %s",
            name,
            self._provider,
        )
        raise SecretError(
            f"Secret manager adapter for {self._provider} is not implemented",
            "secret_manager_not_configured",
        )


def build_secret_provider(settings: Settings) -> SecretProvider:
    if settings.is_local_lab or not settings.is_production_saas:
        return EnvironmentSecretProvider()
    provider = settings.secret_manager_provider.strip().lower()
    if provider not in SUPPORTED_SECRET_MANAGER_PROVIDERS:
        raise SecretError(
            "SECRET_MANAGER_PROVIDER is not configured for production-saas",
            "secret_manager_missing",
        )
    return DisabledProductionSecretProvider(provider)
