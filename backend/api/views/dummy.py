from fastapi import APIRouter

from api.services.dummy import DummyResponse

router = APIRouter()


@router.get(
    "/dummy",
    response_model=DummyResponse,
    summary="Dummy endpoint",
    description="A placeholder endpoint that returns a static greeting.",
    tags=["Dummy"],
)
async def dummy() -> DummyResponse:
    """Example endpoint to be replaced by real business logic."""

    return DummyResponse(message="Hello from the dummy endpoint")
