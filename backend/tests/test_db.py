"""Tests for verify_schema_migrated() and _expected_head_revision()
(api/db.py).

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


def test_expected_head_revision_reads_a_real_revision_from_disk():
    revision = _expected_head_revision()

    assert isinstance(revision, str)
    assert revision != ""


async def test_verify_schema_migrated_raises_when_revision_does_not_match(
    monkeypatch,
):
    async def _fake_current_revision(db_url: str | None = None) -> str | None:
        return "some-old-revision"

    monkeypatch.setattr(db_module, "_current_schema_revision", _fake_current_revision)
    monkeypatch.setattr(db_module, "_expected_head_revision", lambda: "head-revision")

    with pytest.raises(RuntimeError) as exc_info:
        await verify_schema_migrated()

    message = str(exc_info.value)
    assert "some-old-revision" in message
    assert "head-revision" in message
    assert "make db-upgrade" in message


async def test_verify_schema_migrated_passes_when_revision_matches(monkeypatch):
    async def _fake_current_revision(db_url: str | None = None) -> str | None:
        return "head-revision"

    monkeypatch.setattr(db_module, "_current_schema_revision", _fake_current_revision)
    monkeypatch.setattr(db_module, "_expected_head_revision", lambda: "head-revision")

    await verify_schema_migrated()  # must not raise
