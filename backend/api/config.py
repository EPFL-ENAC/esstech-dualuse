from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Config() itself has no other way to see `.env`: local dev's only reason
# this has worked at all is that every Makefile target runs commands
# through `dotenv -f ../.env run ...` (backend/Makefile), which loads
# `.env` into the process environment *before* Python ever starts. Any
# command invoked directly instead -- uvicorn, pytest, alembic, bypassing
# `make` -- silently never saw `.env` and failed with a confusing
# "Field required" error with no hint that the wrapper was the reason it
# worked elsewhere. This makes `.env` a source Config() reads itself,
# independent of how it's invoked.
#
# The three `.parent` hops below only mean "the repo root" in the local
# checkout: this file lives at <repo root>/backend/api/config.py, so
# parent -> backend/api, parent.parent -> backend/, parent.parent.parent
# -> <repo root>, where `.env` actually lives (next to this repo's own
# top-level Makefile and README.md).
#
# In the deployed container this same computation does NOT reach an
# equivalent "repo root" -- there isn't one to reach. backend/Dockerfile
# sets WORKDIR /app and copies api/, alembic.ini, migrations/, package/
# directly under it with no wrapping directory, i.e. /app *is* what
# corresponds to this repo's backend/, one nesting level shallower than
# here. So the same three-parent hop instead lands on the container's
# filesystem root (/), which will never contain a .env file -- Infisical
# injects real env vars straight into the process environment, and no
# COPY instruction ever adds a .env to the image (see backend/Dockerfile).
# That's a safe outcome, but by coincidence of the container's shallower
# layout, not because / is "the repo root" there. Verified directly by
# building backend/Dockerfile and checking, inside the built image:
# Path("/app/api/config.py").resolve().parent.parent.parent == Path("/"),
# and that Path("/.env").exists() is False.
#
# Whoever changes backend/Dockerfile's WORKDIR or COPY layout in the
# future should re-check this comment: it would change what these three
# `.parent` hops land on inside the container.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Config(BaseSettings):
    """Application settings loaded from environment variables (and .env)."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE)

    APP_URL: str = "http://localhost:9000"
    API_PATH: str = ""
    SECRET_KEY: str = "change-me"
    DATA_PATH: str = ""

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "app"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"

    @property
    def DB_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    OPENAI_API_URL: str = "https://inference-rcp.epfl.ch/v1"
    OPENAI_API_KEY: str
    MODEL_NAME: str = "deepseek-ai/DeepSeek-V4-Flash-0731"

    # None in an environment (e.g. a dev-branch deploy) where Google OAuth
    # credentials aren't provisioned yet -- api.services.auth gates the
    # routes that need them behind google_oauth_configured() rather than
    # crashing Config() itself at import time.
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    # Must exactly match what's registered in Google Cloud Console --
    # defaults to the local-dev value already registered there.
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"


@lru_cache()
def get_config():
    # Fields are injected from environment variables by pydantic-settings,
    # so ty cannot see them as arguments here.
    return Config()  # type: ignore


config = get_config()
