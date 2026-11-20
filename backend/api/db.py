import logging
from collections.abc import AsyncIterator
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSQLModelSession

from api.config import config

logger = logging.getLogger("uvicorn.error")

engine: AsyncEngine | None = None

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_engine() -> AsyncEngine:
    global engine
    if engine is None:
        engine = create_async_engine(
            config.DB_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
            pool_use_lifo=True,
            pool_timeout=30,
        )
    return engine


async def dispose_engine():
    """Dispose the async engine and its connection pool on shutdown."""
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None


def _expected_head_revision() -> str | None:
    """The revision `alembic upgrade head` would land on, read from the
    migration scripts on disk. alembic.ini's `script_location` is relative
    to the working directory, hence the absolute path."""

    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    return ScriptDirectory.from_config(alembic_cfg).get_current_head()


async def _current_schema_revision() -> str | None:
    """The database's current Alembic revision, or None if `alembic_version`
    doesn't exist yet (schema never migrated).

    A separate function so tests can monkeypatch it: SQLite raises
    OperationalError for a missing table, not the ProgrammingError
    asyncpg/Postgres raises, so it can't exercise this branch.
    """

    async with get_engine().connect() as conn:
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        except ProgrammingError:
            return None
        row = result.first()
        return row[0] if row is not None else None


async def verify_schema_migrated() -> None:
    """Fail fast if the database isn't at Alembic's head revision, rather
    than surfacing asyncpg "relation does not exist" errors on first use.
    `alembic upgrade head` runs before startup (backend/start.sh in Docker,
    `make db-upgrade` locally)."""

    current_revision = await _current_schema_revision()
    expected_revision = _expected_head_revision()
    if current_revision != expected_revision:
        message = (
            "Database schema is not migrated (found revision "
            f"{current_revision!r}, expected {expected_revision!r}). "
            "Run `make db-upgrade` first."
        )
        logger.error(message)
        raise RuntimeError(message)


async def get_db_session() -> AsyncIterator[AsyncSQLModelSession]:
    # expire_on_commit=False: expired attributes reload on access, and that
    # implicit IO raises MissingGreenlet under async SQLAlchemy. Services
    # read fields off records they just committed.
    async with AsyncSQLModelSession(get_engine(), expire_on_commit=False) as session:
        yield session
