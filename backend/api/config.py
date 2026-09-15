from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application settings loaded from environment variables (and .env)."""

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

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    # Must exactly match what's registered in Google Cloud Console --
    # defaults to the local-dev value already registered there.
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"


@lru_cache()
def get_config():
    # Fields are injected from environment variables by pydantic-settings,
    # so ty cannot see them as arguments here.
    return Config()  # type: ignore


config = get_config()
