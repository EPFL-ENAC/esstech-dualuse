from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import INFO, basicConfig, warning

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from pydantic import BaseModel

from api.config import config
from api.db import create_db_and_tables, dispose_engine
from api.services.errors import ServiceError
from api.views.cases import router as cases_router
from api.views.dummy import router as dummy_router
from api.views.encounters import router as encounters_router
from api.views.sessions import router as sessions_router

basicConfig(level=INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    await create_db_and_tables()
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(root_path=config.API_PATH, lifespan=lifespan)

origins = [config.APP_URL] if config.APP_URL else []
if not config.APP_URL:
    warning(
        "config.APP_URL is not set. CORS will not allow any origins. "
        "Set config.APP_URL to enable cross-origin requests."
    )

# In addition to the configured URL, allow any local development origin
# (localhost or 127.0.0.1 on any port), so the dev frontend works regardless
# of the exact host and port used to open it.
LOCAL_ORIGIN_REGEX = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=LOCAL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheck(BaseModel):
    """Response model for the health check endpoint."""

    status: str = "OK"


@app.get(
    "/healthz",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
async def get_health() -> HealthCheck:
    """Endpoint to perform an API healthcheck."""

    return HealthCheck(status="OK")


@app.exception_handler(ServiceError)
async def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
    """Render a service-layer rejection, so services need no FastAPI import."""

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(
    dummy_router,
    tags=["Dummy"],
)

app.include_router(
    sessions_router,
    tags=["Sessions"],
)

app.include_router(
    cases_router,
    tags=["Cases"],
)

app.include_router(
    encounters_router,
    tags=["Encounters"],
)
