"""Phase 3 eval harness: run pipeline on 10 prompts and report metrics.

Not interactive — prompts live in tests/eval/prompts.py. Run:
  uv run pytest tests/test_eval.py -m integration -s
"""

from __future__ import annotations

from typing import Any

import pytest

from agent.agent import run_story
from tests.eval.prompts import EVAL_PROMPTS, EvalPrompt
from tests.eval.report import build_eval_record, format_eval_line


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    EVAL_PROMPTS,
    ids=[p.id for p in EVAL_PROMPTS],
)
def test_eval_prompt(
    case: EvalPrompt,
    require_openai_api_key: None,
    eval_json_records: list[dict[str, Any]],
) -> None:
    """Run one eval prompt through the pipeline and print a summary line (-s)."""
    state = run_story(case.request)
    line = format_eval_line(state, case.request)
    print(f"[{case.category}] {line}")

    eval_json_records.append(
        build_eval_record(
            case_id=case.id,
            category=case.category,
            request=case.request,
            state=state,
        )
    )

    assert state.plot, f"{case.id}: plot_writer produced no outline"
    assert state.story, f"{case.id}: story_writer produced no story"
