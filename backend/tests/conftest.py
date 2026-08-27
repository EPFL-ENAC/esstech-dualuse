import os

import pytest
from httpx import ASGITransport, AsyncClient

# These must be set before any test module imports `api.config`, so the
# settings singleton is built with a valid API key (which is required).
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key-for-testing-only")


@pytest.fixture
async def client():
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache-test")

    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
