class ServiceError(Exception):
    """A rejection raised by the service layer, carrying its HTTP status.

    Services stay free of FastAPI imports: `main.py` registers a single
    handler that turns these into responses, so business rules are expressed
    once and the web layer decides how to render them.
    """

    status_code: int = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(ServiceError):
    """The resource does not exist, or does not belong to this learner.

    Ownership violations deliberately reuse this rather than a dedicated
    "forbidden" error: another learner's session must be indistinguishable
    from one that never existed, so probing an id reveals nothing.
    """

    status_code = 404


class ConflictError(ServiceError):
    """The request contradicts the current state, and a retry would too."""

    status_code = 409


class ValidationError(ServiceError):
    """The request's content is invalid, independent of who sent it or when."""

    status_code = 422
