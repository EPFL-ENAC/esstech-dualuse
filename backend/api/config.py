from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Locally this is <repo root>/.env. In the container (WORKDIR /app, no
# wrapping directory) the same hops resolve to /.env, which never exists:
# Infisical injects env vars directly. Re-check if the Dockerfile layout
# changes.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Config(BaseSettings):
    """Application settings loaded from environment variables (and .env)."""

    # extra="ignore": .env also carries values for other tools (docker-compose)
    # and settings this app no longer reads; neither should stop startup.
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    APP_URL: str = "http://localhost:9000"
    API_PATH: str = ""
    SECRET_KEY: str = "change-me"

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

    # None where Google OAuth credentials aren't provisioned (e.g. a
    # dev-branch deploy); the routes that need them are gated instead.
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    # Must exactly match what's registered in Google Cloud Console; the
    # default is the local-dev value registered there.
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"


config = Config()
