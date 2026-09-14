from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Session
from api.models.enums import SessionMode, SessionRoute
from api.services.errors import NotFoundError


class SessionCreate(BaseModel):
    """Request body for starting a session. Defaults to the Student route,
    unchanged from before this field existed."""

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
    route: SessionRoute = SessionRoute.STUDENT,
) -> SessionCreated:
    """Start an individual session for this learner, on the given route.

    route defaults to STUDENT, matching this function's behavior before
    Researcher-route sessions could be created at all -- an existing
    caller that never mentions route is unaffected.
    """

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


async def get_owned_session(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID
) -> Session:
    """Load a session, treating another learner's session as nonexistent.

    Ownership-only: unlike require_researcher_route on the Researcher side
    (api/services/researcher.py), nothing here -- or in any Student-route
    service that calls this (intake.py, encounters.py::create_encounter) --
    checks Session.route. A Researcher-route session_id currently passes
    every Student-route ownership check unchanged. Known gap, correctly out
    of scope as of the M1 route-choice screen: flagged explicitly rather
    than fixed silently. If this is ever closed, add a symmetric
    require_student_route(route) check to each caller, mirroring
    require_researcher_route.
    """

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
