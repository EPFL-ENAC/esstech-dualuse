from uuid import UUID, uuid4

from fastapi import Request, Response

LEARNER_ID_COOKIE = "dev_learner_id"


async def get_current_learner(request: Request, response: Response) -> UUID:
    """Development identity seam.

    Returns a pseudonymous learner id, stored in a cookie so repeated
    requests from the same browser resolve to the same learner. This is the
    only place that knows how a learner is identified: once real auth
    (User + AuthIdentity + LearningIdentity) exists, only this function's
    body changes -- callers keep depending on `get_current_learner` as-is.
    """

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
