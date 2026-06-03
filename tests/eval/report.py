from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent.state import StoryState
from bedtime_story_agent.metrics import story_flesch_kincaid_grade, story_word_count

EVAL_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "eval_results" / "eval_results.json"
)


def build_eval_record(
    *,
    case_id: str,
    category: str,
    request: str,
    state: StoryState,
) -> dict[str, Any]:
    return {
        "id": case_id,
        "category": category,
        "request": request,
        "plot_passed": state.plot_passed,
        "story_passed": state.story_passed,
        "words": story_word_count(state.story or ""),
        "grade": round(story_flesch_kincaid_grade(state.story or ""), 1),
        "plot_revisions": state.plot_revisions,
        "story_revisions": state.story_revisions,
        "summary_line": format_eval_line(state, request),
    }


def format_eval_line(state: StoryState, request: str) -> str:
    plot_ok = "✓" if state.plot_passed else "✗"
    story_ok = "✓" if state.story_passed else "✗"
    words = story_word_count(state.story or "")
    grade = story_flesch_kincaid_grade(state.story or "")
    revisions = f"{state.plot_revisions}p+{state.story_revisions}s"
    preview = " ".join(request.split())
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return (
        f"plot={plot_ok}  story={story_ok}  words={words}  "
        f"grade={grade:.1f}  revisions={revisions}  {preview}"
    )


def write_eval_results(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at": datetime.now(UTC).isoformat(),
        "count": len(records),
        "results": records,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
