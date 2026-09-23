import asyncio
from logging.config import fileConfig
from typing import Any, Literal

from alembic import context
from alembic.autogenerate.api import AutogenContext
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel
from sqlmodel.sql.sqltypes import AutoString

from api.config import config as app_config
from api.models import (
    Case,
    CaseEncounter,
    CaseTaggedGate,
    CaseTaggedPattern,
    Commitment,
    ContrastEntry,
    CounterCaseLink,
    FeedbackRecord,
    Item,
    Session,
)

# Import the models so their tables are registered on SQLModel.metadata.
_models = (
    Case,
    CaseEncounter,
    CaseTaggedGate,
    CaseTaggedPattern,
    Commitment,
    ContrastEntry,
    CounterCaseLink,
    FeedbackRecord,
    Item,
    Session,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

config.set_main_option("sqlalchemy.url", app_config.DB_URL)


def render_item(
    type_: str, obj: Any, autogen_context: AutogenContext
) -> str | Literal[False]:
    """Render SQLModel's AutoString as the plain sa.String() it wraps.

    Without this, autogenerate embeds the fully-qualified
    `sqlmodel.sql.sqltypes.AutoString()` for every plain str column, but
    never adds a matching import for it: AutoString is a TypeDecorator
    from outside the sqlalchemy package, so Alembic's default type
    renderer (alembic.autogenerate.render._repr_type) falls through to
    its generic "unknown type" branch, which embeds the qualified name
    without ever adding the import (unlike its sqlalchemy.dialects.*
    branch, which does). A known Alembic/SQLModel interaction, not
    specific to this project.

    sa.String() produces identical DDL: AutoString adds no behavior
    beyond a MySQL-only default length, irrelevant on this project's
    Postgres. False falls back to Alembic's own rendering for every
    other type (enums, JSON, ... all render fine already, since this
    codebase always sets those explicitly via sa_column=Column(...)
    rather than letting SQLModel infer them).
    """

    if type_ == "type" and isinstance(obj, AutoString):
        return f"sa.String(length={obj.impl.length!r})"
    return False


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
