from uuid import UUID, uuid4

from fastapi import Depends, Request, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from api.cookies import AUTH_SESSION_COOKIE, LEARNER_ID_COOKIE, set_private_cookie
from api.db import get_db_session
from api.models import CaseEncounter, Session
from api.models.enums import SessionRoute
from api.services.auth import (
    SESSION_COOKIE_MAX_AGE,
    find_learning_identity,
    verify_session_cookie,
)
from api.services.encounters import get_owned_encounter
from api.services.sessions import get_owned_session


async def get_current_learner(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> UUID:
    """Learner identity seam.

    Tier (a): a signed session cookie set by /auth/google/callback resolves
    through LearningIdentity to a real learner_id.

    Tier (b): a pseudonymous learner id kept in a cookie, minted here if
    absent: the identity of every learner not signed in with Google, which
    is every learner while the frontend has no sign-in.
    """

    raw_session_cookie = request.cookies.get(AUTH_SESSION_COOKIE)
    if raw_session_cookie is not None:
        user_id = verify_session_cookie(raw_session_cookie)
        if user_id is not None:
            learning_identity = await find_learning_identity(session, user_id=user_id)
            if learning_identity is not None:
                return learning_identity.learner_id

    raw_cookie = request.cookies.get(LEARNER_ID_COOKIE)
    if raw_cookie is not None:
        try:
            return UUID(raw_cookie)
        except ValueError:
            pass

    learner_id = uuid4()
    set_private_cookie(
        response, LEARNER_ID_COOKIE, str(learner_id), max_age=SESSION_COOKIE_MAX_AGE
    )
    return learner_id


def owned_session(route: SessionRoute):
    """Dependency that loads the path's session, if this learner owns it and it
    is on `route`; 404 otherwise."""

    async def dependency(
        session_id: UUID,
        session: AsyncSession = Depends(get_db_session),
        learner_id: UUID = Depends(get_current_learner),
    ) -> Session:
        return await get_owned_session(
            session, session_id=session_id, learner_id=learner_id, route=route
        )

    return dependency


get_student_session = owned_session(SessionRoute.STUDENT)
get_researcher_session = owned_session(SessionRoute.RESEARCHER)


async def get_student_encounter(
    encounter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> CaseEncounter:
    return await get_owned_encounter(
        session, encounter_id=encounter_id, learner_id=learner_id
    )
