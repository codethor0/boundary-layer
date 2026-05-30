"""Application lifespan hooks."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.config import Settings, get_settings

logger = logging.getLogger("boundary_layer.api")


def _run_migrations(settings: Settings) -> None:
    if not settings.run_migrations:
        return

    try:
        from alembic import command
        from alembic.config import Config
    except ImportError as exc:
        raise RuntimeError(
            "Alembic is required when BOUNDARY_LAYER_RUN_MIGRATIONS=true"
        ) from exc

    alembic_cfg = Config("alembic.ini")
    logger.info("running database migrations")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.run_migrations:
        _run_migrations(settings)
    logger.info(
        "BoundaryLayer API started env=%s auth_enabled=%s",
        settings.boundary_layer_env,
        settings.auth_enabled,
    )
    yield
    logger.info("BoundaryLayer API shutdown complete")
