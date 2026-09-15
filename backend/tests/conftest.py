import os
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# These must be set before any test module imports `api.config`, so the
# settings singleton is built with a valid API key (which is required).
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key-for-testing-only")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id-for-testing-only")
os.environ.setdefault(
    "GOOGLE_CLIENT_SECRET", "test-google-client-secret-for-testing-only"
)

# Registers every model's table on SQLModel.metadata for the db_session fixture.
import api.models  # noqa: E402, F401


@pytest.fixture
async def client():
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache-test")

    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """An isolated, in-memory SQLite session with all tables created.

    A single StaticPool connection is required so the in-memory database
    survives across checkouts -- the default pool would otherwise hand out
    a fresh (empty) `:memory:` database per connection.
    """

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # expire_on_commit=False: tests read ids off committed objects (e.g.
    # `case.id`) without an explicit refresh, which async SQLAlchemy can't
    # do safely via plain attribute access once those attributes expire.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()


@pytest.fixture
def learner() -> dict[str, UUID]:
    """The identity `app_client` requests run as.

    A mutable holder rather than a plain value so a test can become a second
    learner mid-test (`learner["id"] = uuid4()`), which is what the ownership
    checks need. The override reads it per request.
    """

    return {"id": uuid4()}


@pytest.fixture
async def app_client(db_session, learner):
    """An HTTP client whose endpoints run against `db_session`.

    IMPORTANT: the API and the test share one session, so commit any fixture
    data with `await db_session.commit()` *before* calling the API. A service
    that hits a conflict rolls the session back, which silently discards
    uncommitted setup rows -- the test then fails looking like missing data
    rather than like the rollback it actually is.
    """

    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache-test")

    from api.db import get_db_session
    from api.dependencies import get_current_learner
    from api.main import app

    async def _override_session():
        yield db_session

    async def _override_learner() -> UUID:
        return learner["id"]

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_current_learner] = _override_learner

    # try/finally, not cleanup after the yield: a failing assertion propagates
    # through the yield point, and `app` is a module-level singleton whose
    # overrides would leak into every later test.
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_current_learner, None)
