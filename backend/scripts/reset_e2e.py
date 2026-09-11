"""Reset the end-to-end test database to a clean, seedable state.

Run before an E2E suite, ahead of migrations and seeding:

    DB_NAME=app_e2e uv run python -m scripts.reset_e2e
    DB_NAME=app_e2e uv run alembic upgrade head
    DB_NAME=app_e2e uv run python -m scripts.seed_cases

This is destructive by design, so it refuses to run anywhere but a database
whose name starts with `app_e2e`. That guard is not hypothetical caution: the
connection target is built by `config.DB_URL`, a computed property, and an
attempt to override it through a `DB_URL` environment variable is silently
ignored -- which has already sent a migration at the real development
database once. `DB_NAME` *is* a real settings field and does take effect, but
the guard checks the resolved URL rather than trusting that.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from api.config import config

# Prefix, not an exact name: `app_e2e` locally and `app_e2e_ci` (or similar)
# on CI must both be allowed.
E2E_DB_PREFIX = "app_e2e"


def _resolved_database() -> str:
    """The database name that will actually be connected to."""

    resolved = make_url(config.DB_URL).database
    if resolved is None or not resolved.startswith(E2E_DB_PREFIX):
        raise RuntimeError(
            f"E2E reset may run only against an {E2E_DB_PREFIX}* database, "
            f"but the resolved database is {resolved!r}. Set DB_NAME."
        )
    if resolved != config.DB_NAME:
        # They are built from each other today; if that ever stops being true,
        # fail rather than truncate a database nobody named.
        raise RuntimeError(
            f"Resolved database {resolved!r} does not match DB_NAME "
            f"{config.DB_NAME!r}; refusing to guess which one is meant."
        )
    return resolved


async def _ensure_database_exists(name: str) -> None:
    """Create the E2E database if it is not there yet.

    Connects to the server's default `postgres` database, since a database
    cannot be created from inside itself. CREATE DATABASE cannot run in a
    transaction, hence the AUTOCOMMIT isolation level.
    """

    server_url = make_url(config.DB_URL).set(database="postgres")
    engine = create_async_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            exists = (
                await connection.execute(
                    text("select 1 from pg_database where datname = :name"),
                    {"name": name},
                )
            ).scalar()
            if exists is None:
                # The name is validated against E2E_DB_PREFIX above and comes
                # from settings, not from user input.
                await connection.execute(text(f'create database "{name}"'))
                print(f"created database {name}")
    finally:
        await engine.dispose()


async def _truncate_session_data(name: str) -> None:
    """Empty every table that hangs off `session`, leaving case content alone.

    TRUNCATE ... CASCADE walks the foreign-key graph itself, so this keeps
    working as tables are added: anything that references `session`, or
    references something that references it, goes too. Nothing in `case`,
    `case_tagged_pattern`, `case_tagged_gate` or `counter_case_link` points at
    `session`, so the cascade never reaches the seeded content.

    No RESTART IDENTITY: every primary key here is a UUID, not a sequence.
    """

    engine = create_async_engine(config.DB_URL)
    try:
        async with engine.begin() as connection:
            present = (
                await connection.execute(text("select to_regclass('public.session')"))
            ).scalar()
            if present is None:
                # First run against a brand-new database: migrations have not
                # created anything yet, so there is nothing to clear.
                print(f"{name}: no session table yet, nothing to truncate")
                return

            await connection.execute(text("truncate table session cascade"))
            print(f"{name}: truncated session and everything cascading from it")
    finally:
        await engine.dispose()


async def main() -> None:
    name = _resolved_database()
    await _ensure_database_exists(name)
    await _truncate_session_data(name)


if __name__ == "__main__":
    asyncio.run(main())
