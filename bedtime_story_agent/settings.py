import os
from pathlib import Path

from dotenv import load_dotenv

# load .env from project root (parent of this package)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
MODEL_NAME: str = "gpt-3.5-turbo"

MAX_PLOT_REVISIONS: int = 2
MAX_STORY_REVISIONS: int = 2

DEFAULT_MAX_TOKENS: int = 3000
DEFAULT_TEMPERATURE: float = 0.1
