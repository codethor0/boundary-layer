"""Alert webhook configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebhookSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    auth_enabled: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_ALERT_WEBHOOK_AUTH_ENABLED",
    )
    auth_token: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN",
    )
    max_stored_alerts: int = Field(
        default=1000,
        validation_alias="BOUNDARY_LAYER_ALERT_WEBHOOK_MAX_ALERTS",
    )
    boundary_layer_env: str = Field(
        default="development",
        validation_alias="BOUNDARY_LAYER_ENV",
    )

    @model_validator(mode="after")
    def apply_production_defaults(self) -> WebhookSettings:
        if self.boundary_layer_env.strip().lower() == "production":
            self.auth_enabled = True
        return self

    @model_validator(mode="after")
    def validate_production_requirements(self) -> WebhookSettings:
        if self.auth_enabled and not self.auth_token.strip():
            raise ValueError(
                "BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN is required when "
                "webhook auth is enabled"
            )
        if self.auth_token.strip() and len(self.auth_token.strip()) < 24:
            raise ValueError(
                "BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN must be at least 24 characters"
            )
        return self


@lru_cache
def get_webhook_settings() -> WebhookSettings:
    return WebhookSettings()
