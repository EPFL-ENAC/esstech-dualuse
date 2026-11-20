import tempfile
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from api.config import Config


def test_config_ignores_env_file_keys_it_does_not_define(monkeypatch):
    # A developer's .env also carries keys for other tools and settings this
    # app no longer reads (e.g. OPENAI_API_KEY); startup must not fail on them.
    # The process environment outranks env_file, so clear APP_URL to observe
    # the file.
    monkeypatch.delenv("APP_URL", raising=False)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_URL=https://from-the-env-file.example\n")
        f.write("OPENAI_API_KEY=a-setting-this-app-no-longer-reads\n")
        env_file_path = f.name

    try:

        class ConfigWithEnvFile(Config):
            model_config = SettingsConfigDict(env_file=env_file_path)

        assert ConfigWithEnvFile().APP_URL == "https://from-the-env-file.example"
    finally:
        Path(env_file_path).unlink()


def test_config_builds_without_google_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

    class ConfigWithNoEnvFile(Config):
        # The developer's real .env may hold Google credentials, which would
        # otherwise fill these back in despite the delenv above.
        model_config = SettingsConfigDict(
            env_file="/definitely/does/not/exist/nope.env"
        )

    fresh_config = ConfigWithNoEnvFile()

    assert fresh_config.GOOGLE_CLIENT_ID is None
    assert fresh_config.GOOGLE_CLIENT_SECRET is None
