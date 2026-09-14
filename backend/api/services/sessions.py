from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Session
from api.models.enums import SessionMode, SessionRoute
from api.services.errors import ConflictError, NotFoundError


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

    Ownership-only, deliberately: this stays route-agnostic so both routes'
    services can share it, the same way require_researcher_route
    (api/services/researcher.py) and require_student_route below are two
    separate, explicit checks rather than being folded in here.
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


def require_student_route(route: SessionRoute) -> None:
    """Reject a session that is not on the Student route.

    Symmetric to require_researcher_route (api/services/researcher.py):
    ownership alone (get_owned_session/get_owned_encounter) only confirms
    whose session this is, not which flow it belongs to. Every Student-route
    service function calls this immediately after obtaining the session's
    route -- directly from get_owned_session, or via a second
    get_owned_session lookup keyed on encounter.session_id for the
    encounter-scoped ones, since CaseEncounter itself carries no route.
    """

    if route != SessionRoute.STUDENT:
        raise ConflictError("Session is not a Student-route session")
