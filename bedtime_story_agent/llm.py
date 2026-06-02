import logging
from functools import lru_cache

from openai import OpenAI, OpenAIError

from bedtime_story_agent.settings import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    MODEL_NAME,
    OPENAI_API_KEY,
)
from bedtime_story_agent.tracing import configure_langsmith, langsmith_enabled

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> OpenAI | None:
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set")
        return None

    configure_langsmith()
    client = OpenAI(api_key=OPENAI_API_KEY)
    if langsmith_enabled():
        from langsmith.wrappers import wrap_openai

        return wrap_openai(client)
    return client


def call_model(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    json_mode: bool = False,
) -> str | None:
    """Call gpt-3.5-turbo; returns None on failure."""
    client = _get_client()
    if client is None:
        return None

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = client.chat.completions.create(**kwargs)
    except OpenAIError as e:
        logger.exception("OpenAI API call failed: %s", e)
        return None

    content = resp.choices[0].message.content
    if content is None:
        logger.error("OpenAI returned empty content")
        return None
    return content
