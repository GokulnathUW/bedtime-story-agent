#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROMPT_PREFIX = "bedtime-story-agent"
PROJECT_TAG = "bedtime-story-agent"
SYSTEM_PROMPTS = (
    "plot_writer_system",
    "plot_judge_system",
    "story_writer_system",
    "story_judge_system",
)


def _escape_braces_for_hub(text: str) -> str:
    # ChatPromptTemplate treats { } as variables; double them for literal JSON in judge prompts
    return text.replace("{", "{{").replace("}", "}}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Version prompts in LangSmith Hub.")
    parser.add_argument("--commit-description", default="")
    parser.add_argument(
        "--commit-tags",
        default="",
        help="Comma-separated tags (e.g. v2,story-writer)",
    )
    args = parser.parse_args()

    from langchain_core.prompts import ChatPromptTemplate
    from langsmith import Client
    from langsmith.utils import LangSmithConflictError

    from bedtime_story_agent.settings import LANGSMITH_API_KEY
    from prompts import templates

    if not LANGSMITH_API_KEY:
        print("Set LANGSMITH_API_KEY in .env before pushing prompts.", file=sys.stderr)
        return 1

    client = Client(api_key=LANGSMITH_API_KEY)
    commit_tags = [t.strip() for t in args.commit_tags.split(",") if t.strip()]
    if PROJECT_TAG not in commit_tags:
        commit_tags.insert(0, PROJECT_TAG)

    for name in SYSTEM_PROMPTS:
        content: str = getattr(templates, name)
        if not content.strip():
            print(f"Skip {name}: empty", file=sys.stderr)
            continue

        prompt = ChatPromptTemplate.from_messages([("system", _escape_braces_for_hub(content))])
        identifier = f"{PROMPT_PREFIX}-{name}"
        try:
            url = client.push_prompt(
                identifier,
                object=prompt,
                commit_description=args.commit_description or None,
                commit_tags=commit_tags or None,
            )
        except LangSmithConflictError:
            print(f"Skipped {identifier}: unchanged since latest commit")
            continue
        print(f"Pushed {identifier} -> {url}")

    print("Done. Open LangSmith → Prompts to compare commits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
