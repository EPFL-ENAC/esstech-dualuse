"""Tests for Config's env_file mechanism (api/config.py) -- the fallback
that lets `.env` values reach the app even when a command bypasses the
Makefile's `dotenv run` wrapper (uvicorn/alembic/pytest invoked directly).
"""

import tempfile
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from api.config import Config


def test_config_with_missing_env_file_does_not_raise():
    """The critical case, proven first as a throwaway script before this
    test existed: a computed env_file path that doesn't exist on disk
    (the deployed container's real situation -- see _ENV_FILE's comment
    in api/config.py) must not raise or warn, and must still read real
    process environment variables normally."""

    class ConfigWithMissingEnvFile(Config):
        model_config = SettingsConfigDict(
            env_file="/definitely/does/not/exist/nope.env"
        )

    # Fields are injected from the environment by pydantic-settings (see
    # get_config()'s own comment, api/config.py), so ty cannot see them
    # as arguments here.
    instance = ConfigWithMissingEnvFile()  # type: ignore

    assert instance.OPENAI_API_KEY  # still reads real os.environ (conftest.py)


def test_config_with_real_env_file_reads_its_values():
    """The positive path: a real, existing env_file must actually be
    read. Nothing else in this suite exercises this -- conftest.py sets
    real process environment variables via os.environ.setdefault, which
    always outranks env_file by pydantic-settings' own precedence, so
    the rest of the suite passing proves nothing about file-reading
    actually working."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("DATA_PATH=value-read-from-the-real-env-file\n")
        env_file_path = f.name

    try:

        class ConfigWithRealEnvFile(Config):
            model_config = SettingsConfigDict(env_file=env_file_path)

        instance = ConfigWithRealEnvFile()  # type: ignore

        assert instance.DATA_PATH == "value-read-from-the-real-env-file"
    finally:
        Path(env_file_path).unlink()
