#!/usr/bin/env python3
"""Push system prompts from prompts/templates.py to the LangSmith Prompt Hub."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROMPT_PREFIX = "bedtime-story-agent"
SYSTEM_PROMPTS = (
    "plot_writer_system",
    "plot_judge_system",
    "story_writer_system",
    "story_judge_system",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Version prompts in LangSmith Hub.")
    parser.add_argument(
        "--commit-description",
        default="",
        help="Optional description for this prompt commit",
    )
    parser.add_argument(
        "--commit-tags",
        default="",
        help="Comma-separated tags for this commit (e.g. v2,story-writer,dialogue)",
    )
    args = parser.parse_args()

    from langchain_core.prompts import ChatPromptTemplate
    from langsmith import Client

    from bedtime_story_agent.settings import LANGSMITH_API_KEY
    from prompts import templates

    if not LANGSMITH_API_KEY:
        print("Set LANGSMITH_API_KEY in .env before pushing prompts.", file=sys.stderr)
        return 1

    client = Client(api_key=LANGSMITH_API_KEY)
    commit_tags = [t.strip() for t in args.commit_tags.split(",") if t.strip()] or None

    for name in SYSTEM_PROMPTS:
        content: str = getattr(templates, name)
        if not content.strip():
            print(f"Skip {name}: empty", file=sys.stderr)
            continue

        prompt = ChatPromptTemplate.from_messages([("system", content)])
        identifier = f"{PROMPT_PREFIX}/{name}"
        url = client.push_prompt(
            identifier,
            object=prompt,
            commit_description=args.commit_description or None,
            commit_tags=commit_tags,
        )
        print(f"Pushed {identifier} -> {url}")

    print("Done. Open LangSmith → Prompts to compare commits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
