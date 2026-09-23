import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSQLModelSession

from api.config import config

logger = logging.getLogger("uvicorn.error")

engine: AsyncEngine | None = None

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_engine(db_url: str | None = None) -> AsyncEngine:
    global engine
    if engine is None:
        url = db_url or config.DB_URL
        kwargs: dict = {
            "pool_pre_ping": True,
        }
        if url.startswith("postgresql"):  # Skip for SQLite
            kwargs.update(
                pool_size=5,
                max_overflow=10,
                # Reclaim connections older than this (seconds)
                pool_recycle=1800,
                # Reuse the most-recently-used connection first
                pool_use_lifo=True,
                # How long to wait for a connection from the pool before raising
                pool_timeout=30,
            )
        engine = create_async_engine(url, **kwargs)
    return engine


async def dispose_engine():
    """Dispose the async engine and its connection pool on shutdown."""
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None


async def _retry_on_db_error(
    coro_factory,
    *,
    operation_name: str = "database operation",
    max_retries: int = 10,
    retry_interval: float = 2.0,
):
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except (OSError, OperationalError) as exc:
            last_exception = exc
            logger.warning(
                f"{operation_name} attempt {attempt + 1}/{max_retries} failed: {exc}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_interval)

    if last_exception is not None:
        raise last_exception
    raise RuntimeError(f"Failed {operation_name} after {max_retries} attempts")


def _expected_head_revision() -> str | None:
    """The revision `alembic upgrade head` would land on, read straight
    from the migration scripts on disk -- no DB call. Built from an
    absolute path rather than alembic.ini's relative `script_location` so
    this doesn't depend on the caller's current working directory."""

    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    return ScriptDirectory.from_config(alembic_cfg).get_current_head()


async def _current_schema_revision(db_url: str | None = None) -> str | None:
    """The database's current Alembic revision, or None if `alembic_version`
    doesn't exist yet (schema never migrated).

    Its own function, like exchange_google_code in api/services/auth.py,
    so tests can replace it with monkeypatch.setattr instead of needing a
    real Postgres to produce a "table does not exist" error: SQLite (the
    rest of this suite's usual Postgres-free stand-in) raises
    OperationalError for a missing table, not the ProgrammingError
    asyncpg/Postgres raises here, so it can't exercise this branch
    faithfully.
    """

    e = get_engine(db_url)

    async def _read() -> str | None:
        async with e.connect() as conn:
            try:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version")
                )
            except ProgrammingError:
                return None
            row = result.first()
            return row[0] if row is not None else None

    return await _retry_on_db_error(_read, operation_name="Database connection")


async def verify_schema_migrated(db_url: str | None = None) -> None:
    """Fail fast, with a clear message, if the database isn't at
    Alembic's head revision -- instead of letting the app start and only
    surfacing a raw asyncpg "relation does not exist" error on the first
    request that touches an unmigrated table.

    `alembic upgrade head` runs before this in every real environment
    (backend/start.sh in Docker, `make db-upgrade` for local dev per the
    README), so on the expected path this is one cheap SELECT plus a
    read of the migration files already on disk -- not a heavy check.
    """

    current_revision = await _current_schema_revision(db_url)
    expected_revision = _expected_head_revision()
    if current_revision != expected_revision:
        message = (
            "Database schema is not migrated (found revision "
            f"{current_revision!r}, expected {expected_revision!r}). "
            "Run `make db-upgrade` first."
        )
        logger.error(message)
        raise RuntimeError(message)


async def get_session(db_url: str | None = None):
    e = get_engine(db_url)

    async def _connect():
        async with e.connect() as conn:
            pass

    await _retry_on_db_error(
        _connect,
        operation_name="Database connection",
    )

    # expire_on_commit=False: after a commit, expired attributes reload on
    # access, and that implicit IO cannot run during plain attribute access
    # under async SQLAlchemy -- it raises MissingGreenlet. Services read ids
    # and fields off records they just wrote, so keep those loaded.
    async with AsyncSQLModelSession(e, expire_on_commit=False) as session:
        yield session


async def get_db_session() -> AsyncIterator[AsyncSQLModelSession]:
    """Route-facing session dependency.

    Wraps `get_session` because FastAPI reads a dependency's signature: the
    optional `db_url` argument would otherwise surface as a query parameter on
    every endpoint, letting a caller point the app at another database.
    """

    async for session in get_session():
        yield session
