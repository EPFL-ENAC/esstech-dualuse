import pytest
from openai import OpenAIError

from api.config import config
from api.llm import get_openai_client


def test_openai_config_defaults():
    assert config.OPENAI_API_URL == "https://inference-rcp.epfl.ch/v1"
    assert config.MODEL_NAME == "deepseek-ai/DeepSeek-V4-Flash-0731"
    assert isinstance(config.OPENAI_API_KEY, str)


def test_get_openai_client_requires_key():
    # Without a configured key, building the client must fail with a clear error.
    if not config.OPENAI_API_KEY:
        with pytest.raises(OpenAIError):
            get_openai_client()
    else:
        # A key is configured, so the client must construct successfully.
        assert get_openai_client() is not None
