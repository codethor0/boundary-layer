"""Runtime configuration for BoundaryLayer API."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_AUTH_PROVIDERS = frozenset({"oidc", "oidc-test"})
SUPPORTED_OBJECT_STORAGE_BACKENDS = frozenset({"s3", "gcs", "r2"})
SUPPORTED_SECRET_MANAGER_PROVIDERS = frozenset(
    {"aws", "gcp", "azure", "doppler", "vault"}
)
LOCAL_MANAGED_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "postgres",
        "redis",
        "boundary-layer-postgres",
        "boundary-layer-redis",
    }
)

INSECURE_SECRET_KEY_MARKERS = (
    "changeme",
    "change-me",
    "local-dev-hmac-secret-change-me",
    "your-secret-here",
    "placeholder-secret",
)


def is_valid_https_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    boundary_layer_env: str = Field(
        default="development",
        validation_alias="BOUNDARY_LAYER_ENV",
    )
    boundary_layer_profile: str = Field(
        default="local-lab",
        validation_alias="BOUNDARY_LAYER_PROFILE",
    )
    app_version: str = "1.3.5"

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
    trust_proxy_headers: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_TRUST_PROXY_HEADERS",
    )

    auth_provider: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_AUTH_PROVIDER",
    )
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="", validation_alias="REDIS_URL")
    secret_key: str = Field(default="", validation_alias="BOUNDARY_LAYER_SECRET_KEY")
    allowed_origins: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_ALLOWED_ORIGINS",
    )
    public_base_url: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_PUBLIC_BASE_URL",
    )
    secure_cookies: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_SECURE_COOKIES",
    )
    file_storage_backend: str = Field(
        default="",
        validation_alias="BOUNDARY_LAYER_FILE_STORAGE_BACKEND",
    )
    audit_log_enabled: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_AUDIT_LOG_ENABLED",
    )

    oidc_issuer_url: str = Field(default="", validation_alias="OIDC_ISSUER_URL")
    oidc_audience: str = Field(default="", validation_alias="OIDC_AUDIENCE")
    oidc_jwks_url: str = Field(default="", validation_alias="OIDC_JWKS_URL")
    oidc_algorithms: str = Field(
        default="RS256",
        validation_alias="OIDC_ALGORITHMS",
    )
    oidc_required_claims: str = Field(
        default="",
        validation_alias="OIDC_REQUIRED_CLAIMS",
    )
    oidc_tenant_claim: str = Field(
        default="https://boundarylayer.dev/tenant_id",
        validation_alias="OIDC_TENANT_CLAIM",
    )
    oidc_roles_claim: str = Field(
        default="https://boundarylayer.dev/roles",
        validation_alias="OIDC_ROLES_CLAIM",
    )
    oidc_subject_claim: str = Field(
        default="sub",
        validation_alias="OIDC_SUBJECT_CLAIM",
    )
    oidc_email_claim: str = Field(default="email", validation_alias="OIDC_EMAIL_CLAIM")
    oidc_required_roles: str = Field(
        default="",
        validation_alias="OIDC_REQUIRED_ROLES",
    )
    oidc_clock_skew_seconds: int = Field(
        default=60,
        validation_alias="OIDC_CLOCK_SKEW_SECONDS",
    )

    db_pool_min_size: int = Field(default=1, validation_alias="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=10, validation_alias="DB_POOL_MAX_SIZE")
    db_connect_timeout_seconds: int = Field(
        default=5,
        validation_alias="DB_CONNECT_TIMEOUT_SECONDS",
    )
    db_ssl_mode: str = Field(default="", validation_alias="DB_SSL_MODE")

    redis_connect_timeout_seconds: int = Field(
        default=3,
        validation_alias="REDIS_CONNECT_TIMEOUT_SECONDS",
    )
    redis_key_prefix: str = Field(default="", validation_alias="REDIS_KEY_PREFIX")

    object_storage_bucket: str = Field(
        default="",
        validation_alias="OBJECT_STORAGE_BUCKET",
    )
    object_storage_region: str = Field(
        default="",
        validation_alias="OBJECT_STORAGE_REGION",
    )
    object_storage_prefix: str = Field(
        default="",
        validation_alias="OBJECT_STORAGE_PREFIX",
    )
    object_storage_kms_key_id: str = Field(
        default="",
        validation_alias="OBJECT_STORAGE_KMS_KEY_ID",
    )
    object_storage_presigned_url_ttl_seconds: int = Field(
        default=900,
        validation_alias="OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS",
    )

    secret_manager_provider: str = Field(
        default="",
        validation_alias="SECRET_MANAGER_PROVIDER",
    )
    secret_manager_project_or_path: str = Field(
        default="",
        validation_alias="SECRET_MANAGER_PROJECT_OR_PATH",
    )
    secret_rotation_required: bool = Field(
        default=False,
        validation_alias="SECRET_ROTATION_REQUIRED",
    )

    allow_local_managed_endpoints: bool = Field(
        default=False,
        validation_alias="BOUNDARY_LAYER_ALLOW_LOCAL_MANAGED_ENDPOINTS",
    )

    @field_validator("boundary_layer_profile")
    @classmethod
    def normalize_profile(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"local-lab", "production-like", "production-saas"}
        if normalized not in allowed:
            raise ValueError(
                "BOUNDARY_LAYER_PROFILE must be one of: "
                "local-lab, production-like, production-saas"
            )
        return normalized

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
        self.trust_proxy_headers = True
        return self

    @model_validator(mode="after")
    def validate_production_requirements(self) -> Settings:
        if self.boundary_layer_env != "production":
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

    @model_validator(mode="after")
    def validate_production_saas_requirements(self) -> Settings:
        if not self.is_production_saas:
            return self

        issues: list[str] = []
        provider = self.auth_provider.strip().lower()
        if provider not in SUPPORTED_AUTH_PROVIDERS:
            issues.append(
                "BOUNDARY_LAYER_AUTH_PROVIDER must be one of: "
                + ", ".join(sorted(SUPPORTED_AUTH_PROVIDERS))
            )
        if not self.auth_enabled:
            issues.append("BOUNDARY_LAYER_AUTH_ENABLED must be true")
        if not self.oidc_issuer_url.strip() or not is_valid_https_url(
            self.oidc_issuer_url
        ):
            issues.append("OIDC_ISSUER_URL must be a valid https URL")
        if not self.oidc_audience.strip():
            issues.append("OIDC_AUDIENCE is required")
        if not self.oidc_jwks_url.strip() or not is_valid_https_url(self.oidc_jwks_url):
            issues.append("OIDC_JWKS_URL must be a valid https URL")
        algorithms = self.oidc_algorithms_list
        if not algorithms:
            issues.append("OIDC_ALGORITHMS is required")
        elif any(algorithm.lower() == "none" for algorithm in algorithms):
            issues.append("OIDC_ALGORITHMS must not allow none")
        if not self.auth_provider.strip():
            issues.append("BOUNDARY_LAYER_AUTH_PROVIDER is required")
        if not self.database_url.strip():
            issues.append("DATABASE_URL is required")
        if not self.redis_url.strip():
            issues.append("REDIS_URL is required")
        if len(self.secret_key.strip()) < 32:
            issues.append("BOUNDARY_LAYER_SECRET_KEY must be at least 32 characters")
        elif self._secret_key_is_insecure():
            issues.append("BOUNDARY_LAYER_SECRET_KEY must not use insecure defaults")
        if not self.allowed_origins.strip():
            issues.append("BOUNDARY_LAYER_ALLOWED_ORIGINS is required")
        elif self._origins_allow_wildcard(self.allowed_origins):
            issues.append("BOUNDARY_LAYER_ALLOWED_ORIGINS must not use wildcards")
        if not self.public_base_url.strip():
            issues.append("BOUNDARY_LAYER_PUBLIC_BASE_URL is required")
        if not self.secure_cookies:
            issues.append("BOUNDARY_LAYER_SECURE_COOKIES must be true")
        if not self.trust_proxy_headers:
            issues.append("BOUNDARY_LAYER_TRUST_PROXY_HEADERS must be explicitly true")
        if not self.metrics_token.strip():
            issues.append("BOUNDARY_LAYER_METRICS_TOKEN is required")
        if not self.file_storage_backend.strip():
            issues.append("BOUNDARY_LAYER_FILE_STORAGE_BACKEND is required")
        else:
            backend = self.file_storage_backend.strip().lower()
            if backend in {"local", "disk", "filesystem"}:
                issues.append(
                    "BOUNDARY_LAYER_FILE_STORAGE_BACKEND must not use local disk"
                )
        if not self.audit_log_enabled:
            issues.append("BOUNDARY_LAYER_AUDIT_LOG_ENABLED must be true")
        if not self.oidc_tenant_claim.strip():
            issues.append("OIDC_TENANT_CLAIM is required")
        if not self.oidc_roles_claim.strip():
            issues.append("OIDC_ROLES_CLAIM is required")
        if not self.secret_manager_provider.strip():
            issues.append("SECRET_MANAGER_PROVIDER is required")
        else:
            provider_name = self.secret_manager_provider.strip().lower()
            if provider_name not in SUPPORTED_SECRET_MANAGER_PROVIDERS:
                issues.append(
                    "SECRET_MANAGER_PROVIDER must be one of: "
                    + ", ".join(sorted(SUPPORTED_SECRET_MANAGER_PROVIDERS))
                )
        if not self.secret_manager_project_or_path.strip():
            issues.append("SECRET_MANAGER_PROJECT_OR_PATH is required")
        if not self.redis_key_prefix.strip():
            issues.append("REDIS_KEY_PREFIX is required")
        if self.file_storage_backend.strip():
            backend = self.file_storage_backend.strip().lower()
            if backend in SUPPORTED_OBJECT_STORAGE_BACKENDS:
                if not self.object_storage_bucket.strip():
                    issues.append("OBJECT_STORAGE_BUCKET is required")
                if not self.object_storage_region.strip():
                    issues.append("OBJECT_STORAGE_REGION is required")
        issues.extend(self._validate_managed_database_url())
        issues.extend(self._validate_managed_redis_url())

        if self.is_staging:
            if provider == "oidc-test":
                issues.append(
                    "BOUNDARY_LAYER_AUTH_PROVIDER must be oidc in staging; "
                    "oidc-test is test-only"
                )
            if self.public_base_url.strip() and not is_valid_https_url(
                self.public_base_url
            ):
                issues.append(
                    "BOUNDARY_LAYER_PUBLIC_BASE_URL must be a valid https URL"
                )

        if issues:
            raise ValueError("; ".join(issues))
        return self

    def _validate_managed_database_url(self) -> list[str]:
        issues: list[str] = []
        url = self.database_url.strip()
        if not url:
            return issues
        parsed = urlparse(url)
        host = (parsed.hostname or "").strip().lower()
        if (
            host
            and host in LOCAL_MANAGED_HOSTS
            and not self.allow_local_managed_endpoints
        ):
            issues.append(
                "DATABASE_URL must not use localhost or container hostnames "
                "in production-saas"
            )
        sslmode = self._database_ssl_mode()
        if sslmode != "require":
            issues.append(
                "DATABASE_URL or DB_SSL_MODE must require SSL (sslmode=require)"
            )
        return issues

    def _validate_managed_redis_url(self) -> list[str]:
        issues: list[str] = []
        url = self.redis_url.strip()
        if not url:
            return issues
        parsed = urlparse(url)
        if parsed.scheme != "rediss":
            issues.append("REDIS_URL must use rediss:// in production-saas")
        host = (parsed.hostname or "").strip().lower()
        if (
            host
            and host in LOCAL_MANAGED_HOSTS
            and not self.allow_local_managed_endpoints
        ):
            issues.append(
                "REDIS_URL must not use localhost or container hostnames "
                "in production-saas"
            )
        return issues

    def _database_ssl_mode(self) -> str:
        configured = self.db_ssl_mode.strip().lower()
        if configured:
            return configured
        parsed = urlparse(self.database_url.strip())
        if parsed.query:
            for part in parsed.query.split("&"):
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                if key.strip().lower() in {"sslmode", "ssl_mode"}:
                    return value.strip().lower()
        return ""

    def _secret_key_is_insecure(self) -> bool:
        normalized = self.secret_key.strip().lower()
        if len(normalized) < 32:
            return True
        return normalized in INSECURE_SECRET_KEY_MARKERS

    @staticmethod
    def _origins_allow_wildcard(origins: str) -> bool:
        for origin in origins.split(","):
            cleaned = origin.strip()
            if cleaned == "*" or cleaned.endswith("/*"):
                return True
        return False

    @property
    def oidc_algorithms_list(self) -> list[str]:
        if not self.oidc_algorithms.strip():
            return []
        return [
            part.strip() for part in self.oidc_algorithms.split(",") if part.strip()
        ]

    @property
    def oidc_required_claims_list(self) -> list[str]:
        if not self.oidc_required_claims.strip():
            return []
        return [
            part.strip()
            for part in self.oidc_required_claims.split(",")
            if part.strip()
        ]

    @property
    def is_staging(self) -> bool:
        return self.boundary_layer_env == "staging"

    @property
    def oidc_required_roles_list(self) -> list[str]:
        if not self.oidc_required_roles.strip():
            return []
        return [
            part.strip() for part in self.oidc_required_roles.split(",") if part.strip()
        ]

    @property
    def is_production_saas(self) -> bool:
        return self.boundary_layer_profile == "production-saas"

    @property
    def is_production(self) -> bool:
        if self.boundary_layer_profile in {"production-like", "production-saas"}:
            return True
        return self.boundary_layer_env == "production"

    @property
    def is_local_lab(self) -> bool:
        return (
            self.boundary_layer_profile == "local-lab"
            and self.boundary_layer_env != "production"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        origins = self.allowed_origins.strip() or self.cors_origins.strip()
        if not origins:
            return []
        return [origin.strip() for origin in origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        if not self.trusted_hosts.strip():
            return []
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
