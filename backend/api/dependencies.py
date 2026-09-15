from uuid import UUID, uuid4

from fastapi import Depends, Request, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.services.auth import (
    AUTH_SESSION_COOKIE,
    find_learning_identity,
    verify_session_cookie,
)

LEARNER_ID_COOKIE = "dev_learner_id"


async def get_current_learner(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> UUID:
    """Learner identity seam.

    Tier (a): a real, signed session cookie (set by
    /auth/google/callback, api/views/auth.py) resolves through
    LearningIdentity to a real learner_id.

    Tier (b): unchanged since before real auth existed. A pseudonymous
    learner id, stored in a cookie so repeated requests from the same
    browser resolve to the same learner, minted here if absent. Kept
    for local dev/manual-testing convenience (e.g. the frontend's "Skip
    to student flow (dev)" bypass) -- not because the automated test
    suite depends on it: app_client's fixture overrides this whole
    function for every other test in this suite (tests/conftest.py), so
    tier (b)'s own correctness is instead covered by a dedicated
    regression test that calls this function directly.
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
    response.set_cookie(
        LEARNER_ID_COOKIE, str(learner_id), httponly=True, samesite="lax"
    )
    return learner_id
