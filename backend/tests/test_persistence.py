"""insert_once (api/services/persistence.py) settles every write-once race.

Simulated rather than observed: the fixture's single SQLite connection
serializes writers, so this proves the losing INSERT falls back to the winning
row, not that Postgres blocks the loser until the winner commits.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from api.models import LearningIdentity, User
from api.services.persistence import insert_once


async def _user(db_session) -> User:
    user = User()
    db_session.add(user)
    await db_session.commit()
    return user


async def test_insert_once_creates_the_row_when_none_exists(db_session):
    user = await _user(db_session)

    row, created = await insert_once(
        db_session, LearningIdentity(user_id=user.id), lambda: _never_called()
    )
    await db_session.commit()

    assert created
    assert (await db_session.exec(select(LearningIdentity))).one().learner_id == (
        row.learner_id
    )


async def test_insert_once_returns_the_winner_when_the_insert_loses(db_session):
    user = await _user(db_session)
    winner = LearningIdentity(user_id=user.id)
    db_session.add(winner)
    await db_session.commit()
    winner_id, user_id = winner.learner_id, user.id

    async def find_existing():
        return (
            await db_session.exec(
                select(LearningIdentity).where(LearningIdentity.user_id == user_id)
            )
        ).first()

    row, created = await insert_once(
        db_session, LearningIdentity(user_id=user_id), find_existing
    )

    assert not created
    assert row.learner_id == winner_id
    assert len((await db_session.exec(select(LearningIdentity))).all()) == 1


async def test_insert_once_reraises_a_violation_it_cannot_explain(db_session):
    user = await _user(db_session)
    db_session.add(LearningIdentity(user_id=user.id))
    await db_session.commit()

    async def find_nothing():
        return None

    with pytest.raises(IntegrityError):
        await insert_once(db_session, LearningIdentity(user_id=user.id), find_nothing)


async def _never_called():
    raise AssertionError("find_existing must not run when the insert succeeds")
