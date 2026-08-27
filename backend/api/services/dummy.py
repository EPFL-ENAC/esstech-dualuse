from pydantic import BaseModel


class DummyResponse(BaseModel):
    """Payload returned by the dummy endpoint."""

    message: str
