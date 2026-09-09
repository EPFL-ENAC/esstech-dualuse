from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Session
from api.models.enums import SessionMode, SessionRoute
from api.services.errors import NotFoundError


class SessionCreated(BaseModel):
    """A newly started session."""

    id: UUID
    route: SessionRoute
    mode: SessionMode
    started_at: datetime


async def create_session(session: AsyncSession, *, learner_id: UUID) -> SessionCreated:
    """Start a student/individual session for this learner."""

    record = Session(
        route=SessionRoute.STUDENT,
        mode=SessionMode.INDIVIDUAL,
        learner_id=learner_id,
    )
    session.add(record)
    await session.commit()

    return SessionCreated(
        id=record.id,
        route=record.route,
        mode=record.mode,
        started_at=record.started_at,
    )


async def get_owned_session(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID
) -> Session:
    """Load a session, treating another learner's session as nonexistent."""

    record = (
        await session.exec(
            select(Session).where(
                Session.id == session_id, Session.learner_id == learner_id
            )
        )
    ).first()
    if record is None:
        raise NotFoundError("Session not found")

    return record
