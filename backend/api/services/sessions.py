from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Session
from api.models.enums import SessionMode, SessionRoute
from api.services.errors import ConflictError, NotFoundError


class SessionCreate(BaseModel):
    """Request body for starting a session."""

    route: SessionRoute = SessionRoute.STUDENT


class SessionCreated(BaseModel):
    """A newly started session."""

    id: UUID
    route: SessionRoute
    mode: SessionMode
    started_at: datetime


async def create_session(
    session: AsyncSession,
    *,
    learner_id: UUID,
    route: SessionRoute,
) -> SessionCreated:
    """Start an individual session for this learner, on the given route."""

    record = Session(
        route=route,
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


def require_route(actual: SessionRoute, expected: SessionRoute) -> None:
    if actual != expected:
        raise ConflictError(
            f"Session is not a {expected.value.capitalize()}-route session"
        )


async def get_owned_session(
    session: AsyncSession,
    *,
    session_id: UUID,
    learner_id: UUID,
    route: SessionRoute,
) -> Session:
    """Load a session, treating another learner's session as nonexistent, and
    reject one that belongs to the other route."""

    record = (
        await session.exec(
            select(Session).where(
                Session.id == session_id, Session.learner_id == learner_id
            )
        )
    ).first()
    if record is None:
        raise NotFoundError("Session not found")

    require_route(record.route, route)
    return record
