"""Runtime configuration for BoundaryLayer API."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    boundary_layer_env: str = Field(
        default="development",
        validation_alias="BOUNDARY_LAYER_ENV",
    )
    app_version: str = "1.2.0"

    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    api_log_level: str = Field(default="info", validation_alias="API_LOG_LEVEL")

    auth_enabled: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_AUTH_ENABLED",
    )
    api_key: str = Field(default="", validation_alias="BOUNDARY_LAYER_API_KEY")
    metrics_token: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_METRICS_TOKEN",
    )
    metrics_auth_required: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_METRICS_AUTH_REQUIRED",
    )

    allow_vulnerable: bool = Field(
        default=True,
        validation_alias="BOUNDARY_LAYER_ALLOW_VULNERABLE",
    )

    rate_limit_enabled: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_RATE_LIMIT_ENABLED",
    )
    rate_limit_requests: int = Field(
        default=120,
        validation_alias="BOUNDARY_LAYER_RATE_LIMIT_REQUESTS",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        validation_alias="BOUNDARY_LAYER_RATE_LIMIT_WINDOW_SECONDS",
    )
    rate_limit_backend: str = Field(
        default="memory",
        validation_alias="BOUNDARY_LAYER_RATE_LIMIT_BACKEND",
    )

    postgres_password: str = Field(default="", validation_alias="POSTGRES_PASSWORD")
    redis_password: str = Field(default="", validation_alias="REDIS_PASSWORD")
    session_hmac_secret: str = Field(
        default="",
        validation_alias="SESSION_HMAC_SECRET",
    )

    forwarded_allow_ips: str = Field(
        default="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        validation_alias="BOUNDARY_LAYER_FORWARDED_ALLOW_IPS",
    )
    expose_openapi: bool = Field(
        default=True,
        validation_alias="BOUNDARY_LAYER_EXPOSE_OPENAPI",
    )

    cors_enabled: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_CORS_ENABLED",
    )
    cors_origins: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_CORS_ORIGINS",
    )

    log_json: bool = Field(default=False, validation_alias="BOUNDARY_LAYER_LOG_JSON")
    log_request_id: bool = Field(
        default=True,
        validation_alias="BOUNDARY_LAYER_LOG_REQUEST_ID",
    )

    run_migrations: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_RUN_MIGRATIONS",
    )

    trusted_hosts: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_TRUSTED_HOSTS",
    )

    @field_validator("boundary_layer_env")
    @classmethod
    def normalize_env(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def apply_production_defaults(self) -> Settings:
        if not self.is_production:
            return self

        self.allow_vulnerable = False
        self.auth_enabled = True
        self.metrics_auth_required = True
        self.rate_limit_enabled = True
        self.rate_limit_backend = "redis"
        self.log_json = True
        self.run_migrations = True
        self.expose_openapi = False
        return self

    @model_validator(mode="after")
    def validate_production_requirements(self) -> Settings:
        if not self.is_production:
            return self

        if self.auth_enabled and not self.api_key.strip():
            raise ValueError(
                "BOUNDARY_LAYER_API_KEY is required when BOUNDARY_LAYER_ENV=production"
            )
        if self.metrics_auth_required and not self.metrics_token.strip():
            raise ValueError(
                "BOUNDARY_LAYER_METRICS_TOKEN is required when "
                "BOUNDARY_LAYER_ENV=production"
            )
        if self.api_key.strip() and len(self.api_key.strip()) < 24:
            raise ValueError("BOUNDARY_LAYER_API_KEY must be at least 24 characters")
        if self.metrics_token.strip() and len(self.metrics_token.strip()) < 24:
            raise ValueError(
                "BOUNDARY_LAYER_METRICS_TOKEN must be at least 24 characters"
            )
        for name, value in (
            ("POSTGRES_PASSWORD", self.postgres_password),
            ("REDIS_PASSWORD", self.redis_password),
            ("SESSION_HMAC_SECRET", self.session_hmac_secret),
        ):
            if len(value.strip()) < 16:
                raise ValueError(f"{name} must be at least 16 characters in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.boundary_layer_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return []
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def trusted_host_list(self) -> list[str]:
        if not self.trusted_hosts.strip():
            return []
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
