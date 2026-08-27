from functools import lru_cache

from openai import AsyncOpenAI

from api.config import config


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    """Build the shared async OpenAI client from the configured variables.

    The client is created lazily so the module can be imported even when no
    API key is set. Calling it without a key raises a clear error.
    """

    return AsyncOpenAI(
        base_url=config.OPENAI_API_URL,
        api_key=config.OPENAI_API_KEY,
    )


async def complete(prompt: str) -> str:
    """Send a simple prompt to the configured LLM and return its text answer.

    Example usage:

        from api.llm import complete
        answer = await complete("Explain this project in one sentence.")
    """

    client = get_openai_client()
    response = await client.responses.create(
        model=config.MODEL_NAME,
        input=prompt,
    )
    return response.output_text
