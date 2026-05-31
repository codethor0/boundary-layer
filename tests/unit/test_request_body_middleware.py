"""Request body size middleware tests."""

import pytest
from starlette.requests import Request

from apps.api.middleware import RequestBodySizeMiddleware
from tests.helpers.auth_tenancy import production_saas_settings


async def _call_middleware(settings, content_length: str | None):
    middleware = RequestBodySizeMiddleware(app=None)

    async def call_next(request):
        from starlette.responses import Response

        return Response(status_code=200)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/labs/redis/run",
        "headers": [],
        "query_string": b"",
    }
    if content_length is not None:
        scope["headers"] = [(b"content-length", content_length.encode())]
    request = Request(scope)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("apps.api.middleware.get_settings", lambda: settings)
        return await middleware.dispatch(request, call_next)


@pytest.mark.asyncio
async def test_local_lab_skips_body_size_guard():
    from apps.api import config

    settings = config.Settings()
    response = await _call_middleware(settings, "999999")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_production_saas_rejects_oversized_body():
    settings = production_saas_settings(MAX_REQUEST_BODY_BYTES="128")
    response = await _call_middleware(settings, "256")
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_production_saas_allows_small_body():
    settings = production_saas_settings(MAX_REQUEST_BODY_BYTES="1024")
    response = await _call_middleware(settings, "100")
    assert response.status_code == 200
