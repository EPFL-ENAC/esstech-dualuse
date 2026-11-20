"""verify_schema_migrated() (api/db.py) against a faked current revision.

_current_schema_revision is monkeypatched rather than exercised against a
real database: on the "never migrated" branch it would need to trigger a
"relation does not exist" error, and SQLite (this suite's usual
Postgres-free stand-in) raises a different exception type for that than
asyncpg/Postgres does (see _current_schema_revision's docstring), so it
can't stand in here. That branch, and the rest of this function's real
DB behavior, was instead verified manually against a real Postgres.
"""

import pytest

import api.db as db_module
from api.db import _expected_head_revision, verify_schema_migrated


def _database_at(monkeypatch, revision: str | None) -> None:
    async def _fake_current_revision() -> str | None:
        return revision

    monkeypatch.setattr(db_module, "_current_schema_revision", _fake_current_revision)


async def test_verify_schema_migrated_raises_on_an_outdated_revision(monkeypatch):
    _database_at(monkeypatch, "some-old-revision")

    with pytest.raises(RuntimeError) as exc_info:
        await verify_schema_migrated()

    message = str(exc_info.value)
    assert "some-old-revision" in message
    assert "make db-upgrade" in message


async def test_verify_schema_migrated_raises_on_a_never_migrated_database(
    monkeypatch,
):
    _database_at(monkeypatch, None)

    with pytest.raises(RuntimeError):
        await verify_schema_migrated()


async def test_verify_schema_migrated_passes_at_the_head_revision(monkeypatch):
    _database_at(monkeypatch, _expected_head_revision())

    await verify_schema_migrated()
