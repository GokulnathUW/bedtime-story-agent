import logging
import os

from bedtime_story_agent.settings import (
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)

logger = logging.getLogger(__name__)

_configured = False


def configure_langsmith() -> bool:
    """Apply LangSmith env vars from settings. Returns True if tracing is on."""
    global _configured
    if _configured:
        return LANGSMITH_TRACING and bool(LANGSMITH_API_KEY)

    _configured = True
    if not LANGSMITH_API_KEY:
        logger.info("LangSmith: disabled (set LANGSMITH_API_KEY in .env to enable)")
        return False

    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
    if LANGSMITH_ENDPOINT:
        os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT

    if LANGSMITH_TRACING:
        os.environ["LANGSMITH_TRACING"] = "true"
        logger.info("LangSmith: tracing enabled (project=%s)", LANGSMITH_PROJECT)
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.info("LangSmith: API key set but LANGSMITH_TRACING is false")

    return LANGSMITH_TRACING
